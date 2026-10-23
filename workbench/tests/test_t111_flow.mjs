// Contract expectations come from T-111. Failure modes: absent page/data path,
// phase guessed from task row, double-counted rejection, stale attempt or
// missing parent assigned, role guessed from text, and read-time mutation.
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh report path required');
const report = { status: 'INCOMPLETE', task: 'T-111', model_calls: 0 };
try {
  assert.ok(existsSync(resolve(source, 'workbench/src/flow.ts')), 'T-111 read-only flow projection is missing');
  const { projectFlow } = await import(pathToFileURL(resolve(source, 'workbench/src/flow.ts')));
  const tasks = [{task_id:'T-A', project_id:'p', title:'审查员字样不决定阶段', current_attempt:{attempt_id:'a'}},
    {task_id:'T-B', project_id:'p', title:'并行票', current_attempt:{attempt_id:'b'}}];
  const agents = [
    {id:'controller',role:'controller',preset:'executor',project:'p',task:'T-A',attempt:null,parent:null,state:'idle'},
    ...['w1','w2'].map(id=>({id,role:'worker',project:'p',task:'T-A',attempt:'a',parent:'controller',state:'running'})),
    {id:'r',role:'reviewer',project:'p',task:'T-B',attempt:'b',parent:'controller',state:'idle'},
    {id:'old',role:'worker',project:'p',task:'T-A',attempt:'old',parent:'controller',state:'running'},
    {id:'orphan',role:'worker',project:'p',task:'T-A',attempt:'a',parent:null,state:'running'},
    {id:'monitor',role:'monitor',project:'p',task:'T-A',attempt:'a',parent:'controller',state:'idle'},
    {id:'ended',role:'worker',project:'p',task:'T-A',attempt:'a',parent:'controller',state:'ended'},
  ];
  const events = [
    {task:'T-A',attempt:'a',type:'claimed',details:{}},
    {task:'T-B',attempt:'b',type:'claimed',details:{}},
    {task:'T-B',attempt:'b',type:'submitted',details:{}},
    {task:'T-B',attempt:'b',type:'verification_result',details:{verification:{state:'passed'}}},
    {task:'T-A',attempt:'old',type:'integrated',details:{}},
  ];
  const frozen = JSON.stringify({tasks,agents,events});
  const view = projectFlow(tasks, agents, events);
  assert.equal(view.lanes.length, 2);
  assert.equal(view.lanes[0].stage, 'implementation');
  assert.deepEqual(view.lanes[0].agents.map(a=>a.id), ['w1','w2','ended']);
  assert.equal(view.lanes[0].agents.find(a=>a.id === 'ended').state, 'ended', 'T-146 B retains ended sessions');
  assert.deepEqual(view.lanes[0].monitors.map(a=>a.id), ['monitor']);
  assert.equal(view.lanes[1].stage, 'review');
  assert.deepEqual(view.lanes[1].agents.map(a=>a.id), ['r']);
  assert.deepEqual(view.unassigned.map(a=>a.id), ['controller','old','orphan']);
  assert.equal(JSON.stringify({tasks,agents,events}), frozen);
  assert.equal(projectFlow(tasks, agents, [...events, {task:'T-B',attempt:'b',type:'review_result',details:{review:{state:'passed'}}}]).lanes[1].stage, 'integration');
  const rejected = [...events, {task:'T-B',attempt:'b',type:'review_result',details:{review:{state:'needs_fix'}}},
    {task:'T-B',attempt:'b',type:'delivery_rejected',details:{repair:{check:'independent_review'}}}];
  const retry = projectFlow(tasks, agents, rejected).lanes[1];
  assert.equal(retry.stage, 'implementation'); assert.equal(retry.returns.length, 1); assert.equal(retry.returns[0].from, 'review');
  assert.equal(projectFlow(tasks, agents, [...events, {task:'T-A',attempt:'old',type:'delivery_rejected',details:{repair:{check:'completion'}}}]).lanes[0].returns.length, 1, 'Ticket return count includes recorded earlier attempts');
  // One ticket: an earlier mechanical rejection and two current review
  // rejections. Each review result accompanies, rather than adds, one return.
  const multiRejected = [
    {task:'T-B',attempt:'previous-b',type:'claimed',details:{}},
    {task:'T-B',attempt:'previous-b',type:'submitted',details:{}},
    {task:'T-B',attempt:'previous-b',type:'verification_result',details:{verification:{verification_id:'v-old',state:'failed'}}},
    {task:'T-B',attempt:'previous-b',type:'delivery_rejected',details:{repair:{verification_id:'v-old',check:'completion',count:1}}},
    ...events,
    {task:'T-B',attempt:'b',type:'review_result',details:{review:{state:'needs_fix'}}},
    {task:'T-B',attempt:'b',type:'delivery_rejected',details:{repair:{verification_id:'v-b1',check:'independent_review',count:1}}},
    {task:'T-B',attempt:'b',type:'submitted',details:{}},
    {task:'T-B',attempt:'b',type:'verification_result',details:{verification:{verification_id:'v-b2',state:'passed'}}},
    {task:'T-B',attempt:'b',type:'review_result',details:{review:{state:'needs_fix'}}},
    {task:'T-B',attempt:'b',type:'delivery_rejected',details:{repair:{verification_id:'v-b2',check:'independent_review',count:2}}},
  ];
  const multi = projectFlow(tasks, agents, multiRejected).lanes[1];
  assert.equal(multi.returns.length, 3, 'Ticket rejection facts must accumulate across attempts');
  assert.deepEqual(multi.returns.map(item=>item.from), ['checks','review','review'], 'Return origins must match the three gate rejection facts');
  assert.equal(multi.stage, 'implementation');
  const currentOnly = projectFlow(tasks, agents, multiRejected.filter(event=>event.attempt !== 'previous-b')).lanes[1];
  assert.equal(currentOnly.returns.length, 2, 'Earlier attempt contributes one additional return');
  assert.deepEqual(currentOnly.returns.map(item=>item.from), ['review','review']);
  assert.deepEqual(projectFlow(tasks, agents, multiRejected.filter(event=>event.type !== 'review_result')).lanes[1].returns,
    multi.returns, 'Review results must not add or remove rejection facts');
  assert.equal(projectFlow(tasks, agents, multiRejected.filter(event=>event.type !== 'delivery_rejected')).lanes[1].returns.length,
    0, 'Review results alone must not count as returns');
  assert.equal(projectFlow(tasks, agents, [{task:'T-A',attempt:'a',type:'rejected',details:{}}]).lanes[0].stage, null);
  assert.equal(projectFlow([], [], []).lanes.length, 0);
  const withoutAttempt = projectFlow([{task_id:'T-no-attempt',project_id:'p'}],
    [{id:'missing-attempt',role:'worker',project:'p',task:'T-no-attempt',parent:'controller',state:'unknown'}], []);
  assert.equal(withoutAttempt.lanes[0].agents.length, 0, 'Missing attempt binding must stay unassigned');
  assert.equal(withoutAttempt.unassigned[0].id, 'missing-attempt');
  report.status = 'PASS';
} catch(error) { report.error = String(error); report.stack = error.stack; }
writeFileSync(output, JSON.stringify(report,null,2)+'\n', {flag:'wx'});
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
