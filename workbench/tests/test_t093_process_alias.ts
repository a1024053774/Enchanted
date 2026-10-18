// Real managed start/release; owned symlinks, mocked exec and PTY, no process queries.
import assert from 'node:assert/strict';
import childProcess from 'node:child_process';
import {createRequire,syncBuiltinESMExports} from 'node:module';
import {promisify} from 'node:util';
import {mkdtempSync,mkdirSync,writeFileSync,symlinkSync,unlinkSync,realpathSync,rmSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
const output=process.argv[2];assert(!existsSync(output));
const root=realpathSync(mkdtempSync('/private/tmp/t078-2-t093-alias-unit-'));
const target=join(root,'claude-real'),alias=join(root,'claude-alias'),other=join(root,'claude-other');
writeFileSync(target,'owned test executable placeholder',{mode:0o700});writeFileSync(other,'other test placeholder',{mode:0o700});symlinkSync(target,alias);
let observedPath=target;const calls:any[]=[];let shellArgv:string[]=[];
const fake=Object.assign(()=>{throw new Error('unexpected exec style');},{[promisify.custom]:async(file:string,args:string[])=>{
 calls.push({file,args});
 if(args[0]==='--version'){assert.equal(file,alias);return{stdout:'2.1.302 (Claude Code)\n',stderr:''};}
 assert.equal(file,'/usr/bin/python3');
 return{stdout:JSON.stringify({schema:1,root_pid:501,method:'macOS libproc',rows:[{pid:501,ppid:1,pgid:501,tpgid:501,command:observedPath}]}),stderr:''};
}});
childProcess.execFile=fake as any;syncBuiltinESMExports();
const require=createRequire(import.meta.url),pty=require('node-pty'),originalSpawn=pty.spawn;
pty.spawn=(_file:string,argv:string[])=>{shellArgv=argv;return{pid:501,onData(){},onExit(){}};};
const {Panes}=await import('../src/panes.ts');const{OrchestrationStore}=await import('../src/store.ts');
for(const name of ['state','repo'])mkdirSync(join(root,name));
for(const name of ['home','claude','tmp','shell','requests','hooks','user-data'])mkdirSync(join(root,'roles/ideation',name),{recursive:true});
writeFileSync(join(root,'roles/ideation/role.md'),'合成角色');
const store=new OrchestrationStore(join(root,'state'));const panes=new Panes(join(root,'state'),store,{},()=>{});
const task:any={task_id:'alias-task',project_id:'alias-project',repo:join(root,'repo'),spec_rev:1,base_commit:'a'.repeat(40)};
const input:any={schema:1,root,state:join(root,'state'),task:task.task_id,preset:'ideation',launch:randomUUID(),session:randomUUID(),thread:randomUUID(),executable:alias,version:'2.1.302',role_file:join(root,'roles/ideation/role.md'),code_revision:'a'.repeat(40),source_snapshot:root,api_url:'http://127.0.0.1:23101',turn_limit:3};
const checks:any[]=[];
try{
 const record=await panes.startController(task,input);
 try{
  assert.equal(record.argv[0],alias,'actual_launch_argv_must_keep_alias');assert(shellArgv.at(-1)?.includes(alias));
  try{await panes.release(input.thread,'owned alias fixture');}catch{throw new Error('valid_alias_must_keep_foreground_identity');}
  assert.equal(panes.status(input.thread).state,'idle');assert.equal(record.executable_path,target,'live_launch_must_capture_canonical_executable');
  checks.push({case:'valid_absolute_alias',status:'PASS',argv_preserved:true,canonical_identity_captured:true});
 }catch(error){checks.push({case:'valid_absolute_alias',status:'FAIL',business_failure:(error as Error).message});}
 const pane=panes.get(input.thread);pane.state='unknown';pane.failed=null;
 // Retarget after launch: resolving the alias during the query would wrongly
 // bless the different executable. The original captured identity must win.
 unlinkSync(alias);symlinkSync(other,alias);observedPath=other;
 try{
  await assert.rejects(()=>panes.release(input.thread,'changed alias target'),'different_target_must_not_take_over_identity');
  assert.equal(pane.state,'unknown');checks.push({case:'retargeted_alias',status:'PASS',replacement_refused:true});
 }catch(error){checks.push({case:'retargeted_alias',status:'FAIL',business_failure:(error as Error).message});}
}finally{pty.spawn=originalSpawn;store.close();rmSync(root,{recursive:true});}
const status=checks.every(value=>value.status==='PASS')?'PASS':'FAIL';writeFileSync(output,JSON.stringify({status,scope:'real managed start/release with synthetic symlink and mocked process/PTY boundaries; no executable run',checks,calls:calls.map(value=>({file:value.file,version_probe:value.args[0]==='--version'}))},null,2)+'\n',{flag:'wx',mode:0o600});console.log(JSON.stringify({status,checks:checks.length}));process.exitCode=status==='PASS'?0:2;
