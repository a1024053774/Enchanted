// Run the production daemon and reviewer constructor with their real PTY/hooks.
// The fixture owns task objects; this is a launch/sandbox test, not gate delivery.
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const manifest = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const source = pathToFileURL(resolve(manifest.source) + '/');
const { serve } = await import(new URL('src/daemon.ts', source));
const { A2AGates } = await import(new URL('src/gates/core.ts', source));
const { OrchestrationStore } = await import(new URL('src/store.ts', source));
const { createOperatorCredential } = await import(new URL('src/credentials.ts', source));
const { request } = await import(new URL('src/transport.ts', source));
const root = manifest.root, state = join(root, 'state');
const sessionInventory = () => {
  const directory = join(root, 'reviewer-home', 'sessions');
  const walk = path => readdirSync(path, { withFileTypes: true }).flatMap(entry => {
    const file = join(path, entry.name);
    return entry.isDirectory() ? walk(file) : entry.isFile() ? [{ path: file, bytes: statSync(file).size,
      ...(entry.name.endsWith('.jsonl') ? { first_line: readFileSync(file, 'utf8').split('\n', 1)[0].slice(0, 4096) } : {}) }] : [];
  });
  return { directory, exists: existsSync(directory), files: existsSync(directory) ? walk(directory) : [] };
};
mkdirSync(state);
process.env.A2A_OPERATOR_CREDENTIAL = join(root, 'operator.json');
createOperatorCredential(state);
const config = { codex_bin: manifest.binary, codex_home: join(root, 'worker-home'),
  role_card: join(root, 'role.md'), role_card_revision: 'T112/permission-native',
  code_revision: manifest.revision, hook_authorization: 'T112 isolated local API only', turn_limit: 1,
  reviewers: [{ codex_home: join(root, 'reviewer-home'), role_card: join(root, 'role.md'),
    role_card_revision: 'T112/permission-native', hook_authorization: 'T112 isolated local API only' }] };
let panes;
await serve(state, config, (directory, instance) => { panes = instance; return new A2AGates(directory, instance); });
const until = async (read, predicate, description) => {
  const end = Date.now() + 45000;
  for (;;) {
    const value = await read();
    if (predicate(value)) return value;
    assert.ok(Date.now() < end, description + ': ' + JSON.stringify(value));
    await new Promise(resolve => setTimeout(resolve, 100));
  }
};
try {
  await until(() => request(state, { command: 'pane_layout' }), row => !row.recovering, 'Daemon recovery');
  const settings = new OrchestrationStore(state);
  try { if (settings.saveExecutionSettings) settings.saveExecutionSettings('reviewer', { effort: 'low' }); }
  finally { settings.close(); }
  const task = { task_id: 'T112', project_id: 'fixture', spec_rev: 1,
    card: { executor: { cli: 'Codex', model: 'gpt-6.1-sol', effort: 'xhigh' } } };
  const attempt = { runtime_mode: 'workspace-write', workspace: root, attempt_id: 'a1',
    session_id: 'worker-session', thread_id: 'worker', fence: 1, spec_rev: 1 };
  const review = { attempt, session_id: 'review-session', thread_id: 'review',
    candidate_workspace: join(root, 'candidate'), review_id: 'review-id',
    verification_id: 'verification-id', workspace: root };
  await panes.createReview(task, review, '执行本地固定 shell 探针，不提交或验收。');
  writeFileSync(join(root, 'launch.json'), JSON.stringify(panes.get('review').record, null, 2) + '\n', { flag: 'wx' });
  // Initial release requires the foreground CLI, as production Panes.release
  // does. A new rollout/session may not exist until that first input is sent.
  const foreground = await until(() => panes.processInfo('review'), row => row.leader && !row.failed, 'Foreground reviewer process');
  writeFileSync(join(root, 'pre-release.json'), JSON.stringify({ foreground, sessions: sessionInventory() }, null, 2) + '\n', { flag: 'wx' });
  await panes.release('review', 'T112 explicitly authorized local fake API sandbox probe');
  writeFileSync(join(root, 'released.json'), JSON.stringify({ released: true }) + '\n', { flag: 'wx' });
  const identity = await until(() => panes.processInfo('review'), row => row.leader && row.native_session && !row.failed, 'Native reviewer identity after first input');
  assert.equal(identity.leader, foreground.leader, 'Reviewer leader changed during first input');
  writeFileSync(join(root, 'identity.json'), JSON.stringify(identity, null, 2) + '\n', { flag: 'wx' });
  writeFileSync(join(root, 'post-identity.json'), JSON.stringify(sessionInventory(), null, 2) + '\n', { flag: 'wx' });
} catch (error) {
  writeFileSync(join(root, 'host-error.json'), JSON.stringify({ error: String(error), stack: error.stack }) + '\n', { flag: 'wx' });
  // Keep the real server available for identity-bound shutdown after a failure.
}
