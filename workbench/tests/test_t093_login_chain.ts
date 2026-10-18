// Sole runtime entry: run_t093_login_chain.py outside the caller sandbox.
// The daemon, PTY fixture, native hook/inbox clients and fact child inherit C.
import assert from "node:assert/strict";
import { constants, closeSync, copyFileSync, existsSync, fstatSync, lstatSync, openSync, readFileSync, rmSync, unlinkSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { serve } from "../src/daemon.ts";
import { A2AGates } from "../src/gates/core.ts";
import { createOperatorCredential, readOperatorCredential } from "../src/credentials.ts";
import { request } from "../src/transport.ts";
import { credentialHits, countForwarderRecords, homeReferences, redactCredentials, scanCredentialFiles } from "../src/claudeLoginFacts.ts";
import { recordLoginProcess } from "../src/claudeLoginProcessTrace.ts";
import { observeHomeReadBoundary } from "./t093_home_read_boundary.ts";
import { fileURLToPath } from "node:url";

const load=(path:string)=>JSON.parse(readFileSync(path,"utf8"));
const session=load(process.env.A2A_CLAUDE_LOGIN_SESSION!), privateRoot=session.private_root;
const fixture=load(join(privateRoot,"fixture.json")), root=fixture.root, state=join(root,"state"), output=fixture.output;
assert(!existsSync(output),"preserve earlier evidence");
const services=load(join(privateRoot,"services.json")), testServices=load(join(privateRoot,"test-services.json"));
const {claudeAiOauth:oauth}=load(join(privateRoot,"home/.claude/.credentials.json"));
const token=oauth.accessToken, secrets=[token,oauth.refreshToken];
const exec=promisify(execFile), checks:string[]=[], cleanupFailures:string[]=[];
const run=(file:string,args:string[],options:object={})=>{const value=exec(file,args,{cwd:join(root,"repo"),timeout:30000,maxBuffer:1024*1024,...options});recordLoginProcess("test helper: "+file.split("/").at(-1),(value as any).child.pid);return value;};
async function wait(test:()=>boolean,name:string,timeout=25000){const until=Date.now()+timeout;while(!test()){if(Date.now()>until)throw new Error(name);await new Promise(r=>setTimeout(r,30));}}
async function file(path:string){await wait(()=>existsSync(path),"fixture_file_deadline");return load(path);}
let panes:any, launch:any, facts:any, daemonStarted=false, failure:string|null=null, receipts:any[]=[], rawRecords:any[]=[], counterexamples:any={};
let removed=false;
let stage="wait_services", childExit:number|null=null;
const audit=session.audit_directory, ledger=join(audit,"forwarder/journal/requests.jsonl");
const injectionCases = [
  {name:"raw",value:token}, {name:"json",value:JSON.stringify(token).slice(1,-1)},
  {name:"url",value:encodeURIComponent(token).replace(/[!'()*]/g,c=>"%"+c.charCodeAt(0).toString(16).toUpperCase())},
  {name:"base64",value:Buffer.from(token).toString("base64")},
  {name:"base64_unpadded",value:Buffer.from(token).toString("base64").replace(/=+$/,"")},
  {name:"base64url",value:Buffer.from(token).toString("base64url")},
]; // injection cases end
const safe=(value:unknown)=>assert.equal(credentialHits(JSON.stringify(value),secrets),0,"credentials_must_not_enter_public_evidence");
try {
  assert.equal(process.pid,session.c_root_pid);
  stage="home_read_boundary";
  const readBoundary=observeHomeReadBoundary(session.real_home,fixture.read_boundary_target,fileURLToPath(import.meta.url));
  counterexamples.home_read_boundary_C=readBoundary;
  assert(readBoundary.entry_resolved&&readBoundary.metadata.every(v=>v.is_directory),"C_source_ancestor_metadata_must_be_readable");
  assert(readBoundary.content.denied&&readBoundary.content.bytes_read===0,"C_actual_HOME_content_read_must_remain_denied");
  assert(readBoundary.ancestor_directory_entries.denied,"C_ancestor_directory_enumeration_must_remain_denied");
  await file(join(session.metadata_directory,"ready.json"));
  stage="compile";
  await run("/usr/bin/clang",["-O0","-Wall","-Werror",join(fixture.source,"workbench/tests/t093_fake_claude.c"),"-o",session.manifest.executable]);
  copyFileSync(join(fixture.source,"workbench/tests/t093_fake_login_peer.py"),join(root,"fake-login-peer.py"));
  copyFileSync(join(fixture.source,"workbench/tests/probe_t093_parent_sandbox.py"),join(root,"probe_helpers.py"));
  const parentGuard:any={path:join(session.real_home,".a2a-t093-deny-"+randomUUID().replaceAll("-","")),exclusive_create:true,created:false,deleted:false,denied:false};
  try{const fd=openSync(parentGuard.path,constants.O_WRONLY|constants.O_CREAT|constants.O_EXCL|constants.O_NOFOLLOW,0o600);parentGuard.created=true;let own;try{own=fstatSync(fd);}finally{closeSync(fd);}const now=lstatSync(parentGuard.path);assert(own.ino===now.ino&&own.dev===now.dev,"exclusive_guard_file_owner_must_match");unlinkSync(parentGuard.path);parentGuard.deleted=true;}
  catch(error:any){parentGuard.errno=error.errno;parentGuard.denied=!parentGuard.created&&["EPERM","EACCES"].includes(error.code);}
  assert.equal(parentGuard.denied,true,"C_parent_home_write_must_be_denied");counterexamples.parent_home_write=parentGuard;
  createOperatorCredential(state);const operator=readOperatorCredential(state)!;
  await serve(state,{},(directory,value)=>{panes=value;return new A2AGates(directory,value);});daemonStarted=true;
  const task:any={task_id:"t093-chain",project_id:"t093-fixture",repo:join(root,"repo"),spec_rev:1,base_commit:"a".repeat(40),state:"registered",current_attempt:null};
  panes.store.db.prepare("INSERT INTO tasks VALUES (?,?)").run(task.task_id,JSON.stringify(task));
  panes.store.db.prepare("INSERT INTO inbox_records VALUES (?,?)").run(fixture.inbox_sentinel,JSON.stringify({schema:1,id:fixture.inbox_sentinel,kind:"report",from:"executor",to:"ideation",body:"独立 Stop 转交哨兵",reply_to:null,refs:[],created_at:new Date().toISOString()}));
  stage="controller_start";
  const started=await request(state,{command:"controller_start",task:task.task_id,manifest:session.manifest},operator);
  assert.equal(started.ok,true,"controller_start_must_succeed: "+started.error);launch=started.launch;
  const preflight=load(join(audit,"preflight.json"));
  assert.equal(preflight.phase,"before_cli_input");assert.equal(preflight.counts.model_requests,0);assert.equal(preflight.counts.counts_match,true);
  assert.equal(preflight.credential_scan.hits,0);assert.equal(preflight.credential_scan.launch_record_hits,0);assert.equal(preflight.inventory.comparison_pending,true);
  const initialFacts=JSON.parse((await run(process.execPath,[join(fixture.source,"workbench/src/claudeLoginCheck.ts"),"--preflight",audit])).stdout);
  assert.equal(initialFacts.counts.model_requests,0);assert.equal(initialFacts.inventory.before_phase,"before_original_auth_read");
  counterexamples.preflight=initialFacts;
  const trace=join(state,"traces",launch.id,"pty.raw");
  stage="boundaries";
  await wait(()=>readFileSync(trace,"utf8").includes("fixture-ready"),"fixture_startup_deadline");
  assert.equal(launch.shell_argv.at(-1).includes("sandbox-exec"),false,"CLI_must_inherit_outer_C");
  checks.push("controller_start; single inherited C; original source HOME inaccessible");
  const cliGuard=load(join(root,"cli-guards.json"));
  assert.equal(cliGuard.real_home_write.denied,true,"CLI_child_home_write_must_be_denied");
  assert.equal(cliGuard.upstream_bypass.denied,true,"CLI_upstream_bypass_must_be_denied");counterexamples.cli=cliGuard;
  assert.deepEqual(cliGuard.source_home,{r:true,a:true},"source_home_read_and_write_must_be_denied");assert.equal(cliGuard.config_matches,true,"minimal_onboarding_and_trust_state_must_match");
  const fGuard=await file(join(session.forwarder_directory,"guards.json"));
  assert.equal(fGuard.real_home_write.denied,true,"F_home_write_must_be_denied");
  assert(fGuard.home_read_boundary.entry_resolved&&fGuard.home_read_boundary.metadata.every((v:any)=>v.is_directory),"F_source_ancestor_metadata_must_be_readable");
  assert(fGuard.home_read_boundary.content.denied&&fGuard.home_read_boundary.content.bytes_read===0,"F_actual_HOME_content_read_must_remain_denied");
  assert(fGuard.home_read_boundary.ancestor_directory_entries.denied,"F_ancestor_directory_enumeration_must_remain_denied");
  assert.equal(fGuard.outside_records_write.denied,true,"F_write_must_stay_in_records");
  assert.equal(fGuard.unconfigured_upstream.denied,true,"F_unconfigured_upstream_must_be_denied");
  assert.equal(fGuard.other_listener.denied,true,"F_other_listener_must_be_denied");assert.equal(fGuard.fork.denied,true,"F_fork_must_be_denied");counterexamples.forwarder=fGuard;
  const pythonGuards=[];
  for(const path of [join(session.forwarder_directory,"python-guards.json"),join(session.metadata_directory,"guards.json"),join(root,"U/guards.json")]){
    const value=await file(path);assert(value.real_home_write.denied);assert(value.fork.denied);assert.deepEqual(Object.values(value.security),[1100,1100]);pythonGuards.push(value);
  }
  counterexamples.protected_helpers=pythonGuards;
  const baseline=await file(join(root,"S/result.json")),mutant=await file(join(root,"M/result.json"));
  assert.equal(baseline.primary_failure,null,"synthetic_home_control_must_pass");
  assert.equal(mutant.primary_failure,"home_write_must_be_denied","removed_guard_must_fail_business_assertion");
  assert(mutant.synthetic_write.created&&mutant.synthetic_write.deleted&&mutant.synthetic_write.absent_after);
  assert(baseline.real_home_write.denied&&mutant.real_home_write.denied);
  counterexamples.synthetic_guard={baseline,mutant,mutant_rejected:true,limit:"Only synthetic HOME deny rule removed; actual HOME deny remains."};
  const probes=[parentGuard.path,cliGuard.real_home_write.path,fGuard.real_home_write.path,...pythonGuards.map(v=>v.real_home_write.path),baseline.real_home_write.path,mutant.real_home_write.path];
  writeFileSync(join(privateRoot,"home-probes.json"),JSON.stringify(probes),{mode:0o600,flag:"wx"});
  checks.push("actual HOME writes denied; F peer/listener/fork/write boundaries; CLI direct upstream denied; synthetic missing guard rejected and deleted");
  stage="turns";
  assert((await request(state,{command:"pane_release",thread:launch.thread,reason:"deterministic fixture ready"},operator)).ok);
  assert((await request(state,{command:"pane_dispatch",thread:launch.thread,body:fixture.prompt},operator)).ok);
  await wait(()=>readFileSync(trace,"utf8").includes("fixture-turn-2-complete"),"two_hook_Stop_cycles_deadline");
  receipts=load(join(root,"U/received.json"));rawRecords=readFileSync(ledger,"utf8").split("\n").filter(Boolean).map(JSON.parse);
  assert.equal(receipts.length,2,"independent_upstream_must_receive_two_attempts");
  assert.equal(rawRecords.filter(row=>row.kind==="request").length,receipts.length,"forwarder_record_count_must_match_upstream");
  assert(receipts.every(v=>v.recorded_before_receipt),"durable_records_must_precede_upstream");
  assert(receipts.every(v=>v.bearer_matches_copy&&v.messages_present&&v.prompt_matches_fixture&&v.method==="POST"&&v.path==="/v1/messages"));
  assert.deepEqual(rawRecords.filter(row=>row.kind==="outcome").map(v=>v.status),[400,200]);
  const results=panes.store.db.prepare("SELECT data FROM relay_results").all().map((r:any)=>JSON.parse(r.data));
  assert.equal(results.length,1);assert.equal(results[0].ok,true);assert.deepEqual(results[0].entries.map((v:any)=>v.entry.id),[fixture.inbox_sentinel]);assert.equal(panes.status(launch.thread).state,"idle");
  checks.push("two attempts journaled before independent upstream; 400 retry counted; native hook/Stop inbox sentinel delivered once");
  stage="counterexamples";
  const extra=launch.argv.length, injected={...launch,argv:[...launch.argv,session.real_home+"/t093-path-counterexample"]};
  const refs=homeReferences(injected,session.real_home);
  counterexamples.home_references=refs;assert(refs.some(v=>v.field===`launch.argv[${extra}]`&&v.occurrences===1),"home_path_injection_must_be_reported");
  counterexamples.credential_injection_case_count=injectionCases.length;
  assert(injectionCases.length>0,"credential_injection_cases_must_not_be_empty");
  const leaked=join(state,"synthetic-credential-injection"),injections:any[]=[];
  counterexamples.credential_injections=injections;
  for(const sample of injectionCases){writeFileSync(leaked,sample.value,{mode:0o600});assert.equal(readFileSync(leaked,"utf8"),sample.value,"credential_injection_must_execute");const found=scanCredentialFiles(state,secrets);injections.push({variant:sample.name,hits:found.hits});assert(found.hits>0,"credential_injection_must_be_detected");}
  assert.equal(injections.length,injectionCases.length,"all_credential_injections_must_execute");rmSync(leaked);assert.equal(scanCredentialFiles(state,secrets).hits,0);counterexamples.credential_injections=injections;
  checks.push("actual launch record HOME injection reported; independent raw/JSON/URL/base64 injections detected and removed");
  stage="finalization";
  assert((await request(state,{command:"daemon_stop"},operator)).ok);
  await wait(()=>!existsSync(join(state,"daemon.pid")),"daemon_shutdown_deadline");daemonStarted=false;
  facts=load(join(audit,"facts.json"));
  assert.equal(facts.counts.counts_match,true,"final_counts_must_match");assert.equal(facts.counts.model_requests,receipts.length);assert.equal(facts.forwarder.forwarded,receipts.length);assert.equal(facts.credential_scan.hits,0);
  assert.equal(facts.isolated_home_removed,true);assert.equal(existsSync(privateRoot),false);
  assert.equal(facts.inventory.pass_condition,false);assert.equal(facts.inventory.collection_complete,true);assert(Array.isArray(facts.inventory.changed));assert.equal(facts.onboarding.preflight_observed,false);assert.equal(facts.auth_original_reads,1);
  assert.equal(facts.onboarding.state_intact,true);
  assert(facts.processes.D.home_probe_paths.length===probes.length&&facts.processes.D.home_probe_paths.every((v:any)=>v.absent),"independent_real_home_probe_files_must_be_absent");
  assert.equal(facts.cleanup.primary_failure,null);assert.deepEqual(facts.cleanup.cleanup_failures,[]);
  const checked=JSON.parse((await run(process.execPath,[join(fixture.source,"workbench/src/claudeLoginCheck.ts"),audit])).stdout);assert.equal(checked.counts.model_requests,receipts.length);
  checks.push("fact child inherits C; raw recount agrees; entire private HOME removed; independent post inventory complete and informational; scan zero");
  stage="missing_record";
  const original=readFileSync(ledger,"utf8"),missing=rawRecords.filter(row=>!(row.kind==="request"&&row.sequence===2));writeFileSync(ledger,missing.map(v=>JSON.stringify(v)).join("\n")+"\n");
  const missingCounts=countForwarderRecords(ledger,receipts.length);counterexamples.missing_record={counts:missingCounts,raw_records:missing};assert.equal(missingCounts.counts_match,false,"missing_raw_request_must_be_detected");
  const reread=JSON.parse((await run(process.execPath,[join(fixture.source,"workbench/src/claudeLoginCheck.ts"),audit])).stdout);assert.equal(reread.counts.counts_match,false,"fact_child_must_report_missing_raw_request");
  counterexamples.missing_record={counts:missingCounts,raw_records:missing};writeFileSync(ledger,original);
  checks.push("missing raw request detected by both recount and actual fact command");
}catch(error){const message=error instanceof Error?error.message.split("\n",1)[0].split(":",1)[0]:"chain_failed";failure=/^[A-Za-z0-9_]{1,120}$/.test(message)?message:"chain_operation_failed";childExit=typeof (error as any)?.code==="number"?(error as any).code:null;}
finally{
  const leak=join(state,"synthetic-credential-injection");if(existsSync(leak))rmSync(leak);
  if(daemonStarted){try{await request(state,{command:"daemon_stop"},readOperatorCredential(state));await wait(()=>!existsSync(join(state,"daemon.pid")),"cleanup_daemon_deadline");}catch{cleanupFailures.push("daemon_cleanup_unconfirmed");}}
  if(existsSync(privateRoot)){try{const abort=join(session.metadata_directory,"abort");if(!existsSync(abort))writeFileSync(abort,"\n",{flag:"wx",mode:0o600});await file(join(session.metadata_directory,"removed.json"));}catch{cleanupFailures.push("session_abort_cleanup_unconfirmed");}}
  try{writeFileSync(join(root,"U/stop"),"\n",{flag:"wx",mode:0o600});await file(join(root,"U/closed.json"));}catch{cleanupFailures.push("upstream_shutdown_unconfirmed");}
  for(const value of Object.values(testServices) as any[]){try{process.kill(-value.pgrp,"SIGKILL");}catch(error:any){if(error.code!=="ESRCH")cleanupFailures.push("test_group_cleanup_failed");}try{await wait(()=>{try{process.kill(-value.pgrp,0);return false;}catch(e:any){return e.code==="ESRCH";}},"test_group_exit_deadline",5000);}catch{cleanupFailures.push("test_group_exit_unconfirmed");}}
  if(existsSync(privateRoot))cleanupFailures.push("private_home_cleanup_unconfirmed");
  if(!facts&&existsSync(join(audit,"facts.json")))facts=load(join(audit,"facts.json"));
  const processLog=existsSync(join(audit,"C-processes.jsonl"))?readFileSync(join(audit,"C-processes.jsonl"),"utf8").split("\n").filter(Boolean).map(JSON.parse):[];
  const result:any={status:failure||cleanupFailures.length?"INCOMPLETE":"PASS",task:"T-093",candidate:fixture.candidate,mutation:fixture.mutation,checks,primary_failure:failure,cleanup_failures:cleanupFailures,upstream_requests:receipts.length,independent_upstream_receipts:receipts,real_upstream_requests:0,real_cli_starts:0,real_model_turns:0,auth_source:"synthetic file only; one original read in independent preparation",git_index_credential_hits:fixture.git_index_hits,facts,forwarder_raw_records:rawRecords,counterexamples,processes:{C:processLog,F:services.F,D:services.D,...testServices,G:fixture.G_processes},profiles:{...session.profiles,...fixture.test_profiles,G:fixture.G_profile},fixture_removed:false};
  result.processes.baseline=session.initial_inventory_process;
  result.real_auth_reads=0;result.node_version=process.version;result.scope="compiled deterministic fixture, not the vendor CLI";
  result.failure_stage=failure?stage:null;result.child_exit=childExit;
  result.service_receipts={};
  for(const [name,path] of Object.entries({F:join(session.forwarder_directory,"closed.json"),D:join(session.metadata_directory,"closed.json"),cleanup:join(session.metadata_directory,"removed.json"),F_guards:join(session.forwarder_directory,"guards.json"),F_python_guards:join(session.forwarder_directory,"python-guards.json"),D_guards:join(session.metadata_directory,"guards.json"),U_guards:join(root,"U/guards.json")}))if(existsSync(path))result.service_receipts[name]=load(path);
  try{safe(result);assert.equal(scanCredentialFiles(state,secrets).hits,0,"final_state_must_be_credential_free");}catch{result.status="INCOMPLETE";result.primary_failure??="public_credential_scan_failed";}
  rmSync(root,{recursive:true});removed=!existsSync(root);result.fixture_removed=removed;
  const encoded=redactCredentials(JSON.stringify(result,null,2),secrets)+"\n";
  // Independent writer checks remain active even in the empty-injection-case
  // mutation. No raw credentials, assertion diffs or header bodies escape.
  for(const value of secrets)for(const secret of [value,JSON.stringify(value).slice(1,-1),encodeURIComponent(value),Buffer.from(value).toString("base64"),Buffer.from(value).toString("base64url")])assert(!encoded.includes(secret),"public_writer_must_remove_credentials");
  writeFileSync(output,encoded,{flag:"wx",mode:0o600});
  console.log(redactCredentials(JSON.stringify({status:result.status,checks:checks.length,primary_failure:result.primary_failure,cleanup_failures:cleanupFailures,upstream_requests:receipts.length}),secrets));process.exitCode=result.status==="PASS"?0:2;
}
