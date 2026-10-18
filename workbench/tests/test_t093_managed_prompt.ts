// Actual dispatch/store/PTY write boundary, with an external managed-text oracle.
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,existsSync,writeFileSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
import {Panes} from '../src/panes.ts';
import {OrchestrationStore} from '../src/store.ts';
const output=process.argv[2];assert(!existsSync(output));const root=mkdtempSync('/private/tmp/t093-managed-text-'),store=new OrchestrationStore(root);
const input='独立 '+randomUUID()+'\n中间  空白 “精确” 😀';
const expected='⟦主控 #1⟧\n'+input,expectedBody={messages:[{role:'user',content:expected}]};
const writes:string[]=[];const record:any={id:randomUUID(),thread:randomUUID(),task:'managed-text',attempt:null,cli:'Claude Code',turn_limit:3};
const pane:any={record,pty:{write:(text:string)=>writes.push(text)},state:'idle',active:null,failed:null,stopped:false,queue:[],writing:false,pendingInputs:0,userDraft:false,interrupted:false,writes:Promise.resolve()};
const panes=new Panes(root,store,{},()=>{});store.launch(record);panes.panes.set(record.thread,pane);
let status='PASS',failure:string|null=null;
try{
 const dispatched=await panes.dispatch(pane,input);
 assert.equal(dispatched.seq,1,'fresh_fixture_first_sequence_must_be_one');
 assert.equal(dispatched.text,expected,'managed_dispatch_must_match_external_text_contract');
 assert.deepEqual(writes,['\x1b[200~'+expected+'\x1b[201~','\r'],'PTY_bytes_must_preserve_exact_managed_text');
 const body={messages:[{role:'user',content:writes[0]!.slice(6,-6)}]};
 assert.deepEqual(body,expectedBody,'fake_CLI_payload_must_include_managed_envelope');
}catch(error){status='FAIL';failure=(error as Error).message.split('\n')[0];}
finally{store.close();rmSync(root,{recursive:true});}
writeFileSync(output,JSON.stringify({status,scope:'actual dispatch/store and supplied PTY sink; no CLI/auth/network/process query',failure,managed_prefix:true,checks:4},null,2)+'\n',{flag:'wx',mode:0o600});console.log(JSON.stringify({status,checks:4}));process.exitCode=status==='PASS'?0:2;
