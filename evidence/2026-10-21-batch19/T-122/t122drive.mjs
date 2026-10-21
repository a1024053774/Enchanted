// Test-only CDP driver for T-122, extending the T-121 driver. It plays the user: opens a project
// terminal, starts their own claude, asks it to become the executor controller, approves in the
// Enchanted UI, then asks it to dispatch a Claude Code worker and carry the task to integration.
// It presses Enter on Claude's own tool prompts (the default choice) and, when the controller ends
// a turn before the task is integrated, asks it to continue (at most 4 times). Every action is logged.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
const [port, out, model, state, source, repo] = process.argv.slice(2);
process.env.A2A_OPERATOR_CREDENTIAL = JSON.parse(readFileSync(join(state, 'desktop-connection.json'), 'utf8')).credential;
const { request } = await import(join(source, 'src/transport.ts'));
const { readOperatorCredential } = await import(join(source, 'src/credentials.ts'));
const operator = readOperatorCredential(state);
const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws, id = 0; const waiting = new Map();
async function attach() {
  for (let n = 0; n < 100; n++) {
    try { const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
      if (page) { ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; }); break; } } catch {}
    await sleep(200);
  }
  if (!ws) throw new Error('no page target');
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); } };
}
const send = (method, params = {}) => new Promise((resolve, reject) => { const n = ++id;
  const timer = setTimeout(() => { waiting.delete(n); reject(new Error('CDP timeout: ' + method)); }, 5000);
  waiting.set(n, m => { clearTimeout(timer); m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result); }); ws.send(JSON.stringify({ id: n, method, params })); });
const evaluate = async expression => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; };
const until = async (expression, label, ms = 30000) => { const end = Date.now() + ms; while (Date.now() < end) { try { if (await evaluate(expression)) return; } catch {} await sleep(150); } throw new Error('timeout: ' + label); };
const shot = async name => { const r = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(`${out}/${name}.png`, Buffer.from(r.data, 'base64')); };
let terminalLaunch = null;
const pane = () => terminalLaunch ? `section.pane[data-launch-id="${terminalLaunch}"]` : 'section.pane';
const screen = () => evaluate(`document.querySelector('${pane()} .xterm-rows')?.innerText ?? ''`);
const focus = async () => { await evaluate(`document.querySelector('${pane()} .xterm-helper-textarea').focus()`); await sleep(200); };
const key = async (k, code, vk, text) => { await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, ...(text ? { text } : {}) }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk }); };
const enter = () => key('Enter', 'Enter', 13, '\r');
const type = async value => { for (const ch of value) { await send('Input.dispatchKeyEvent', { type: 'keyDown', text: ch, key: ch, unmodifiedText: ch }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ch }); await sleep(15); } };
const log = { checks: [], failures: [], actions: [], states: [], started: new Date().toISOString() };
const act = (what, detail) => { log.actions.push({ at: new Date().toISOString(), what, ...(detail ? { detail } : {}) }); };
const taskState = async () => { const status = await request(state, { command: 'status', task: 'T-1' }, operator); return status.ok ? status.task.state : null; };
const dispatchText = `派一个 Claude Code worker，模型 claude-haiku-5-5，强度 low：任务号 T-1，在项目仓库根目录新建 hello.txt，内容一行 hello。` +
  `允许路径只有 hello.txt；验收文件 check.py；完成条件 python3 check.py；工作分支 main。走完交付、验收（含独立审查）、打分、集成到 main，按 a2a skill 的步骤做。`;
try {
  await attach();
  await until(`document.querySelectorAll('[data-project-id="demo"]').length===1`, 'project listed');
  await evaluate(`document.querySelector('[data-project-id="demo"]').click()`);
  await until(`document.querySelector('h1')?.textContent==='demo' && !!document.querySelector('.task-header .primary-button')`, 'project view');
  await sleep(1000);
  await evaluate(`document.querySelector('.task-header .primary-button').click()`);
  await until(`document.querySelectorAll('section.pane[data-input-enabled="true"]').length===1`, 'terminal writable');
  terminalLaunch = await evaluate(`document.querySelector('section.pane').dataset.launchId`);
  log.terminal_launch = terminalLaunch;
  await until(`(document.querySelector('section.pane .xterm-rows')?.innerText??'').includes('demo')`, 'shell prompt', 30000); await sleep(2000);
  await focus(); await send('Page.bringToFront');
  await type(`claude --model ${model}`); await enter(); act('typed claude command', `claude --model ${model}`);
  let asked = false, approved = false, dispatched = false, prompts = 0, nudges = 0, quietSince = null, workerSeen = false, reviewerSeen = false;
  const end = Date.now() + 25 * 60_000;
  while (Date.now() < end) {
    await sleep(1000);
    const text = await screen();
    if (/Yes, I trust this folder/.test(text) && !asked) {
      // Claude's default choice here is "No, exit": move to "Yes, I trust this folder" first.
      await shot('01-trust-prompt'); await focus(); await key('ArrowDown', 'ArrowDown', 40); await sleep(600);
      if (!/❯\s*Yes, I trust this folder/.test(await screen())) throw new Error('trust choice not selected');
      await enter(); act('selected "Yes, I trust this folder" and pressed Enter'); await sleep(2500); continue;
    }
    if (!asked && /for shortcuts|Try "|\? for/i.test(text)) {
      await sleep(1500); await shot('02-claude-ready'); await focus();
      await type('你去做这个项目的执行主控。'); await sleep(500); await enter(); asked = true; act('typed request', '你去做这个项目的执行主控。'); continue;
    }
    if (asked && /Do you want to proceed\?|Do you want to (run|allow|make this edit|create)/i.test(text) && prompts < 80) {
      prompts++; if (prompts <= 3 || prompts % 10 === 0) await shot(`03-tool-prompt-${prompts}`);
      act('pressed Enter on tool permission prompt', text.slice(-500)); await focus(); await enter(); quietSince = null; await sleep(2000); continue;
    }
    if (!approved && await evaluate(`!!document.querySelector('.role-request')`)) {
      await shot('04-roleRequest-banner');
      for (let i = 0; i < 50 && await evaluate(`[...document.querySelectorAll('.role-request button')].find(b=>b.textContent.trim()==='批准')?.disabled !== false`); i++) await sleep(100);
      await evaluate(`[...document.querySelectorAll('.role-request button')].find(b=>b.textContent.trim()==='批准').click()`);
      approved = true; act('clicked 批准'); log.checks.push('role_request_approved');
      await until(`[...document.querySelectorAll('[data-agent-launch] .agent-role')].some(n=>n.textContent==='执行主控')`, 'sidebar shows 执行主控', 15000);
      await shot('05-sidebar-executor'); quietSince = null; continue;
    }
    const sidebar = await evaluate(`[...document.querySelectorAll('[data-agent-launch]')].map(n=>({id:n.dataset.agentLaunch,parent:n.dataset.agentParent,level:n.dataset.agentLevel,text:n.innerText}))`);
    if (!workerSeen && sidebar.some(row => /worker/.test(row.text) && row.parent === terminalLaunch)) {
      workerSeen = true; log.sidebar_with_worker = sidebar; log.checks.push('sidebar_worker_under_controller'); await shot('06-sidebar-worker');
    }
    if (!reviewerSeen && sidebar.some(row => /审查员/.test(row.text))) {
      reviewerSeen = true; log.sidebar_with_reviewer = sidebar; log.checks.push('sidebar_reviewer_shown'); await shot('07-sidebar-reviewer');
    }
    const current = await taskState();
    if (current !== log.states.at(-1)) { log.states.push(current); act('task state', current); }
    if (current === 'accepted') { await sleep(3000); await shot('08-accepted'); log.checks.push('task_accepted'); break; }
    // Idle: Claude shows "esc to interrupt" while it works; quiet for 8 s with no prompt means the turn ended.
    if (approved && !/esc to interrupt/.test(text)) {
      quietSince ??= Date.now();
      if (Date.now() - quietSince < 8000) continue;
      quietSince = null;
      if (!dispatched) { await shot('05b-controller-ready'); await focus(); await type(dispatchText); await sleep(500); await enter(); dispatched = true; act('typed dispatch request', dispatchText); continue; }
      if (nudges < 4) { nudges++; await focus(); await type('继续，直到 T-1 集成到 main。'); await sleep(400); await enter(); act('typed nudge', String(nudges)); continue; }
      log.failures.push('controller stopped before integration'); break;
    } else quietSince = null;
  }
  if (!approved) log.failures.push('no roleRequest banner appeared');
  if (!log.checks.includes('task_accepted')) log.failures.push('task not accepted: ' + JSON.stringify(log.states));
  if (!workerSeen) log.failures.push('worker never shown under the controller');
  log.prompts = prompts; log.nudges = nudges;
  log.final_screen = await screen(); await shot('09-terminal-after');
} catch (error) { log.failures.push(String(error)); try { log.final_screen = await screen(); await shot('99-failure'); } catch {} }
log.finished = new Date().toISOString();
writeFileSync(`${out}/ui-driver.json`, JSON.stringify(log, null, 2) + '\n');
console.log(JSON.stringify({ checks: log.checks, failures: log.failures }));
process.exit(log.failures.length ? 1 : 0);
