// T-124: a terminal controller that runs out of quota is announced inside the workbench.
// Failure modes (listed before writing): a quota row gives no notice; the same run-out shows twice;
// the notice stays after the quota is restored; a second run-out after recovery is swallowed;
// notifications switched off still show it, or switching them back on replays it; quota rows change
// question notices or the dock badge (which counts answers the user owes).
// node tests/test_t124_quota_notice.mjs <new report path> [notificationCenter.ts to test]
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const output = process.argv[2];
if (!output || existsSync(output)) throw new Error('New report path required');
const source = process.argv[3] ? pathToFileURL(resolve(process.argv[3])).href : new URL('../app/notificationCenter.ts', import.meta.url).href;
const { NotificationCenter } = await import(source);
const report = { status: 'INCOMPLETE', source, checks: [] };
const check = (name, fn) => { fn(); report.checks.push(name); };
try {
  const center = new NotificationCenter(mkdtempSync('/private/tmp/t124-quota-notice-'));
  const question = { id: 'worker-1', state: 'waiting_user_answer', question_id: 'q-1', project: 'demo', role_label: 'worker', task: 'T-1' };
  const out = { role_request: 'rr-1', launch: 'terminal-1', project: 'demo', role_label: '执行主控', resets_at: '2026-10-22T12:00:00.000Z',
    since: '2026-10-22T09:00:00.000Z' };
  check('quota_row_gives_one_notice', () => {
    const notices = center.observe([], [out]);
    assert.equal(notices.length, 1);
    assert.equal(notices[0].kind, 'quota');
    assert.equal(notices[0].launch, 'terminal-1');
    assert.equal(notices[0].project, 'demo');
    assert.equal(notices[0].role, '执行主控');
    assert.equal(notices[0].resets_at, '2026-10-22T12:00:00.000Z');
  });
  check('same_run_out_not_repeated', () => assert.equal(center.observe([], [out]).length, 1));
  check('questions_unchanged_beside_quota', () => {
    const notices = center.observe([question], [out]);
    assert.deepEqual(notices.map(notice => notice.kind).sort(), ['question', 'quota']);
    assert.equal(center.badgeCount(), 1);
  });
  check('restored_quota_clears_notice', () => assert.deepEqual(center.observe([question], []).map(notice => notice.kind), ['question']));
  check('second_run_out_noticed', () => {
    const again = { ...out, since: '2026-10-22T13:00:00.000Z' };
    assert.deepEqual(center.observe([], [again]).map(notice => notice.id), ['quota:rr-1:2026-10-22T13:00:00.000Z']);
  });
  check('disabled_hides_and_does_not_replay', () => {
    const later = { ...out, since: '2026-10-22T15:00:00.000Z' };
    center.setting(false);
    assert.deepEqual(center.observe([], [later]), []);
    center.setting(true);
    assert.deepEqual(center.observe([], [later]), []);
  });
  report.status = 'PASS';
} catch (error) {
  report.error = String(error?.stack ?? error);
  process.exitCode = 1;
} finally {
  writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ status: report.status, checks: report.checks.length, error: report.error?.split('\n')[0] }));
}
