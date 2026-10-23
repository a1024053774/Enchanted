// Failure modes: saved directories disappear on replay; removal overwrites history;
// settings leak between projects or survive removal/reopening of a project.
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { OrchestrationStore } from '../src/store.ts';

const root = mkdtempSync(join(tmpdir(), 't140-events-'));
const store = new OrchestrationStore(root);
store.event('project_opened', { project_id: 'demo', repo: '/fixture/demo' });
store.event('project_opened', { project_id: 'other', repo: '/fixture/other' });
store.event('project_settings_saved', { project_id: 'demo', extra_directories: ['/fixture/X'] });
assert.deepEqual(store.openedProjects().find(p => p.project_id === 'demo')?.extra_directories, ['/fixture/X']);
assert.deepEqual(store.openedProjects().find(p => p.project_id === 'other')?.extra_directories, []);
store.event('project_settings_saved', { project_id: 'demo', extra_directories: [] });
assert.deepEqual(store.openedProjects().find(p => p.project_id === 'demo')?.extra_directories, []);
assert.equal(store.db.prepare("SELECT count(*) AS n FROM orchestration_events WHERE type='project_settings_saved'").get()!.n, 2);
store.db.close();
const reopened = new OrchestrationStore(root);
assert.deepEqual(reopened.openedProjects().find(p => p.project_id === 'demo')?.extra_directories, []);
reopened.event('project_removed', { project_id: 'demo' });
reopened.event('project_opened', { project_id: 'demo', repo: '/fixture/new' });
assert.deepEqual(reopened.openedProjects().find(p => p.project_id === 'demo')?.extra_directories, []);
reopened.db.close();
console.log(JSON.stringify({ status: 'PASS', fixture: root }));
