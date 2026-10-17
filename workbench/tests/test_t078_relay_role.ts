// Roles outside worker/reviewer/controller must never reach the gate executor.
import assert from 'node:assert/strict';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {OrchestrationStore} from '../src/store.ts';import {RequestRelay} from '../src/relay.ts';
const out=resolve(process.argv[2]);mkdirSync(out);const checks=[];
for(const role of ['monitor','unknown']){
 const store=new OrchestrationStore(mkdtempSync('/tmp/t78-relay-role-'));const relay=new RequestRelay(store);let effects=0,error;
 const binding:any={id:'role-launch',task:'role-task',attempt:'role-attempt',session:'role-session',fence:1,spec_rev:1,role};
 const raw=JSON.stringify({schema:1,request_id:'role-request',command:'status',task:binding.task,attempt:binding.attempt,session:binding.session,fence:1,spec_rev:1});
 const receipt=await relay.receive(binding,{name:'role-request.json',raw},true,async()=>{effects++;return {ok:true};});
 try{assert.equal(effects,0);assert.equal(receipt.result.error,'relay_role_required');}catch(e){error=String(e);}
 checks.push({name:'deny-'+role,status:error?'INCOMPLETE':'PASS',effects,receipt,error});store.close();
}
const result={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,scope:'Production relay only; no native CLI or transport',real_model_turns:0};
writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({status:result.status,checks:checks.length}));process.exitCode=result.status==='PASS'?0:1;
