import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {stripTypeScriptTypes} from 'node:module';
import {randomInt,randomUUID} from 'node:crypto';
import {finishChain} from '/Users/luckye/Documents/Code/a2a-wt-t093/workbench/tests/t093_chain_evidence.ts';
const root='/Users/luckye/Documents/Code/a2a-wt-t093';
const source=readFileSync(join(root,'workbench/tests/test_t093_login_chain.ts'),'utf8');
const start=source.indexOf('  const gone='),end=source.indexOf('\n  const steps=',start);
const s=source.indexOf('    {name:"upstream_shutdown_unconfirmed",',end),e=source.indexOf('\n    {name:',s+1);
assert(start>0&&end>start&&s>end&&e>s,'actual C lifecycle anchors required');
const gone=source.slice(start,end), callback=source.slice(s,e).trim().replace(/,$/,'');
const inputCode=stripTypeScriptTypes(gone)+'return ('+callback+');';
const checks=[];
const suppliedRoot='/private/tmp/supplied-C-'+randomUUID(),group=randomInt(310000,410000),pid=group+9;
const valid={pid,pgrp:group,startup_completed:false,listeners_bound:0,closed_listeners:0,all_closed:true,close_errors:[]};
async function exercise(sample,mutate=false){
 const code=mutate?inputCode.replace('if(error.code==="EPERM")return false','if(error.code==="EPERM")return true'):inputCode;
 if(mutate)assert.notEqual(code,inputCode,'targeted EPERM mutant must apply');
 const factory=new Function('process','existsSync','writeFileSync','file','wait','root','testServices','join','assert','result',code);
 let queried=0,esrch=false,removed=false;
 const observations=[],publications=[];
 const result={status:'INCOMPLETE',primary_failure:'independent-primary-'+randomUUID(),cleanup_failures:[],service_receipts:{}};
 const original=result.primary_failure;
 const receipt={...valid,...sample.receipt};
 const step=factory({kill:(identity,signal)=>{
   assert.equal(identity,-group);assert.equal(signal,0,'only supplied read-only probe allowed');
   const value=sample.signals[Math.min(queried++,sample.signals.length-1)];observations.push(value);
   if(value==='alive')return;
   if(value==='ESRCH')esrch=true;
   throw Object.assign(new Error('supplied '+value),{code:value});
 }},()=>false,(path,text,opts)=>{assert.equal(path,join(suppliedRoot,'U/stop'));assert.equal(text,'\n');assert.equal(opts.flag,'wx');},async path=>{
   assert.equal(path,join(suppliedRoot,'U/closed.json'));
   if(sample.missing)throw new Error('independent_receipt_missing');
   return receipt;
 },async (predicate,label,timeout)=>{
   assert.equal(timeout,5000);
   for(let i=0;i<7;i++){if(predicate())return;}
   throw new Error(label);
 },suppliedRoot,{U:{pid,pgrp:group}},join,assert,result);
 const writer={publish:value=>publications.push(structuredClone(value))};
 await finishChain(result,writer,[step],async()=>({all_exited:esrch}),()=>{removed=true;return true;});
 assert.equal(result.primary_failure,original,'cleanup must preserve original primary failure');
 assert(publications.every(value=>value.primary_failure===original),'every checkpoint must preserve primary');
 const failed=result.cleanup_failures.includes('upstream_shutdown_unconfirmed');
 if(sample.expected){assert.equal(failed,false,'valid closure and ESRCH should confirm U cleanup');assert(esrch&&removed);}
 else assert.equal(failed,true,'missing/failed closure or EPERM/alive must not confirm U cleanup');
 if(sample.expectedQueries!==undefined)assert.equal(queried,sample.expectedQueries);
 if(!sample.expected&&sample.signals.every(value=>value!=='ESRCH'))assert.equal(removed,false,'uncertain process absence must block removal');
 return {signals:observations,receipt,queries:queried,closure_confirmed:!failed,fixture_removed:removed,primary_preserved:true,errors:result.cleanup_errors};
}
for(const sample of [
 {name:'zero_listeners',signals:['ESRCH'],expected:true,expectedQueries:1},
 {name:'partial_listeners',signals:['ESRCH'],receipt:{listeners_bound:1,closed_listeners:1},expected:true},
 {name:'permission_window',signals:['EPERM','alive','ESRCH'],expected:true,expectedQueries:3},
 {name:'still_alive',signals:['alive'],expected:false},
 {name:'EPERM_is_not_exit',signals:['EPERM'],expected:false},
 {name:'receipt_missing',signals:['ESRCH'],missing:true,expected:false,expectedQueries:0},
 {name:'close_failed',signals:['ESRCH'],receipt:{all_closed:false,close_errors:[{errno:5}]},expected:false,expectedQueries:0},
 {name:'partial_close_count',signals:['ESRCH'],receipt:{listeners_bound:2,closed_listeners:1},expected:false,expectedQueries:0},
 {name:'wrong_pid',signals:['ESRCH'],receipt:{pid:pid+1},expected:false,expectedQueries:0},
 {name:'wrong_group',signals:['ESRCH'],receipt:{pgrp:group+1},expected:false,expectedQueries:0},
 {name:'invalid_bound_count',signals:['ESRCH'],receipt:{listeners_bound:3,closed_listeners:3},expected:false,expectedQueries:0},
]){
 try{checks.push({case:sample.name,status:'PASS',detail:await exercise(sample)});}
 catch(error){checks.push({case:sample.name,status:'FAIL',error:error.message});}
}
try{
 await exercise({signals:['EPERM'],expected:false},true);
 checks.push({case:'EPERM_false_exit_mutant',status:'FAIL',error:'mutant accepted'});
}catch(error){
 assert.match(error.message,/missing\/failed closure or EPERM\/alive/,'mutant must fail on closure business assertion');
 checks.push({case:'EPERM_false_exit_mutant',status:'PASS',rejected_by_business_assertion:error.message});
}
const report={candidate:'e5b8329e4f7d0c8104b7e666c346531357612372',scope:'L1 actual C callback and finishChain; PID queries supplied; no kernel probes',checks,status:checks.every(row=>row.status==='PASS')?'PASS':'FAIL'};
writeFileSync(new URL('./cleanup-result-v2.json',import.meta.url),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:report.status,checks:checks.length}));
process.exitCode=report.status==='PASS'?0:2;
