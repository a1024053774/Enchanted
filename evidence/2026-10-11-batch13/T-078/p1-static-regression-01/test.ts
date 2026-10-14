// Static construction and SQLite recording only. No Claude binary, hook,
// emulated API, terminal, subprocess, credential or model is run here.
// Failures: missing argv/settings or role binding; fake worker attempt; a
// prepared record claims a running CLI; global configuration writes; invalid
// settings get recorded; an earlier record changes when a new plan is prepared.
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { Panes } from "../src/panes.ts";
import { OrchestrationStore } from "../src/store.ts";

const out=resolve(process.argv[2]!);mkdirSync(out);
const root=mkdtempSync('/tmp/t78-controller-plan-');
const role=join(root,'role.md');writeFileSync(role,'固定角色卡：只记录启动计划。\n');
const store=new OrchestrationStore(root);
const configs:any={
  ideation:{executable:join(root,'absent-claude'),'model':'static-model-A',effort:'medium',
    settings:{permissions:{allow:['Read']},hooks:{}},role_card:role,role_card_revision:'role-r1'},
  executor:{executable:join(root,'absent-claude'),'model':'static-model-B',effort:'high',
    settings:{permissions:{allow:['Read','Bash(git status)']},hooks:{}},role_card:role,role_card_revision:'role-r1'},
};
const panes=new Panes(root,store,{code_revision:'a'.repeat(40),controllers:configs} as any,()=>{});
const task:any={task_id:'plan-task',project_id:'plan-project',repo:root,spec_rev:1,base_commit:'b'.repeat(40)};
const checks:any[]=[];
async function test(name:string,body:()=>void) {
  try{body();checks.push({name,status:'PASS'});}catch(error){checks.push({name,status:'INCOMPLETE',error:String(error)});}
}
await test('controller_argv_and_record_are_static',()=>{
  assert.equal(typeof (panes as any).prepareControllerLaunch,'function','Controller launch preparation must exist');
  const records=['ideation','executor'].map(preset=>(panes as any).prepareControllerLaunch(task,preset));
  assert.notEqual(records[0].session,records[1].session);
  for(let i=0;i<records.length;i++){
    const row=records[i],preset=['ideation','executor'][i]!,c=configs[preset];
    assert.equal(row.role,'controller');assert.equal(row.preset,preset);assert.equal(row.attempt,null);
    assert.equal(row.execution_state,'prepared');assert.equal(row.cli_version,'unknown');
    assert.equal(row.validation,'待真实 Claude 复核');assert.equal(row.role_text,'固定角色卡：只记录启动计划。\n');
    assert.deepEqual(row.argv,[c.executable,'--session-id',row.session,'--model',c.model,'--effort',c.effort,'--settings',JSON.stringify(c.settings)]);
    assert.deepEqual(row.settings,c.settings);assert.deepEqual(store.launchRecord(row.id),row);
    assert.equal(row.env.A2A_TASK,task.task_id);assert.equal(row.env.A2A_LAUNCH,row.id);
    assert.equal(Object.hasOwn(row.env,'A2A_CAPABILITY'),false);assert.equal(Object.hasOwn(row.env,'A2A_ATTEMPT'),false);
    assert.equal(panes.status(row.thread).lifecycle,'not_started');
  }
  const first=JSON.stringify(store.launchRecord(records[0].id));
  configs.ideation.settings.permissions.allow.push('Write');
  assert.equal(JSON.stringify(store.launchRecord(records[0].id)),first);
  assert.equal(panes.panes.size,0);assert.equal(store.read().filter(x=>x.type==='pane_started').length,0);
  assert.deepEqual(readdirSync(root).filter(x=>!['role.md','state.sqlite3','state.sqlite3-wal','state.sqlite3-shm'].includes(x)),[]);
  panes.recover('new-daemon');assert.equal(store.read().filter(x=>x.type==='pane_recovered').length,0);
});
await test('invalid_plan_has_no_record',()=>{
  const before=store.launches();
  assert.throws(()=>(panes as any).prepareControllerLaunch(task,'worker'),(error:any)=>error.code==='invalid_controller_preset');
  configs.executor.settings={env:{NOT_A_REAL_SECRET:'must not enter settings argv'}};
  assert.throws(()=>(panes as any).prepareControllerLaunch(task,'executor'),(error:any)=>error.code==='invalid_controller_settings');
  assert.deepEqual(store.launches(),before);
});
writeFileSync(join(out,'readback.json'),JSON.stringify({root,launches:store.launches(),events:store.read()},null,2)+'\n');
for(const name of ['panes.ts','store.ts'])writeFileSync(join(out,name),readFileSync(new URL('../src/'+name,import.meta.url)));
writeFileSync(join(out,'test.ts'),readFileSync(new URL(import.meta.url)));
store.close();
const result={status:checks.every(x=>x.status==='PASS')?'PASS':'INCOMPLETE',checks,argv:process.argv,
  claude_started:false,claude_fixture_started:false,real_model_turns:0};
writeFileSync(join(out,'results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
process.exitCode=result.status==='PASS'?0:1;
