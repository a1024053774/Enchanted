// Isolated failure modes: executor inferred from its terminal task instead of
// delegation; cross-project/stale workers attach controllers; paths collapse;
// unassigned sessions have no explanation. UI/CLI evidence is a separate e2e.
import assert from 'node:assert/strict';
import { existsSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const [output, source = '.'] = process.argv.slice(2);
assert.ok(output && !existsSync(output), 'Fresh summary required');
const report = { status: 'INCOMPLETE', checks: [] };
try {
  const { projectFlow } = await import(pathToFileURL(resolve(source, 'workbench/src/flow.ts')));
  const tasks = ['A', 'B'].map(name => ({ task_id: 'p+' + name, name, project_id: 'p', repo: '/project', current_attempt: { attempt_id: 'a1' } }));
  const agents = [
    ...['eA', 'eB', 'loose'].map(id => ({ id, role: 'controller', preset: 'executor', project: 'p', task: 'p+WRONG', parent: null })),
    ...['A', 'B'].map(name => ({ id: 'w' + name, role: 'worker', project: 'p', task: 'p+' + name, attempt: 'a1', parent: 'e' + name })),
    { id: 'stale', role: 'worker', project: 'p', task: 'p+A', attempt: 'old', parent: 'loose' },
    { id: 'foreign', role: 'worker', project: 'other', task: 'p+A', attempt: 'a1', parent: 'loose' },
  ];
  const input = JSON.stringify({ tasks, agents });
  const view = projectFlow(tasks, agents, [], [{ project_id: 'p', repo: '/project', extra_directories: ['/extra-one', '/extra-two'] }]);
  for (const name of ['A', 'B']) {
    const lane = view.lanes.find(lane => lane.task === 'p+' + name);
    assert.deepEqual(lane.agents.map(agent => agent.id).sort(), ['e' + name, 'w' + name], 'Controller follows its dispatched worker only');
    assert.deepEqual(lane.paths, ['/project', '/extra-one', '/extra-two']);
  }
  assert.deepEqual(view.unassigned.map(agent => agent.id), ['loose', 'stale', 'foreign']);
  assert.ok(view.unassigned.every(agent => agent.unassigned_reason));
  assert.equal(JSON.stringify({ tasks, agents }), input, 'Read-only projection');
  report.status = 'PASS';
  report.checks.push('delegation_not_terminal_task', 'task_isolation', 'stale_and_foreign_excluded', 'multiple_paths', 'unassigned_reason', 'read_only');
} catch (error) {
  report.error = String(error);
  process.exitCode = 1;
} finally {
  writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
}
