// Compile and execute the exact renderer prompt used by the real Electron driver.
// Expected bytes come from the terminal bracketed-paste/Enter protocol.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import { firstAnswerReceipt } from './t108_answer_receipt.mjs';
import vm from 'node:vm';
const summary=process.argv[2];assert(summary);
const source=readFileSync(new URL('./t108_questions_driver.mjs',import.meta.url),'utf8');
const part=source.split("request.command==='prompt'")[1].split("request.command==='answer'")[0];
const template=part.slice(part.indexOf('executeJavaScript(')+'executeJavaScript('.length,part.lastIndexOf(');'));
const script=new Function('JSON','return '+template)(JSON);
const knownBad=script.replace(JSON.stringify('\r'),'\'\r\'');
assert.notEqual(knownBad,script);assert.throws(()=>new vm.Script(knownBad),SyntaxError);
const received=[];
await new vm.Script(script).runInNewContext({window:{a2a:{input:async(...args)=>received.push(args)}},
  document:{querySelector:()=>({dataset:{paneKey:'fixture-key'}})},setTimeout:callback=>callback()});
assert.deepEqual(received,[['fixture-key','\x1b[200~Please ask the region question.\x1b[201~'],['fixture-key','\r']]);
const fixture=mkdtempSync('/private/tmp/t108-driver-receipt-');
const db=new DatabaseSync(fixture+'/state.sqlite3');
db.exec('CREATE TABLE orchestration_events(seq INTEGER PRIMARY KEY,launch TEXT,type TEXT,data TEXT)');
const append=(type,data,launch=null)=>db.prepare('INSERT INTO orchestration_events(launch,type,data) VALUES(?,?,?)').run(launch,type,JSON.stringify(data));
const receivedRequest=(id='transport-1',request='window-1')=>append('request_received',{id,input:{command:'window_answer',request_id:request,sequence:7}});
const admitted=()=>append('window_request_admitted',{command:'window_answer',request_id:'window-1',sequence:7},'original-launch');
const receiptCases=[];
try {
  receivedRequest();admitted();
  // Waiting for the request's final receipt is essential; the DOM click and
  // native confirmation alone do not establish success.
  append('native_question_resolved',{status:'answered'},'original-launch');
  const pending=firstAnswerReceipt(db,0,'original-launch',250);
  setTimeout(()=>append('request_result',{id:'transport-1',command:'window_answer',ok:true}),30);
  const receipt=await pending;assert.equal(receipt.transport_id,'transport-1');assert.equal(receipt.request_id,'window-1');
  assert.equal(receipt.final_receipt.ok,true);receiptCases.push('await_first_final_receipt');
  db.exec('DELETE FROM orchestration_events');receivedRequest();admitted();
  append('request_rejected',{id:'transport-1',result:{ok:false,error:'question_input_changed'}});
  receivedRequest('transport-2','window-2');append('request_result',{id:'transport-2',ok:true});
  await assert.rejects(firstAnswerReceipt(db,0,'original-launch',0),/First window_answer failed/);
  receiptCases.push('first_rejection_not_masked_by_later_success');
  db.exec('DELETE FROM orchestration_events');receivedRequest();admitted();
  append('request_result',{id:'unrelated',ok:true});
  await assert.rejects(firstAnswerReceipt(db,0,'original-launch',0),/timed out/);receiptCases.push('unrelated_receipt_not_accepted');
  append('request_result',{id:'transport-1',ok:true});
  await assert.rejects(firstAnswerReceipt(db,0,'wrong-launch',0),/First window_answer failed/);receiptCases.push('launch_admission_required');
}finally{db.close();}
const followup=source.split("request.command==='followup'")[1].split("request.command==='duplicate'")[0];
const followupTemplate=followup.slice(followup.indexOf('executeJavaScript(')+'executeJavaScript('.length,followup.lastIndexOf(');'));
const followupScript=new Function('JSON','request','return '+followupTemplate)(JSON,{text:'fresh nonce'});
const followupBytes=[];
await new vm.Script(followupScript).runInNewContext({window:{a2a:{input:async(...args)=>followupBytes.push(args)}},
  document:{querySelector:()=>({dataset:{paneKey:'same-original-pane'}})}});
assert.deepEqual(followupBytes,[['same-original-pane','\x1b[200~fresh nonce\x1b[201~']]);
// The main process also orders renderer commands. Returning an error to one
// caller must not make the next independently checked request inherit it.
const main=readFileSync(new URL('../app/main.ts',import.meta.url),'utf8');
const send=main.slice(main.indexOf('function sendWindowCommand('),main.indexOf('\nfunction registerHandlers()'))
  .replace('(context: WindowBinding, pane: PaneBinding, input: Record<string, unknown>)','(context, pane, input)')
  .replace('(result: any)','(result)').replace('let response: Promise<any>;','let response;');
let calls=0;
const context={options:{state:'original-state'}},pane={identity:{launch:'original-launch'},sequence:0,inputQueue:Promise.resolve()};
const sendCommand=new vm.Script(send+';sendWindowCommand').runInNewContext({randomUUID:()=>String(calls),request:async()=>{
  calls++;return calls===1?{ok:false,error:'Identity revoked'}:{ok:true,written:true};}});
await assert.rejects(sendCommand(context,pane,{command:'window_answer'}),/Identity revoked/);
let nextError,nextReceipt;
try{nextReceipt=await sendCommand(context,pane,{command:'window_input'});}catch(error){nextError=String(error);}
assert.equal(nextError,undefined,'A refused renderer command cannot poison the next request');
assert.equal(calls,2);assert.equal(nextReceipt.ok,true);
const result={status:'PASS',model_calls:0,vendor_calls:0,fixture,checks:['old_literal_CR_rejected_by_parser','actual_driver_prompt_parses',
  'exact_bracketed_paste_and_enter_bytes','followup_same_pane_nonce_without_enter','main_command_queue_survives_refusal',...receiptCases]};
writeFileSync(summary,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result));
