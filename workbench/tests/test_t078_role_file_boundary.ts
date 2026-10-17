// Known-bad boundary probe: the pre-09B dual-path implementation accepts root/role.md.
import assert from 'node:assert/strict';import {mkdirSync,mkdtempSync,realpathSync,writeFileSync} from 'node:fs';import {join,resolve} from 'node:path';import {randomUUID} from 'node:crypto';import {claudeLaunch} from '../src/claudeLaunch.ts';
const out=resolve(process.argv[2]);mkdirSync(out);const root=realpathSync(mkdtempSync('/tmp/t078-2-role-boundary-'));
for(const n of ['state','repo'])mkdirSync(join(root,n));for(const p of ['ideation','executor'])for(const n of ['home','claude','tmp','shell','requests','hooks','user-data'])mkdirSync(join(root,'roles',p,n),{recursive:true});
writeFileSync(join(root,'role.md'),'legacy root role\n');const task:any={task_id:'boundary',project_id:'boundary',repo:join(root,'repo'),spec_rev:1,base_commit:'a'.repeat(40)};
const input:any={schema:1,root,state:join(root,'state'),task:'boundary',preset:'ideation',launch:randomUUID(),session:randomUUID(),thread:randomUUID(),executable:'/Users/luckye/.local/share/claude/versions/2.1.296',version:'2.1.296',role_file:join(root,'role.md'),code_revision:'a'.repeat(40),source_snapshot:join(root,'sources.tar.gz'),api_url:'http://127.0.0.1:12345'};
let accepted=false,error:any;try{claudeLaunch(task,input);accepted=true;}catch(e){error=e;}
const result={status:accepted?'INCOMPLETE':'PASS',expected:'controller_launch_config_required',observed:accepted?'accepted':error?.code,scope:'Known-bad current dual-path implementation; no process'};
writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=accepted?1:0;
