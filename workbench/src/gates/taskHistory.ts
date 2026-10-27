// T-192: a task's gate history in steps a person can read, whether or not any of its panes is still alive.
// The events table keeps every detail; this keeps the milestone, whether it passed, and one line of why.

export type HistoryEvent = { seq: number; time: string; attempt: string | null; type: string; details: any };
export type HistoryStep = { seq: number; time: string; attempt: string | null; label: string; passed: boolean | null; detail: string | null };
export type ReviewFinding = { path: string | null; line: number | null; text: string; suggestion: string | null };
export type ReviewRecord = { seq: number; time: string; attempt: string | null; verdict: string; findings: ReviewFinding[]; report: Record<string, string> };
export type TaskHistory = {
  steps: HistoryStep[];
  reviews: ReviewRecord[];
  score: { attempt: string | null; source: string; data: Record<string, unknown> } | null;
  integration: { attempt: string | null; commit: string; trailers: Record<string, string[]> | null } | null;
  closed: { time: string; reason: string } | null;
};

// Drafting a card and reading state are refused often while a controller works; they never moved the task.
const quietRefusals = new Set(['card_template', 'card_validate', 'card_save', 'card_show', 'create', 'status', 'events', 'task_history', 'issues']);
const verificationStates: Record<string, string> = { passed: '通过', failed: '未通过', merge_failed: '合并失败', interrupted: '中断', unknown: '结果未知', running: '进行中' };
const short = (value: unknown, length = 10) => typeof value === 'string' ? value.slice(0, length) : null;
const list = (values: unknown) => Array.isArray(values) && values.length ? values.join('、') : null;
const tail = (argv: unknown) => Array.isArray(argv) && argv.length ? String(argv[argv.length - 1]).split('/').pop()! : null;
const exit = (result: any) => result?.returncode ?? result?.exit ?? '无';

function step(event: HistoryEvent): Omit<HistoryStep, 'seq' | 'time' | 'attempt'> | null {
  const d = event.details ?? {};
  switch (event.type) {
    case 'created': return { label: '创建任务', passed: null, detail: null };
    case 'rejected': return quietRefusals.has(d.input?.command) ? null : { label: '门禁拒绝', passed: false,
      detail: `${d.input?.command ?? '请求'}：${d.error ?? '原因未知'}${d.details?.reason ? `（${d.details.reason}）` : ''}` };
    // T-197: a clean check is noise; an overlap let through shows the reason the controller wrote.
    case 'claim_path_check': return Array.isArray(d.conflicts) && d.conflicts.length ? { label: '路径重叠', passed: Boolean(d.passed),
      detail: `与 ${d.conflicts.map((c: any) => `${c.task}（${list(c.paths) ?? '路径'}）`).join('、')}${d.reason ? `；放行理由：${d.reason}` : ''}` } : null;
    case 'claimed': return { label: '认领', passed: null, detail: null };
    case 'dispatched': return { label: '启动 worker', passed: null, detail: null };
    case 'submitted': return { label: '交付', passed: null, detail: short(d.commit) && `候选提交 ${short(d.commit)}` };
    // T-198: out-of-card files wait for the controller's judgement; older events refused them as `forbidden`.
    case 'path_check': return d.out_of_card ? { label: '路径检查', passed: d.out_of_card.length ? null : true,
      detail: d.out_of_card.length ? `卡外改动待主控判断：${list(d.out_of_card)}` : null }
      : { label: '路径检查', passed: Boolean(d.passed), detail: d.passed ? null : `卡外改动：${list(d.forbidden) ?? '未知'}` };
    case 'out_of_card_judged': return { label: d.decision === 'accept' ? '放行卡外改动' : '打回卡外改动', passed: d.decision === 'accept',
      detail: `${list(d.out_of_card) ?? ''}；理由：${d.reason ?? '无'}` };
    case 'oracle_check': return { label: '验收文件未改动', passed: Boolean(d.passed), detail: d.passed ? null : `改动了：${list(d.modified) ?? '未知'}` };
    case 'completion_check': return { label: `完成条件 ${d.index ?? ''}`.trim(), passed: Boolean(d.passed), detail: tail(d.result?.argv) };
    case 'red_check': return { label: `红态检查 ${d.index ?? ''}`.trim(), passed: Boolean(d.passed),
      detail: `基线退出 ${exit(d.base_result)}，候选退出 ${exit(d.candidate_result)}` };
    case 'rule_check': return { label: `规则检查 ${d.id ?? ''}`.trim(), passed: Boolean(d.passed), detail: d.passed ? null : `退出 ${exit(d.result)}` };
    case 'trailer_check': return { label: '提交尾注', passed: Boolean(d.passed), detail: d.passed ? null : d.error ?? '尾注缺失' };
    case 'red_not_applicable': return { label: '红态检查', passed: null, detail: '不适用' };
    case 'rules_not_applicable': return { label: '规则检查', passed: null, detail: '不适用' };
    case 'verification_result': {
      // A merge failure saves the verification itself; the other outcomes wrap it.
      const v = d.verification ?? d;
      return { label: '验收', passed: v.state === 'passed', detail: verificationStates[v.state] ?? v.state ?? null };
    }
    case 'verification_conflict': return { label: '合并冲突', passed: false, detail: list(d.conflict?.files) };
    case 'review_result': return { label: '独立审查', passed: d.review?.result?.verdict === '可合并', detail: d.review?.result?.verdict ?? d.review?.state ?? null };
    case 'delivery_rejected': return { label: '打回', passed: false,
      detail: d.repair?.check === 'independent_review' ? `独立审查：${d.repair?.failure?.verdict ?? '需修复'}` : `${d.repair?.check ?? '检查'}：${d.repair?.failure?.error ?? '未通过'}` };
    case 'conflict_worker_replaced': return { label: '合并冲突后更换 worker', passed: null,
      detail: short(d.repair?.replacement_attempt, 8) && `新执行尝试 ${short(d.repair.replacement_attempt, 8)}` };
    case 'integration_compare_failed': return { label: '集成', passed: false, detail: '工作分支已变，需重新验收' };
    case 'integrated': return { label: '集成', passed: true, detail: short(d.intent?.M) && `合并提交 ${short(d.intent.M)}` };
    case 'score_recorded': return { label: '打分', passed: null,
      detail: `${d.data?.result ?? ''} · 边界纪律 ${d.data?.boundary_discipline ?? '-'}/3 · 工程品味 ${d.data?.engineering_taste ?? '-'}/3`.replace(/^ · /, '') };
    case 'attempt_ended': return { label: '结束执行尝试', passed: null, detail: d.result ?? null };
    case 'issue_issue': return { label: '上报问题', passed: null, detail: d.title ?? null };
    case 'revoked': return { label: '撤销执行尝试', passed: null, detail: d.reason ?? null };
    case 'reclaimed': return { label: '回收', passed: null, detail: null };
    case 'closed': return { label: '关闭任务', passed: null, detail: d.reason ?? null };
    default: return null;
  }
}

export function taskHistory(events: HistoryEvent[]): TaskHistory {
  const history: TaskHistory = { steps: [], reviews: [], score: null, integration: null, closed: null };
  const trailers = new Map<string, Record<string, string[]>>();
  // What the last verification of each attempt sent back (its error code), until the refused verify that reports it.
  const open = new Map<string | null, string>();
  for (const event of events) {
    const d = event.details ?? {};
    const shown = step(event);
    // A refused verify repeats what its own verification just recorded: the send-back with the same error, or the
    // merge conflict. Feedback, cleanup or a replacement worker may sit in between; any other refusal stays.
    // The row's attempt is whatever was current when the refusal was written (a replacement worker after a conflict);
    // the refusal itself names the attempt whose verification it reports.
    const verify = event.type === 'rejected' && d.input?.command === 'verify';
    const attempt = verify ? d.details?.attempt?.attempt_id ?? event.attempt : event.attempt;
    let repeat = false;
    if (verify && open.has(attempt)) {
      repeat = open.get(attempt) === d.error;
      open.delete(attempt);
    }
    if (event.type === 'submitted' || event.type === 'verification_result') open.delete(event.attempt);
    if (event.type === 'delivery_rejected') open.set(event.attempt, d.repair?.failure?.error);
    if (event.type === 'verification_conflict') open.set(event.attempt, 'merge_conflict');
    if (shown && !repeat) history.steps.push({ seq: event.seq, time: event.time, attempt, ...shown });
    if (event.type === 'trailer_check' && d.commit) trailers.set(d.commit, d.trailers ?? null);
    if (event.type === 'review_result' && d.review?.result) {
      const result = d.review.result;
      history.reviews.push({ seq: event.seq, time: event.time, attempt: event.attempt, verdict: String(result.verdict ?? ''),
        findings: (Array.isArray(result.findings) ? result.findings : []).map((f: any) => ({ path: f?.location?.path ?? null,
          line: f?.location?.line ?? null, text: String(f?.failure_scenario ?? ''), suggestion: f?.suggestion ? String(f.suggestion) : null })),
        report: Object.fromEntries(Object.entries(result.report ?? {}).map(([key, value]) => [key, String(value)])) });
    }
    if (event.type === 'score_recorded') history.score = { attempt: event.attempt, source: String(d.source ?? ''), data: d.data ?? {} };
    if (event.type === 'integrated' && d.intent?.M)
      history.integration = { attempt: event.attempt, commit: d.intent.M, trailers: trailers.get(d.intent.C) ?? null };
    if (event.type === 'closed') history.closed = { time: event.time, reason: String(d.reason ?? '') };
  }
  return history;
}

// Where the timeline names an attempt: wherever the steps move to another attempt, including a return to an earlier one
// (after a conflict, the original attempt records replacing its worker once the new attempt has started).
// Steps with no attempt stay under the attempt shown above them.
export function attemptStarts(steps: HistoryStep[]): boolean[] {
  let shown: string | null = null;
  return steps.map(step => {
    const start = step.attempt !== null && step.attempt !== shown;
    if (step.attempt !== null) shown = step.attempt;
    return start;
  });
}
