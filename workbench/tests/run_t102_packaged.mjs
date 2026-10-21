// Launch the installed application through LaunchServices. CDP observes the real
// renderer and sends DOM clicks / keyboard events; it does not import main.run,
// replace IPC replies, or start the daemon on the application's behalf.
import assert from 'node:assert/strict';
import { cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { execFileSync, spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

const out = resolve(process.argv[2]);
assert.ok(out.startsWith('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-102/'));
assert.notEqual(statSync('/Volumes/WD-Elements').dev, statSync('/Volumes').dev);
mkdirSync(out); // Caller chooses a new run. Failures remain available.
const fixture = mkdtempSync('/private/tmp/a2at102-');
const state = join(fixture, 'state'), userData = join(fixture, 'ui');
const app = '/Applications/Enchanted.app', executable = join(app, 'Contents/MacOS/Enchanted');
const resources = join(app, 'Contents/Resources/app');
const report = { task: 'T-102', attempt: 'a2', status: 'INCOMPLETE', argv: process.argv,
  app, fixture, checks: [], commands: [], screenshots: [], model_calls: 0 };
const env = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
  !key.startsWith('A2A_') && !key.startsWith('GIT_CONFIG_') && !['NODE_OPTIONS', 'NODE_PATH', 'ELECTRON_RUN_AS_NODE'].includes(key)));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(read, description, seconds = 30) {
  const end = Date.now() + seconds * 1000;
  while (Date.now() < end) { const value = await read(); if (value) return value; await sleep(100); }
  throw new Error(description);
}
function command(argv, extra = {}) {
  const record = { argv }; report.commands.push(record);
  try { const result = execFileSync(argv[0], argv.slice(1), { env, encoding: 'utf8', timeout: 30_000, ...extra }); record.exit = 0; return result; }
  catch (error) { record.exit = error.status; record.stderr = String(error.stderr); throw error; }
}
function call(name, ...fields) {
  const connection = JSON.parse(readFileSync(join(state, 'desktop-connection.json'), 'utf8'));
  return JSON.parse(command([executable, join(resources, 'src/gates/cli.ts'), '--state', state, name, ...fields],
    { env: { ...env, ELECTRON_RUN_AS_NODE: '1', A2A_OPERATOR_CREDENTIAL: connection.credential } }));
}
function alive(pid) {
  try { process.kill(pid, 0); return true; } catch (error) { if (error.code === 'ESRCH') return false; throw error; }
}
class CDP {
  constructor(ws) { this.ws = ws; this.next = 0; this.pending = new Map();
    ws.addEventListener('message', event => { const message = JSON.parse(event.data); if (!message.id) return;
      const entry = this.pending.get(message.id); if (!entry) return;
      clearTimeout(entry.timer); this.pending.delete(message.id);
      message.error ? entry.reject(new Error(JSON.stringify(message.error))) : entry.resolve(message.result);
    });
    ws.addEventListener('close', () => { for (const entry of this.pending.values()) { clearTimeout(entry.timer); entry.reject(new Error('CDP closed')); } this.pending.clear(); });
  }
  send(method, params = {}) { return new Promise((resolve, reject) => {
    const id = ++this.next;
    const timer = setTimeout(() => { this.pending.delete(id); reject(new Error('CDP deadline: ' + method)); }, 10_000);
    this.pending.set(id, { resolve, reject, timer }); this.ws.send(JSON.stringify({ id, method, params }));
  }); }
  async evaluate(expression) {
    const result = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
  async capture(name) {
    await this.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');
    const { data } = await this.send('Page.captureScreenshot');
    const path = join(out, name + '.png'); writeFileSync(path, Buffer.from(data, 'base64'), { flag: 'wx' }); report.screenshots.push(path);
  }
}
let view, opener, daemon, epoch = 0;
async function open() {
  // 0 asks Chromium for a free loopback debugger port. No debugging on normal double-click.
  const log = join(out, `gui-${++epoch}.stderr.log`);
  const argv = ['/usr/bin/open', '-n', '-W', '--stdout', join(out, `gui-${epoch}.stdout.log`), '--stderr', log,
    app, '--args', '--state', state, '--user-data', userData, '--remote-debugging-port=0'];
  report.commands.push({ argv });
  opener = spawn(argv[0], argv.slice(1), { env, detached: true, stdio: 'ignore' });
  opener.unref();
  const port = await until(() => existsSync(log) && /DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)\//.exec(readFileSync(log, 'utf8'))?.[1], '打包应用没有打开调试端点');
  const target = await until(async () => {
    const response = await fetch(`http://127.0.0.1:${port}/json/list`);
    return (await response.json()).find(target => target.type === 'page' && target.url.startsWith('file://' + resources));
  }, '没有打包产物的 renderer');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.addEventListener('open', resolve, { once: true }); ws.addEventListener('error', reject, { once: true }); });
  view = new CDP(ws);
  await until(() => view.evaluate('document.readyState === "complete" && !!window.a2a && !!document.querySelector(\'nav[aria-busy="false"]\')'), '选择页未就绪');
  assert.equal(await view.evaluate('typeof window.require'), 'undefined');
  return view;
}
const inspect = () => view.evaluate(`({text:document.body.innerText, tasks:[...document.querySelectorAll('[data-task-option]')].map(n=>({id:n.dataset.taskOption,current:n.getAttribute('aria-current')})), alerts:[...document.querySelectorAll('[role="alert"]')].map(n=>n.innerText), panes:[...document.querySelectorAll('section.pane')].map(n=>({launch:n.dataset.launchId,role:n.dataset.role,input:n.dataset.inputEnabled,text:n.innerText}))})`);
async function click(expression) { await view.evaluate(`(()=>{const n=${expression};if(!n||n.disabled)throw new Error('UI target unavailable');n.click()})()`); }
const button = name => `[...document.querySelectorAll('button')].find(n=>n.textContent===${JSON.stringify(name)})`;
async function select(task) {
  await click(`document.querySelector('[data-task-option="${task}"]')`);
  await until(async () => (await inspect()).tasks.some(item => item.id === task && item.current === 'page'), '任务选择未完成');
}
async function closeView() {
  const closed = new Promise(resolve => view.ws.addEventListener('close', resolve, { once: true }));
  await view.send('Page.close'); await closed;
  await until(() => !alive(opener.pid), 'open -W 尚未确认界面退出');
  view = null;
}
try {
  assert.ok(existsSync(executable));
  command(['/usr/bin/codesign', '--verify', '--deep', '--strict', app]);
  report.runtime = JSON.parse(command([executable, '-p', 'JSON.stringify(process.versions)'], { env: { ...env, ELECTRON_RUN_AS_NODE: '1' } }));
  assert.equal(report.runtime.electron, '43.4.1');
  await open();
  const initial = await inspect();
  assert.ok(initial.text.includes('还没有项目') && initial.alerts.length === 0);
  await view.capture('01-no-task-picker');
  const started = call('daemon_status'); assert.ok(started.ok); daemon = started.pid;
  const descriptor = join(state, 'desktop-connection.json');
  const credential = JSON.parse(readFileSync(descriptor, 'utf8')).credential;
  assert.ok(credential.startsWith(state + '/desktop-operator-'));
  for (const path of [descriptor, credential]) assert.equal(statSync(path).mode & 0o077, 0, '桌面凭据／描述文件必须私有');
  const processInfo = command(['/bin/ps', '-p', String(daemon), '-o', 'pid=,ppid=,pgid=,command=']);
  report.daemon_process = processInfo;
  assert.equal(Number(processInfo.trim().split(/\s+/)[2]), daemon, '后台必须拥有独立进程组');
  assert.ok(processInfo.includes(resources + '/src/daemon.ts'));
  assert.ok(started.helper.includes('/build/Release/spawn-helper'));
  assert.ok((statSync(started.helper).mode & 0o111) !== 0);
  report.checks.push('无 --task 打开选择页；应用自行启动打包后台；node-pty 使用重建产物');

  for (const project of ['alpha', 'beta']) {
    const repo = join(fixture, '中文项目 ' + project); mkdirSync(repo);
    command(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo]);
    writeFileSync(join(repo, 'criterion.py'), 'assert True\n');
    command(['git', '-C', repo, 'add', 'criterion.py']);
    command(['git', '-C', repo, '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', '-c', 'user.name=T102 fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'T102 fixture']);
    const task = project + '-task', card = join(fixture, task + '.json');
    writeFileSync(card, JSON.stringify({ id: task, source: null, goal: '打包应用验收', non_goals: ['不调用模型'],
      paths: { allow: ['criterion.py'], deny: [] }, oracle_paths: ['criterion.py'], completion_conditions: [{ argv: ['python3', 'criterion.py'] }],
      red_commands: [], task_type: '前端界面', repair_target: null, complexity: 'M', executor: { cli: 'Codex', model: 'gpt-6.1-sol', effort: 'xhigh' }, base_commit: null, writer: null }));
    assert.ok(call('card_save', '--task', task, '--card', card, '--expected-version', '0').ok);
    assert.ok(call('create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', project, '--title', '打包验收 ' + task).ok);
  }
  await click(button('刷新列表'));
  await until(async () => (await inspect()).tasks.length === 2, '项目／任务列表未加载');
  await view.capture('02-projects-tasks');
  await select('alpha-task'); await click(button('新建终端'));
  await until(async () => (await inspect()).panes.some(pane => pane.role === 'shell' && pane.input === 'true'), 'zsh 未启动');
  const pane = (await inspect()).panes.find(pane => pane.role === 'shell');
  const record = call('launch_show', '--launch', pane.launch).launch;
  const shell = call('pane_status', '--thread', record.thread).shell_pid;
  report.shell = { launch: pane.launch, pid: shell, cwd: record.worktree };
  assert.equal(record.project, 'alpha'); assert.equal(record.task, null); assert.equal(record.attempt, null);
  const nonce = 'T102-' + randomUUID(), proof = join(fixture, 'shell-proof.txt');
  const text = `printf '%s\\n' '${nonce}'; pwd; print -r -- T102_ZSH=$ZSH_VERSION; printf '%s\\n' '${nonce}' > '${proof}'`;
  await view.evaluate(`(()=>{const textarea=document.querySelector('section.pane[data-role="shell"] .xterm-helper-textarea');textarea.focus();const data=new DataTransfer();data.setData('text/plain',${JSON.stringify(text)});textarea.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true}))})()`);
  await view.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r' });
  await view.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await until(() => existsSync(proof) && readFileSync(proof, 'utf8') === nonce + '\n', '经 xterm 输入的 zsh 命令未执行');
  const output = Buffer.from(call('pane_output', '--launch', pane.launch, '--offset', '0', '--max-bytes', '65536').data_base64, 'base64').toString();
  assert.ok(output.includes(record.worktree) && output.includes('T102_ZSH=5.') && output.includes(nonce));
  writeFileSync(join(out, 'shell-output.txt'), output);
  await view.capture('03-zsh-command');
  await select('beta-task'); assert.equal((await inspect()).panes.some(p=>p.role==='shell'), false);
  await select('alpha-task'); await until(async () => (await inspect()).panes.some(p=>p.launch===pane.launch), '原项目终端未回来');
  report.checks.push('真实选择两个项目／任务；点击新建终端；经 xterm／键盘执行 zsh；跨项目保留终端');
  await closeView();
  assert.equal(call('daemon_status').pid, daemon); assert.ok(alive(shell));
  report.checks.push('关闭整个界面进程后，同一后台和 zsh 仍活动');
  await open(); await select('alpha-task');
  await until(async () => (await inspect()).panes.some(p=>p.launch===pane.launch && p.input==='true'), '重开后未接回原终端');
  assert.equal(call('daemon_status').pid, daemon);
  await view.capture('04-reopened-same-shell');
  report.checks.push('重新经 LaunchServices 打开打包产物；选择任务接回同一终端和后台');
  await closeView();
  assert.ok(call('shell_close', '--launch', pane.launch).ok);
  assert.ok(call('daemon_stop').ok);
  await until(() => !existsSync(join(state,'control.sock')) && !alive(daemon) && !alive(shell), '后台／shell 退出未确认');
  daemon = null;
  report.cleanup_complete = true;
  // Credentials are never included in the archived fixture.
  for (const name of readdirSync(state).filter(name=>/^desktop-operator-.*\.json$/.test(name))) rmSync(join(state,name));
  const archive = join(out, 'fixture'); cpSync(fixture, archive, { recursive: true, verbatimSymlinks: true });
  function inventory(root) { let files=0,bytes=0;for(const name of readdirSync(root,{withFileTypes:true})){const path=join(root,name.name);if(name.isDirectory()){const child=inventory(path);files+=child.files;bytes+=child.bytes;}else{files++;bytes+=lstatSync(path).size;}}return {files,bytes}; }
  report.fixture_inventory = inventory(fixture); assert.deepEqual(inventory(archive),report.fixture_inventory);
  rmSync(fixture,{recursive:true});
  report.status = 'PASS';
} catch (error) {
  report.error = String(error); report.stack = error.stack;
  // Keep the isolated process identities and state. A controller can inspect and
  // close them; do not guess at or kill another daemon after an unknown result.
  report.cleanup_complete = false; report.remaining_daemon = daemon;
} finally {
  writeFileSync(join(out,'run.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(report,null,2));
}
process.exit(report.status === 'PASS' ? 0 : 1);
