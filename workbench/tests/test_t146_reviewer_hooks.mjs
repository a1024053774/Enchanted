// T-146/controller #9: accept the one added SessionEnd hook, retaining every
// other reviewer launch check. Isolated gate validator; not a live reviewer.
// Failure modes: approved hook list rejected; missing/extra hook admitted;
// foreign SessionEnd command or timeout accepted; broader sandbox/permissions,
// changed CLI flags or injected Git configuration accepted.
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', argv: process.argv, checks: [] };
try {
  const { A2AGates } = await import(pathToFileURL(resolve(source, 'workbench/src/gates/core.ts')));
  const workspace = mkdtempSync('/private/tmp/t146-review-hooks-');
  report.fixture = workspace;
  const events = ['SessionStart', 'SessionEnd', 'UserPromptSubmit', 'Stop', 'PermissionRequest', 'PreToolUse', 'PostToolUse'];
  const argv = id => ['/fixture/claude', '--session-id', 'native-' + id, '--model', 'claude-haiku-5-5', '--effort', 'low',
    '--permission-mode', 'dontAsk', '--setting-sources', '', '--strict-mcp-config', '--disallowedTools', 'AskUserQuestion', '--settings',
    JSON.stringify({ permissions: { allow: ['Bash', 'Read', 'Glob', 'Grep', `Edit(/${workspace}/**)`] },
      sandbox: { enabled: true, autoAllowBashIfSandboxed: true, allowUnsandboxedCommands: false, filesystem: { allowWrite: [] } },
      hooks: Object.fromEntries(events.map(event => [event, [{ hooks: [{ type: 'command', command: `signal '--launch' '${id}'`, timeout: 10 }] }]])),
      fastMode: false })];
  const worker = { id: 'worker', role: 'worker', cli: 'Claude Code', argv: argv('worker') };
  const launch = { id: 'reviewer', role: 'reviewer', cli: 'Claude Code', review_id: 'review', review_verification_id: 'verification',
    session: 'review-session', thread: 'review-thread', attempt: 'attempt', native_session: 'native-reviewer',
    sandbox: 'workspace-write', worktree: workspace, env: {}, argv: argv('reviewer') };
  const review = { review_id: 'review', verification_id: 'verification', session_id: 'review-session', thread_id: 'review-thread',
    launch_id: 'reviewer', candidate_workspace: workspace, attempt: { attempt_id: 'attempt', runtime_identity: { launch: 'worker' } } };
  const validate = candidate => A2AGates.prototype.reviewLaunch.call({
    launchRecord: id => id === 'reviewer' ? candidate : id === 'worker' ? worker : null,
    boundCard: () => ({ executor: { cli: 'Claude Code' } }),
  }, {}, review, { workspace, runtime_identity: {} });
  assert.equal(validate(launch).id, 'reviewer');
  report.checks.push('approved_session_end_hook_accepted');
  const changeSettings = (candidate, change) => {
    const settings = JSON.parse(candidate.argv[15]); change(settings); candidate.argv[15] = JSON.stringify(settings);
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
