// Real Panes.release/processInfo with a controlled process-query boundary.
import assert from 'node:assert/strict';
import childProcess from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';
import {promisify} from 'node:util';
import {mkdtempSync,mkdirSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {randomInt} from 'node:crypto';
const output=process.argv[2];assert(!existsSync(output));
let kind='healthy',rootPid=201;let calls:any[]=[];
const rows=[{pid:201,ppid:1,pgid:201,tpgid:202,command:'/bin/zsh'},{pid:202,ppid:201,pgid:202,tpgid:202,command:'/fixture/claude'},{pid:203,ppid:202,pgid:202,tpgid:202,command:'/fixture/hook'}];
const fake=Object.assign(()=>{throw new Error('unexpected callback execution');},{[promisify.custom]:async(file:string,args:string[],options:any)=>{
 calls.push({file,args});
 assert.notEqual(file,'/bin/ps','foreground_query_must_not_execute_setuid_ps');
 assert.equal(file,'/usr/bin/python3');assert.deepEqual(args.slice(0,3),['-I','-S','-B']);assert.equal(args.at(-1),String(rootPid));assert.equal(options.timeout,5000);
 if(kind==='denied')throw Object.assign(new Error('synthetic observer denied'),{code:'EPERM'});
 if(kind==='malformed')return{stdout:'[]',stderr:''};
 const observed=structuredClone(rows);
 if(kind==='healthy_nonce')for(const row of observed){row.pid+=rootPid-201;row.pgid+=rootPid-201;row.tpgid+=rootPid-201;if(row.ppid>1)row.ppid+=rootPid-201;}
 if(kind==='wrong_parent')observed[1].ppid=999;
 if(kind==='background')observed[1].tpgid=201;
 if(kind==='wrong_path')observed[1].command='/fixture/other';
 if(kind==='empty_tree')observed.splice(0);
 if(kind==='missing_root')observed.shift();
 return {stdout:JSON.stringify({schema:1,root_pid:kind==='wrong_root'?999:rootPid,method:'macOS libproc',rows:observed}),stderr:''};
}});
childProcess.execFile=fake as any;syncBuiltinESMExports();
const {Panes}=await import('../src/panes.ts');
const {OrchestrationStore}=await import('../src/store.ts');
const directory=mkdtempSync('/private/tmp/t093-process-boundary-');const checks:any[]=[];
for(kind of ['healthy','healthy_nonce','denied','malformed','wrong_parent','background','wrong_path','empty_tree','missing_root','wrong_root','replaced_leader']){
 rootPid=kind==='healthy_nonce'?randomInt(1000,50000):201;
 const root=join(directory,kind);mkdirSync(root);const store=new OrchestrationStore(root);
 const pane:any={record:{id:kind,task:'task',attempt:null,cli:'Claude Code',argv:['/fixture/claude'],executable_path:'/fixture/claude',session:'fixture-session'},pty:{pid:201},state:'unknown',failed:null,active:null,native:'fixture-session',nativeEnded:false,queue:[],writing:false,userDraft:false,stopped:false,archived:false,leader:null};
 const panes=new Panes(root,store,{},()=>{});panes.panes.set('fixture-thread',pane);
 pane.pty.pid=rootPid;
 if(kind==='replaced_leader')pane.leader=777;
 let error:any;let result:any;
 try{
  try{result=await panes.release('fixture-thread','independent fixture');}catch(value){error=value;}
  assert(calls.at(-1)?.file!=='/bin/ps','foreground_query_must_not_execute_setuid_ps');
  if(kind.startsWith('healthy')){assert.ifError(error);assert.equal(result.state,'idle');assert.equal(pane.leader,rootPid+1);}
  else {assert(error,'bad_process_observation_must_refuse_release');assert.equal(pane.state,'unknown');}
  checks.push({case:kind,status:'PASS',released:!error});
 }catch(value){checks.push({case:kind,status:'FAIL',business_failure:(value as Error).message.split('\n')[0]});}
 finally{store.close();}
}
rmSync(directory,{recursive:true});const status=checks.every(v=>v.status==='PASS')?'PASS':'FAIL';
writeFileSync(output,JSON.stringify({status,scope:'actual Panes release; observer exec mocked; no real process query or OS profile',checks,calls},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({status,checks:checks.length}));process.exitCode=status==='PASS'?0:2;
