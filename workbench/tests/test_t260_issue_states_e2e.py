"""T-260：原始问题链 → 真实门禁 → 后台 → Electron 三个显示面。

独立期望见同票 worker/PLAN.md；不运行供应商 CLI，不替换产品 IPC/网络/React。
失败方式：已答/已关仍计数；当前未决被隐藏；旧问题自动关闭/删除；重开沿用旧答复；
15 分钟边界偏移；跨任务/项目计数污染；刷新/重连使历史或计数回退。
默认打印完整 JSON，失败非零。--summary 保存新文件；--gates-only 是明确的局部诊断，
不能当作完整验收。变异只写临时源码副本；不修改 checkout 的产品或旧测试。
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
FIXED_MS = 1794225600000
PROJECT = 't260-demo'
TASK = PROJECT + '+matrix'
OTHER_TASK = PROJECT + '+other'
MUTANTS = {
    'answered-waits': ('src/gates/core.ts',
        '? answer?.from === "user" ? "已答复" : "主控已答"', '? "等你决定"'),
    'count-all': ('src/daemon.ts',
        ".filter((view: any) => view.state === '等你决定').length", '.length'),
    'all-attempts-superseded': ('src/gates/core.ts',
        'if (revised.get(issue.attempt_id)) superseded', 'if (true) superseded'),
}
# Each expected value is written from T-210/T-171, independently of production output.
# Events: report, needs-user, answer by executor/user, delivered, close, reopen.
CASES = [
    ('fresh', 'current', False, [], '待判断'),
    ('fresh-blocking', 'current', True, [], '待判断'),
    ('before-15m', 'current', True, [], '待判断'),
    ('at-15m', 'current', False, [], '等你决定'),
    ('description-only', 'current', True, ['needs-user'], '等你决定'),
    ('controller-answer', 'current', True, ['needs-user', 'executor'], '主控已答'),
    ('user-answer', 'current', True, ['needs-user', 'user'], '已答复'),
    ('controller-delivered', 'current', True, ['needs-user', 'executor', 'delivered'], '主控已答'),
    ('user-delivered', 'current', True, ['needs-user', 'user', 'delivered'], '已送达'),
    ('closed', 'current', True, ['needs-user', 'close'], '已关闭'),
    ('reopened', 'current', True, ['needs-user', 'close', 'reopen'], '等你决定'),
    ('asked-again', 'current', True, ['executor', 'delivered', 'needs-user'], '等你决定'),
    ('answered-reopened', 'current', True, ['user', 'close', 'reopen'], '等你决定'),
    ('old-open', 'revised', True, ['needs-user'], '可能已随修订失效'),
    ('current-open', 'current', True, ['needs-user'], '等你决定'),
    ('ordinary-revoke', 'revoked', True, ['needs-user'], '等你决定'),
    ('system-old', 'revised', True, ['needs-user'], '等你决定'),
    ('old-answered', 'revised', True, ['executor', 'delivered'], '主控已答'),
    ('old-closed', 'revised', True, ['needs-user', 'close'], '已关闭'),
]
EXPECTED = {name: state for name, _, _, _, state in CASES}
EXPECTED["other-task"] = '等你决定'
EXPECTED_WAITING = 9  # 8 in matrix + 1 in the other task; an empty project has zero.


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(argv, env, cwd=None, timeout=60):
    result = subprocess.run(list(map(str, argv)), env=env, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(json.dumps(dict(argv=list(map(str, argv)), exit=result.returncode,
            stdout=result.stdout, stderr=result.stderr), ensure_ascii=False))
    return result.stdout


def wait(label, predicate, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        result = predicate()
        if result:
            return result
        time.sleep(.2)
    raise AssertionError('超时：' + label)


def prepare_source(directory, mutant):
    # Resolve existing dependencies via the common Git directory; never install or write into them.
    common = Path(subprocess.check_output(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                                         cwd=ROOT, text=True).strip()).parent
    dependencies = next((p for p in [ROOT / 'workbench/node_modules', common / 'workbench/node_modules'] if p.is_dir()), None)
    if dependencies is None:
        raise RuntimeError('缺少已有 workbench/node_modules；不自动安装依赖')
    source = directory / 'source/workbench'
    source.mkdir(parents=True)
    for name in ['src', 'app', 'terminal', 'roles', 'hooks']:
        shutil.copytree(ROOT / 'workbench' / name, source / name)
    for name in ['package.json', 'LICENSE.synara']:
        shutil.copy2(ROOT / 'workbench' / name, source / name)
    (source / 'node_modules').symlink_to(dependencies, target_is_directory=True)
    if mutant:
        path, old, new = MUTANTS[mutant]
        target = source / path
        value = target.read_text(encoding='utf-8')
        assert value.count(old) == 1, '变异定位必须唯一：' + mutant
        target.write_text(value.replace(old, new), encoding='utf-8')
    return source, common


def seed(state, source, directory, env, fixed):
    reference = FIXED_MS if fixed else int(time.time() * 1000)
    run(['node', '--input-type=module', '-e',
         f"import {{ A2AGates }} from {json.dumps((source / 'src/gates/core.ts').as_uri())}; new A2AGates({json.dumps(str(state))});"], env)
    attempts = {}
    for label, status, reason in [('current', 'claimed', None), ('revised', 'revoked', 'spec revised'), ('revoked', 'revoked', 'manual revoke')]:
        attempts[label] = dict(task_id=TASK, attempt_id='attempt-' + label, session_id='session-' + label,
            thread_id='thread-' + label, fence=1, spec_rev=1, workspace=str(directory / 'demo'),
            state=status, revocation_reason=reason, reclaimed=False, runtime_identity=None, turn_id=None)
    tasks = [dict(task_id=task, project_id=project, title=task.split('+')[1], repo=str(directory / 'demo'),
        state='ready', spec_rev=2, current_attempt=attempts['current'] if task == TASK else None,
        attachments=[], version=1, fence_counter=1, integration_ref='refs/heads/main')
        for task, project in [(TASK, PROJECT), (OTHER_TASK, PROJECT), ('t260-empty+empty', 't260-empty')]]
    records = []
    for number, (name, attempt, blocking, events, _) in enumerate(CASES, 1):
        age = 60_000
        if name == 'before-15m':
            age = 899_999 if fixed else 600_000
        if name == 'at-15m':
            age = 900_000 if fixed else 1_200_000
        issue = dict(id=name, issue_id=name, schema=1, kind='issue', task_id=TASK,
            attempt_id=attempts[attempt]['attempt_id'], thread_id=attempts[attempt]['thread_id'],
            turn_id='fixture-turn', number=number, title='T260 ' + name, body='原始问题正文：' + name,
            blocking=blocking, **{'from': 'system' if name == 'system-old' else 'worker:thread-' + attempt},
            to='executor', reply_to=None, refs=[], created_at=iso(reference - age))
        records.append(issue)
        for index, action in enumerate(events, 1):
            answer = action in ('executor', 'user')
            records.append({**issue, 'id': name + '-' + str(index), 'kind': 'answer' if answer else 'disposition',
                'from': action if answer else 'user' if action in ('close', 'reopen') else 'executor' if action == 'needs-user' else 'system',
                'reply_to': issue['id'], 'created_at': iso(reference - 30_000 + index),
                'body': '明确答复：' + name if answer else '处置说明不等于答复：' + name,
                **({} if answer else {'action': action, 'reason': '隔离矩阵', 'basis': 'T-210/T-171'}),
                **({'input_id': name + '-input', 'message_id': name + '-message', 'bundle_id': name + '-bundle'}
                   if answer or action == 'delivered' else {})})
    other = {**records[0], 'id': 'other-task', 'issue_id': 'other-task', 'task_id': OTHER_TASK,
             'attempt_id': None, 'title': 'T260 other-task', 'body': '另一任务的未决问题', 'created_at': iso(reference - 1_200_000)}
    records.append(other)
    with sqlite3.connect(state / 'state.sqlite3') as db:
        for task in tasks:
            db.execute('INSERT INTO tasks(id,data) VALUES (?,?)', (task['task_id'], json.dumps(task)))
        for attempt in attempts.values():
            db.execute('INSERT INTO attempts(id,data) VALUES (?,?)', (attempt['attempt_id'], json.dumps(attempt)))
        for row in records:
            db.execute('INSERT INTO issue_records(id,task,thread,data) VALUES (?,?,?,?)',
                       (row['id'], row['task_id'], row['thread_id'], json.dumps(row, ensure_ascii=False)))
    return dict(reference_ms=reference, reference_utc=iso(reference), fixed_clock=fixed,
                tasks=tasks, attempts=attempts, records=records)


class Audit:
    def __init__(self, report):
        self.report = report

    def equal(self, label, actual, expected):
        row = dict(check=label, actual=actual, expected=expected)
        self.report['checks'].append(row)
        if actual != expected:
            self.report['failed'].append(row)

    def gates(self, label, results, expected, raw):
        assert all(result.get('ok') for result in results), results
        views = [view for result in results for view in result['issues']]
        self.equal(label + ':states', {v['issue']['id']: v['state'] for v in views}, expected)
        self.equal(label + ':originals', {v['issue']['id']: v['issue'] for v in views},
                   {r['id']: r for r in raw if r['kind'] == 'issue'})
        observed = {r['id']: r for result in results for r in result['records']}
        self.equal(label + ':retained-records', {r['id']: observed.get(r['id']) for r in raw}, {r['id']: r for r in raw})
        self.equal(label + ':old-answer-invalidated',
                   [v['issue']['id'] for v in views if v['issue']['id'] in ['asked-again', 'answered-reopened'] and v.get('answer')], [])
        return views


class Desktop:
    def __init__(self, directory, source, state, env, report):
        self.directory, self.env, self.report = directory, dict(env), report
        self.process = None
        self.slot = directory / ('a2a-build-t260-' + uuid.uuid4().hex[:8])
        self.env.pop('ELECTRON_RUN_AS_NODE', None)
        built = run(['node', source / 'app/build.mjs', '--slot', self.slot.name[len('a2a-build-'):]], env,
                    cwd=source, timeout=180)
        self.build = json.loads(built.strip().splitlines()[-1])
        assert Path(self.build['out']).parent == self.slot
        binary = run(['node', '-p', "require('electron')"], env, cwd=source).strip()
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            self.port = probe.getsockname()[1]
        self.log = (directory / 'electron.log').open('w', encoding='utf-8')
        self.process = subprocess.Popen([binary, str(ROOT / 'workbench/tests/cdp_launch.cjs'), self.build['main'],
            str(state), str(directory / 'ui'), str(self.port)], env=self.env, stdout=self.log, stderr=subprocess.STDOUT,
            start_new_session=True)

    def evaluate(self, expression):
        if self.process.poll() is not None:
            raise RuntimeError('Electron 已退出：' + str(self.process.returncode))
        return json.loads(run(['node', ROOT / 'workbench/tests/cdp.mjs', str(self.port), 'eval', expression], self.env, timeout=20))

    def ready(self):
        def connected():
            if self.process.poll() is not None:
                raise RuntimeError('Electron 已退出：' + str(self.process.returncode))
            try:
                with socket.create_connection(('127.0.0.1', self.port), timeout=.2):
                    return True
            except (ConnectionRefusedError, TimeoutError):
                return False
        wait('Electron 调试端口', connected)
        wait('项目出现', lambda: self.evaluate(f"!!document.querySelector('[data-project-id=\"{PROJECT}\"]')"))
        self.evaluate(f"document.querySelector('[data-project-id=\"{PROJECT}\"]').click()")
        wait('问题页签', lambda: self.evaluate("!!document.querySelector('[data-issues-tab]')"))
        self.evaluate("document.querySelector('[data-issues-tab]').click()")
        wait('历史卡片出现', lambda: self.evaluate("document.querySelectorAll('.issue-card').length > 0"))

    def snapshot(self):
        return self.evaluate("({cards:[...document.querySelectorAll('.issue-card')].map(c=>({id:c.dataset.issueId,"
            "state:c.dataset.issueState,text:c.innerText,processor:c.querySelector('[data-issue-processor]')?.textContent})),"
            f"project:document.querySelector('[data-project-id=\"{PROJECT}\"] [data-project-issues]')?.dataset.projectIssues ?? '0',"
            "tab:document.querySelector('[data-issues-tab] .tab-needs')?.textContent ?? '0',"
            "error:document.querySelector('.issues-page [role=alert]')?.textContent ?? null})")

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
            self.log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path)
    parser.add_argument('--mutant', choices=MUTANTS)
    parser.add_argument('--gates-only', action='store_true')
    args = parser.parse_args()
    if args.summary and args.summary.exists():
        parser.error('保留既有证据，--summary 必须是新路径')
    report = dict(status='INCOMPLETE', argv=[sys.executable, *sys.argv], mutant=args.mutant,
        scope='gates-only' if args.gates_only else 'gates-daemon-electron', checks=[], failed=[], snapshots={},
        real_cli=False, real_model_calls=0, computer_use='未运行', cdp='未运行')
    audit = Audit(report)
    directory = Path(tempfile.mkdtemp(prefix='t260-', dir=os.environ.get('A2A_REQUEST_DIR', tempfile.gettempdir()))).resolve()
    state = directory / 'live'
    desktop = None
    daemon = None
    env = {k: os.environ[k] for k in ['PATH', 'LANG'] if k in os.environ}
    for name in ['home', 'demo', 'live']:
        (directory / name).mkdir()
    env.update(HOME=str(directory / 'home'), TMPDIR=str(directory), SHELL='/bin/zsh', ELECTRON_RUN_AS_NODE='1',
               A2A_OPERATOR_CREDENTIAL=str(directory / 'operator.json'))
    report['fixture'] = str(directory)

    def request(command, **data):
        identity = json.loads((directory / 'operator.json').read_text(encoding='utf-8'))
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(20)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command=command, **data), identity=identity)) + '\n').encode())
            raw = b''
            while b'\n' not in raw:
                part = connection.recv(65536)
                assert part, '后台断开，结果未知'
                raw += part
        result = json.loads(raw.split(b'\n')[0])
        assert result.get('ok'), (command, result)
        return result

    def snapshot(label, expected, count, raw):
        results = [request('issues', task=task) for task in [TASK, OTHER_TASK]]
        audit.gates(label, results, expected, raw)
        sidebar = request('sidebar_snapshot')
        audit.equal(label + ':backend-counts', {p['project_id']: p['issues_waiting'] for p in sidebar['projects']},
                    {PROJECT: count, 't260-empty': 0})
        # Poll only until actual UI values settle. A timeout records the last observation as a defect.
        end = time.monotonic() + 12
        while True:
            ui = desktop.snapshot()
            states = {c['id']: c['state'] for c in ui['cards']}
            if (states == expected and ui['project'] == str(count) and ui['tab'] == str(count) and not ui['error']) or time.monotonic() >= end:
                break
            time.sleep(.3)
        report['snapshots'][label] = ui
        audit.equal(label + ':ui-states', states, expected)
        audit.equal(label + ':ui-counts', [ui['project'], ui['tab'], ui['error']], [str(count), str(count), None])
        audit.equal(label + ':full-original-text',
            sorted(c['id'] for c in ui['cards'] if any(r['id'] == c['id'] and r['title'] in c['text'] and r['body'] in c['text'] for r in raw)),
            sorted(expected))

    def start_daemon():
        # Keep the same bootstrap credential on normal restart, as an already-open window does.
        nonlocal daemon
        log = (directory / 'daemon.log').open('a', encoding='utf-8')
        daemon = subprocess.Popen(['node', str(source / 'src/daemon.ts'), str(state), '{}'],
            env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        log.close()
        def ready():
            if daemon.poll() is not None:
                raise RuntimeError('后台退出：' + (directory / 'daemon.log').read_text(encoding='utf-8'))
            return (state / 'control.sock').exists()
        wait('后台 socket', ready, 30)
        wait('后台恢复结束', lambda: request('pane_layout').get('recovering') is False)

    try:
        report['revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        source, common = prepare_source(directory, args.mutant)
        env['ENCHANTED_HC_CACHE_DIR'] = str(common.parent / 'hc-cache')
        fixed = seed(directory / 'fixed', source, directory, env, True)
        report['fixed_fixture'] = fixed
        code = f"""import {{ A2AGates }} from {json.dumps((source / 'src/gates/core.ts').as_uri())};
const gate = new A2AGates({json.dumps(str(directory / 'fixed'))}, undefined, () => {FIXED_MS});
const before = await Promise.all({json.dumps([TASK, OTHER_TASK])}.map(task => gate.call({{command:'issues',task}})));
const closed = await gate.call({{command:'disposition',task:{json.dumps(TASK)},issue:'description-only',action:'close',reason:'已核对',basis:'原始记录'}});
const reopened = await gate.call({{command:'disposition',task:{json.dumps(TASK)},issue:'description-only',action:'reopen'}});
console.log(JSON.stringify({{before,closed,reopened}}));"""
        gate_result = json.loads(run(['node', '--input-type=module', '-e', code], env))
        audit.gates('fixed', gate_result['before'], EXPECTED, fixed['records'])
        for phase, expected_state in [('closed', '已关闭'), ('reopened', '等你决定')]:
            result = gate_result[phase]
            assert result.get('ok'), result
            audit.equal('gate-' + phase, next(v['state'] for v in result['issues'] if v['issue']['id'] == 'description-only'), expected_state)
        if args.gates_only:
            report['status'] = 'FAIL' if report['failed'] else 'PASS'
        else:
            live = seed(state, source, directory, env, False)
            report['live_fixture'] = live
            # Explicit private hc endpoint in our fixture, avoiding the runtime's default /private/tmp location.
            write_json(state / 'hc-runtime.json', dict(session='enchanted-' + str(uuid.uuid4()), socket=str(directory / 'core.sock')))
            run(['node', '--input-type=module', '-e',
                f"import {{createOperatorCredential}} from {json.dumps((source / 'src/credentials.ts').as_uri())}; createOperatorCredential({json.dumps(str(state))});"], env)
            start_daemon()
            desktop = Desktop(directory, source, state, env, report)
            desktop.ready()
            report['cdp'] = '真实 Electron，DOM 观察和控件操作'
            snapshot('initial', EXPECTED, EXPECTED_WAITING, live['records'])
            request('disposition', task=TASK, issue='description-only', action='close', reason='已核对处置', basis='隔离原始记录')
            expected = {**EXPECTED, 'description-only': '已关闭'}
            snapshot('gate-closed', expected, 8, live['records'])
            desktop.evaluate("[...document.querySelector('[data-issue-id=\"description-only\"]').querySelectorAll('button')].find(b=>b.textContent==='重新打开').click()")
            snapshot('ui-reopened', EXPECTED, 9, live['records'])
            # Real user answer entry, to a deliberately absent historical thread: forwarded, never called delivered.
            answered = request('answer_issue', task=OTHER_TASK, issue='other-task', answer='隔离审计答复：已有证据，无需用户继续选择。')
            report['answer_entry'] = answered
            expected = {**EXPECTED, 'other-task': '已转交'}
            snapshot('user-answer-forwarded', expected, 8, live['records'])
            audit.equal('user-answer-recorded', [v['answer']['from'] for v in answered['issues'] if v['issue']['id'] == 'other-task'], ['user'])
            audit.equal('user-answer-input', [v['form'] for v in answered['user_inputs'] if v['reply_to'] == 'other-task'], ['answer'])
            desktop.evaluate('location.reload(); true')
            desktop.ready()
            snapshot('refresh', expected, 8, live['records'])
            request('daemon_stop')
            daemon.wait(timeout=20)
            wait('离线错误出现', lambda: desktop.snapshot()['error'])
            start_daemon()
            snapshot('reconnect', expected, 8, live['records'])
            # Settle every still-pending item via the gate; zero is checked as well as nonzero counts.
            for issue, state_name in expected.items():
                if state_name == '等你决定':
                    request('disposition', task=TASK, issue=issue, action='close', reason='矩阵确认关闭', basis='隔离测试记录')
                    expected[issue] = '已关闭'
            snapshot('zero-waiting-history-retained', expected, 0, live['records'])
            report['status'] = 'FAIL' if report['failed'] else 'PASS'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['status'] = 'INCOMPLETE'
    finally:
        cleanup_errors = []
        if desktop:
            try:
                desktop.stop()
            except Exception as error:
                cleanup_errors.append('Electron: ' + str(error))
        if daemon:
            try:
                if daemon.poll() is None:
                    daemon.terminate()
                    daemon.wait(timeout=20)
            except Exception as error:
                cleanup_errors.append('daemon: ' + str(error))
        # No ps fallback: stop only the private core named by this fixture's manifest.
        binaries = list(state.glob('hc/herdr-core-*/herdr-core'))
        if binaries and (state / 'hc-runtime.json').exists():
            try:
                identity = json.loads((state / 'hc-runtime.json').read_text(encoding='utf-8'))
                private_env = dict(env, HC_SESSION=identity['session'], HC_SOCKET=identity['socket'],
                    XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'))
                report['core_stop'] = run([binaries[0], 'server', 'stop'], private_env, timeout=20)
            except Exception as error:
                cleanup_errors.append('private core: ' + str(error))
        for name in ['daemon.log', 'electron.log']:
            if (directory / name).exists():
                report[name] = (directory / name).read_text(encoding='utf-8', errors='replace')[-20000:]
        files = [p for p in directory.rglob('*') if p.is_file() and not p.is_symlink() and 'node_modules' not in p.parts]
        report['cleanup'] = dict(directory=str(directory), time=iso(int(time.time() * 1000)), files=len(files),
            bytes=sum(p.stat().st_size for p in files), result=report['status'], errors=cleanup_errors)
        if cleanup_errors:
            report['status'] = 'INCOMPLETE'
        # Persist the text inventory before deleting large owned fixtures.
        if args.summary:
            write_json(args.summary, report)
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
        if not cleanup_errors:
            shutil.rmtree(directory)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
