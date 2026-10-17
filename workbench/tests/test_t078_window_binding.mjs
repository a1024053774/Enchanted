import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
const out = process.argv[2]; mkdirSync(out);
const base = 'evidence/2026-10-11-batch13/T-078/p1-materials-09/continue-esc/';
const snapshots = readFileSync(base + 'electron/snapshots.ndjson', 'utf8').trim().split('\n').map(JSON.parse);
const actual = snapshots.find(v => v.pane.state === 'busy' && v.pane.active);
const code = readFileSync(new URL('../app/main.ts', import.meta.url), 'utf8');
const start = code.indexOf("    const writable =");
const end = code.indexOf('\n  });', start);
const evaluate = new Function('result', 'identity', 'closing', 'return (async()=>{' + code.slice(start, end) + '})()');
const driver = readFileSync(process.argv[3] ?? new URL('./electron_driver.mjs', import.meta.url), 'utf8');
const marker = "        } else if (request.command === 'terminal-key') {";
const keyStart = driver.indexOf(marker) + marker.length;
const keyEnd = driver.indexOf("        } else if (request.command === 'queue-release')", keyStart);
const simulate = new Function('request', 'window', 'inspect', 'values', 'let value; return (async()=>{' + driver.slice(keyStart, keyEnd) + ';return value;})()');
const request = {key:'Escape', launch:actual.launch.id, thread:actual.launch.thread, dispatch:actual.pane.active.dispatch};
const good = {launch:request.launch, thread:request.thread, active_dispatch:request.dispatch, state:'busy', lifecycle:'running', input_enabled:true};
const checks = [];
async function test(name, f) {try {await f(); checks.push({name,status:'PASS'});} catch(e) {checks.push({name,status:'INCOMPLETE',error:String(e)});}}
await test('nullable_controller_window_accepts_input', async()=>assert.equal((await evaluate(actual, {id:'window'}, false)).input_enabled, true));
await test('stale_worker_remains_readonly', async()=>{
  const v = structuredClone(actual); v.launch.role='worker'; v.launch.attempt='old'; v.task.current_attempt={attempt_id:'new'};
  assert.equal((await evaluate(v, {id:'window'}, false)).input_enabled, false);
});
await test('closing_window_remains_readonly', async()=>assert.equal((await evaluate(actual, {id:'window'}, true)).input_enabled, false));
for (const [name, view] of [['unconnected_key_is_not_sent', {state:'unknown'}], ['wrong_pane_is_not_sent', {...good,launch:'other'}],
  ['wrong_active_dispatch_is_not_sent', {...good,active_dispatch:'other'}], ['disabled_input_is_not_sent', {...good,input_enabled:false}]]) {
  await test(name, async()=>{
    const writes=[]; const window={focus(){writes.push('focus');},webContents:{executeJavaScript:async()=>{},sendInputEvent:e=>writes.push(e)}};
    await assert.rejects(()=>simulate(request,window,async()=>view,{launch:request.launch}),/Window is not bound to the requested busy dispatch/);
    assert.deepEqual(writes,[]);
  });
}
await test('bound_key_reports_attempt_not_delivery', async()=>{
  const writes=[]; const window={focus(){},webContents:{executeJavaScript:async()=>{},sendInputEvent:e=>writes.push(e)}};
  const v=await simulate(request,window,async()=>good,{launch:request.launch});
  assert.equal(v.attempted,true); assert.equal(v.sent,undefined); assert.equal(writes.length,2);
});
const controlRequest = {...request, key:'Control+C', window_id:'held-window', interruption:91};
const held = {...good, active_dispatch:'', interrupted:true, window_id:'held-window', interruption:91};
await test('bound_control_c_is_one_attempt_via_window_keys', async()=>{
  const writes=[];const window={focus(){},webContents:{executeJavaScript:async()=>{},sendInputEvent:e=>writes.push(e)}};
  const v=await simulate(controlRequest,window,async()=>held,{launch:request.launch});
  assert.equal(v.attempted,true);assert.equal(v.source,'test-simulated-user');assert.equal(v.sent,undefined);
  assert.deepEqual(writes,[{type:'keyDown',keyCode:'C',modifiers:['control']},{type:'keyUp',keyCode:'C',modifiers:['control']}]);
});
for (const [name,view] of [['control_c_rejects_active_generation',{...held,active_dispatch:request.dispatch}],
  ['control_c_rejects_wrong_interruption',{...held,interruption:92}], ['control_c_rejects_other_window',{...held,window_id:'other'}],
  ['control_c_rejects_readonly_window',{...held,input_enabled:false}]]) {
  await test(name, async()=>{
    const writes=[];const window={focus(){writes.push('focus');},webContents:{executeJavaScript:async()=>{},sendInputEvent:e=>writes.push(e)}};
    await assert.rejects(()=>simulate(controlRequest,window,async()=>view,{launch:request.launch}));assert.deepEqual(writes,[]);
  });
}
const r={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,argv:process.argv,
  scope:'Exact snapshot predicate and Electron key branch; archived 09A identity and a simulated renderer, no UI/socket/model starts'};
writeFileSync(join(out,'results.json'),JSON.stringify(r,null,2)); console.log(JSON.stringify(r)); process.exitCode=r.status==='PASS'?0:1;
