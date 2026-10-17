import assert from "node:assert/strict";
import {mkdtempSync,mkdirSync,realpathSync,writeFileSync} from "node:fs";
import {join} from "node:path";
import {randomUUID} from "node:crypto";
const {claudeLaunch}=await import(process.argv[3]??new URL("../src/claudeLaunch.ts",import.meta.url).href);
const out=process.argv[2];mkdirSync(out);const root=realpathSync(mkdtempSync('/tmp/t078-2-budget-'));
for(const n of ['state','repo','home','claude'])mkdirSync(join(root,n));for(const preset of ['ideation','executor'])for(const n of ['home','claude','tmp','shell','requests','hooks','user-data'])mkdirSync(join(root,'roles',preset,n),{recursive:true});writeFileSync(join(root,'roles','ideation','role.md'),'只回复 nonce。\n');
const task:any={task_id:'budget',project_id:'budget',repo:join(root,'repo'),spec_rev:1,base_commit:'a'.repeat(40)};
const input:any={schema:1,root,state:join(root,'state'),task:'budget',preset:'ideation',launch:randomUUID(),session:randomUUID(),thread:randomUUID(),
 executable:'/Users/luckye/.local/share/claude/versions/2.1.296',version:'2.1.296',role_file:join(root,'roles','ideation','role.md'),code_revision:'a'.repeat(40),source_snapshot:join(root,'sources.tar.gz'),api_url:'http://127.0.0.1:12345'};
const checks:any[]=[];
for(const [name,body] of [
 ['explicit_two_turn_budget_is_recorded',()=>assert.equal(claudeLaunch(task,{...input,turn_limit:2}).turn_limit,2)],
 ['undeclared_budget_stays_one',()=>assert.equal(claudeLaunch(task,input).turn_limit,1)],
 ['six_turn_budget_is_recorded',()=>assert.equal(claudeLaunch(task,{...input,turn_limit:6}).turn_limit,6)],
 ['larger_budget_is_denied',()=>assert.throws(()=>claudeLaunch(task,{...input,turn_limit:7}),(e:any)=>e.code==='invalid_controller_turn_limit')]
] as [string,()=>void][]){try{body();checks.push({name,status:'PASS'});}catch(e){checks.push({name,status:'INCOMPLETE',error:String(e)});}}
const r={status:checks.every(c=>c.status==='PASS')?'PASS':'INCOMPLETE',checks,argv:process.argv,scope:'Pure parameter construction, no CLI or API'};
writeFileSync(join(out,'results.json'),JSON.stringify(r,null,2));console.log(JSON.stringify(r));process.exitCode=r.status==='PASS'?0:1;
