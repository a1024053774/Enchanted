// Diagnostic only: call the actual reviewer launch constructor with a supplied
// PTY, record its complete argv, and run the installed binary's version check.
// This does not claim that a native reviewer session ran.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
const [sourcePath, root, binary, revision] = process.argv.slice(2);
const source = pathToFileURL(resolve(sourcePath) + '/');
const { OrchestrationStore } = await import(new URL('src/store.ts', source));
const { Panes } = await import(new URL('src/panes.ts', source));
const pty = createRequire(new URL('src/panes.ts', source))('node-pty');
const spawn = pty.spawn;
pty.spawn = () => ({ pid: 99999, onData() {}, onExit() {}, write() {} });
for (const directory of ['worker-home', 'reviewer-home', 'candidate']) mkdirSync(join(root, directory));
const role = join(root, 'role.md');
writeFileSync(role, '权限诊断夹具。不调用模型。\n');
const store = new OrchestrationStore(root);
const report = { revision, supplied_pty: true, model_calls: 0 };
try {
  if (store.saveExecutionSettings) store.saveExecutionSettings('reviewer', { effort: 'low' });
  const config = { codex_bin: binary, codex_home: join(root, 'worker-home'), role_card: role,
    role_card_revision: 'T112/permission-diagnostic', code_revision: revision,
    hook_authorization: 'T112 local diagnostic only', turn_limit: 1,
    reviewers: [{ codex_home: join(root, 'reviewer-home'), role_card: role,
      role_card_revision: 'T112/permission-diagnostic', hook_authorization: 'T112 local diagnostic only' }] };
  const task = { task_id: 'T112', project_id: 'fixture', spec_rev: 1,
    card: { executor: { cli: 'Codex', model: 'gpt-6.1-sol', effort: 'xhigh' } } };
  const attempt = { runtime_mode: 'workspace-write', workspace: root, attempt_id: 'a1',
    session_id: 'worker-session', thread_id: 'worker', fence: 1, spec_rev: 1 };
  const review = { attempt, session_id: 'review-session', thread_id: 'review',
    candidate_workspace: join(root, 'candidate'), review_id: 'review-id',
    verification_id: 'verification-id', workspace: root };
  await new Panes(root, store, config, () => {}).createReview(task, review, '权限诊断。');
  const records = store.launches();
  assert.equal(records.length, 1);
  report.launch = records[0];
} catch (error) {
  report.error = { name: error.constructor.name, message: error.message, code: error.code, details: error.details };
} finally {
  const requests = store.launches().map(row => row.request_dir).filter(Boolean);
  store.close(); pty.spawn = spawn;
  for (const directory of requests) rmSync(directory, { recursive: true });
}
writeFileSync(join(root, 'record.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
