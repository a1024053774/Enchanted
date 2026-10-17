import { readFileSync,writeFileSync } from "node:fs";
import { join } from "node:path";
import { claudeLaunch } from "../src/claudeLaunch.ts";
const [inputFile,outputFile]=process.argv.slice(2);
if (!inputFile || !outputFile || process.argv.length!==4) throw new Error("Explicit input and new output files are required");
const input=JSON.parse(readFileSync(inputFile,"utf8"));
const task:any={task_id:input.task,project_id:"t078-p1-project",repo:join(input.root,"repo"),spec_rev:1,base_commit:input.code_revision};
const launch=claudeLaunch(task,input);
writeFileSync(outputFile,JSON.stringify({status:"INCOMPLETE",phase:"launch material only; no CLI started",input,launch,
  preflight_argv:[[input.executable,"--version"],[input.executable,"--help"]],
  permission:"P1 must separately approve these two preflights and the interactive CLI start",
  secrets:"The backend will add a fresh private A2A_CAPABILITY; no user credential is read or copied."},null,2),{flag:"wx"});
