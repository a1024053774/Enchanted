"""T-257：真实 Codex 在 Stop 返回前收到回执，同 turn 续跑后的结束与回收。

独立期望来自 T-257 票：原生回合结束后 idle、排队消息送达、reclaim 成功；真实工作中
reclaim 必须 worker_working。默认运行完整场景；--revision 用指定版本的产品源码。
只复用既有 scripted_claude 的后台/门禁夹具和 t112_native_api 的 Responses 协议，不启动
Claude，不调用供应商模型，不依赖可选 TS 测试或其他本票新增文件。

顺序不变式（在写测试前确定）：
1. Stop 期间的回执被真实 CLI 并入同 turn 后，其后续 Stop 仍能结束当前提交。
2. 模型请求尚未完成时，不得回收；排队消息不能越过正在工作的回合。
3. 一批显式请求只执行一次；旧 Stop 不能借续跑重复执行它们。
4. 身份/attempt/fence/操作锁/中断检查不因上述顺序而放宽。

失败方式：未命中真实续轮却判绿；把环境失败算缺陷红态；只看模型回复却没有 native
task_complete；结束后 busy/队列卡住/worker_working；真实工作中误回收；请求重复执行。

调度探针：仅在 /tmp 下的产品副本中包装现有 signal 命令，原样运行一次，原样返回 stdout、
stderr、退出码。首次 Stop 在真实 signal 子进程返回后等待测试屏障（最长 4 秒，原有 hook
10 秒超时不改）；测试观察到回执的 turn_submitted 才释放。包装不改 hook 输入、窗格状态、
门禁逻辑或 rollout。hook_release 是向 CLI 返回前的边界时间，后续原生 UPS 证明 CLI 已消费
返回；不把 daemon request_result 冒充 CLI 收到返回的时间。未命中窗口或同 turn 续轮则
INCOMPLETE，绝不自动重试。首次 Stop 是真实 CLI 发出的，不注入假 Stop/task_complete。
这是一个有屏障的真实入口场景；不能代替后续对真实模块做的 0～2 次顺序搜索。
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripted_claude import Fixture, quote, source_tree
from t112_native_api import message_events, request_source, request_tools, shell_item, tool_events

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'gpt-6.1-sol'
TASK = 'demo+T-1'
SIGNAL_POINT = '    const signalCommand = "ELECTRON_RUN_AS_NODE=1 " + shellCommand([process.execPath, cli, "--state", this.root, "signal", "--launch", launch]);'

# Generated only inside this run's fixture. It observes the existing command; it does not implement a signal endpoint.
HOOK_OBSERVER = r'''
import json, os, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
root = Path(__file__).resolve().parent
raw = sys.stdin.buffer.read()
value = json.loads(raw)
trace = root / 'out' / ('hook-' + uuid.uuid4().hex + '.jsonl')
binding = dict(hook=value.get('hook_event_name'), turn=value.get('turn_id'),
               session=value.get('session_id'), stop_hook_active=value.get('stop_hook_active'), pid=os.getpid())
def note(kind, **details):
    with trace.open('a', encoding='utf-8') as out:
        out.write(json.dumps(dict(kind=kind, time=datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                                  monotonic_ns=time.monotonic_ns(), **binding, **details)) + '\n')
note('hook_enter')
result = subprocess.run(sys.argv[1:], input=raw, capture_output=True)
note('signal_returned', code=result.returncode, stdout=result.stdout.decode('utf-8', errors='replace'),
     stderr=result.stderr.decode('utf-8', errors='replace')[-2000:])
hold = False
if value.get('hook_event_name') == 'Stop':
    try:
        with (root / 'out' / 'first-stop').open('x', encoding='utf-8') as out:
            out.write(str(trace))
        hold = True
    except FileExistsError:
        pass
if hold:
    note('stop_held')
    deadline = time.monotonic() + 4
    while not (root / 'out' / 'release-stop').exists() and time.monotonic() < deadline:
        time.sleep(.02)
    note('stop_barrier_finished', released=(root / 'out' / 'release-stop').exists())
note('hook_release', code=result.returncode)
sys.stdout.buffer.write(result.stdout)
sys.stdout.buffer.flush()
sys.stderr.buffer.write(result.stderr)
sys.stderr.buffer.flush()
sys.exit(result.returncode)
'''


class Incomplete(Exception):
    """An environmental or scenario prerequisite is missing, not a defect-specific red result."""


class Defect(Exception):
    """A contract assertion failed after its real-boundary prerequisites were observed."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def text_of(item):
    content = item.get('content', [])
    return content if isinstance(content, str) else '\n'.join(part.get('text', '') for part in content if isinstance(part, dict))


def hook_traces(fixture):
    rows = []
    for path in fixture.out.glob('hook-*.jsonl'):
        # A concurrent hook writer may not yet have finished its last line.
        rows.extend(dict(trace=path.name, **json.loads(line))
                    for line in path.read_text(encoding='utf-8').split('\n')[:-1] if line)
    # Python 3.9/macOS monotonic_ns has a process-local epoch. Keep it for durations
    # within one hook only; UTC orders different hooks, daemon seq orders its events.
    return sorted(rows, key=lambda row: datetime.fromisoformat(row['time']))


def compact_events(events, launch):
    """Keep sequence/clock/identity facts, without whole tool prompts, environments or credentials."""
    rows = []
    plain = {'dispatch_queued', 'paste_intent', 'paste_written', 'turn_submit_intent', 'turn_submitted',
             'dispatch_prompt_claimed', 'pane_idle', 'pane_completion_held', 'stop_not_matched',
             'turn_start_missing', 'native_question_unverified', 'pane_failed', 'stop_transfer_failed',
             'relay_received', 'relay_processed', 'relay_rejected', 'relay_replayed', 'gate_feedback_registered',
             'pane_native_session', 'native_session_bind_failed'}
    for event in events:
        if event.get('launch') != launch:
            continue
        kind, data = event['type'], event['data']
        base = dict(seq=event['seq'], time=event['time'], type=kind)
        if kind == 'native_record':
            record = data.get('record', {})
            payload = record.get('payload', {})
            if record.get('type') == 'event_msg' and payload.get('type') in ('task_started', 'task_complete', 'turn_aborted'):
                rows.append(dict(base, native_time=record.get('timestamp'), native_type=payload['type'],
                                 turn=payload.get('turn_id')))
        elif kind in ('hook_received', 'turn_start_signal', 'turn_end_signal'):
            value = json.loads(data['raw_stdin']) if kind == 'hook_received' else data
            if value.get('hook_event_name') in ('Stop', 'UserPromptSubmit'):
                rows.append(dict(base, hook=value.get('hook_event_name'), turn=value.get('turn_id'),
                                 session=value.get('session_id'), stop_hook_active=value.get('stop_hook_active')))
        elif kind in plain:
            kept = {key: data[key] for key in ('id', 'dispatch', 'submission', 'state', 'source', 'nativeTurn',
                    'native_session', 'key', 'request_id', 'reason', 'error', 'stage') if key in data}
            if 'stop' in data:
                kept['stop_turn'] = data['stop'].get('turn_id')
            if 'result' in data:
                kept['result'] = {key: data['result'].get(key) for key in ('ok', 'error')}
            if kind == 'relay_received':
                kept['command'] = data.get('input', {}).get('command')
            rows.append(dict(base, **kept))
    return rows


def directory_state(path):
    """Do not traverse links to shared dependencies while measuring our own fixture."""
    count = size = 0
    for directory, _, names in os.walk(path, followlinks=False):
        for name in names:
            item = Path(directory) / name
            if not item.is_symlink():
                count += 1
                size += item.stat().st_size
    return dict(path=str(path), files=count, bytes=size, time=now())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, help='必须是不存在的新文件；默认带时间和 UUID，stdout 打印绝对路径')
    parser.add_argument('--revision', help='完整已知坏提交或候选提交；默认当前工作区，复制产品源码后仅加 hook 时间观测')
    parser.add_argument('--codex', default=shutil.which('codex') or str(Path.home() / '.local/bin/codex'))
    args = parser.parse_args()
    summary = (args.summary or ROOT / 'evidence/2026-11-08-batch34/T-257/worker' /
               ('t257-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex + '.json')).resolve()
    if summary.exists():
        parser.error('保留已有证据，请给 --summary 一个新文件：' + str(summary))
    summary.parent.mkdir(parents=True, exist_ok=True)
    # Reserve before starting any process; another run must not overwrite it.
    with summary.open('x', encoding='utf-8') as out:
        out.write(json.dumps(dict(status='INCOMPLETE', phase='starting', started_at=now()), ensure_ascii=False) + '\n')
    print('SUMMARY=' + str(summary), flush=True)
    report = dict(status='INCOMPLETE', started_at=now(), argv=sys.argv, summary=str(summary),
                  revision=args.revision, runtime='真实后台/门禁/交互 Codex；本地 scripted Responses；无 Claude/供应商调用',
                  checks=[], preconditions=[], observed={}, schedule='初始模型屏障 → 首 Stop 返回屏障 → 同 turn 模型屏障 → 排队消息',
                  limitations=['这是受控真实入口顺序，未执行隔离模块的 0～2 次事件搜索。'])
    fixture = server = None
    launch = attempt = None
    request_dir = None
    initial_release, continuation_release = threading.Event(), threading.Event()
    initial_seen, continuation_seen, marker_seen = threading.Event(), threading.Event(), threading.Event()
    marker = 'T257-queued-' + uuid.uuid4().hex
    api = dict(requests=0, error=None, phases=[])

    def save():
        summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')

    def require(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        if not condition:
            report.setdefault('preconditions_unmet', []).append(name)
            raise Incomplete(name)
        report['preconditions'].append(name)

    def check(name, condition, detail=None, fatal=False):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)
        if not condition and fatal:
            raise Defect(name)

    def wait(label, predicate, seconds=30, required=True):
        deadline = time.monotonic() + seconds
        while True:
            if api['error']:
                raise Incomplete('scripted Responses: ' + api['error'])
            value = predicate()
            if value:
                return value
            if time.monotonic() >= deadline:
                if required:
                    raise Incomplete('超时：' + label)
                return None
            time.sleep(.1)

    def step(body):
        items = body['input']
        at = max(index for index, item in enumerate(items) if item.get('type') == 'message' and item.get('role') == 'user')
        prompt = text_of(items[at])
        submitted = re.search(r'显式交付：\n(.+)\n', prompt)
        if submitted:
            initial_seen.set()
            if not initial_release.wait(45):
                raise Incomplete('初始模型屏障未释放')
            done = sum(item.get('type') == 'custom_tool_call' for item in items[at + 1:])
            if done < 4:
                cwd = re.search(r'<cwd>([^<]+)</cwd>', json.dumps(body, ensure_ascii=False)).group(1)
                line = submitted.group(1)
                command = line[:line.index("'submit'")] + "'status' '--task' " + quote(TASK)
                api['phases'].append(dict(time=now(), phase='status-tool', index=done))
                return tool_events(shell_item(request_tools(body), command, cwd), body['model'])
            api['phases'].append(dict(time=now(), phase='initial-final'))
            return message_events('四个查询请求已写入，结束本回合。', body['model'])
        if marker in prompt:
            marker_seen.set()
            api['phases'].append(dict(time=now(), phase='queued-marker', marker=marker))
            return message_events('收到排队标记：' + marker, body['model'])
        if '门禁回执（' in prompt:
            continuation_seen.set()
            api['phases'].append(dict(time=now(), phase='receipt-model-held'))
            if not continuation_release.wait(45):
                raise Incomplete('回执续轮模型屏障未释放')
            api['phases'].append(dict(time=now(), phase='receipt-final'))
            return message_events('收到门禁回执。', body['model'])
        raise Incomplete('收到未预期的原生用户消息；不能猜测步骤')

    class Responses(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def do_GET(self):
            payload = json.dumps({'object': 'list', 'data': [{'id': MODEL, 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                api['requests'] += 1
                events = (message_events('{"title":"T257 fixture"}', body['model'])
                          if request_source(body) == 'thread_title' else step(body))
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                for sequence, (name, payload) in enumerate(events):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api['error'] = f'{type(error).__name__}: {error}'
                self.send_error(500)

    try:
        report['source_head'] = subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=ROOT, text=True).strip()
        report['source_worktree_status'] = subprocess.check_output(['git', 'status', '--short', '--', 'workbench/src', 'workbench/terminal'], cwd=ROOT, text=True)
        report['versions'] = dict(codex=subprocess.check_output([args.codex, '--version'], text=True).strip(),
                                  node=subprocess.check_output(['node', '--version'], text=True).strip(), python=sys.version)
        # The existing helper starts only an unused local Messages stub, never a Claude process.
        fixture = Fixture('t257-', lambda body: ('unused', [], 'unused'), source=ROOT)
        report['fixture'] = str(fixture.dir)
        fixture.source = source_tree(fixture.dir, revision=args.revision, copy=True)
        fixture.cli = fixture.source / 'workbench/src/gates/cli.ts'
        observer = fixture.dir / 'hook_observer.py'
        observer.write_text(HOOK_OBSERVER, encoding='utf-8')
        panes = fixture.source / 'workbench/src/panes.ts'
        source = panes.read_text(encoding='utf-8')
        require('hook_probe_anchor_unique', source.count(SIGNAL_POINT) == 1)
        instrumented = SIGNAL_POINT.replace('[process.execPath, cli,', '[' + json.dumps(sys.executable) + ', ' + json.dumps(str(observer)) + ', process.execPath, cli,')
        panes.write_text(source.replace(SIGNAL_POINT, instrumented), encoding='utf-8')
        report['instrumentation'] = dict(file='workbench/src/panes.ts', before=SIGNAL_POINT, after=instrumented,
                                         boundary='只包装启动时的 hook 命令；不改生产仓库、门禁或状态处理')
        home = fixture.home / '.codex'
        (home / 'rules').mkdir(parents=True)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        (home / 'config.toml').write_text('model_provider="t257"\ncli_auth_credentials_store="file"\n'
            f'[projects.{json.dumps(str(fixture.repo.resolve()))}]\ntrust_level="trusted"\n'
            '[model_providers.t257]\nname="T257 local fixture"\n'
            f'base_url="http://127.0.0.1:{server.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
        (home / 'rules/default.rules').write_text('prefix_rule(pattern=["git","add"],decision="allow")\n'
                                                'prefix_rule(pattern=["git","commit"],decision="allow")\n', encoding='utf-8')
        # /usr/bin/false cannot start Claude. Production daemon_start detaches its child (transport.ts: detached:true).
        fixture.start('/usr/bin/false', {'README.md': 'T257 isolated fixture\n',
                      'check.py': 'from pathlib import Path\nassert Path("README.md").read_text() == "T257 isolated fixture\\n"\n'},
                      dict(codex_bin=args.codex, codex_home=str(home)))
        fixture.card('T-1', 'answer.txt', 'check.py', executor=dict(cli='Codex', model=MODEL, effort='high'))
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write', model=MODEL, effort='high')
        require('real_gate_dispatched', dispatched.get('ok'), {key: dispatched.get(key) for key in ('ok', 'error', 'details')})
        attempt = dispatched['attempt']
        thread = attempt['thread_id']
        launch = next(row['id'] for row in fixture.request('sidebar_snapshot')['agents']
                      if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        record = fixture.request('launch_show', fixture.operator, launch=launch)['launch']
        request_dir = Path(record['request_dir']).resolve()
        report['launch'] = {key: record.get(key) for key in ('id', 'cli_version', 'argv', 'executable_path', 'code_revision', 'created_at')}
        report['attempt'] = {key: attempt.get(key) for key in ('attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id')}
        events = lambda: fixture.request('orchestration_events', task=TASK)['events']
        timeline = lambda: compact_events(events(), launch)
        pane = lambda: fixture.request('pane_status', thread=thread)
        reclaim = lambda: fixture.request('reclaim', fixture.terminal, task='T-1', attempt=attempt['attempt_id'])
        wait('原生模型请求处于等待中', initial_seen.is_set)
        info = fixture.request('pane_process_info', thread=thread)
        current = fixture.request('status', fixture.operator, task=TASK)['task']['current_attempt']
        require('native_identity_bound', info.get('leader') and not info.get('failed') and
                (current.get('runtime_identity') or {}).get('native_session'),
                dict(leader=info.get('leader'), failed=info.get('failed'), identity=current.get('runtime_identity')))
        working = reclaim()
        report['observed']['reclaim_initial_working'] = {key: working.get(key) for key in ('ok', 'error', 'details')}
        check('working_reclaim_refused', working.get('ok') is False and working.get('error') == 'worker_working',
              report['observed']['reclaim_initial_working'], fatal=True)
        initial_release.set()

        held = wait('首个真实 Stop signal 已返回，hook 仍在屏障',
                    lambda: next((row for row in hook_traces(fixture) if row['kind'] == 'stop_held'), None), 90)
        require('first_stop_is_native_root', held.get('turn') and held.get('stop_hook_active') is False, held)
        first_turn, first_session = held['turn'], held['session']
        initial_processed = [row for row in timeline() if row['type'] == 'relay_processed']
        require('four_real_status_receipts', len(initial_processed) == 4 and
                all(row.get('result', {}).get('ok') is True for row in initial_processed), initial_processed)

        def receipt_submitted():
            rows = timeline()
            gates = {row['id'] for row in rows if row['type'] == 'dispatch_queued' and row.get('source') == 'gate'}
            return next((row for row in rows if row['type'] == 'turn_submitted' and row.get('dispatch') in gates), None)

        pasted = wait('Stop 返回窗口内提交真实门禁回执', receipt_submitted, 4)
        report['observed']['receipt_submitted'] = pasted
        (fixture.out / 'release-stop').write_text('release\n', encoding='utf-8')
        returned = wait('首个 Stop 的返回边界', lambda: next((row for row in hook_traces(fixture)
                        if row['trace'] == held['trace'] and row['kind'] == 'hook_release'), None))
        barrier = next(row for row in hook_traces(fixture) if row['trace'] == held['trace'] and row['kind'] == 'stop_barrier_finished')
        require('receipt_before_stop_return', barrier['released'] and
                datetime.fromisoformat(pasted['time'].replace('Z', '+00:00')) < datetime.fromisoformat(returned['time']),
                dict(held=held, pasted=pasted, returned=returned, barrier=barrier))
        wait('回执进入真实 Codex 模型请求', continuation_seen.is_set)
        starts = [row for row in timeline() if row['type'] == 'turn_start_signal']
        require('receipt_ups_same_turn', len(starts) == 2 and all(row.get('turn') == first_turn and
                row.get('session') == first_session for row in starts), starts)
        native_starts = [row for row in timeline() if row.get('native_type') == 'task_started']
        require('continuation_without_new_task_started', len(native_starts) == 1 and native_starts[0]['turn'] == first_turn, native_starts)
        report['observed']['continuation_held_pane'] = pane()
        continuing = reclaim()
        report['observed']['reclaim_continuation_working'] = {key: continuing.get(key) for key in ('ok', 'error', 'details')}
        check('continuation_working_reclaim_refused', continuing.get('ok') is False and continuing.get('error') == 'worker_working',
              report['observed']['reclaim_continuation_working'], fatal=True)
        queued = fixture.request('pane_dispatch', fixture.operator, thread=thread, body=marker)
        require('followup_queued_through_real_entry', queued.get('ok'), {key: queued.get(key) for key in ('ok', 'error')})
        followup = queued['dispatch']['id']
        queued_pane = pane()
        report['observed']['queued_during_continuation'] = queued_pane
        check('followup_waits_for_working_turn', followup in queued_pane['queued'] and not marker_seen.is_set(),
              dict(dispatch=followup, pane=queued_pane), fatal=True)
        continuation_release.set()
        second = wait('同 turn 第二个真实 Stop', lambda: next((row for row in timeline()
                       if row['type'] == 'turn_end_signal' and row.get('turn') == first_turn and
                       row.get('session') == first_session and row['seq'] > starts[-1]['seq']), None))
        complete = wait('原生 task_complete（不是模型自报）', lambda: next((row for row in timeline()
                         if row.get('native_type') == 'task_complete' and row.get('turn') == first_turn and row['seq'] > second['seq']), None))
        report['observed']['same_turn_stop_and_complete'] = dict(stop=second, complete=complete)
        stops_returned = [row for row in hook_traces(fixture) if row['kind'] == 'hook_release' and
                          row['hook'] == 'Stop' and row['turn'] == first_turn and row['session'] == first_session]
        require('both_native_stop_hooks_returned_zero', len(stops_returned) == 2 and
                all(row['code'] == 0 for row in stops_returned), stops_returned)

        def settled():
            current_pane = pane()
            if not (marker_seen.is_set() and current_pane.get('state') == 'idle' and not current_pane.get('active') and
                    not current_pane.get('queued') and not current_pane.get('writing')):
                return False
            rows = timeline()
            starts = [row for row in rows if row['type'] == 'turn_start_signal' and row['seq'] > second['seq']]
            return starts and any(row.get('native_type') == 'task_complete' and row.get('turn') == starts[-1]['turn'] and
                                  row['seq'] > starts[-1]['seq'] for row in rows)

        settled_result = wait('排队消息原生完成且窗格空闲', settled, 20, required=False)
        rows = timeline()
        last = pane()
        report['observed']['final_pane_before_reclaim'] = last
        check('continuation_stop_reaches_idle', any(row['type'] == 'pane_idle' and row.get('stop_turn') == first_turn and
              row['seq'] > second['seq'] for row in rows), second)
        delivered = [row for row in rows if row['type'] == 'turn_submitted' and row.get('dispatch') == followup]
        check('queued_message_delivered_once', len(delivered) == 1 and marker_seen.is_set(), delivered)
        check('queued_message_native_complete', bool(settled_result))
        check('pane_settled_idle', last.get('state') == 'idle' and not last.get('active') and not last.get('queued') and
              not last.get('failed') and not last.get('interrupted'), last)
        processed = [row for row in rows if row['type'] == 'relay_processed']
        check('requests_processed_once', len(processed) == 4 and len({row.get('key') for row in processed}) == 4 and
              {row.get('key') for row in processed} == {row.get('key') for row in initial_processed}, processed)
        report['timeline'] = rows
        outcome = reclaim()
        report['observed']['reclaim_after_native_complete'] = {key: outcome.get(key) for key in ('ok', 'error', 'details')}
        check('completed_attempt_reclaimed', outcome.get('ok') is True, report['observed']['reclaim_after_native_complete'])
        report['defect_reproduced'] = (last.get('state') == 'busy' and followup in last.get('queued', []) and
                                      outcome.get('error') == 'worker_working' and not delivered)
        if report.get('failed'):
            raise Defect('、'.join(report['failed']))
        report['status'] = 'PASS'
    except Defect as error:
        report.update(status='FAIL', error=str(error))
    except BaseException as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
    finally:
        initial_release.set()
        continuation_release.set()
        if fixture:
            (fixture.out / 'release-stop').touch(exist_ok=True)
            try:
                report['hook_timeline'] = hook_traces(fixture)
                if launch:
                    report['timeline'] = compact_events(fixture.request('orchestration_events', task=TASK)['events'], launch)
                for name in ('daemon.stdout.log', 'daemon.stderr.log'):
                    path = fixture.state / name
                    if path.exists():
                        report.setdefault('daemon_logs', {})[name] = path.read_text(encoding='utf-8', errors='replace')[-6000:]
            except Exception as diagnostic:
                report.setdefault('diagnostic_errors', []).append(str(diagnostic))
            try:
                fixture.stop()
                report['cleanup'] = dict(processes_stopped=True, core=getattr(fixture, 'core_cleanup', None))
            except Exception as cleanup:
                report.setdefault('cleanup_errors', []).append(str(cleanup))
                report['status'] = 'INCOMPLETE'
        if server:
            server.shutdown()
            server.server_close()
        report['api'] = api
        report['finished_at'] = now()
        if api['error']:
            report['status'] = 'INCOMPLETE'
        # Preserve the run state and diagnostics BEFORE deleting this run's temporary files.
        if fixture and not report.get('cleanup_errors'):
            paths = [fixture.dir]
            if request_dir and request_dir.exists():
                if request_dir.parent == Path('/private/tmp') and request_dir.name.startswith('a2a-requests-'):
                    paths.append(request_dir)
                else:
                    report.setdefault('cleanup_errors', []).append('请求目录不满足本次隔离清理范围：' + str(request_dir))
                    report['status'] = 'INCOMPLETE'
            report['cleanup_state_before_removal'] = [directory_state(path) for path in paths]
            save()
            if not report.get('cleanup_errors'):
                for path in paths:
                    try:
                        shutil.rmtree(path)
                        report.setdefault('removed', []).append(str(path))
                    except OSError as cleanup:
                        report.setdefault('cleanup_errors', []).append(str(cleanup))
                        report['status'] = 'INCOMPLETE'
        save()
    print(report['status'] + ': ' + report.get('error', ''), flush=True)
    print('SUMMARY=' + str(summary), flush=True)
    return 0 if report['status'] == 'PASS' else 1 if report['status'] == 'FAIL' else 2


if __name__ == '__main__':
    sys.exit(main())
