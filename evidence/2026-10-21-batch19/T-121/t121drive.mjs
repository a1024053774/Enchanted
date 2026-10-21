// Test-only CDP driver for T-121: the user opens a project terminal, starts their own
// claude, says "你去做这个项目的执行主控", and approves the roleRequest in the Enchanted UI.
// The driver plays the user: it presses Enter on Claude's folder-trust and tool
// prompts (the default choice), and clicks 批准 on the roleRequest banner. Every action is logged.
import { writeFileSync } from 'node:fs';
const [port, out, model] = process.argv.slice(2);
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
const screen = () => evaluate(`document.querySelector('section.pane .xterm-rows')?.innerText ?? ''`);
const key = async (k, code, vk, text) => { await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, ...(text ? { text } : {}) }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk }); };
const enter = () => key('Enter', 'Enter', 13, '\r');
const type = async value => { for (const ch of value) { await send('Input.dispatchKeyEvent', { type: 'keyDown', text: ch, key: ch, unmodifiedText: ch }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ch }); await sleep(15); } };
const log = { checks: [], failures: [], actions: [], started: new Date().toISOString() };
const act = (what, detail) => { log.actions.push({ at: new Date().toISOString(), what, ...(detail ? { detail } : {}) }); };
try {
  await attach();
  await until(`document.querySelectorAll('[data-project-id="demo"]').length===1`, 'project listed');
  await evaluate(`document.querySelector('[data-project-id="demo"]').click()`);
  await until(`document.querySelector('h1')?.textContent==='demo' && !!document.querySelector('.task-header .primary-button')`, 'project view');
  await sleep(1000);
  await evaluate(`document.querySelector('.task-header .primary-button').click()`);
  await until(`document.querySelectorAll('section.pane[data-input-enabled="true"]').length===1`, 'terminal writable');
  await until(`(document.querySelector('section.pane .xterm-rows')?.innerText??'').includes('demo')`, 'shell prompt', 30000); await sleep(2000);
  await evaluate(`document.querySelector('section.pane .xterm-helper-textarea').focus()`); await sleep(300);
  await send('Page.bringToFront');
  await type(`claude --model ${model}`); await enter(); act('typed claude command', `claude --model ${model}`);
  let asked = false, approved = false, prompts = 0;
  const end = Date.now() + 8 * 60_000;
  while (Date.now() < end) {
    await sleep(1000);
    const text = await screen();
    if (/Yes, I trust this folder/.test(text) && !asked) {
      // Claude's default choice here is "No, exit": move to "Yes, I trust this folder" first.
      await shot('01-trust-prompt'); await key('ArrowDown', 'ArrowDown', 40); await sleep(600);
      const moved = await screen();
      if (!/❯\s*Yes, I trust this folder/.test(moved)) throw new Error('trust choice not selected: ' + moved.slice(-400));
      await enter(); act('selected "Yes, I trust this folder" and pressed Enter'); await sleep(2500); continue;
    }
    if (!asked && /for shortcuts|Try "|\? for/i.test(text)) {
      await sleep(1500); await shot('02-claude-ready');
      await type('你去做这个项目的执行主控。'); await sleep(500); await enter(); asked = true; act('typed request', '你去做这个项目的执行主控。'); continue;
    }
    if (asked && /Do you want to proceed\?|Do you want to (run|allow)/i.test(text) && prompts < 6) {
      prompts++; await shot(`03-tool-prompt-${prompts}`); act('pressed Enter on tool permission prompt', text.slice(-600)); await enter(); await sleep(2000); continue;
    }
    if (!approved && await evaluate(`!!document.querySelector('.role-request')`)) {
      log.banner_text = await evaluate(`document.querySelector('.role-request p').innerText`);
      log.banner_pane_highlighted = await evaluate(`!!document.querySelector('.pane-slot[data-role-request-pending="true"]')`);
      log.banner_number = await evaluate(`document.querySelector('.role-request-number')?.innerText ?? null`);
      log.pane_tag = await evaluate(`document.querySelector('.pane-slot[data-role-request-pending="true"] .role-request-tag')?.innerText ?? null`);
      if (log.pane_tag !== `申请 ${log.banner_number} · 执行主控`) log.failures.push('pane tag does not match the banner number');
      await shot('04-roleRequest-banner');
      // The buttons stay disabled for a moment after the request list changes.
      for (let i = 0; i < 50 && await evaluate(`[...document.querySelectorAll('.role-request button')].find(b=>b.textContent.trim()==='批准')?.disabled !== false`); i++)
        await new Promise(resolve => setTimeout(resolve, 100));
      await evaluate(`[...document.querySelectorAll('.role-request button')].find(b=>b.textContent.trim()==='批准').click()`);
      approved = true; act('clicked 批准'); log.checks.push('role_request_banner_shown');
      await until(`[...document.querySelectorAll('[data-agent-launch] .agent-role')].some(n=>n.textContent==='执行主控')`, 'sidebar shows 执行主控', 15000);
      log.sidebar_row = await evaluate(`[...document.querySelectorAll('[data-agent-launch]')].map(n=>n.innerText)`);
      log.checks.push('sidebar_shows_executor'); await shot('05-sidebar-executor');
      continue;
    }
    // Claude prints "<verb> for Ns" when its turn ends.
    if (approved && /\p{Lu}\p{Ll}+ed for \d+[ms]/u.test(text)) {
      await sleep(1500); await shot('06-turn-finished');
      // Read the identity back the way the user would: Claude's "!" shell mode in the same terminal.
      await type('!'); await sleep(400); await type('a2a whoami'); await sleep(300); await enter(); act('typed !a2a whoami');
      await until(`(document.querySelector('section.pane .xterm-rows')?.innerText??'').includes('"role": "executor"')`, 'whoami shows executor', 30000);
      log.whoami_screen = (await screen()).split('\n').filter(line => /"(role|project|terminal)"/.test(line));
      log.checks.push('whoami_reports_executor'); await sleep(1000); await shot('07-whoami');
      break;
    }
  }
  if (!asked) log.failures.push('claude never became ready for input');
  if (!approved) log.failures.push('no roleRequest banner appeared');
  if (approved && !log.checks.includes('whoami_reports_executor')) log.failures.push('whoami was never checked (turn end not seen)');
  log.final_screen = await screen(); await shot('08-terminal-after');
} catch (error) { log.failures.push(String(error)); try { log.final_screen = await screen(); await shot('99-failure'); } catch {} }
log.finished = new Date().toISOString();
writeFileSync(`${out}/ui-driver.json`, JSON.stringify(log, null, 2) + '\n');
console.log(JSON.stringify({ checks: log.checks, failures: log.failures }));
process.exit(log.failures.length ? 1 : 0);
