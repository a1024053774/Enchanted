// 历史测试：只针对 e161476d6bb17e6f372d4a3d98ed03feccf36755，当前 main 不跑；当前无人守护：五角色设置持久化、覆盖优先级、角色隔离、权限字段拒绝、未知 effort 透传、原生启动失败记录（证据与边界见 HISTORICAL.md）。
// Failure cases: stale settings, role leakage, wrong precedence, enum filtering,
// lost Fast selection, permission injection, reviewer using worker selection,
// CLI startup error masked by a shell. PTY is supplied; this is not native E2E.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, copyFileSync, chmodSync, rmSync, realpathSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFile, execFileSync } from 'node:child_process';
import { promisify } from 'node:util';
const source = pathToFileURL(resolve(process.argv[3] ?? new URL('../', import.meta.url).pathname) + '/');
const { OrchestrationStore } = await import(new URL('src/store.ts', source));
const { Panes } = await import(new URL('src/panes.ts', source));
const { ClaudeModelOptions, CodexModelOptions } = await import(new URL('src/contracts/modelOptions.ts', source));
const { Schema } = await import('effect');

const output = process.argv[2];
assert.ok(output);
const root = mkdtempSync(process.env.T112_FIXTURE_PREFIX ?? '/private/tmp/t112-contract-');
const store = new OrchestrationStore(root);
const databases = [store];
const report = { status: 'INCOMPLETE', argv: process.argv, scope: 'real SQLite/Panes with supplied PTY/helper discovery; installed CLI version probe and actual recorded zsh with a private failing CLI stub', model_calls: 0, checks: [], fixture: root };
const require = createRequire(new URL('src/panes.ts', source)), pty = require('node-pty');
const utils = require(join(dirname(require.resolve('node-pty')), 'utils.js'));
const native = utils.loadNativeModule('pty');
const helperRoot = join(root, 'helper'); mkdirSync(helperRoot);
copyFileSync(join(dirname(require.resolve('node-pty')), native.dir, 'spawn-helper'), join(helperRoot, 'spawn-helper'));
chmodSync(join(helperRoot, 'spawn-helper'), 0o755);
const loadNative = utils.loadNativeModule, spawn = pty.spawn;
const terminals = [];
utils.loadNativeModule = () => ({ ...native, dir: relative(dirname(require.resolve('node-pty')), helperRoot) });
pty.spawn = (shell, argv, options) => {
  const terminal = { shell, argv, options, pid: 99999, onData() {}, onExit(fn) { this.exit = fn; }, write() {} };
  terminals.push(terminal); return terminal;
};
try {
  assert.equal(Schema.decodeUnknownSync(ClaudeModelOptions)({effort: 'future-effort-sentinel'}).effort, 'future-effort-sentinel');
  assert.equal(Schema.decodeUnknownSync(CodexModelOptions)({reasoningEffort: 'future-effort-sentinel'}).reasoningEffort, 'future-effort-sentinel');
  report.checks.push('legacy_codex_claude_contracts_do_not_filter_effort');
  const expected = { model: 'gpt-6.1-sol', effort: 'high', fast: false };
  for (const role of ['worker', 'reviewer', 'monitor']) assert.deepEqual(store.executionSelection(role), expected);
  for (const role of ['ideation', 'executor']) assert.deepEqual(store.executionSelection(role),
    { model: 'claude-haiku-5-5', effort: 'low', fast: false }, 'Claude controller must retain its native factory defaults');
  store.saveExecutionSettings('worker', { model: 'custom-model', effort: 'medium', fast: true });
  store.saveExecutionSettings('reviewer', { effort: 'low' });
  const reopened = new OrchestrationStore(root);
  databases.push(reopened);
  assert.deepEqual(reopened.executionSelection('worker'), { model: 'custom-model', effort: 'medium', fast: true });
  assert.deepEqual(reopened.executionSelection('worker', { effort: 'xhigh', fast: false }), { model: 'custom-model', effort: 'xhigh', fast: false });
  assert.deepEqual(reopened.executionSelection('reviewer'), { ...expected, effort: 'low' });
  assert.throws(() => store.saveExecutionSettings('worker', { sandbox: 'danger-full-access' }));
  assert.throws(() => store.saveExecutionSettings('unknown', {}));
  report.checks.push('five_factory_defaults', 'restart_persists_role_settings', 'field_override_precedence', 'role_isolation', 'permission_fields_rejected');
  const home = join(root, 'home'); mkdirSync(home);
  // A worker always starts in a Git worktree; its repository root is the folder opened untrusted (T-127).
  execFileSync('git', ['init', '-q', root]);
  const candidate = join(root, 'candidate'); mkdirSync(candidate);
  const config = { codex_bin: '/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex',
    codex_home: home, role_card: import.meta.filename, role_card_revision: 'T112/a1', code_revision: 'contract', hook_authorization: 'fixture', turn_limit: 1,
    reviewer_role_card: import.meta.filename, reviewer_role_card_revision: 'T112/review' };
  const task = { task_id: 'T112', project_id: 'fixture', spec_rev: 1, card: { executor: { cli: 'Codex', model: 'obsolete-card-model', effort: 'xhigh' } } };
  const attempt = { runtime_mode: 'workspace-write', workspace: root, attempt_id: 'a1', session_id: 'session', thread_id: 'worker', fence: 1, spec_rev: 1 };
  const panes = new Panes(root, store, config, () => {});
  await panes.createThread(task, attempt, { model: 'override-model', effort: 'high', fast: false });
  const worker = store.threadLaunch('worker');
  assert.equal(worker.model_requested, 'override-model'); assert.equal(worker.effort_requested, 'high');
  assert.ok(worker.argv.includes('model_reasoning_effort="high"')); assert.ok(worker.argv.includes('service_tier="default"'));
  assert.equal(worker.argv[worker.argv.indexOf('-m') + 1], 'override-model');
  const review = { attempt, session_id: 'review-session', thread_id: 'review', candidate_workspace: candidate, review_id: 'review-id', verification_id: 'verification-id', workspace: root };
  await panes.createReview(task, review, 'Do not write to protected directories.');
  const reviewer = store.threadLaunch('review');
  assert.equal(reviewer.effort_requested, 'low'); assert.equal(reviewer.model_requested, 'gpt-6.1-sol');
  assert.equal(reviewer.argv[reviewer.argv.indexOf('--sandbox') + 1], 'workspace-write');
  assert.equal(reviewer.argv[reviewer.argv.indexOf('-C') + 1], candidate);
  for (const flag of ['sandbox_workspace_write.network_access=false', 'features.network_proxy=false',
    'sandbox_workspace_write.exclude_slash_tmp=true', 'sandbox_workspace_write.exclude_tmpdir_env_var=true']) assert.ok(reviewer.argv.includes(flag));
  assert.ok(!Object.keys(reviewer.env).some(key => key.startsWith('GIT_CONFIG_')));
  // T-127 (user ruling 2026-10-21): the reviewer runs in the worker's Codex home, with its candidate copy opened untrusted.
  assert.equal(reviewer.env.CODEX_HOME, worker.env.CODEX_HOME);
  assert.ok(reviewer.argv.includes(`projects={${JSON.stringify(realpathSync(candidate))}={trust_level="untrusted"}}`));
  assert.equal(reviewer.env.A2A_ROLE, 'reviewer');
  report.checks.push('worker_selected_argv', 'reviewer_own_selection', 'reviewer_candidate_copy_sandbox_unchanged', 'reviewer_no_worker_git_hooks');
  // Unsupported values must cross a2a unchanged; only native startup may reject.
  const failingCLI = join(root, 'failing-cli');
  writeFileSync(failingCLI, '#!/bin/zsh\nif [[ $1 == --version ]]; then print "codex-cli 0.163.0"; exit 0; fi\nprint -u2 "native startup sentinel"\nexit 23\n');
  chmodSync(failingCLI, 0o755);
  const other = new Panes(root, store, { ...config, codex_bin: failingCLI }, () => {});
  await other.createThread(task, { ...attempt, thread_id: 'invalid-effort' }, { effort: 'unsupported-sentinel' });
  const invalid = store.threadLaunch('invalid-effort');
  assert.ok(invalid.argv.includes('model_reasoning_effort="unsupported-sentinel"'));
  // T-118: a newer native CLI is launched and its own version recorded, never refused.
  assert.equal(invalid.cli_version, 'codex-cli 0.163.0');
  // Execute the exact recorded zsh command with a private CLI that exits 23.
  // Closing stdin also makes a broken fallback shell exit 0 instead of hang.
  let nativeExit = 0;
  const operation = promisify(execFile)(invalid.shell, invalid.shell_argv,
    { cwd: invalid.worktree, env: terminals.at(-1).options.env, timeout: 3000 });
  operation.child.stdin.end();
  try { await operation; } catch (error) { nativeExit = error.code; }
  assert.equal(nativeExit, 23, 'Recorded shell must propagate native startup failure');
  terminals.at(-1).exit({ exitCode: nativeExit });
  assert.ok(store.read().some(row => row.launch === invalid.id && row.type === 'launch_failed'));
  assert.match(other.get('invalid-effort').failed, /launch_failed/);
  report.checks.push('updated_codex_version_recorded', 'unsupported_effort_not_coerced', 'native_startup_failure_recorded');
  report.status = 'PASS';
} catch (error) { report.error = String(error); report.stack = error.stack; }
finally {
  utils.loadNativeModule = loadNative; pty.spawn = spawn;
  const requests = store.launches().map(record => record.request_dir).filter(Boolean);
  databases.forEach(database => database.close());
  requests.forEach(directory => rmSync(directory, { recursive: true }));
  if (!process.env.T112_FIXTURE_PREFIX) { rmSync(root, { recursive: true }); report.fixture_removed = true; }
}
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
