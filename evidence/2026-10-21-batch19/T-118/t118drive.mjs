// Test-only CDP driver: T-118 restore without visible replay, renderer recovery, dark screenshot.
import { writeFileSync } from 'node:fs';
const [port, out, framesScript] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function connect() {
  for (let n = 0; n < 100; n++) {
    try { const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
      if (page) { const ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; }); return ws; } } catch {}
    await sleep(200);
  }
  throw new Error('no page target');
}
let ws, id = 0; const waiting = new Map();
async function attach() { ws = await connect(); ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); } }; }
const send = (method, params = {}) => new Promise((resolve, reject) => { const n = ++id;
  const timer = setTimeout(() => { waiting.delete(n); reject(new Error('CDP timeout: ' + method)); }, 5000);
  waiting.set(n, m => { clearTimeout(timer); m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result); }); ws.send(JSON.stringify({ id: n, method, params })); });
const evaluate = async expression => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; };
const until = async (expression, label, ms = 30000) => { const end = Date.now() + ms; while (Date.now() < end) { try { if (await evaluate(expression)) return; } catch {} await sleep(150); } throw new Error('timeout: ' + label); };
const shot = async name => { const r = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(`${out}/${name}.png`, Buffer.from(r.data, 'base64')); };
const log = { checks: [], failures: [] };
const text = `(document.querySelector('section.pane .xterm-accessibility-tree')?.innerText??'')`;
try {
  await attach();
  await until(`document.querySelectorAll('[data-project-id]').length>=1`, 'project listed');
  await evaluate(`document.querySelector('[data-project-id]').click()`);
  await until(`document.querySelector('h1')?.textContent==='demo' && !!document.querySelector('.task-header .primary-button')`, 'project view');
  await sleep(1000);
  await evaluate(`document.querySelector('.task-header .primary-button').click()`);
  await until(`document.querySelectorAll('section.pane[data-input-enabled="true"]').length===1`, 'terminal writable');
  await until(`${text}.includes('/repos/demo')`, 'shell prompt', 30000); await sleep(1500);
  await evaluate(`document.querySelector('section.pane .xterm-helper-textarea').focus()`); await sleep(300);
  await send('Page.bringToFront');
  for (const ch of `python3 ${framesScript}`) { await send('Input.dispatchKeyEvent', { type: 'keyDown', text: ch, key: ch, unmodifiedText: ch }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ch }); }
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r' });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await until(`${text}.includes('FINAL-FRAME-MARK')`, 'frames finished', 90000);
  log.trace_bytes = await evaluate(`Number(document.querySelector('.terminal-scroll').dataset.outputOffset)`);
  await sleep(500);
  // Reopen: reload the renderer and sample what the user would see while it catches up.
  await send('Page.reload'); await sleep(50);
  const samples = [];
  const end = Date.now() + 60000;
  while (Date.now() < end) {
    let s; try { s = await evaluate(`(()=>{const m=document.querySelector('section.pane .terminal-mount');if(!m)return null;
      const t=document.querySelector('section.pane .xterm-rows')?.textContent??'';return {rows:!!document.querySelector('section.pane .xterm-rows'),visible:getComputedStyle(m).visibility!=='hidden',overlay:!!document.querySelector('.terminal-restoring'),
      offset:Number(document.querySelector('.terminal-scroll')?.dataset.outputOffset),frame:(t.match(/frame (\\d+)/)||[])[1]??null,final:t.includes('FINAL-FRAME-MARK')}})()`); } catch { s = null; }
    if (s) { samples.push(s); if (s.final && s.visible && s.offset >= log.trace_bytes) break; }
    await sleep(20);
  }
  log.samples_total = samples.length;
  const replayVisible = samples.filter(s => s.visible && s.frame && !s.final);
  log.intermediate_frames_visible = replayVisible.length;
  log.distinct_visible_frames = [...new Set(replayVisible.map(s => s.frame))].length;
  log.overlay_seen = samples.some(s => s.overlay);
  log.first_samples = samples.slice(0, 5); log.last_sample = samples.at(-1); log.visible_intermediate_samples = replayVisible;
  if (replayVisible.length) log.failures.push('intermediate frames visible during restore'); else log.checks.push('no_visible_replay');
  if (!samples.at(-1)?.final || !samples.at(-1)?.visible) log.failures.push('final screen not shown'); else log.checks.push('final_screen_shown');
  // Renderer killed from outside: the window must come back with its pane.
  try { await send('Page.crash'); } catch {}
  ws.close(); await sleep(1500);
  try {
    await attach();
    await until(`${text}.includes('FINAL-FRAME-MARK') && getComputedStyle(document.querySelector('section.pane .terminal-mount')).visibility!=='hidden'`, 'pane back after renderer crash', 20000);
    log.checks.push('renderer_recovered_with_pane');
  } catch (error) { log.failures.push('renderer not recovered: ' + error.message); }
  try { await sleep(500); await shot('dark-after-recovery'); } catch (error) { log.shot_error = String(error); }
  // A close whose reply this renderer never handles (as after a crash reload), of a zoomed
  // pane next to another: the pane set must resync and the remaining pane must be visible.
  try {
    const menuButton = `[...document.querySelectorAll('[aria-label="窗格菜单"]')][0]`;
    const item = label => `[...document.querySelectorAll('[role=menuitem]')].find(n=>n.textContent.trim()==='${label}')`;
    await evaluate(`${menuButton}.click()`); await sleep(200); await evaluate(`${item('向右分屏')}.click()`);
    await until(`document.querySelectorAll('section.pane').length===2`, 'split', 15000);
    const closing = await evaluate(`document.querySelector('section.pane').dataset.paneKey`);
    await evaluate(`${menuButton}.click()`); await sleep(200); await evaluate(`${item('放大')}.click()`);
    await until(`document.querySelectorAll('.pane-slot:not([hidden])').length===1`, 'zoomed', 5000);
    await evaluate(`window.a2a.closePane(${JSON.stringify(closing)}).then(()=>true)`);
    await until(`document.querySelectorAll('section.pane').length===1`, 'pane set resynced from main', 10000);
    log.checks.push('pane_set_resynced');
    await until(`document.querySelectorAll('.pane-slot:not([hidden])').length===1`, 'remaining pane visible after zoomed pane closed', 3000);
    log.checks.push('remaining_pane_visible_after_zoomed_close');
  } catch (error) { log.failures.push('resync: ' + error.message); }
  try { log.dark = await evaluate(`matchMedia('(prefers-color-scheme: dark)').matches`); } catch (error) { log.dark_error = String(error); }
} catch (error) { log.failures.push(String(error)); }
log.status = log.failures.length ? 'FAIL' : 'PASS';
writeFileSync(`${out}/log.json`, JSON.stringify(log, null, 2));
console.log(JSON.stringify(log, null, 2));
process.exit(log.status === 'PASS' ? 0 : 1);
