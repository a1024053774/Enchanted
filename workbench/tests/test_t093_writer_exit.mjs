// Regression from the independent r14 review. Actual D/final writer callbacks; supplied queries only.
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {join} from 'node:path';
import {finishChain} from './t093_chain_evidence.ts';

const output = process.argv[2];
assert(output,'new output path required');
const source = readFileSync(process.argv[3] ?? new URL('./test_t093_login_chain.ts',import.meta.url),'utf8');
const from = source.indexOf('  const gone=');
const until = source.indexOf('  const steps=',from);
const goneText = stripTypeScriptTypes(source.slice(from,until));
const stepFrom = source.indexOf('    {name:"source_home_cleanup_unconfirmed",');
const stepUntil = source.indexOf('\n    {name:',stepFrom+1);
const dText = stripTypeScriptTypes('('+source.slice(stepFrom,stepUntil).trim().replace(/,$/,'')+')');
const writerFrom = source.indexOf('  await finishChain(result,writer,steps,async()=>{')+'  await finishChain(result,writer,steps,async()=>{'.length;
const writerUntil = source.indexOf('\n  },()=>{rmSync(root',writerFrom);
assert(from>=0&&until>from&&stepFrom>=0&&stepUntil>stepFrom&&writerUntil>writerFrom,'frozen callback markers');
const writerText = stripTypeScriptTypes('async()=>{'+source.slice(writerFrom,writerUntil)+'\n}');
const roles = ['F','D','U','S','M','G0','G1','G2'];
const ids = Object.fromEntries(roles.map((role,i)=>[role,927401+i]));
const root='/private/tmp/t093-r14-review-synthetic-927400';
const session={metadata_directory:join(root,'metadata')};
const services={F:{pgrp:ids.F},D:{pgrp:ids.D}};
const testServices=Object.fromEntries(['U','S','M'].map(role=>[role,{pgrp:ids[role]}]));
const fixture={G_processes:['G0','G1','G2'].map(role=>({pid:ids[role]}))};
const rows=[];
async function one(name,kind,signals,expected){
  const queries=[];const perIdentity=new Map();const waits=[];const publications=[];
  const result={primary_failure:'independent-primary-927499',cleanup_failures:[],processes:{C:[{pid:927411},{pid:927412}]},source_home_cleanup:{removed:true}};
  let removed=false;
  const fakeProcess={pid:927412,kill(identity,signal){
    assert.equal(signal,0,'read-only synthetic signal');
    assert([-927401,-927402,-927403,-927404,-927405,-927406,-927407,-927408,927411].includes(identity),'registered identity');
    const index=perIdentity.get(identity)??0;perIdentity.set(identity,index+1);
    const schedule=signals[identity]??['ESRCH'];const value=schedule[Math.min(index,schedule.length-1)];
    queries.push({identity,value});
    if(value==='alive')return;
    throw Object.assign(new Error('supplied '+value),{code:value});
  }};
  const gone=new Function('process',goneText+'return gone;')(fakeProcess);
  const wait=async(test,label,deadline)=>{
    waits.push({label,deadline});
    assert.equal(deadline,kind==='D'?5000:8000,'existing bounded wait');
    let ticks=0;while(!test()){if(++ticks>deadline/1000)throw new Error(label);}
  };
  const publish=value=>publications.push(structuredClone(value));
  const receipt={source_home:join(root,'source-home'),removed:true,checkpoint_sequence:2};
  if(kind==='D'){
    const step=new Function('file','join','root','session','result','services','wait','gone','assert','return '+dText)(async path=>{
      assert.equal(path,join(session.metadata_directory,'source-home-removed.json'));
      assert.equal(publications[0].primary_failure,'independent-primary-927499','primary published before D cleanup');return receipt;
    },join,root,session,result,services,wait,gone,assert);
    await finishChain(result,{publish},[step],async()=>({all_exited:!result.cleanup_failures.length}),()=>{removed=true;return true;});
  }else{
    const writer=new Function('gone','wait','services','testServices','fixture','result','process','daemonStarted','existsSync','privateRoot','state','join','return '+writerText)(gone,wait,services,testServices,fixture,result,fakeProcess,false,()=>false,join(root,'private'),join(root,'state'),join);
    await finishChain(result,{publish},[],writer,()=>{removed=true;return true;});
  }
  let businessFailure=null;
  try{
    assert.equal(result.primary_failure,'independent-primary-927499','primary must survive');
    assert.equal(publications[0].phase,'cleanup_pending','primary before cleanup');
    assert.equal(removed,expected,'unconfirmed final writer must prevent fixture deletion');
    if(kind!=='D'&&result.writer_exit?.all_exited)assert(result.writer_exit.groups?.every(row=>row.exited)&&result.writer_exit.children?.every(row=>row.exited),'all_exited must agree with every final row');
  }catch(error){businessFailure=error.message;}
  rows.push({name,status:businessFailure?'FAIL':'PASS',businessFailure,removed,cleanup_failures:result.cleanup_failures,writer_exit:result.writer_exit,waits,supplied_sequences:signals,query_count:queries.length,unconfirmed_queries:queries.filter(row=>row.value!=='ESRCH')});
}
await one('D unseen EPERM-alive-EPERM-ESRCH','D',{[-ids.D]:['EPERM','alive','EPERM','ESRCH']},true);
await one('D persistent denial','D',{[-ids.D]:['EPERM']},false);
await one('barrier child denial then absence','barrier',{927411:['EPERM','alive','EPERM','ESRCH']},true);
await one('barrier group permanent denial','barrier',{[-ids.M]:['EPERM']},false);
await one('barrier child permanent alive','barrier',{927411:['alive']},false);
await one('barrier final group recheck denied','barrier',{[-ids.U]:['ESRCH','ESRCH','EPERM']},false);
await one('barrier final child recheck denied','barrier',{927411:['ESRCH','ESRCH','EPERM']},false);
const status=rows.every(row=>row.status==='PASS')?'PASS':'FAIL';
writeFileSync(output,JSON.stringify({status,scope:'Independent unseen signal schedules through frozen D and final writer callbacks; all process queries supplied, no actual OS query',checks:rows},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({status,checks:rows.map(({name,status,businessFailure,removed})=>({name,status,businessFailure,removed}))}));
process.exitCode=status==='PASS'?0:2;
