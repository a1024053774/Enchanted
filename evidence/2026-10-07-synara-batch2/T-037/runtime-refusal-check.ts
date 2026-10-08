// A known native identity refusal must preserve its reason and raw observation.
// Failure modes: replace known refusal with unknown; lose the observation;
// reclaim after identity conflict; run the oracle; accept or move the Git ref.
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { A2AGates, Refusal } from "/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts";
const root=mkdtempSync(join(tmpdir(),"a2a-t037-runtime-refusal-"));console.log(JSON.stringify({fixture_root:root}));
const repo=join(root,"repo");mkdirSync(repo);
const git=(...args:string[])=>execFileSync("git",["-C",repo,...args],{encoding:"utf8",env:{...process.env,GIT_CONFIG_NOSYSTEM:"1",GIT_CONFIG_GLOBAL:"/dev/null"}}).trim();
git("init");git("config","user.name","Independent refusal fixture");git("config","user.email","fixture@example.invalid");git("config","commit.gpgsign","false");writeFileSync(join(repo,"input.txt"),"Independent input\n");git("add","input.txt");git("commit","-m","Independent base");const base=git("rev-parse","HEAD");
const oracle=join(root,"oracle.py"),instructions=join(root,"instructions.txt");writeFileSync(oracle,"raise RuntimeError('Oracle must not run after identity refusal')\n");writeFileSync(instructions,"Native refusal record probe\n");
let live:any;let reads=0;const closes:string[]=[];
const observation={nonce:"independent-native-cwd-change",actual_workspace:join(root,"foreign-worktree")};
const gates=new A2AGates(join(root,"state"),{ensureProject:async()=>{},createThread:async(_t,a)=>{live={workspace:a.workspace,provider:"codex",turn:null,running:false,stopped:false,archived:false};},startThread:async()=>{live.turn="owned-turn";},readThread:async()=>{if(++reads===3)throw new Refusal("identity_conflict",observation);return {...live};},stopThread:async t=>{closes.push(t);},archiveThread:async t=>{closes.push(t);}});
try {
 assert.equal((await gates.call({command:"create",task:"refusal",project:"literal-project",repo,base,oracle,instructions})).ok,true);
 const result=await gates.call({command:"run",task:"refusal",runtimeMode:"approval-required",wait_seconds:2});console.log(JSON.stringify({result,closes}));
 assert.equal(result.ok,false);assert.equal(result.error,"identity_conflict","BUSINESS_RED known native refusal was relabeled as unknown");assert.deepEqual(result.details,observation,"Raw identity observation must survive");
 assert.equal(result.run!.outcome,"paused");assert.equal(result.task!.state,"claimed");assert.deepEqual(closes,[]);assert.equal(git("rev-parse","refs/a2a/integration"),base);assert.equal(result.task!.candidate_commit,null);
 const events=(await gates.call({command:"events",task:"refusal"})).events!;assert.ok(events.some(e=>e.type==="run_finished"&&(e.details as any).details?.nonce===observation.nonce));
 console.log(JSON.stringify({status:"PASS",fixture_root:root,cases:["preserve-known-refusal","retain-raw-observation","no-reclaim","no-acceptance"]}));
} finally {gates.close();}
