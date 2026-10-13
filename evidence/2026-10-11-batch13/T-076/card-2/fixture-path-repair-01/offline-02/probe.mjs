
import assert from 'node:assert/strict';
import {readFileSync, mkdirSync, realpathSync, statSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const [source, control, mode] = process.argv.slice(2);
const {installControlledPTY} = await import(pathToFileURL(join(source,'workbench/tests/controlled_quality_pty.ts')));
const config = JSON.parse(readFileSync(join(control,'config.json'),'utf8'));
const bind = installControlledPTY(source,control,config);
bind({store:{db:{prepare:()=>({all:()=>[]})}}});
const require = createRequire(join(source,'workbench/src/panes.ts'));
const pty = require('node-pty'); // spawn below is the installed JS fixture only.
const home = realpathSync(config.reviewers[0].codex_home);
const requestDir = join(control,'requests'); mkdirSync(requestDir);
const env = {CODEX_HOME:home,A2A_ROLE:'reviewer',A2A_LAUNCH:'fixture-path-probe',
  A2A_REQUEST_DIR:realpathSync(requestDir),A2A_CAPABILITY:'local-fixture-token'};
const refused = /Controlled terminal received an unexpected shell or home\./;
if(mode==='before') {
  assert.throws(()=>pty.spawn('/bin/zsh',[],{env}),refused);
  console.log(JSON.stringify({status:'PASS',scope:'old fixture reproduced its alias rejection'}));
} else {
  assert.equal(config.reviewers[0].codex_home,home);
  assert.throws(()=>pty.spawn('/bin/sh',[],{env}),refused);
  const alien=join(control,'unregistered'); mkdirSync(alien);
  assert.throws(()=>pty.spawn('/bin/zsh',[],{env:{...env,CODEX_HOME:alien}}),refused);
  const terminal=pty.spawn('/bin/zsh',['fixture-arguments'],{env});
  terminal.write('\x1b[200~fixture\x1b[201~'); terminal.write('\r');
  const metadata=JSON.parse(readFileSync(join(control,'fixture-path-probe.json'),'utf8'));
  assert.deepEqual(metadata.env,env);
  assert.equal(metadata.log,join(home,'sessions','rollout-fixture-native-fixture-path-probe.jsonl'));
  const records=readFileSync(metadata.log,'utf8').trimEnd().split('\n').map(JSON.parse);
  assert.deepEqual(records.map(r=>r.type),['session_meta','event_msg','turn_context']);
  assert.deepEqual(records[0].payload,{source:'cli',id:metadata.native});
  assert.equal(records[1].payload.type,'task_started');
  assert.equal(records[1].payload.turn_id,'fixture-turn-1');
  assert.deepEqual(records[2].payload,{turn_id:'fixture-turn-1',model:'gpt-6.1-sol',effort:'xhigh'});
  const {reviewRequest}=await import(pathToFileURL(join(source,'workbench/src/gates/qualityProtocol.ts')));
  const {writeReviewRequest,readWorkerRequests}=await import(pathToFileURL(join(source,'workbench/src/relayFiles.ts')));
  const packet={schema:1,request_id:'review-fixture-review',command:'review_submit',task:'fixture-task',
    attempt:'fixture-attempt',session:'fixture-reviewer',fence:1,spec_rev:1,review_id:'fixture-review',
    candidate_commit:'a'.repeat(40),verdict:'可合并',findings:[]};
  const parsed=reviewRequest(JSON.stringify(packet));
  const file=writeReviewRequest(env.A2A_REQUEST_DIR,parsed);
  assert.deepEqual(readWorkerRequests(env.A2A_REQUEST_DIR),[file]);
  assert.deepEqual(JSON.parse(file.raw),packet);
  assert.equal(statSync(join(env.A2A_REQUEST_DIR,file.name)).mode & 0o777,0o600);
  assert.deepEqual(writeReviewRequest(env.A2A_REQUEST_DIR,parsed),file);
  let exited=false; terminal.onExit(()=>{exited=true;}); terminal.kill('fixture-only');
  assert.equal(exited,true); // JS callback, no process signal is sent.
  writeFileSync(join(control,'offline-observations.json'),JSON.stringify({metadata,records,file})+'\n');
  console.log(JSON.stringify({status:'PASS',scope:'strict fixture homes/shell, session bytes and B file helpers only'}));
}
