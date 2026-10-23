// Failure modes: an unclaimed/released shell remains in the agent catalog;
// moving it out of the agent catalog removes its ordinary-terminal navigation.
// Real SQLite projection; controlled lifecycle, no Electron or native CLI proof.
import { mkdtempSync, existsSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { OrchestrationStore } from '../src/store.ts';
import { sidebarSnapshot } from '../src/sidebar.ts';
const output = process.argv[2];
assert(output && !existsSync(output), 'New report path required');
const root = mkdtempSync('/private/tmp/t139-terminal-catalog-');
const store = new OrchestrationStore(root);
const report = { status: 'INCOMPLETE', fixture: root, checks: [] };
try {
  store.db.exec(`CREATE TABLE relay_requests (key TEXT PRIMARY KEY,launch TEXT,task TEXT,attempt TEXT,request_id TEXT,input TEXT,created_at TEXT);
    CREATE TABLE relay_results (key TEXT PRIMARY KEY,data TEXT,created_at TEXT);`);
  store.launch({ id: 'released-terminal', thread: 'shell-thread', project: 'demo', task: null, role: 'shell', attempt: null,
    session: null, fence: null, cli: 'zsh' });
  const actual = await sidebarSnapshot({ listProjects: () => [] }, store,
    { status: () => ({ lifecycle: 'running' }) }, { all: () => [] });
  assert.equal(actual.agents.length, 0, 'Released/unclaimed terminal is not an agent');
  report.checks.push('released_role_not_in_agents');
  assert.equal(actual.terminals.length, 1);
  assert.equal(actual.terminals[0].id, 'released-terminal');
  assert.equal(actual.terminals[0].role, 'shell');
  assert.equal(actual.terminals[0].terminal, true);
  assert.deepEqual(actual.terminals[0].descendants, { count: 0, state: 'unknown', state_label: '未知', counts: [] });
  report.checks.push('ordinary_terminal_has_its_own_navigation');
  report.status = 'PASS';
} catch (error) { report.status = 'NO_GO'; report.error = String(error); }
finally { store.close(); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
