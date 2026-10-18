// Synthetic daemon replies only. No daemon, CLI, network or process inventory.
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { ChainEvidence, errorSummary } from './t093_chain_evidence.ts';
const output=process.argv[2],source=process.argv[3]??new URL('./test_t093_login_chain.ts',import.meta.url);
assert(!existsSync(output));const text=readFileSync(source,'utf8'),checks:any[]=[];
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const start=text.indexOf('  stage="turns";'),end=text.indexOf('  assert((await request(state,{command:"pane_dispatch"',start);
// Both revisions have a fixed end marker after the release call.
const retained=text.indexOf('  const releaseObservation=',start);
const stop=end>=0?end:retained>=0?retained:text.indexOf('  const dispatched=',start);
assert(start>=0&&stop>start,'actual_chain_release_block_required');
const code=text.slice(start,stop);
for(const rejection of ['initial_release_only','foreground_claude_required','orchestration_failed']){
 const directory=mkdtempSync('/private/tmp/t093-daemon-reply-unit-'),target=join(directory,'result.json');
 const secret='synthetic-reply/"\\-'+randomUUID();
 const reply={ok:false,error:rejection,details:'independent daemon detail '+secret};
 let error:any;
 try{
  const helpers=await import('./t093_chain_evidence.ts');
  const request=async()=>reply;
  const invoke=new AsyncFunction('request','assert','assertDaemonOk','state','launch','operator','panes','counterexamples','let stage;'+code);
  try{await invoke(request,assert,(helpers as any).assertDaemonOk,'synthetic-state',{thread:'fixture-thread'},{}, {status:()=>({state:'unknown',queued:[],active:null,writing:false,user_draft:false})},{});}catch(value){error=value;}
  const summary:any=errorSummary(error);
  assert.equal(summary.daemon_response?.error,rejection,'daemon_error_field_must_survive_actual_chain_assertion');
  assert.equal(summary.daemon_response.command,'pane_release');
  assert.equal(summary.daemon_response.details,reply.details);
  assert(summary.message.includes(rejection),'error_message_must_name_daemon_rejection');
  new ChainEvidence(target,()=>[secret]).publish({error_summary:summary});
  const saved=JSON.parse(readFileSync(target,'utf8'));assert.equal(saved.error_summary.daemon_response.error,rejection);
  assert(!saved.error_summary.daemon_response.details.includes('synthetic-reply'),'daemon_details_must_be_redacted_before_publication');
  checks.push({rejection,status:'PASS',command:'pane_release',details_retained_and_redacted:true});
 }catch(value){checks.push({rejection,status:'FAIL',business_failure:(value as Error).message.split('\n')[0]});}
 finally{rmSync(directory,{recursive:true});}
}
const status=checks.every(v=>v.status==='PASS')?'PASS':'FAIL';
writeFileSync(output,JSON.stringify({status,scope:'actual chain release block with synthetic daemon replies; no OS/runtime boundary execution',checks},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({status,checks:checks.length}));process.exitCode=status==='PASS'?0:2;
