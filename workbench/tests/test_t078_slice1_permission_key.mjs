// Execute the actual Electron key branch with a simulated, independently bound view.
// No Electron, window, daemon, PTY, CLI or model is started.
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import assert from 'node:assert/strict';
const out=process.argv[2];mkdirSync(out);
const code=readFileSync(new URL('./electron_driver.mjs',import.meta.url),'utf8');
const marker="        } else if (request.command === 'terminal-key') {";
const start=code.indexOf(marker)+marker.length,end=code.indexOf("        } else if (request.command === 'queue-release')",start);
const simulate=new Function('request','window','inspect','values','let value;return (async()=>{'+code.slice(start,end)+';return value;})()');
const view={launch:'l1',thread:'t1',active_dispatch:'d1',window_id:'w1',state:'busy',lifecycle:'running',input_enabled:true};
const request={key:'Enter',launch:'l1',thread:'t1',dispatch:'d1',window_id:'w1',permission:true,source:'test-simulated-user',approval_ref:'independent-approval'};
const checks=[];
async function test(name,req,v,allowed){const writes=[];const window={focus(){writes.push('focus');},webContents:{executeJavaScript:async()=>{},sendInputEvent:e=>writes.push(e)}};
 try{const value=await simulate(req,window,async()=>v,{launch:'l1'});assert.equal(allowed,true);assert.equal(value.attempted,true);
  assert.deepEqual(writes,['focus',{type:'keyDown',keyCode:'Enter',modifiers:[]},{type:'keyUp',keyCode:'Enter',modifiers:[]}]);checks.push({name,status:'PASS'});
 }catch(e){if(!allowed&&writes.length===0)checks.push({name,status:'PASS'});else checks.push({name,status:'INCOMPLETE',error:String(e),writes});}}
await test('one-approved-bound-permission-Enter',request,view,true);
await test('missing-approval-ref-denied',{...request,approval_ref:''},view,false);
await test('no-permission-purpose-denied',{...request,permission:false},view,false);
await test('foreign-window-denied',request,{...view,window_id:'other'},false);
await test('foreign-active-dispatch-denied',request,{...view,active_dispatch:'other'},false);
await test('idle-window-denied',request,{...view,state:'idle'},false);
const result={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,argv:process.argv,scope:'Actual key branch; simulated view only; no UI/native boundary proof'};
writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({status:result.status,checks:checks.length}));process.exitCode=result.status==='PASS'?0:1;
