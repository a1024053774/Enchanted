"""T-262：无模型的真实 Electron / IPC / 后台读取路径测试。

失败方式（实现前确定）：双区筛选不一致；漏掉单一来源会话；同名主控混淆；
乱序及同时间记录不稳定；刷新/切项目被旧响应覆盖；错误被当空态；原文、人工
介入或完整回执丢失；长文本撑破窄窗；筛选控件不能选择；详情键盘无法展开。
原始记录直接写入本次隔离后台的库，期望来自下列场景；不启动任何 agent CLI，
不替换 window.a2a 或 DOM 数据。--revision 运行父版，--summary 独占写入证据。
筛选走真实 select 的标准表单选择与 input/change；原生选择器键盘由主控另做
Computer Use 验收。本脚本保留 details 的真实 Enter，不把表单选择称作键盘证明。
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import socketserver
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
J = lambda value: json.dumps(value, ensure_ascii=False)
LONG = '原文 <script>不执行</script> & "引号"\n' + '很长的中文和<>特殊字符' * 100
# Deliberately out of timestamp order, with equal-time entries in reverse ID order.
INPUTS = [
    ('i-old', '2026-11-01T10:00:00Z', 'alpha', 'T-1', 'worker-one', '较早输入', True),
    ('i-z', '2026-11-03T10:00:00Z', 'alpha', 'T-1', 'worker-one', LONG, True),
    ('i-ctrl2', '2026-11-04T10:00:00Z', 'alpha', None, 'control-two', '第二个主控', False),
    ('i-b', '2026-11-06T10:00:00Z', 'beta', 'T-1', 'worker-beta', '另一个项目', True),
    ('i-a', '2026-11-03T10:00:00Z', 'alpha', 'T-1', 'worker-one', '\r', True),
    ('i-ctrl1', '2026-11-02T10:00:00Z', 'alpha', None, 'control-one', '第一个主控', False),
    ('i-two', '2026-11-05T10:00:00Z', 'alpha', 'T-2', 'worker-two', '第二个任务', False),
    ('i-loose', '2026-11-02T11:00:00Z', 'alpha', 'T-1', 'loose-thread', '无 launch 输入', False),
]
RECEIPTS = [
    ('r-z', '2026-11-03T12:00:00Z', 'alpha', 'T-1', 'worker-one'),
    ('r-old', '2026-11-01T12:00:00Z', 'alpha', 'T-1', 'worker-one'),
    ('r-only', '2026-11-05T12:00:00Z', 'alpha', 'T-3', 'receipt-only'),
    ('r-two', '2026-11-04T12:00:00Z', 'alpha', 'T-2', 'worker-two'),
    ('r-b', '2026-11-06T12:00:00Z', 'beta', 'T-1', 'worker-beta'),
    ('r-a', '2026-11-03T12:00:00Z', 'alpha', 'T-1', 'worker-one'),
]
# Distinct identities also remain distinct when their first eight characters match.
LAUNCHES = {name: '11111111-' + name for name in
            ['worker-one', 'worker-two', 'worker-beta', 'receipt-only', 'control-one', 'control-two']}
MUTANTS = {
    'no-sort': ('].sort(newestFirst);', '];'),
    'receipt-task': ('const inTask = (entry: Entry) => !task || (entry.task ?? projectScope) === task;',
                     'const inTask = (entry: Entry) => Boolean(entry.receipt) || !task || (entry.task ?? projectScope) === task;'),
    'ignore-session': ('inTask(entry) && (!session || entry.session === session)', 'inTask(entry)'),
    'no-full-receipt': ('JSON.stringify(receipt.result, null, 2)', 'JSON.stringify({ truncated: true }, null, 2)'),
}


def ordered(rows):
    return [r[0] for r in sorted(rows, key=lambda r: (-datetime.fromisoformat(r[1].replace('Z', '+00:00')).timestamp(), r[0]))]


def run(argv, env=None, timeout=60):
    result = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} exit={result.returncode}: {result.stderr[-3000:]} {result.stdout[-1000:]}')
    return result.stdout


class BusinessFailure(AssertionError):
    """A reachable product page violates a scenario assertion, not a setup error."""


class ReadProxy:
    """Forward real daemon replies unchanged; hold/drop selected replies to test I/O order.

    No fake records or gate outcomes. The daemon finishes its real SQLite read before
    a fault affects delivery. Only this fixture's socket names are changed.
    """
    def __init__(self, state):
        self.plans, self.events, self.errors = [], [], []
        self.lock = threading.Lock()
        original = state / 'control.sock'
        self.backend = state / 'backend.sock'
        original.rename(self.backend)
        owner = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                try:
                    line = self.rfile.readline()
                    if not line:
                        return
                    request = json.loads(line)['input']
                    plan = None
                    with owner.lock:
                        for index, item in enumerate(owner.plans):
                            if item['command'] == request.get('command') and item['project'] == request.get('project'):
                                plan = owner.plans.pop(index)
                                break
                    with socket.socket(socket.AF_UNIX) as upstream:
                        upstream.settimeout(30)
                        upstream.connect(str(owner.backend))
                        upstream.sendall(line)
                        response = upstream.makefile('rb').readline()
                    if plan:
                        owner.events.append(dict(command=plan['command'], project=plan['project'], mode=plan['mode'],
                                                 real_reply_ok=json.loads(response).get('ok')))
                        plan['captured'].set()
                        if plan['mode'] == 'drop':
                            return  # Natural transport rejection; never a fabricated JSON result.
                        if not plan['release'].wait(30):
                            raise TimeoutError('受控延迟未释放')
                    self.wfile.write(response)
                except Exception as error:
                    owner.errors.append(f'{type(error).__name__}: {error}')

        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads = True

        self.server = Server(str(original), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def next(self, command, project, mode):
        plan = dict(command=command, project=project, mode=mode, captured=threading.Event(), release=threading.Event())
        with self.lock:
            self.plans.append(plan)
        return plan

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)


DRIVER = r"""
const [port, method, params] = process.argv.slice(2);
const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const page = pages.find(p => p.type === 'page');
if (!page) throw new Error('no page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = fail; });
const timer = setTimeout(() => { throw new Error('CDP deadline'); }, 15000);
const result = await new Promise((ok, fail) => {
  ws.onmessage = event => { const m = JSON.parse(event.data); if (m.id === 1) m.error ? fail(Error(JSON.stringify(m.error))) : ok(m.result); };
  ws.send(JSON.stringify({ id: 1, method, params: JSON.parse(params) }));
});
clearTimeout(timer); ws.close(); console.log(JSON.stringify(result));
"""


LAUNCHER = r"""
// Owned by this fixture. Product run() returns its actual BrowserWindow.
const { app } = require('electron');
const { appendFileSync } = require('node:fs');
const { pathToFileURL } = require('node:url');
const [main, state, userData, port, observations] = process.argv.slice(2);
app.commandLine.appendSwitch('remote-debugging-port', port);
// Keep entry-module evaluation detached from Electron's ready event, as in cdp_launch.cjs.
import(pathToFileURL(main).href).then(({ run }) => run({ state, userData })).then(window => {
  const record = stage => appendFileSync(observations, JSON.stringify({ stage,
    time: new Date().toISOString(), pid: process.pid, window_id: window.id,
    bounds: window.getBounds(), content_size: window.getContentSize() }) + '\n');
  window.setBounds({ width: 900, height: 700 }, false);
  record('configured');
  window.on('resize', () => record('resize'));
}).catch(error => { console.error(error); app.exit(1); });
"""


class Fixture:
    def __init__(self, report, diagnostics_file=None):
        self.report = report
        # Managed workers may only write to their own request directory. Outside a managed
        # worker, use a short private root: macOS's default TMPDIR exceeds the socket limit.
        self.root = Path(tempfile.mkdtemp(prefix='t262-', dir=os.environ.get('A2A_REQUEST_DIR') or '/private/tmp')).resolve()
        report['fixture'] = str(self.root)
        self.diagnostics_file = diagnostics_file or self.root.with_suffix('.diagnostics.jsonl')
        self.diagnostics_written = False
        report['diagnostics_file'] = str(self.diagnostics_file)
        self.source = self.root / 'source'
        self.state = self.root / 's'
        self.process = None
        self.log = None
        self.running = False
        self.proxy = None
        self.phase = 'prepare'
        self.env = {key: os.environ[key] for key in ['PATH', 'LANG'] if key in os.environ}

    def prepare(self, revision, mutant=None):
        # Keep setup outside __init__ so finally can preserve evidence even if setup fails.
        self.state.mkdir()
        for name in ['home', 'tmp']:
            (self.root / name).mkdir()
        sockets = dict(control=str(self.state / 'control.sock'), core=str(self.root / 'core.sock'),
                       holder=str(self.root / 'core.holder.12345678.sock'),
                       terminal=str(self.root / 'tmp/enchanted-123456/terminal.sock'))
        self.report['socket_bytes'] = {name: len(path.encode('utf-8')) for name, path in sockets.items()}
        if max(self.report['socket_bytes'].values()) > 103:
            raise RuntimeError(f'夹具根目录过长；不切换 worker 写入边界：{self.report["socket_bytes"]}')
        common = Path(run(['git', 'rev-parse', '--git-common-dir']).strip())
        if not common.is_absolute():
            common = ROOT / common
        deps = ROOT / 'workbench/node_modules'
        if not deps.exists():
            deps = common.resolve().parent / 'workbench/node_modules'
        if not deps.exists():
            raise RuntimeError('缺少项目现有 node_modules；不安装新依赖')
        package = deps / 'electron'
        # Reading path.txt avoids electron/index.js's implicit download if the binary is absent.
        self.electron = package / 'dist' / (package / 'path.txt').read_text(encoding='utf-8').strip()
        if not self.electron.is_file():
            raise RuntimeError('缺少项目既有 Electron 二进制；不自动下载')
        self.report['versions'] = dict(node=run(['node', '--version']).strip(), python=sys.version.split()[0],
                                       electron=json.loads((package / 'package.json').read_text(encoding='utf-8'))['version'])
        self.env.update(HOME=str(self.root / 'home'), TMPDIR=str(self.root / 'tmp'),
                        A2A_OPERATOR_CREDENTIAL=str(self.root / 'operator.json'),
                        ENCHANTED_HC_CACHE_DIR=str(common.resolve().parent.parent / 'hc-cache'))
        parts = ['app', 'src', 'roles', 'hooks', 'terminal']
        for part in parts:
            shutil.copytree(ROOT / 'workbench' / part, self.source / 'workbench' / part, symlinks=True)
        for name in ['package.json', 'LICENSE.synara']:
            shutil.copy2(ROOT / 'workbench' / name, self.source / 'workbench' / name)
        (self.source / 'workbench/node_modules').symlink_to(deps, target_is_directory=True)
        if revision:
            # Only this task's behavior varies; backend/launcher stays at the specified
            # base contract. No mutation touches the gate worktree or shared outputs.
            for name in ['RecordsPage.tsx', 'records.css']:
                data = run(['git', 'show', f'{revision}:workbench/app/{name}'])
                (self.source / 'workbench/app' / name).write_text(data, encoding='utf-8')
        if mutant:
            page = self.source / 'workbench/app/RecordsPage.tsx'
            before, after = MUTANTS[mutant]
            data = page.read_text(encoding='utf-8')
            if data.count(before) != 1:
                raise RuntimeError('变异目标必须恰好出现一次：' + mutant)
            page.write_text(data.replace(before, after), encoding='utf-8')
        self.driver = self.root / 'cdp.mjs'
        self.driver.write_text(DRIVER, encoding='utf-8')
        self.launcher = self.root / 't262-launch.cjs'
        self.launcher.write_text(LAUNCHER, encoding='utf-8')
        self.window_observations = self.root / 'window-bounds.jsonl'
        self.cli = self.source / 'workbench/src/gates/cli.ts'
        # Seed an isolated private-core identity so every runtime file is under this
        # fixture's writable root (the production runtime also supports saved identity).
        (self.state / 'hc-runtime.json').write_text(J(dict(session='enchanted-' + str(uuid.uuid4()),
                                                          socket=str(self.root / 'core.sock'))), encoding='utf-8')

    def cli_run(self, *args):
        return json.loads(run(['node', str(self.cli), '--state', str(self.state), *args], self.env))

    def start(self):
        self.phase = 'daemon_start'
        self.cli_run('daemon_start')
        self.running = True
        self.proxy = ReadProxy(self.state)
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            for project in ['alpha', 'beta', 'empty']:
                repo = self.root / project
                repo.mkdir()
                db.execute('INSERT INTO orchestration_events(time,type,data) VALUES (?,?,?)',
                           ('2026-11-01T00:00:00Z', 'project_opened', J(dict(project_id=project, repo=str(repo)))))
        self.phase = 'build'
        built = run(['node', str(self.source / 'workbench/app/build.mjs'), '--slot', 'records'], self.env, 180)
        self.report['build'] = built.strip().splitlines()[-1]
        build = json.loads(self.report['build'])
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            self.port = probe.getsockname()[1]
        argv = [str(self.electron), str(self.launcher), build['main'],
                str(self.state), str(self.root / 'ui'), str(self.port), str(self.window_observations)]
        # Keep Electron in GUI mode with isolated data. The fixture-owned launcher
        # sets the real window bounds before any scenario action; it starts no model.
        electron_env = {key: value for key, value in self.env.items() if key != 'ELECTRON_RUN_AS_NODE'}
        self.report['electron_start'] = dict(argv=argv, cwd=str(ROOT), start_new_session=True,
                                             env={key: electron_env.get(key) for key in ['HOME', 'TMPDIR', 'ELECTRON_RUN_AS_NODE']})
        self.phase = 'electron_start'
        self.log = (self.root / 'electron.log').open('w', encoding='utf-8')
        self.process = subprocess.Popen(argv, cwd=ROOT, env=electron_env,
                                        stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
        self.report['electron_start']['pid'] = self.process.pid
        self.phase = 'electron_ready'
        deadline = time.monotonic() + 20
        while not self.window_observations.exists():
            if self.process.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError(f'真实窗口尺寸未就绪：returncode={self.process.poll()}')
            time.sleep(.15)
        self.read_window_bounds('scenario_start')
        self.until("!!document.querySelector('[data-project-id=\"alpha\"]')")
        self.phase = 'seed_records'
        # These are historical input/receipt records, not live dispatched tasks. Seed them
        # after the empty project window opens: startupView otherwise tries to restore a
        # synthetic worker whose task was never dispatched. All reads still use the real DB.
        self.seed_records()
        self.phase = 'scenario'

    def seed_records(self):
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            for name, identity in LAUNCHES.items():
                project = 'beta' if name.endswith('beta') else 'alpha'
                task = None if name.startswith('control') else project + '+' + ('T-2' if name == 'worker-two' else 'T-3' if name == 'receipt-only' else 'T-1')
                data = dict(id=identity, thread=name, role='controller' if task is None else 'worker',
                            preset='executor' if task is None else None, project=project, task=task, attempt=None,
                            created_at='2026-11-01T00:00:00Z', cli='Codex')
                db.execute('INSERT INTO launch_records VALUES (?,?,?,?)', (identity, task, None, J(data)))
            for row in INPUTS:
                self.input(db, row)
            for row in RECEIPTS:
                self.receipt(db, row)

    def receipt(self, db, row):
        key, stamp, project, task, name = row
        result = dict(ok=key != 'r-two', marker=key, special=LONG,
                      task=dict(name=task, state='submitted', candidate_commit='a' * 40))
        db.execute('INSERT INTO relay_requests VALUES (?,?,?,?,?,?,?)',
                   (key, LAUNCHES[name], project + '+' + task, None, key, J(dict(command='submit')), stamp))
        db.execute('INSERT INTO relay_results VALUES (?,?,?)', (key, J(result), stamp))

    def input(self, db, row):
        identity, stamp, project, task, thread, text, intervention = row
        task = project + '+' + task if task else None
        data = dict(id=identity, created_at=stamp, form='message', channel='terminal-window', certainty='observed',
                    text=text, target=dict(project=project, task=task, attempt=None, thread=thread), source_ref={})
        db.execute('INSERT INTO user_inputs VALUES (?,?,?,?)', (identity, task, None, J(data)))
        if intervention:
            db.execute('INSERT INTO events(time,task,type,details) VALUES (?,?,?,?)',
                       (stamp, task, 'human_intervention', J(dict(input_id=identity))))

    def cdp(self, method, **params):
        return json.loads(run(['node', str(self.driver), str(self.port), method, J(params)]))

    def read_window_bounds(self, stage):
        observations = [json.loads(line) for line in self.window_observations.read_text(encoding='utf-8').splitlines()]
        actual = observations[-1]
        self.report.setdefault('native_window', []).append(dict(stage=stage, observations=observations))
        if (actual['bounds']['width'], actual['bounds']['height']) != (900, 700):
            raise RuntimeError(f'真实窗口尺寸未达到夹具前提 900x700：{actual}')
        if actual['pid'] != self.process.pid or min(actual['content_size']) <= 0:
            raise RuntimeError(f'真实窗口身份或内容尺寸无效：{actual}')

    def evaluate(self, expression):
        result = self.cdp('Runtime.evaluate', expression=expression, awaitPromise=True, returnByValue=True)
        if result.get('exceptionDetails'):
            raise AssertionError(result['exceptionDetails'])
        return result['result'].get('value')

    def until(self, expression, timeout=20, business=False):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None:
                raise RuntimeError(f'Electron 提前退出：phase={self.phase}, returncode={self.process.returncode}')
            try:
                value = self.evaluate(expression)
                last = None
                if value:
                    return value
            except (RuntimeError, AssertionError) as error:
                last = str(error)
            time.sleep(.15)
        message = f'等待页面超时：{expression}: {last}'
        if business and last is None:
            raise BusinessFailure(message)
        raise RuntimeError(message)

    def click(self, selector):
        rect = self.evaluate(f"(() => {{const e=document.querySelector({J(selector)}); if(!e) return null; e.scrollIntoView({{block:'center'}}); const r=e.getBoundingClientRect(); return {{x:r.x+r.width/2,y:r.y+r.height/2}};}})()")
        if not rect:
            raise BusinessFailure(f'页面没有操作目标：{selector}')
        for kind in ['mousePressed', 'mouseReleased']:
            self.cdp('Input.dispatchMouseEvent', type=kind, button='left', clickCount=1, **rect)

    def key(self, key, code):
        # CDP distinguishes virtual Windows codes from platform native codes. Do not
        # send Windows values as macOS native values. Non-text keys use rawKeyDown;
        # Enter needs its text, and physical code is explicit (CDP Input protocol).
        text = '\r' if key == 'Enter' else ' ' if key == ' ' else ''
        params = dict(key=key, code='Space' if key == ' ' else key, windowsVirtualKeyCode=code)
        commands = {'ArrowDown': ['moveDown'], 'ArrowUp': ['moveUp'], 'Home': ['scrollToBeginningOfDocument']}
        self.cdp('Input.dispatchKeyEvent', type='keyDown' if text else 'rawKeyDown',
                 text=text, unmodifiedText=text, commands=commands.get(key, []), **params)
        self.cdp('Input.dispatchKeyEvent', type='keyUp', **params)

    def choose(self, index, value):
        selects = self.evaluate("[...document.querySelectorAll('.record-filter select')].map(s=>[...s.options].map(o=>o.value))")
        if index >= len(selects) or value not in selects[index]:
            raise BusinessFailure(f'筛选选项缺失：{value}，实际 {selects}')
        self.until(f"document.querySelectorAll('.record-filter select')[{index}]?.disabled === false")
        # selectOption-equivalent form interaction: change only the real control, then
        # let its normal input/change handlers update React. No state/API/row injection.
        # This is deliberately not evidence of native popup keyboard operation.
        interaction = self.evaluate(f"""(() => {{
          const select = document.querySelectorAll('.record-filter select')[{index}];
          const before = select.value, events = [];
          const observe = event => events.push({{type:event.type, trusted:event.isTrusted,
            value:event.target.value, index:event.target.selectedIndex}});
          select.scrollIntoView({{block:'center'}});
          select.focus();
          for (const type of ['input','change']) select.addEventListener(type, observe);
          try {{
            select.value = {J(value)};
            select.dispatchEvent(new Event('input', {{bubbles:true, composed:true}}));
            select.dispatchEvent(new Event('change', {{bubbles:true}}));
            return {{before, value:select.value, events}};
          }} finally {{
            for (const type of ['input','change']) select.removeEventListener(type, observe);
          }}
        }})()""")
        self.report.setdefault('form_selections', []).append(dict(index=index, target=value,
            method='selectOption-equivalent', native_keyboard=False, **interaction))
        self.settled()
        self.until(f"document.querySelectorAll('.record-filter select')[{index}].value === {J(value)}", timeout=5)

    def button(self, text):
        buttons = self.evaluate("[...document.querySelectorAll('.record-filter button')].map(b=>({text:b.textContent,disabled:b.disabled}))")
        index = next((i for i, button in enumerate(buttons) if button['text'] == text), None)
        if index is None:
            raise BusinessFailure(f'没有按钮：{text}')
        self.until(f"!document.querySelectorAll('.record-filter button')[{index}].disabled")
        self.click(f'.record-filter button:nth-of-type({index + 1})')

    def session(self, name):
        values = self.evaluate("[...document.querySelectorAll('.record-filter select')[1].options].map(o=>o.value)")
        identity = LAUNCHES.get(name)
        value = next((v for v in values if v in [name, 'thread:' + name, identity, 'launch:' + str(identity)]), None)
        if value is None:
            raise BusinessFailure(f'缺少夹具会话：{name}，实际 {values}')
        self.choose(1, value)

    def settled(self):
        self.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')

    def rows(self):
        return self.evaluate("({inputs:[...document.querySelectorAll('[data-input-id]')].map(e=>e.dataset.inputId),receipts:[...document.querySelectorAll('[data-receipt-key]')].map(e=>e.dataset.receiptKey)})")

    def diagnostics(self, stage):
        if self.log and not self.log.closed:
            self.log.flush()
        snapshot = dict(phase=self.phase, returncode=self.process.poll() if self.process else None,
                        process_started=self.process is not None, logs={})
        for path in [self.root / 'electron.log', self.root / 'window-bounds.jsonl',
                     self.state / 'daemon.stderr.log', self.state / 'daemon.stdout.log']:
            if path.exists():
                data = path.read_bytes()
                snapshot['logs'][path.name] = dict(bytes=len(data), truncated=len(data) > 16000,
                                                  tail=data[-16000:].decode('utf-8', errors='replace'))
        self.report.setdefault('diagnostics', {})[stage] = snapshot
        # Persist before removing the fixture, including when Electron died before CDP
        # was reachable. Each run has a new sidecar; earlier failure evidence is immutable.
        self.diagnostics_file.parent.mkdir(parents=True, exist_ok=True)
        with self.diagnostics_file.open('a' if self.diagnostics_written else 'x', encoding='utf-8') as saved:
            saved.write(J(dict(stage=stage, time=datetime.now(timezone.utc).isoformat(),
                              fixture=str(self.root), electron_start=self.report.get('electron_start'),
                              error=self.report.get('error'), **snapshot)) + '\n')
        self.diagnostics_written = True

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(10)
        if self.log:
            self.log.close()
        if self.running:
            self.cli_run('daemon_stop')
        if self.proxy:
            self.proxy.stop()
            self.report['transport'] = dict(events=self.proxy.events, errors=self.proxy.errors)
        if self.phase != 'prepare':
            # This invokes ps: only the controller runs the real test while the worker
            # sandbox refuses it. Preparation/diagnostic checks never enter this branch.
            sys.path.insert(0, str(ROOT / 'workbench/tests'))
            from scripted_claude import stop_fixture_core
            self.report['core_cleanup'] = stop_fixture_core(self.state, self.root, self.env)
        self.diagnostics('after_cleanup')
        files = [p for p in self.root.rglob('*') if p.is_file() and not p.is_symlink() and 'node_modules' not in p.parts]
        self.report['cleanup'] = dict(directory=str(self.root), files=len(files), bytes=sum(p.stat().st_size for p in files),
                                      time=datetime.now(timezone.utc).isoformat(), result='自有进程已停止，随后删除夹具和构建缓存')
        shutil.rmtree(self.root)
        self.report['cleanup']['removed'] = not self.root.exists()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=MUTANTS)
    parser.add_argument('--summary', type=Path)
    parser.add_argument('--smoke', action='store_true', help='仅运行排序/任务筛选 Tracer bullet；默认运行完整场景')
    args = parser.parse_args()
    diagnostics_file = args.summary.with_suffix('.diagnostics.jsonl') if args.summary else None
    if args.summary and (args.summary.exists() or diagnostics_file.exists()):
        parser.error('保留既有证据，请使用新 summary 路径')
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, smoke=args.smoke,
                  base=run(['git', 'rev-parse', 'HEAD']).strip(), checks=[], failed=[], real_model_turns=0)
    fixture = None

    def check(name, expected, actual):
        item = dict(name=name, expected=expected, actual=actual)
        report['checks' if expected == actual else 'failed'].append(item)

    inputs, receipts = list(INPUTS), list(RECEIPTS)

    def check_rows(name, project='alpha', task='*', session='*'):
        def relevant(row):
            return row[2] == project and (task == '*' or row[3] == task) and (session == '*' or row[4] == session)
        fixture.settled()
        check(name, dict(inputs=ordered([r for r in inputs if relevant(r)]),
                         receipts=ordered([r for r in receipts if relevant(r)])), fixture.rows())

    def full_scenario():
        fixture.session('worker-one')
        check_rows('同一 launch 的输入与回执一起筛选', task='T-1', session='worker-one')
        fixture.session('loose-thread')
        check_rows('无 launch 输入保留独立 thread 会话', task='T-1', session='loose-thread')
        check('只有输入的会话显示回执空态', True,
              '当前筛选下没有门禁回执' in fixture.evaluate("document.querySelector('.receipts').innerText"))
        fixture.choose(0, 'alpha+T-3')
        fixture.session('receipt-only')
        check_rows('只有回执的任务和会话可选择', task='T-3', session='receipt-only')
        check('只有回执的会话显示输入空态', True,
              '当前筛选下没有用户输入' in fixture.evaluate("document.querySelector('.input-records').innerText"))
        fixture.button('清空筛选')
        check_rows('清空筛选恢复两个完整记录区')
        values = fixture.evaluate("[...document.querySelectorAll('.record-filter select')[1].options].filter(o=>o.value).map(o=>({value:o.value,text:o.textContent,group:o.parentElement.label}))")
        check('合并两种来源得到六个会话', 6, len(values))
        controllers = [v for v in values if any(identity in v['value'] for identity in [LAUNCHES['control-one'], LAUNCHES['control-two']])]
        check('同名主控具有不同可读标签', True, len(controllers) == 2 and len({v['text'] for v in controllers}) == 2
              and all('执行主控' in v['text'] and '首条记录' in v['text'] and v['group'] == '项目级 · 执行主控' for v in controllers))
        for name in ['control-one', 'control-two']:
            fixture.session(name)
            check_rows('按身份选择同名主控 ' + name, session=name)
        fixture.choose(0, ':project:')
        check_rows('项目级与全部任务具有不同选项', task=None)
        fixture.choose(0, 'alpha+T-2')
        fixture.session('worker-two')
        check_rows('切换第二个任务清除旧会话且双区匹配', task='T-2', session='worker-two')
        fixture.button('清空筛选')

        # Existing T-133/T-179 behavior: input provenance and complete gate results.
        marked = fixture.evaluate("[...document.querySelectorAll('[data-input-id][data-intervention]')].map(e=>e.dataset.inputId).sort()")
        check('人工介入标记与原始事件一致', sorted(r[0] for r in inputs if r[2] == 'alpha' and r[6]), marked)
        fixture.evaluate("document.querySelector('[data-input-id=\"i-z\"] summary').focus()")
        fixture.key('Enter', 13)
        check('键盘展开完整原文', True, fixture.evaluate("document.querySelector('[data-input-id=\"i-z\"] details').open"))
        check('长原文与特殊字符原样保留', LONG, fixture.evaluate("document.querySelector('[data-input-id=\"i-z\"] .record-original').textContent"))
        check('控制字符按键可读', True, '回车' in fixture.evaluate("document.querySelector('[data-input-id=\"i-a\"]').innerText"))
        fixture.click('[data-receipt-key="r-z"] summary')
        check('点击展开完整回执', True, fixture.evaluate("document.querySelector('[data-receipt-key=\"r-z\"] details').open"))
        full = fixture.evaluate("document.querySelector('[data-receipt-key=\"r-z\"] .receipt-full').textContent")
        with sqlite3.connect(fixture.state / 'state.sqlite3') as db:
            original = json.loads(db.execute('SELECT data FROM relay_results WHERE key=?', ('r-z',)).fetchone()[0])
        check('完整回执与原始存储一致', original, json.loads(full))
        check('特殊字符不生成 HTML 元素', 0, fixture.evaluate("document.querySelectorAll('.user-input-page script').length"))
        # The real BrowserWindow has been 900x700 since the scenario started.
        fixture.read_window_bounds('narrow_layout')
        fixture.settled()
        size = fixture.evaluate("(() => {const e=document.querySelector('.user-input-page');return {client:e.clientWidth,scroll:e.scrollWidth};})()")
        check('窄窗口长原文及回执不撑破页面', True, size['client'] > 0 and size['scroll'] <= size['client'] + 1)
        fixture.evaluate("document.querySelector('[data-input-id=\"i-z\"] summary').focus()")
        fixture.key('Enter', 13)
        check('键盘可收起详情', False, fixture.evaluate("document.querySelector('[data-input-id=\"i-z\"] details').open"))
        check('键盘焦点可见', True, fixture.evaluate("getComputedStyle(document.activeElement).outlineStyle !== 'none'"))

        fixture.choose(0, 'alpha+T-1')
        fixture.session('worker-one')
        nonce = uuid.uuid4().hex[:8]
        new_input = ('i-fresh-' + nonce, '2026-11-08T10:00:00Z', 'alpha', 'T-1', 'worker-one', '刷新哨兵 ' + nonce, False)
        new_receipt = ('r-fresh-' + nonce, '2026-11-08T11:00:00Z', 'alpha', 'T-1', 'worker-one')
        with sqlite3.connect(fixture.state / 'state.sqlite3') as db:
            fixture.input(db, new_input)
            fixture.receipt(db, new_receipt)
        inputs.append(new_input)
        receipts.append(new_receipt)
        fixture.button('刷新')
        fixture.until(f"!!document.querySelector('[data-input-id=\"{new_input[0]}\"]') && !!document.querySelector('[data-receipt-key=\"{new_receipt[0]}\"]')", business=True)
        check_rows('手动刷新读到新原始记录并保留会话筛选', task='T-1', session='worker-one')

        # Delay a genuine alpha read across a project switch; its late response must
        # never appear in beta. The queue is consumed by the ordinary polling request.
        delayed = fixture.proxy.next('user_input_records', 'alpha', 'hold')
        if not delayed['captured'].wait(10):
            raise RuntimeError('未捕获真实 alpha 读取')
        try:
            check('等待异步结果时明确显示刷新状态', True,
                  '正在刷新' in fixture.evaluate("document.querySelector('.records-count').innerText"))
            fixture.click('[data-project-id="beta"]')
            fixture.until("!!document.querySelector('[data-input-id=\"i-b\"]')", business=True)
            check_rows('切项目不保留 alpha 筛选或记录', project='beta')
        finally:
            delayed['release'].set()
        time.sleep(.4)
        check_rows('旧项目迟到响应不能覆盖新项目', project='beta')
        fixture.click('[data-project-id="alpha"]')
        fixture.until("document.querySelectorAll('[data-input-id]').length === 8", business=True)
        check_rows('切回项目获取完整新记录')
        check('切项目重置任务和会话', ['', ''], fixture.evaluate("[...document.querySelectorAll('.record-filter select')].map(s=>s.value)"))

        fixture.choose(0, 'alpha+T-1')
        fixture.session('worker-one')
        dropped = fixture.proxy.next('relay_receipts', 'alpha', 'drop')
        if not dropped['captured'].wait(10):
            raise RuntimeError('未捕获真实回执读取')
        fixture.until("!!document.querySelector('.user-input-page [role=alert]')", business=True)
        check('读取错误不展示部分双区数据', dict(inputs=[], receipts=[]), fixture.rows())
        check('回执读取错误明确说明来源', True,
              '门禁回执读取失败' in fixture.evaluate("document.querySelector('.user-input-page [role=alert]').innerText"))
        check('错误不冒充空结果', False,
              '没有用户输入' in fixture.evaluate("document.querySelector('.user-input-page').innerText"))
        fixture.button('刷新')
        fixture.until("!document.querySelector('.user-input-page [role=alert]') && document.querySelectorAll('[data-input-id]').length === 4", business=True)
        check_rows('读取恢复后保留正确筛选', task='T-1', session='worker-one')
        fixture.click('[data-project-id="empty"]')
        fixture.until("document.querySelector('.input-records')?.innerText.includes('这个项目还没有用户输入')", business=True)
        check('空项目两个分类都有提示', True,
              '这个项目还没有门禁回执' in fixture.evaluate("document.querySelector('.receipts').innerText"))
        check_rows('空项目没有其他项目的数据', project='empty')
        fixture.click('.free-terminals')
        fixture.until("document.querySelector('.user-input-page')?.innerText.includes('先在左侧选一个项目')", business=True)
        check('清空项目不残留记录', dict(inputs=[], receipts=[]), fixture.rows())
        check('真实传输故障计划都已执行且无代理异常', [], fixture.proxy.errors)

    try:
        fixture = Fixture(report, diagnostics_file)
        fixture.prepare(args.revision, args.mutant)
        fixture.start()
        fixture.click('[data-project-id="alpha"]')
        fixture.click('[data-records-tab]')
        fixture.until("document.querySelectorAll('[data-input-id]').length === 7 && document.querySelectorAll('[data-receipt-key]').length === 5", business=True)
        check('每区最新在前，同时间按记录身份稳定排列',
              dict(inputs=ordered([r for r in INPUTS if r[2] == 'alpha']), receipts=ordered([r for r in RECEIPTS if r[2] == 'alpha'])), fixture.rows())
        fixture.choose(0, 'alpha+T-1')
        check('任务筛选同时约束双区', dict(inputs=ordered([r for r in INPUTS if r[2:4] == ('alpha', 'T-1')]),
                                           receipts=ordered([r for r in RECEIPTS if r[2:4] == ('alpha', 'T-1')])), fixture.rows())
        if not args.smoke:
            full_scenario()
        report['status'] = 'PASS' if not report['failed'] else 'FAIL'
    except BusinessFailure as error:
        report['failed'].append(dict(name='页面场景断言', detail=str(error)))
        report['status'] = 'FAIL'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['status'] = 'INCOMPLETE'
    finally:
        if fixture:
            fixture.diagnostics('before_cleanup')
            try:
                fixture.stop()
            except Exception as error:
                report['cleanup_error'] = f'{type(error).__name__}: {error}'
                report['status'] = 'INCOMPLETE'
                fixture.diagnostics('cleanup_failed')
        output = J(report)
        if args.summary:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            with args.summary.open('x', encoding='utf-8') as saved:
                saved.write(output + '\n')
        print(output)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
