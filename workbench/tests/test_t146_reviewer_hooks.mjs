// T-146/controller #9: accept the one added SessionEnd hook, retaining every
// other reviewer launch check. Isolated gate validator; not a live reviewer.
// Failure modes: approved hook list rejected; missing/extra hook admitted;
// foreign SessionEnd command or timeout accepted; broader sandbox/permissions,
// changed CLI flags or injected Git configuration accepted.
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [] };
try {
  const { A2AGates } = await import(pathToFileURL(resolve(source, 'workbench/src/gates/core.ts')));
  const { Panes } = await import(pathToFileURL(resolve(source, 'workbench/src/panes.ts')));
  const workspace = mkdtempSync('/private/tmp/t146-review-hooks-');
  report.fixture = workspace;
  execFileSync('git', ['-c', 'core.hooksPath=/dev/null', 'init', '-q', workspace]);
  const home = join(workspace, 'home'); mkdirSync(home);
  const config = { claude_bin: '/usr/bin/true', role_card: resolve(source, 'workbench/roles/worker.md'),
    role_card_revision: 'fixture', code_revision: 'fixture', hook_authorization: 'fixture', turn_limit: 6 };
  const task = { project_id: 'project', task_id: 'task', card: { executor: { cli: 'Claude Code', model: '', effort: '' } } };
  const attempt = { attempt_id: 'attempt', session_id: 'session', thread_id: 'thread',
    workspace, runtime_mode: 'workspace-write', fence: 1, spec_rev: 1 };
  const sentinel = new Error('capture launch before PTY spawn');
  let captured;
  const panes = new Panes(workspace, {
    openedProjects: () => [], executionSelection: () => ({ model: 'claude-haiku-5-5', effort: 'low', fast: false }),
    launch: record => { captured = record; throw sentinel; },
  }, config, () => {});
  // Only fixture input comes from production. The independent assertions and
  // mutations below still decide which hook/permission changes must be refused.
  const argv = async id => {
    const previousHome = process.env.HOME;
    process.env.HOME = home;
    try {
      await panes.createPane(task, attempt, config, id === 'reviewer' ? {
        candidate_workspace: workspace, review_id: 'review', verification_id: 'verification',
      } : undefined);
      throw new Error('launch capture was not reached');
    } catch (error) { if (error !== sentinel) throw error; }
    finally { if (previousHome === undefined) delete process.env.HOME; else process.env.HOME = previousHome; }
    return captured.argv.map(arg => arg.replaceAll(captured.id, id).replaceAll(captured.native_session, 'native-' + id));
  };
  const worker = { id: 'worker', role: 'worker', cli: 'Claude Code', argv: await argv('worker') };
  const launch = { id: 'reviewer', role: 'reviewer', cli: 'Claude Code', review_id: 'review', review_verification_id: 'verification',
    session: 'review-session', thread: 'review-thread', attempt: 'attempt', native_session: 'native-reviewer',
    sandbox: 'workspace-write', worktree: workspace, env: {}, argv: await argv('reviewer') };
  const review = { review_id: 'review', verification_id: 'verification', session_id: 'review-session', thread_id: 'review-thread',
    launch_id: 'reviewer', candidate_workspace: workspace, attempt: { attempt_id: 'attempt', runtime_identity: { launch: 'worker' } } };
  const validate = candidate => A2AGates.prototype.reviewLaunch.call({
    launchRecord: id => id === 'reviewer' ? candidate : id === 'worker' ? worker : null,
    boundCard: () => ({ executor: { cli: 'Claude Code' } }),
  }, {}, review, { workspace, runtime_identity: {} });
  assert.equal(validate(launch).id, 'reviewer');
  report.checks.push('approved_session_end_hook_accepted');
  const changeSettings = (candidate, change) => {
    const index = candidate.argv.indexOf('--settings') + 1;
    const settings = JSON.parse(candidate.argv[index]); change(settings); candidate.argv[index] = JSON.stringify(settings);
  };
  for (const [name, change] of [
    ['missing_session_end', c => changeSettings(c, s => { delete s.hooks.SessionEnd; })],
    ['extra_hook', c => changeSettings(c, s => { s.hooks.ExtraHook = s.hooks.Stop; })],
    ['foreign_session_end_command', c => changeSettings(c, s => { s.hooks.SessionEnd[0].hooks[0].command = 'foreign'; })],
    ['session_end_timeout', c => changeSettings(c, s => { s.hooks.SessionEnd[0].hooks[0].timeout = 11; })],
    ['shell_write_expansion', c => changeSettings(c, s => { s.sandbox.filesystem.allowWrite = ['/tmp']; })],
    ['edit_expansion', c => changeSettings(c, s => { s.permissions.allow.push('Edit(//tmp/**)'); })],
    ['changed_cli_flag', c => { c.argv[11] = '--unknown'; }],
    ['git_configuration', c => { c.env.GIT_CONFIG_COUNT = '1'; }],
  ]) {
    const candidate = structuredClone(launch); change(candidate);
    assert.throws(() => validate(candidate), e => e.code === 'review_launch_boundary', name);
    report.checks.push(name + '_rejected');
  }
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report)); process.exitCode = report.status === 'PASS' ? 0 : 1;
