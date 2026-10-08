// Isolate async result-recording ownership after a known recorder failure.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { A2AGates } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
const root=mkdtempSync(join(tmpdir(),"a2a-t037-inflight-observer-"));console.log(JSON.stringify({fixture_root:root}));
const repo=join(root,"repo");mkdirSync(repo);const git=(...args:string[])=>execFileSync("git",["-C",repo,...args],{encoding:"utf8",env:{...process.env,GIT_CONFIG_NOSYSTEM:"1",GIT_CONFIG_GLOBAL:"/dev/null"}}).trim();
git("init");git("config","user.name","Independent in-flight fixture");git("config","user.email","fixture@example.invalid");git("config","commit.gpgsign","false");writeFileSync(join(repo,"input.txt"),"Independent input\n");git("add","input.txt");git("commit","-m","Independent base");const base=git("rev-parse","HEAD");
const entry=join(root,"oracle-entry"),release=join(root,"oracle-release"),oracle=join(root,"oracle.py"),instructions=join(root,"instructions.txt");
writeFileSync(oracle,`import pathlib,time\npathlib.Path(${JSON.stringify(entry)}).write_text('entered')\nwhile not pathlib.Path(${JSON.stringify(release)}).exists(): time.sleep(0.01)\nraise SystemExit(0)\n`);writeFileSync(instructions,"In-flight failure probe\n");
const gates=new A2AGates(join(root,"state"));
try{
 assert.equal((await gates.call({command:"create",task:"inflight",repo,base,oracle,instructions})).ok,true);
 const a=(await gates.call({command:"claim",task:"inflight",owner:"fixture-owner"})).attempt!;
 assert.equal((await gates.call({command:"submit",task:"inflight",attempt:a.attempt_id,session:a.session_id,fence:a.fence,spec_rev:a.spec_rev,commit:base})).ok,true);
 gates.setHumanInputObserverStatus("healthy");
 const verification=gates.call({command:"verify",task:"inflight",attempt:a.attempt_id});const deadline=performance.now()+5000;
 while(!existsSync(entry)){assert.ok(performance.now()<deadline,"Oracle barrier reached");await new Promise(r=>setTimeout(r,10));}
 gates.setHumanInputObserverStatus("failed",{event_id:"literal-failed-event",reason:"Independent recording failure"});writeFileSync(release,"release");
 const result=await Promise.race([verification,new Promise<never>((_,reject)=>setTimeout(()=>reject(new Error("BUSINESS_RED in-flight verification did not return a structured refusal")),2000))]);console.log(JSON.stringify({result}));assert.equal(result.ok,false);assert.equal(result.error,"human_input_observer_failed");assert.equal(git("rev-parse","refs/a2a/integration"),base);
 const status=await gates.call({command:"status",task:"inflight"});assert.equal(status.ok,true);assert.equal(status.task!.state,"verifying");assert.equal(status.human_input_observer!.state,"failed");
 console.log(JSON.stringify({status:"PASS",fixture_root:root,case:"inflight-result-recording-rejects-without-process-crash"}));
}finally{writeFileSync(release,"release");gates.close();}
