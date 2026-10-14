import assert from "node:assert/strict";
import { mkdtempSync,mkdirSync,realpathSync,readFileSync,writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { claudeLaunch } from "../src/claudeLaunch.ts";

const [helpFile,output]=process.argv.slice(2);mkdirSync(output);
const help=readFileSync(helpFile,"utf8");
assert.ok(help.includes("--append-system-prompt <prompt>"),"Official installed CLI help must name the text option");
const root=realpathSync(mkdtempSync("/tmp/t078-2-role-"));
for(const name of ["state","repo","home","claude"])mkdirSync(join(root,name));
const role="只回复 P1_ROLE_SENTINEL\n保留字符：' \"$()\" `literal`。\n";
writeFileSync(join(root,"role.md"),role,"utf8");
const task:any={task_id:"role-fixture",project_id:"role-project",repo:join(root,"repo"),spec_rev:1,base_commit:"a".repeat(40)};
const input:any={schema:1,root,state:join(root,"state"),task:task.task_id,preset:"ideation",launch:randomUUID(),session:randomUUID(),thread:randomUUID(),
  executable:"/Users/luckye/.local/share/claude/versions/2.1.296",role_file:join(root,"role.md"),code_revision:"a".repeat(40),source_snapshot:join(root,"source.tar.gz"),api_url:"http://127.0.0.1:12345"};
const launch=claudeLaunch(task,input);let passed=false,error:string|null=null;
try {
  const index=launch.argv.indexOf("--append-system-prompt");assert.ok(index>=0);
  assert.equal(launch.argv[index+1],role);assert.equal(launch.role_text,role);
  assert.equal(launch.argv.includes("--append-system-prompt-file"),false);
  assert.equal(launch.argv[0],input.executable);passed=true;
} catch(e){error=String(e);}
const result={status:passed?"PASS":"INCOMPLETE",error,argv:process.argv,observed_argv:launch.argv,
  scope:"Pure construction against saved official CLI help; no vendor CLI or model invocation",real_cli_starts:0};
writeFileSync(join(output,"results.json"),JSON.stringify(result,null,2));console.log(JSON.stringify({status:result.status,error}));
process.exitCode=passed?0:1;
