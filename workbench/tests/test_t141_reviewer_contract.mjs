// Execute the production launch builder, intercept only persistence before PTY spawn,
// then pass its records through the real review gate. No native sandbox claim.
// Failure modes: either CLI's approved launch rejected, broader write roots/approval
// policy accepted, missing hooks or a resumed/foreign reviewer accepted.
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { explainTrustRejection } from './t141_review_trust_rejection.mjs';
const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', checks: [] };
try {
  const { Panes } = await import(pathToFileURL(resolve(source, 'workbench/src/panes.ts')));
  const { A2AGates } = await import(pathToFileURL(resolve(source, 'workbench/src/gates/core.ts')));
  const root = mkdtempSync('/private/tmp/t141-launch-');
  const repo = join(root, 'repo'), candidate = join(root, 'candidate'), extra = join(root, 'extra');
  for (const path of [repo, candidate, extra]) mkdirSync(path);
    execFileSync('git', ['-c', 'core.hooksPath=/dev/null', 'init', '-q', repo]);
  report.fixture = root;
  const home = join(root, 'home'); mkdirSync(home);
  process.env.HOME = home;
  writeFileSync(join(home, '.claude.json'), JSON.stringify({ mcpServers: { sentinel: { command: '/usr/bin/true' } } }));
  const c = { claude_bin: '/usr/bin/true', codex_bin: '/usr/bin/true', codex_home: root,
    role_card: resolve(source, 'workbench/roles/worker.md'), role_card_revision: 'fixture',
    hook_authorization: 'fixture', code_revision: 'fixture', turn_limit: 6 };
  const sentinel = new Error('record captured before PTY spawn');
  let captured;
  const store = { openedProjects: () => [{ project_id: 'project', extra_directories: [extra] }],
    executionSelection: () => ({ model: 'fixture-model', effort: 'high', fast: false }),
    launch: record => { captured = record; throw sentinel; } };
  const panes = new Panes(root, store, c, () => {});
  for (const cli of ['Claude Code', 'Codex']) {
    const task = { project_id: 'project', task_id: 'task', card: { executor: { cli, model: '', effort: '' } } };
    const attempt = { task_id: 'task', attempt_id: 'attempt', session_id: 'worker-session', thread_id: 'worker-thread',
      fence: 1, spec_rev: 1, workspace: repo, runtime_mode: 'workspace-write' };
    await assert.rejects(panes.createPane(task, attempt, c), e => e === sentinel);
    const worker = captured;
    if (cli === 'Codex') {
      assert.ok(!worker.argv.some(arg => arg.startsWith('projects=')), 'Worker inherits user trust');
      await assert.rejects(panes.createPane(task, attempt, c, undefined, { cli: 'Codex' }), e => e === sentinel);
      assert.ok(!captured.argv.some(arg => arg.startsWith('projects=')), 'Monitor inherits user trust');
      report.checks.push('Codex_worker_and_monitor_inherit_user_trust');
    }
    const review = { review_id: 'review', verification_id: 'verification', session_id: 'review-session', thread_id: 'review-thread',
      candidate_workspace: candidate, attempt: { ...attempt, runtime_identity: { launch: worker.id } } };
    await assert.rejects(panes.createPane(task, { ...attempt, session_id: review.session_id, thread_id: review.thread_id }, c, review), e => e === sentinel);
    const launch = captured;
    if (cli === 'Codex') {
      assert.ok(launch.argv.includes(`projects={${JSON.stringify(candidate)}={trust_level="untrusted"}}`),
        'Only the reviewer candidate copy must be opened untrusted');
    }
    review.launch_id = launch.id;
    const validate = row => A2AGates.prototype.reviewLaunch.call({
      launchRecord: id => id === launch.id ? row : id === worker.id ? worker : null,
      boundCard: () => task.card,
    }, task, review, { workspace: candidate, runtime_identity: {} });
    assert.equal(validate(launch).id, launch.id);
    report.checks.push(cli + '_production_launch_accepted');
    if (cli === 'Codex') {
      for (const kind of ['missing', 'trusted']) {
        const row = structuredClone(launch), index = row.argv.findIndex(arg => arg.startsWith('projects='));
        if (kind === 'missing') row.argv.splice(index - 1, 2);
        else row.argv[index] = `projects={${JSON.stringify(candidate)}={trust_level="trusted"}}`;
        const input = { review, launch: row, live: { workspace: candidate, runtime_identity: {} } };
        assert.equal(explainTrustRejection(input, kind).status, 'PASS');
        row.sandbox = 'read-only';
        assert.equal(explainTrustRejection(input, kind).status, 'INCOMPLETE', 'Same error code with unrelated sandbox failure is not trust evidence');
        report.checks.push('Codex_' + kind + '_trust_rejection_specific_and_unrelated_failure_excluded');
      }
    }
    for (const [name, mutate] of [
      ['foreign_workspace', row => { row.worktree = repo; }],
      ['git_configuration', row => { row.env.GIT_CONFIG_COUNT = '1'; }],
      ['broader_writes', row => {
        if (cli === 'Codex') row.argv[row.argv.findIndex(v => v.startsWith('sandbox_workspace_write.writable_roots='))] = 'sandbox_workspace_write.writable_roots=["/"]';
        else { const i = row.argv.indexOf('--settings') + 1; const s = JSON.parse(row.argv[i]); s.permissions.allow.push('Edit(//**)'); row.argv[i] = JSON.stringify(s); }
      }],
      ['native_approval', row => {
        if (cli === 'Codex') row.argv[row.argv.indexOf('-a') + 1] = 'on-request';
        else row.argv[row.argv.indexOf('--permission-mode') + 1] = 'manual';
      }],
      ...(cli === 'Claude Code' ? [['mcp_hook_matches_native_tools', row => {
        const i = row.argv.indexOf('--settings') + 1, s = JSON.parse(row.argv[i]);
        s.hooks.PreToolUse[1].matcher = '.*'; row.argv[i] = JSON.stringify(s);
      }], ['mcp_hook_missing', row => {
        const i = row.argv.indexOf('--settings') + 1, s = JSON.parse(row.argv[i]);
        s.hooks.PreToolUse.pop(); row.argv[i] = JSON.stringify(s);
      }], ['foreign_mcp_configuration', row => {
        row.argv[row.argv.indexOf('--mcp-config') + 1] = '/foreign/.claude.json';
      }]] : []),
      ...(cli === 'Codex' ? [['trust_override_missing', row => {
        const index = row.argv.findIndex(arg => arg.startsWith('projects=')); row.argv.splice(index - 1, 2);
      }], ['trust_override_foreign_folder', row => {
        row.argv[row.argv.findIndex(arg => arg.startsWith('projects='))] = `projects={${JSON.stringify(repo)}={trust_level="untrusted"}}`;
      }], ['trust_override_trusted', row => {
        row.argv[row.argv.findIndex(arg => arg.startsWith('projects='))] = `projects={${JSON.stringify(candidate)}={trust_level="trusted"}}`;
      }]] : []),
    ]) {
      const row = structuredClone(launch); mutate(row);
      assert.throws(() => validate(row), e => e.code === 'review_launch_boundary', cli + ': ' + name);
      report.checks.push(cli + '_' + name + '_rejected');
    }
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
