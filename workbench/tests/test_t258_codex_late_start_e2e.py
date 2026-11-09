"""T-258：真实 Codex 迟于生产启动期限建立身份，经 Stop 交付并回收。

独立期望：来自 T-258 验收与原始现场，不从产品返回推导答案。工作中 reclaim 必须
worker_working；完成后 issue/submit 各执行一次；失配 session 请求必须拒绝；旧请求
留在目录经下一次真实 Stop 再读时只能返回旧结果。原生完成来自 rollout task_complete，
不是模型文字。父版本 --revision 与候选使用相同入口、原生产 120 秒期限。

调度探针通过隔离 CODEX_HOME 的合法 MCP 配置，让本地 stdio server 暂缓 initialize
响应。真实 CLI、shell 和原始 Enter 保持运行；不发暂停信号、不改生产期限、rollout、
结束信号或 DB。短诊断先证明初始化正在等待、原输入已提交、CLI 仍在前台且没有原生
身份，然后释放等待并验证原任务自行开始。任何前提不成立均为 INCOMPLETE。
每会话 hook 包装只观察并原样转交；不延迟 Stop，不伪造 Stop。

--summary 必须使用新路径。沙箱先验 ps 检查失败时，不启动后台/CLI、不换路径绕过。
仅一个真实 Codex；scripted_claude 是共享夹具库名字，Claude executable 为 false。
无真实 auth：隔离 CODEX_HOME 连接本地 Responses，不接供应商服务。
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
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
from test_t257_codex_stop_continuation_e2e import (Incomplete, Defect, now, text_of, hook_traces,
                                                 compact_events, directory_state, SIGNAL_POINT)

ROOT = Path(__file__).resolve().parents[2]
TASK = 'demo+T-1'
MODEL = 'gpt-6-astra'
# This is an external dependency of the isolated CLI, not a product hook/state injection.
# Only initialize waits; there are no tools, model answers or native events here.
MCP_SERVER = r'''
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
root = Path(sys.argv[1])
def note(kind, **extra):
    with (root / 'mcp.jsonl').open('a', encoding='utf-8') as out:
        out.write(json.dumps(dict(kind=kind, time=datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                                 pid=os.getpid(), **extra)) + '\n')
for line in sys.stdin:
    request = json.loads(line)
    method = request.get('method')
    note('request', method=method)
    if method == 'initialize':
        note('initialize_waiting', protocol=request['params']['protocolVersion'])
        deadline = time.monotonic() + 240
        while not (root / 'mcp-release').exists():
            if time.monotonic() >= deadline:
                note('wait_expired')
                sys.exit(2)
            time.sleep(.05)
        result = dict(protocolVersion=request['params']['protocolVersion'], capabilities={'tools': {}},
                      serverInfo={'name': 't258-startup-barrier', 'version': '1'})
        note('initialize_released')
    elif method == 'tools/list':
        result = {'tools': []}
    elif method == 'ping':
        result = {}
    elif 'id' not in request:
        continue
    else:
        print(json.dumps({'jsonrpc': '2.0', 'id': request['id'],
                          'error': {'code': -32601, 'message': 'Method not found'}}), flush=True)
        continue
    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
'''
OBSERVER = r'''
import json, os, subprocess, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
raw = sys.stdin.buffer.read()
value = json.loads(raw)
trace = Path(__file__).resolve().parent / 'out' / ('hook-' + uuid.uuid4().hex + '.jsonl')
binding = dict(hook=value.get('hook_event_name'), turn=value.get('turn_id'), session=value.get('session_id'),
               stop_hook_active=value.get('stop_hook_active'), pid=os.getpid())
def note(kind, **extra):
    with trace.open('a', encoding='utf-8') as out:
        out.write(json.dumps(dict(kind=kind, time=datetime.now(timezone.utc).isoformat(timespec='microseconds'), **binding, **extra)) + '\n')
note('hook_enter')
result = subprocess.run(sys.argv[1:], input=raw, capture_output=True)
note('hook_release', code=result.returncode, stdout=result.stdout.decode('utf-8', errors='replace'),
     stderr=result.stderr.decode('utf-8', errors='replace')[-2000:])
sys.stdout.buffer.write(result.stdout)
sys.stderr.buffer.write(result.stderr)
sys.exit(result.returncode)
'''


def submit_command(line, request_id, session=None):
    """Keep the real dispatch CLI's full submit shape; change only the named fields."""
    argv = shlex.split(line)
    assert argv[0] == 'ELECTRON_RUN_AS_NODE=1' and 'submit' in argv
    commit = argv.index('--commit') + 1
    assert argv[commit] == 'FULL_COMMIT_SHA'
    if session is not None:
        argv[argv.index('--session') + 1] = session
    argv.extend(['--request-id', request_id])
    return argv[0] + ' ' + ' '.join('"$(git rev-parse HEAD)"' if i == commit else quote(arg)
                                   for i, arg in enumerate(argv[1:], 1))


def diagnostic_events(events):
    """Retain EVERY event type/sequence and structured failure facts, without raw prompts, credentials or reasoning."""
    private = {'env', 'token', 'capability', 'raw_stdin', 'role_text', 'prompt', 'body', 'text', 'content',
               'messages', 'tool_input', 'tool_response', 'last_assistant_message', 'argv', 'shell_argv', 'raw'}
    strings = {'error', 'reason', 'state', 'stage', 'source', 'hook_event_name', 'session_id', 'turn_id', 'native_session',
               'type', 'submission', 'dispatch', 'id', 'thread', 'launch', 'method', 'command', 'path', 'workspace',
               'file', 'nativeTurn', 'received_at', 'at', 'code', 'signal', 'request_id', 'record_type', 'native_type'}

    def safe(value, key=''):
        if key in private:
            return {'omitted': True}
        if isinstance(value, dict):
            return {k: safe(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [safe(v, key) for v in value]
        if isinstance(value, str):
            return value if key in strings else {'string_length': len(value)}
        return value

    rows = []
    for event in events:
        data = event.get('data', {})
        if event['type'] == 'native_record':
            record = data.get('record', {}); payload = record.get('payload', {})
            # Native message/reasoning content never enters the diagnostic report.
            data = dict(file=data.get('file'), offset=data.get('offset'), record_type=record.get('type'),
                        native_type=payload.get('type'), turn_id=payload.get('turn_id'))
        rows.append(dict(seq=event['seq'], time=event['time'], type=event['type'], launch=event.get('launch'),
                         data=safe(data)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision')
    parser.add_argument('--summary', type=Path)
    parser.add_argument('--codex', default=shutil.which('codex') or str(Path.home() / '.local/bin/codex'))
    parser.add_argument('--diagnose-startup', action='store_true', help='先观察 MCP 等待5秒，再释放并确认原任务开始；不运行120秒业务验收')
    parser.add_argument('--dependencies', type=Path, required=True, help='稳定的现有 workbench/node_modules 目录；只读使用，复制源码直接指向其真实路径')
    args = parser.parse_args()
    summary = (args.summary or ROOT / 'evidence/2026-11-08-batch34/T-258/worker' /
               ('e2e-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex + '.json')).resolve()
    summary.parent.mkdir(parents=True, exist_ok=True)
    with summary.open('x', encoding='utf-8') as out:
        out.write(json.dumps(dict(status='INCOMPLETE', phase='starting', started_at=now())) + '\n')
    report = dict(status='INCOMPLETE', started_at=now(), argv=sys.argv, revision=args.revision,
                  checks=[], preconditions=[], observed={},
                  boundary='真实后台/门禁/交互 Codex，本地 Responses；合法 MCP 初始化等待；不启动 Claude')
    fixture = server = None
    launch = request_dir = mcp_release = None
    capture = None
    initial_seen, initial_release = threading.Event(), threading.Event()
    final_seen, final_release = threading.Event(), threading.Event()
    receipt_seen = threading.Event()
    nonce = 't258-' + uuid.uuid4().hex
    api = dict(requests=0, error=None, phases=[], tool_results=[])

    def save():
        summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')

    def require(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        if not condition:
            report.setdefault('preconditions_unmet', []).append(name)
            raise Incomplete(name)
        report['preconditions'].append(name)

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        (report['checks'] if condition else report.setdefault('failed', [])).append(name)

    def wait(label, predicate, seconds=30, required=True, observe=None):
        deadline = time.monotonic() + seconds
        next_observation = time.monotonic()
        while True:
            if api['error']:
                raise Incomplete('Responses: ' + api['error'])
            value = predicate()
            if value:
                return value
            if observe and time.monotonic() >= next_observation:
                observe('waiting')
                next_observation = time.monotonic() + 5
            if time.monotonic() >= deadline:
                if observe:
                    observe('before-timeout')
                if required:
                    raise Incomplete('超时：' + label)
                return None
            time.sleep(.1)

    def step(body):
        items = body['input']
        at = max(i for i, item in enumerate(items) if item.get('type') == 'message' and item.get('role') == 'user')
        prompt = text_of(items[at])
        submitted = re.search(r'显式交付：\n(.+)\n', prompt)
        if submitted:
            initial_seen.set()
            if not initial_release.wait(45):
                raise Incomplete('模型工作屏障未释放')
            if args.diagnose_startup:
                return message_events('启动等待诊断已结束。', body['model'])
            cwd = re.search(r'<cwd>([^<]+)</cwd>', json.dumps(body, ensure_ascii=False)).group(1)
            line = submitted.group(1)
            prefix = line[:line.index("'submit'")]
            # Each Git write is its own native tool command. The commit is read
            # by a separate read-only git invocation in the submit command.
            commands = [
                'python3 -c ' + quote('from pathlib import Path; Path("answer.txt").write_text(' + repr(nonce + '\n') + ', encoding="utf-8")'),
                'git add answer.txt',
                'git commit -m ' + quote('T258 isolated late-start ' + nonce),
                submit_command(line, 'submit-' + nonce),
                prefix + "'issue' '--task' " + quote(TASK) + ' --title ' + quote(nonce) + ' --body ' + quote('T258 isolated issue ' + nonce) + ' --request-id ' + quote('issue-' + nonce),
                submit_command(line, 'foreign-' + nonce, session='wrong-session'),
            ]
            done = sum(item.get('type') == 'custom_tool_call' for item in items[at + 1:])
            api['tool_results'] = [item.get('output') for item in items[at + 1:] if item.get('type') == 'custom_tool_call_output']
            if done < len(commands):
                api['phases'].append(dict(time=now(), phase='tool', index=done))
                return tool_events(shell_item(request_tools(body), commands[done], cwd), body['model'])
            final_seen.set()
            if not final_release.wait(45):
                raise Incomplete('结束前屏障未释放')
            api['phases'].append(dict(time=now(), phase='initial-final'))
            return message_events('已显式请求交付及上报，结束回合。', body['model'])
        if '门禁回执（' in prompt:
            receipt_seen.set()
            api['phases'].append(dict(time=now(), phase='receipt-final'))
            return message_events('收到回执。', body['model'])
        raise Incomplete('原生消息不符合受控协议，不能猜测后续步骤')

    class Responses(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'object': 'list', 'data': [{'id': MODEL, 'object': 'model', 'owned_by': 'fixture'}]}).encode())

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                api['requests'] += 1
                events = (message_events('{"title":"T258 fixture"}', body['model'])
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
        report['source_worktree_status'] = subprocess.check_output(['git', 'status', '--short', '--', 'workbench/src'], cwd=ROOT, text=True)
        # Required for identity-checked cleanup. Stop BEFORE allocating a daemon
        # when the caller's sandbox cannot inspect its own test processes.
        preflight = subprocess.run(['/bin/ps', '-p', str(os.getpid()), '-o', 'pid='], capture_output=True, text=True)
        report['process_preflight'] = dict(argv=preflight.args, exit=preflight.returncode, stdout=preflight.stdout, stderr=preflight.stderr)
        require('process_observer_available', preflight.returncode == 0)
        report['versions'] = dict(codex=subprocess.check_output([args.codex, '--version'], text=True).strip(),
                                  node=subprocess.check_output(['node', '--version'], text=True).strip(), python=sys.version)
        dependencies = args.dependencies.resolve(strict=True)
        require('stable_existing_dependencies', (dependencies / 'effect/package.json').is_file(), str(dependencies))
        report['dependencies'] = str(dependencies)
        fixture = Fixture('t258-', lambda body: ('unused', [], 'unused'), source=ROOT)
        report['fixture'] = str(fixture.dir)
        fixture.source = source_tree(fixture.dir, revision=args.revision, copy=True)
        # source_tree's temporary worker link may disappear when this worker ends.
        # Resolve the caller's stable dependency directory instead; never modify it.
        dependency_link = fixture.source / 'workbench/node_modules'
        require('owned_source_dependency_link', dependency_link.is_symlink())
        dependency_link.unlink()
        dependency_link.symlink_to(dependencies, target_is_directory=True)
        fixture.cli = fixture.source / 'workbench/src/gates/cli.ts'
        observer = fixture.dir / 'hook_observer.py'
        observer.write_text(OBSERVER, encoding='utf-8')
        mcp_server = fixture.dir / 'startup_mcp.py'
        mcp_server.write_text(MCP_SERVER, encoding='utf-8')
        mcp_release = fixture.out / 'mcp-release'
        mcp_trace = fixture.out / 'mcp.jsonl'
        def mcp_rows():
            return [json.loads(line) for line in mcp_trace.read_text(encoding='utf-8').splitlines()] if mcp_trace.exists() else []
        panes = fixture.source / 'workbench/src/panes.ts'
        source = panes.read_text(encoding='utf-8')
        require('probe_anchor_unique', source.count(SIGNAL_POINT) == 1)
        wrapped = SIGNAL_POINT.replace('[process.execPath, cli,', '[' + json.dumps(sys.executable) + ', ' + json.dumps(str(observer)) + ', process.execPath, cli,')
        panes.write_text(source.replace(SIGNAL_POINT, wrapped), encoding='utf-8')
        report['instrumentation'] = [dict(before=SIGNAL_POINT, after=wrapped)]
        home = fixture.home / '.codex'
        (home / 'rules').mkdir(parents=True)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Responses)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        (home / 'config.toml').write_text('model_provider="t258"\ncli_auth_credentials_store="file"\n'
            f'[projects.{json.dumps(str(fixture.repo.resolve()))}]\ntrust_level="trusted"\n'
            '[model_providers.t258]\nname="T258 local fixture"\n'
            f'base_url="http://127.0.0.1:{server.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\n'
            '[mcp_servers.t258_startup]\n'
            f'command={json.dumps(sys.executable)}\nargs={json.dumps([str(mcp_server), str(fixture.out)])}\n'
            'required=true\nstartup_timeout_sec=240\n', encoding='utf-8')
        report['startup_configuration'] = dict(transport='stdio', required=True, startup_timeout_sec=240,
            reference='https://learn.chatgpt.com/docs/extend/mcp?surface=cli',
            scope='仅本测试 CODEX_HOME 的 MCP 等待上限；a2a 生产120秒启动期限不变')
        (home / 'rules/default.rules').write_text('prefix_rule(pattern=["git","add"],decision="allow")\n'
                                                'prefix_rule(pattern=["git","commit"],decision="allow")\n', encoding='utf-8')
        fixture.start('/usr/bin/false', {'README.md': 'T258 isolated fixture\n',
            'check.py': 'from pathlib import Path\nassert Path("answer.txt").read_text() == ' + repr(nonce + '\n') + '\n'},
            dict(codex_bin=args.codex, codex_home=str(home)))
        fixture.card('T-1', 'answer.txt', 'check.py', executor=dict(cli='Codex', model=MODEL, effort='xhigh'))
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write', model=MODEL, effort='xhigh')
        require('gate_dispatched', dispatched.get('ok'), {k: dispatched.get(k) for k in ('ok', 'error', 'details')})
        attempt = dispatched['attempt']; thread = attempt['thread_id']
        launch = next(row['id'] for row in fixture.request('sidebar_snapshot')['agents'] if row['attempt'] == attempt['attempt_id'] and row['role'] == 'worker')
        record = fixture.request('launch_show', fixture.operator, launch=launch)['launch']
        request_dir = Path(record['request_dir']).resolve()
        report['launch'] = {k: record.get(k) for k in ('id', 'cli_version', 'argv', 'executable_path', 'code_revision', 'created_at')}
        report['attempt'] = {k: attempt.get(k) for k in ('attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id')}
        events = lambda: fixture.request('orchestration_events')['events']

        def timeline():
            raw = events()
            rows = compact_events(raw, launch)
            rows.extend(dict(seq=e['seq'], time=e['time'], type=e['type'], data=e['data']) for e in raw if e.get('launch') == launch and
                        e['type'] in ('native_session_unbound', 'native_session_late_start_confirmed'))
            return sorted(rows, key=lambda row: row['seq'])

        pane = lambda: fixture.request('pane_status', thread=thread)
        reclaim = lambda: fixture.request('reclaim', fixture.terminal, task='T-1', attempt=attempt['attempt_id'])
        def capture(label):
            sample = dict(label=label, time=now(), pane_status=pane())
            sample['process_info'] = fixture.request('pane_process_info', thread=thread)
            # comm names only executable paths; never read argv/environment.
            pids = [sample['process_info'].get(key) for key in ('leader', 'shell_pid')]
            pids = [pid for pid in pids if isinstance(pid, int) and pid > 0]
            require('own_cli_and_shell_identified', len(set(pids)) == 2, sample['process_info'])
            argv = ['/bin/ps', '-p', ','.join(map(str, pids)), '-o', 'pid=,ppid=,pgid=,tpgid=,stat=,comm=']
            proc = subprocess.run(argv, capture_output=True, text=True)
            sample['job_control'] = dict(argv=argv, exit=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
            sample['pane_status_after_observer'] = pane()
            sample['mcp'] = mcp_rows()
            report.setdefault('runtime_samples', []).append(sample)
            report['diagnostic_events'] = diagnostic_events(events())
            save()  # Keep failures before cleanup can change shell/CLI lifecycle.
            current = sample['pane_status_after_observer']
            if label != 'before-cleanup' and (
                    not current.get('ok') or current.get('stopped') or current.get('failed') and
                    not str(current['failed']).startswith('native_session_unbound:')):
                raise Incomplete('等待期间出现退出或其他失败；不能把它当作晚启动缺陷红态')
            if label in ('startup-waiting', 'startup-waiting-after-5s', 'waiting', 'before-timeout'):
                process_rows = [line.split(None, 5) for line in proc.stdout.splitlines() if line.strip()]
                require('foreground_processes_alive_' + label, proc.returncode == 0 and len(process_rows) == 2 and
                        all(len(row) == 6 and not any(flag in row[4] for flag in 'TZX') for row in process_rows) and
                        any(int(row[0]) == sample['process_info']['leader'] and row[2] == row[3] for row in process_rows), sample['job_control'])
                require('still_waiting_without_native_identity_' + label, current.get('native_session') is None and
                        current.get('active') and current['active'].get('nativeTurn') is None and
                        not initial_seen.is_set() and not any(row['kind'] == 'initialize_released' for row in sample['mcp']), current)

        wait('真实MCP初始化进入等待', lambda: any(row['kind'] == 'initialize_waiting' for row in mcp_rows()), 30)
        wait('原任务已提交', lambda: any(row['type'] == 'turn_submitted' for row in timeline()), 30)
        capture('startup-waiting')
        wait('初始化等待5秒观察', lambda: False, 5, required=False)
        capture('startup-waiting-after-5s')
        if args.diagnose_startup:
            report['scope'] = '合法MCP启动等待机制诊断；未运行120秒期限、交付、回收业务验收'
            report['observed']['startup_release'] = dict(time=now())
            mcp_release.touch(exist_ok=False)
            wait('释放后原任务自行开始', initial_seen.is_set, 40)
            capture('after-diagnostic-release')
            diagnostic = pane()
            rows = timeline()
            starts = [row for row in rows if row.get('native_type') == 'task_started']
            require('diagnostic_original_task_started_once', len(starts) == 1 and
                    len([row for row in rows if row['type'] == 'turn_submitted']) == 1 and
                    len([row for row in rows if row['type'] == 'dispatch_prompt_claimed']) == 1 and
                    diagnostic.get('native_session') and diagnostic.get('active') and
                    diagnostic['active'].get('nativeTurn') == starts[0]['turn'] and not diagnostic.get('failed'), diagnostic)
            report['diagnostic_mechanism'] = 'PASS'
            raise Incomplete('短诊断命中并释放原任务；完整120秒业务红绿尚未运行')
        deadline = wait('生产启动期限自然触发', lambda: next((e for e in timeline() if e['type'] == 'native_session_unbound'), None), 140,
                        observe=capture)
        before = pane()
        require('timeout_before_native_identity', before.get('native_session') is None and before.get('active') and
                before['active'].get('nativeTurn') is None and str(before.get('failed')).startswith('native_session_unbound:'), before)
        submitted = next(e for e in timeline() if e['type'] == 'turn_submitted')
        elapsed = (datetime.fromisoformat(deadline['time'].replace('Z', '+00:00')) - datetime.fromisoformat(submitted['time'].replace('Z', '+00:00'))).total_seconds()
        require('real_deadline_not_shortened', elapsed >= 120, elapsed)
        report['observed']['before_release'] = before
        report['observed']['startup_release'] = dict(time=now())
        mcp_release.touch(exist_ok=False)
        wait('真实原生模型请求', initial_seen.is_set, 40)
        info = fixture.request('pane_process_info', thread=thread)
        require('late_native_identity', info.get('native_session') and info.get('leader'), {k: info.get(k) for k in ('native_session', 'leader', 'failed')})
        starts = [e for e in timeline() if e.get('native_type') == 'task_started']
        require('native_start_after_deadline', len(starts) == 1 and starts[0]['seq'] > deadline['seq'], starts)
        current_turn = starts[0]['turn']
        working = reclaim()
        report['observed']['working_reclaim'] = {k: working.get(k) for k in ('ok', 'error', 'details')}
        check('working_reclaim_refused', working.get('ok') is False and working.get('error') == 'worker_working', report['observed']['working_reclaim'])
        initial_release.set()
        wait('真实工具步骤结束', final_seen.is_set, 90)
        queued = [json.loads(path.read_text(encoding='utf-8')) for path in request_dir.glob('*.json')]
        report['observed']['request_files_before_stop'] = [{k: row.get(k) for k in ('command', 'request_id', 'session', 'commit')} for row in queued]
        require('three_explicit_request_files', {row.get('request_id') for row in queued} == {'submit-' + nonce, 'issue-' + nonce, 'foreign-' + nonce},
                report['observed']['request_files_before_stop'])
        final_release.set()
        complete = wait('真实原生完成', lambda: next((e for e in timeline() if e.get('native_type') == 'task_complete' and e.get('turn') == current_turn), None), 40)
        report['observed']['native_complete'] = complete
        wait('回执回合空闲', lambda: receipt_seen.is_set() and pane().get('state') == 'idle' and not pane().get('active'), 20, required=False)
        rows = timeline(); last = pane()
        outcomes = [e for e in rows if e['type'] in ('relay_processed', 'relay_rejected')]
        for kind in ('submit', 'issue'):
            found = [e for e in outcomes if e.get('request_id') == kind + '-' + nonce]
            check(kind + '_accepted_once', len(found) == 1 and found[0].get('result', {}).get('ok') is True, found)
        foreign = [e for e in outcomes if e.get('request_id') == 'foreign-' + nonce]
        check('foreign_request_refused_once', len(foreign) == 1 and foreign[0].get('result', {}).get('error') == 'relay_identity_mismatch', foreign)
        check('requests_not_executed_again', len(outcomes) == 3 and len({e.get('key') for e in outcomes}) == 3, outcomes)
        check('real_receipt_stop_reuses_results', receipt_seen.is_set() and all(any(e['type'] == 'relay_replayed' and e.get('key') == old.get('key') for e in rows) for old in outcomes), rows)
        check('idle_after_native_complete', last.get('state') == 'idle' and not last.get('active') and not last.get('failed') and not last.get('queued'), last)
        outcome = reclaim()
        report['observed']['completed_reclaim'] = {k: outcome.get(k) for k in ('ok', 'error', 'details')}
        check('completed_attempt_reclaimed', outcome.get('ok') is True, report['observed']['completed_reclaim'])
        report['defect_reproduced'] = bool(str(last.get('failed')).startswith('native_session_unbound:') and last.get('active') and
                                         complete and not outcome.get('ok'))
        if report.get('failed'):
            raise Defect('、'.join(report['failed']))
        report['status'] = 'PASS'
    except Defect as error:
        report.update(status='FAIL', error=str(error))
    except BaseException as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
    finally:
        initial_release.set(); final_release.set()
        if capture and report['status'] != 'PASS':
            try:
                capture('before-cleanup')
            except Exception as diagnostic:
                report.setdefault('diagnostic_errors', []).append(str(diagnostic))
                report['status'] = 'INCOMPLETE'
        if mcp_release:
            mcp_release.touch(exist_ok=True)
        if fixture:
            try:
                report['hook_timeline'] = hook_traces(fixture)
                report['mcp_timeline'] = mcp_rows()
                if launch:
                    report['timeline'] = timeline()
                    report['diagnostic_events_after_cleanup_started'] = diagnostic_events(events())
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
            server.shutdown(); server.server_close()
        report['api'] = api; report['finished_at'] = now()
        if api['error']:
            report['status'] = 'INCOMPLETE'
        if fixture and not report.get('cleanup_errors'):
            paths = [fixture.dir]
            if request_dir and request_dir.exists():
                if request_dir.parent == Path('/private/tmp') and request_dir.name.startswith('a2a-requests-'):
                    paths.append(request_dir)
                else:
                    report.setdefault('cleanup_errors', []).append('请求目录超出隔离清理范围：' + str(request_dir))
                    report['status'] = 'INCOMPLETE'
            report['cleanup_state_before_removal'] = [directory_state(path) for path in paths]
            save()
            if not report.get('cleanup_errors'):
                for path in paths:
                    shutil.rmtree(path)
                    report.setdefault('removed', []).append(str(path))
        save()
    print(report['status'] + ': ' + report.get('error', ''), flush=True)
    print('SUMMARY=' + str(summary), flush=True)
    return 0 if report['status'] == 'PASS' else 1 if report['status'] == 'FAIL' else 2


if __name__ == '__main__':
    sys.exit(main())
