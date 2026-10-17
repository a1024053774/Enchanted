// Real daemon + cli.ts signal transport; no vendor CLI/API/model.
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, realpathSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';
import { serve } from '../src/daemon.ts';
import { A2AGates } from '../src/gates/core.ts';
import { createOperatorCredential, readOperatorCredential } from '../src/credentials.ts';
import { request } from '../src/transport.ts';

const phase=process.argv[2] as 'red'|'green', output=resolve(process.argv[3]); mkdirSync(output);
const fixture=realpathSync(mkdtempSync('/tmp/t078-2-newline-signal-')),state=join(fixture,'state');
mkdirSync(state);mkdirSync(join(fixture,'roles','ideation','hooks'),{recursive:true});mkdirSync(join(fixture,'requests'));
process.env.A2A_OPERATOR_CREDENTIAL=join(state,'operator.json');createOperatorCredential(state);const operator=readOperatorCredential(state)!;
let panes:any,gates:any;await serve(state,{},(root,p)=>{panes=p;gates=new A2AGates(root,p);return gates;});panes.shutdown=async()=>{};
const record:any={id:randomUUID(),task:'newline-task',thread:randomUUID(),project:'newline-project',attempt:null,role:'controller',preset:'ideation',session:randomUUID(),spec_rev:1,cli:'Claude Code',turn_limit:2,authentication:'isolated fake API only',env:{A2A_REQUEST_DIR:join(fixture,'requests')}};
const task={task_id:record.task,project_id:record.project,repo:fixture,spec_rev:1,current_attempt:null};panes.store.db.prepare('INSERT INTO tasks VALUES (?,?)').run(record.task,JSON.stringify(task));panes.store.launch(record);
const writes:any[]=[];const token=randomUUID();const pane:any={record,task,attempt:null,token,pty:{pid:11,write:(v:any)=>writes.push(v)},state:'busy',native:record.session,active:null,queue:[],writing:false,stopInProgress:false,writes:Promise.resolve(),pendingInputs:0,userDraft:false,interrupted:false,sending:null,offsets:new Map(),model:'unknown',effort:'unknown',terminalBuffer:'',claudePromptId:null,claudePromptIds:new Set(),failed:null,stopped:false,archived:false,inputGeneration:0,interruption:null};panes.panes.set(record.thread,pane);panes.processInfo=async()=>({leader:12,shell_pid:11,native_session:record.session,failed:null});gates.registerController(record.thread);
const registered=panes.store.register(record.id,'I1 newline probe\n');pane.active={id:randomUUID(),dispatch:registered.id,at:new Date().toISOString(),nativeTurn:null};panes.store.event('turn_submit_intent',pane.active,record);
const prompt=registered.text.replace(/[\r\n]+$/,'');
async function hook(value:any){const env={...process.env,PATH:'/opt/homebrew/bin:/usr/bin:/bin',A2A_ROLE:'controller',A2A_PRESET:'ideation',A2A_LAUNCH:record.id,A2A_CAPABILITY:token,A2A_NATIVE_SESSION:record.session,A2A_STATE:state,A2A_REQUEST_DIR:record.env.A2A_REQUEST_DIR,A2A_HOOK_TRACE_DIR:join(fixture,'roles','ideation','hooks')};return await new Promise<any>((done,fail)=>{const p=spawn(process.execPath,[resolve('workbench/src/gates/cli.ts'),'--state',state,'signal','--launch',record.id],{env,stdio:['pipe','pipe','pipe']});let stdout='',stderr='';p.stdout.on('data',v=>stdout+=v);p.stderr.on('data',v=>stderr+=v);p.on('error',fail);p.on('close',code=>done({code,stdout,stderr}));p.stdin.end(JSON.stringify(value));});}
const checks:any[]=[];const first=await hook({session_id:record.session,hook_event_name:'UserPromptSubmit',prompt_id:randomUUID(),prompt});
if(phase==='red') checks.push({name:'trimmed-final-newline-blocked-before-fix',status:first.code===0&&JSON.parse(first.stdout).decision==='block'?'PASS':'INCOMPLETE',exit_code:first.code,stdout:first.stdout,stderr:first.stderr,registered:registered.text,observed:prompt});
else {
  checks.push({name:'trimmed-final-newline-accepted',status:first.code===0&&JSON.parse(first.stdout).decision===undefined?'PASS':'INCOMPLETE',exit_code:first.code,stdout:first.stdout,stderr:first.stderr});
  const negative=await hook({session_id:record.session,hook_event_name:'UserPromptSubmit',prompt_id:randomUUID(),prompt:prompt.replace('newline probe','newline PROBE')});
  checks.push({name:'middle-text-mutation-blocked',status:negative.code===0&&JSON.parse(negative.stdout).decision==='block'?'PASS':'INCOMPLETE',exit_code:negative.code,stdout:negative.stdout,stderr:negative.stderr});
}
await request(state,{command:'daemon_stop'},operator);const result={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',phase,checks,registered:registered.text,observed_prompt:prompt,scope:'real daemon/cli.ts signal; no vendor CLI/API/model'};writeFileSync(join(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=result.status==='PASS'?0:1;
