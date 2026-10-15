import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, realpathSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { claudeLaunch } from "../src/claudeLaunch.ts";
const output=process.argv[2];mkdirSync(output);
const root=realpathSync(mkdtempSync("/tmp/t078-2-profile08-"));
for(const n of ["state","repo","home","claude","hooks"])mkdirSync(join(root,n));
for(const preset of ["ideation","executor"])for(const n of ["home","claude","tmp","shell","requests","hooks","user-data"])mkdirSync(join(root,"roles",preset,n),{recursive:true});
writeFileSync(join(root,"role.md"),"仅回复 nonce。\n");
const task:any={task_id:"p08",project_id:"p08",repo:join(root,"repo"),spec_rev:1,base_commit:"a".repeat(40)};
const input:any={schema:1,root,state:join(root,"state"),task:"p08",preset:"ideation",launch:randomUUID(),session:randomUUID(),thread:randomUUID(),
  executable:"/Users/luckye/.local/share/claude/versions/2.1.296",role_file:join(root,"role.md"),code_revision:"a".repeat(40),source_snapshot:join(root,"source.tar.gz"),api_url:"http://127.0.0.1:12345"};
const p=claudeLaunch(task,input),checks:any[]=[];
for(const [name,run] of [
  ["title_disabled_and_demo_removed",()=>{assert.equal((p.env as any).CLAUDE_CODE_DISABLE_TERMINAL_TITLE,"1");assert.equal(Object.hasOwn(p.env,"IS_DEMO"),false);}],
  ["native_debug_and_hook_trace",()=>{const i=p.argv.indexOf("--debug-file");assert.ok(i>=0);assert.equal(p.argv[i+1],join(root,"roles","ideation","claude-debug.log"));assert.equal((p.env as any).A2A_HOOK_TRACE_DIR,join(root,"roles","ideation","hooks"));}],
  ["auth_and_timeout_preserved",()=>{assert.equal(p.env.ANTHROPIC_AUTH_TOKEN,"a2a-fixture-key-not-a-secret");assert.equal(Object.hasOwn(p.env,"ANTHROPIC_API_KEY"),false);assert.deepEqual(Object.keys(p.settings),["hooks"]);for(const group of Object.values(p.settings.hooks) as any[])assert.equal(group[0].hooks[0].timeout,3);assert.equal(p.argv.includes("--bare"),false);assert.equal(p.turn_limit,1);}]
] as [string,()=>void][]){try{run();checks.push({name,status:"PASS"});}catch(e){checks.push({name,status:"INCOMPLETE",error:String(e)});}}
const r={status:checks.every(c=>c.status==="PASS")?"PASS":"INCOMPLETE",checks,argv:process.argv,scope:"Pure construction; no CLI, API, or trust action"};
writeFileSync(join(output,"results.json"),JSON.stringify(r,null,2));console.log(JSON.stringify(r));process.exitCode=r.status==="PASS"?0:1;
