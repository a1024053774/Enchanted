// T-192: taskHistory against real gate events (read-only export of the user's state, command_intent/result,
// human_intervention and the embedded task snapshot dropped). Expected facts come from findings, not from the code:
// lcu T-2 (findings/2026-10-25-lcu-real-use.md): independent review sent it back once, then integrated into work/demo at 9312a70.
// a2a T-138 (findings/2026-10-27-two-real-uses.md U07, U08): its attempt was reclaimed and the task never integrated.
// Run: node history_check.ts [path to taskHistory.ts]
import { readFileSync } from 'node:fs';
const module = process.argv[2] ?? '/Users/luckye/Documents/Code/a2a/workbench/src/gates/taskHistory.ts';
const { taskHistory, attemptStarts } = await import(module);
const fixture = JSON.parse(readFileSync(new URL('./history-fixture.json', import.meta.url), 'utf8'));
const failures: string[] = [];
const expect = (ok: boolean, what: string) => { if (!ok) failures.push(what); };

const t2 = taskHistory(fixture['a2a-lcu-demo+T-2']);
expect(t2.steps.some((s: any) => s.label === '打回' && String(s.detail).startsWith('独立审查')), 'T-2: a send-back by the independent review');
expect(t2.integration?.commit?.startsWith('9312a70'), 'T-2: integrated at 9312a70');
expect(t2.steps.some((s: any) => s.label === '集成' && s.passed === true), 'T-2: an integration step that passed');
expect(t2.reviews.length === 2 && t2.reviews[0].verdict === '需修复' && t2.reviews[1].verdict === '可合并', 'T-2: both reviews, sent back then mergeable');
expect(t2.reviews[0]?.findings.length === 1 && Boolean(t2.reviews[0].findings[0].suggestion), 'T-2: the first review keeps its finding and suggestion');
expect(t2.reviews.every((r: any) => Object.keys(r.report).length > 0), 'T-2: each review keeps its report');
expect(t2.score !== null, 'T-2: a score (integrate requires one)');
expect(t2.integration?.trailers?.task?.[0] === 'a2a-lcu-demo+T-2', 'T-2: trailers of the integrated candidate');
expect(!t2.steps.some((s: any) => s.label === '门禁拒绝' && /^card_|^create/.test(String(s.detail))), 'T-2: no card-drafting refusals');

const t138 = taskHistory(fixture['a2a+T-138']);
expect(t138.steps.some((s: any) => s.label === '回收'), 'T-138: reclaimed');
expect(t138.integration === null, 'T-138: never integrated');
expect(t138.steps.length > 0 && t138.steps[0].label === '创建任务', 'T-138: history starts at creation');
expect(t138.closed === null, 'T-138: not closed in the gate yet');

// Counterexamples from review 01, shaped as core.ts writes them (red_check/rule_check records, a verify refused
// before any verification, a merge conflict saving the verification itself).
const e = (seq: number, type: string, details: any) => ({ seq, time: '2026-10-27T08:00:00Z', attempt: 'a', type, details });
const quality = taskHistory([e(1, 'red_check', { index: 1, base_result: { returncode: 1 }, candidate_result: { returncode: 0 }, passed: true }),
  e(2, 'rule_check', { id: 'lint', result: { returncode: 2 }, passed: false })]).steps;
expect(quality.length === 2 && quality[0].passed === true && quality[1].passed === false, 'red and rule checks are steps');
const early = taskHistory([e(1, 'submitted', { commit: 'c' }), e(2, 'rejected', { input: { command: 'verify' }, error: 'git_failed' })]).steps;
expect(early.some((s: any) => s.label === '门禁拒绝' && String(s.detail).includes('git_failed')), 'a verify refused before verification stays visible');
const merge = taskHistory([e(1, 'verification_result', { state: 'merge_failed' }), e(2, 'verification_conflict', { state: 'merge_failed', conflict: { files: ['x.txt'] } }),
  e(3, 'rejected', { input: { command: 'verify' }, error: 'merge_conflict' })]).steps;
// Review 02 R4: a failed integrate before a verify that fails at Git must not hide the verify's own error.
const unrelated = taskHistory([e(1, 'rejected', { input: { command: 'integrate' }, error: 'not_verified' }),
  e(2, 'command_intent', {}), e(3, 'command_result', {}), e(4, 'rejected', { input: { command: 'verify' }, error: 'git_failed' })]).steps;
expect(unrelated.length === 2 && String(unrelated[1].detail).includes('git_failed'), 'an earlier unrelated failure does not hide a verify refusal');
// The repeat that is folded: a completion send-back followed by verify refused with the same error.
const repeated = taskHistory([e(1, 'delivery_rejected', { repair: { check: 'completion', failure: { error: 'oracle_failed' } } }),
  e(2, 'command_result', {}), e(3, 'rejected', { input: { command: 'verify' }, error: 'oracle_failed' })]).steps;
expect(repeated.length === 1, 'a verify refusal repeating its send-back is folded');
// Review 03 N1: the production order of a conflict that the worker is asked to fix (core.ts writeConflict): feedback
// events sit between the conflict and the verify refusal, and the refusal is still the same conflict.
const conflictEvents = [e(1, 'verification_result', { state: 'merge_failed' }), e(2, 'verification_conflict', { state: 'merge_failed', conflict: { files: ['x.txt'] } }),
  e(3, 'conflict_rework_intent', {}), e(4, 'conflict_feedback_intent', {}), e(5, 'conflict_feedback_delivered', {}),
  e(6, 'verification_cleanup_intent', {}), e(7, 'verification_worktree_removed', {})];
const fed = taskHistory([...conflictEvents, e(8, 'rejected', { input: { command: 'verify' }, error: 'merge_conflict' })]).steps;
expect(fed.length === 2, 'a conflict with feedback in between still shows the refusal once');
// A different error after the conflict is its own fact and stays.
const cleanupFailed = taskHistory([...conflictEvents, e(8, 'rejected', { input: { command: 'verify' }, error: 'git_failed' })]).steps;
expect(cleanupFailed.length === 3 && String(cleanupFailed[2].detail).includes('git_failed'), 'a different verify error after a conflict stays');
// Folding is used once: a later verify refused with the same code (nothing resubmitted) is a new refusal.
const again = taskHistory([e(1, 'delivery_rejected', { repair: { check: 'completion', failure: { error: 'oracle_failed' } } }),
  e(2, 'rejected', { input: { command: 'verify' }, error: 'oracle_failed' }), e(3, 'rejected', { input: { command: 'verify' }, error: 'oracle_failed' })]).steps;
expect(again.length === 2, 'a second refusal with the same code is not folded');
// Review 04 Q1: after a conflict whose worker had ended, core.ts replaces the worker inside the same verify, so the
// refusal row is written while attempt B is current; the refusal's details name A, whose verification it reports.
// conflict_worker_replaced is saved for A explicitly (core.ts save(..., attempt)), after B's claim and dispatch.
const at = (seq: number, attempt: string, type: string, details: any) => ({ seq, time: '2026-10-27T08:00:00Z', attempt, type, details });
const replaced = taskHistory([at(1, 'A', 'verification_result', { state: 'merge_failed' }), at(2, 'A', 'verification_conflict', { conflict: { files: ['novel.txt'] } }),
  at(3, 'A', 'conflict_rework_intent', {}), at(4, 'A', 'conflict_replacement_intent', {}), at(5, 'A', 'reclaimed', {}), at(6, 'A', 'revoked', { reason: 'conflict_session_ended' }),
  at(7, 'B', 'claimed', {}), at(8, 'B', 'dispatched', {}), at(9, 'A', 'conflict_worker_replaced', { repair: { replacement_attempt: 'B' }, original_attempt: 'A' }),
  at(10, 'B', 'rejected', { input: { command: 'verify' }, error: 'merge_conflict', details: { attempt: { attempt_id: 'A' } } })]).steps;
expect(!replaced.some((s: any) => s.label === '门禁拒绝'), 'the replaced worker\'s attempt does not show the old verify refusal');
expect(replaced.some((s: any) => s.label === '合并冲突后更换 worker'), 'the replacement is a visible step');
// Review 05 S1: the timeline names the attempt again when it returns to A after B (A = 1st, B = 2nd, no 3rd).
const replacedStep = replaced.find((s: any) => s.label === '合并冲突后更换 worker');
expect(replacedStep?.attempt === 'A', 'the replacement is recorded under the original attempt');
const heads = attemptStarts(replaced).flatMap((start: boolean, i: number) => start ? [replaced[i].attempt + ':' + replaced[i].label] : []);
expect(JSON.stringify(heads) === JSON.stringify(['A:验收', 'B:认领', 'A:合并冲突后更换 worker']), 'a header at every change of attempt, including the return to A');
const plain = attemptStarts([{ attempt: 'A' }, { attempt: null }, { attempt: 'A' }, { attempt: 'B' }] as any);
expect(JSON.stringify(plain) === JSON.stringify([true, false, false, true]), 'a step with no attempt does not split the attempt it sits in');
// B's own verification later conflicts too and its refusal is not folded by A's: B has its own conflict step first,
// and a B refusal with no conflict of B's own stays.
const own = taskHistory([at(1, 'A', 'verification_conflict', { conflict: { files: ['x'] } }),
  at(2, 'B', 'rejected', { input: { command: 'verify' }, error: 'merge_conflict', details: { attempt: { attempt_id: 'B' } } })]).steps;
expect(own.length === 2 && own[1].attempt === 'B', 'a refusal of another attempt\'s verification is not folded by A\'s conflict');
expect(merge.length === 2 && merge[0].detail === '合并失败' && String(merge[1].detail).includes('x.txt'), 'a merge conflict shows its files once');

console.log(JSON.stringify({ status: failures.length ? 'FAIL' : 'PASS', failures,
  t2: t2.steps.map((s: any) => `${s.label}${s.passed === null ? '' : s.passed ? ' ✓' : ' ✗'}${s.detail ? ' · ' + s.detail : ''}`),
  t138: t138.steps.map((s: any) => `${s.label}${s.passed === null ? '' : s.passed ? ' ✓' : ' ✗'}${s.detail ? ' · ' + s.detail : ''}`) }, null, 1));
process.exit(failures.length ? 1 : 0);
