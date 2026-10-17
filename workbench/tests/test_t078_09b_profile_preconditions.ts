// Static facts for 09B plan review. No product fix or CLI/service start.
import assert from 'node:assert/strict';import {mkdirSync,mkdtempSync,realpathSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';import {randomUUID} from 'node:crypto';import {claudeLaunch} from '../src/claudeLaunch.ts';
const out=resolve(process.argv[2]);mkdirSync(out);const root=realpathSync(mkdtempSync('/tmp/t078-2-09b-preconditions-'));
for(const n of ['state','repo','home','claude'])mkdirSync(join(root,n));
for(const preset of ['ideation','executor'])for(const n of ['home','claude','tmp','shell','requests','hooks','user-data'])mkdirSync(join(root,'roles',preset,n),{recursive:true});
for(const preset of ['ideation','executor'])writeFileSync(join(root,'roles',preset,'role.md'),'09B static profile probe only: '+preset+'\n');
const task:any={task_id:'09b-profile-task',project_id:'09b-profile-project',repo:join(root,'repo'),spec_rev:1,base_commit:'a'.repeat(40)};
const input:any={schema:1,root,state:join(root,'state'),task:task.task_id,preset:'ideation',launch:randomUUID(),session:randomUUID(),thread:randomUUID(),executable:'/Users/luckye/.local/share/claude/versions/2.1.296',version:'2.1.296',role_file:join(root,'roles','ideation','role.md'),code_revision:'a'.repeat(40),source_snapshot:join(root,'sources.tar.gz'),api_url:'http://127.0.0.1:12345',turn_limit:2};
const i=claudeLaunch(task,input),e=claudeLaunch(task,{...input,preset:'executor',role_file:join(root,'roles','executor','role.md'),launch:randomUUID(),session:randomUUID(),thread:randomUUID()});
const shared=['HOME','CLAUDE_CONFIG_DIR','A2A_REQUEST_DIR','A2A_HOOK_TRACE_DIR','TMPDIR','ZDOTDIR'].filter(k=>i.env[k]===e.env[k]);
assert.equal(shared.length,0);
const roleEnv=Object.fromEntries(['HOME','CLAUDE_CONFIG_DIR','TMPDIR','ZDOTDIR','A2A_REQUEST_DIR','A2A_HOOK_TRACE_DIR','A2A_USER_DATA'].map(k=>[k,[i.env[k],e.env[k]]]));
for(const values of Object.values(roleEnv))assert.notEqual(values[0],values[1]);
assert.equal(claudeLaunch(task,{...input,turn_limit:3}).turn_limit,3);
let budgetError;try{claudeLaunch(task,{...input,turn_limit:7});}catch(error){budgetError=error.code;}
assert.equal(budgetError,'invalid_controller_turn_limit');
const result={status:'PASS',scope:'Actual claudeLaunch profile construction; no CLI/service start',desired_09b_contract:'PASS',launch_status:'NO_GO',root,shared_paths:shared,role_env:roleEnv,budget_error:budgetError,accepted_turn_limit:3,rejected_turn_limit:7,real_cli_starts:0,real_model_turns:0};
writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
