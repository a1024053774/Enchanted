import { useEffect, useState } from 'react';
import type { A2AIssueView } from '../src/contracts/a2aGates.ts';
import './records.css';

export type TaskIssues = { task: string; name: string; title: string; issues: A2AIssueView[];
  reviewRecovery?: { attempt: string; review_id: string; thread_id: string } | null };
const roles: Record<string, string> = { worker: 'worker', reviewer: '审查员', monitor: '监视器' };
// The states a user still has to act on come first; the rest keep their reporting order.
const open = new Set(['等你决定', '待判断', '稍后', '已转交', '可能已随修订失效']);
const time = (value: string) => new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });

export function IssuesPage({ project }: { project: string | null }) {
  const [tasks, setTasks] = useState<TaskIssues[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  useEffect(() => {
    if (!project) return;
    let mounted = true;
    const load = () => window.a2a.issues(project).then((value: TaskIssues[]) => {
      if (!mounted) return;
      setTasks(value); setError(null);
    }, (reason: unknown) => { if (mounted) setError('问题列表读取失败：' + String(reason)); });
    void load();
    const timer = setInterval(load, 3000);
    return () => { mounted = false; clearInterval(timer); };
  }, [project, version]);
  const rows = (tasks ?? []).flatMap(task => task.issues.map(view => ({ task, view })))
    .sort((a, b) => Number(open.has(b.view.state)) - Number(open.has(a.view.state)));
  return <div className="records-page issues-page">
    <div className="records-intro"><h2>问题上报</h2>
      <p>worker、审查员和监视器发现任务范围外的问题时报到这里。答复会写进上报它的会话；标了“阻塞”的只有你能关闭。关闭的问题保留记录。</p></div>
    {error && <p className="catalog-error" role="alert">{error}</p>}
    {!project ? <p className="records-empty">先在左侧选一个项目。</p>
      : tasks === null && !error ? <p className="records-empty" role="status">正在读取…</p>
      : tasks !== null && !error && !rows.length ? <p className="records-empty">这个项目还没有问题上报。</p> : null}
    {rows.map(({ task, view }) => <Issue key={view.issue.id} task={task} view={view} changed={() => setVersion(value => value + 1)} />)}
  </div>;
}

function Issue({ task, view, changed }: { task: TaskIssues; view: A2AIssueView; changed: () => void }) {
  const { issue } = view;
  const [answer, setAnswer] = useState('');
  const [closing, setClosing] = useState(false);
  const [reason, setReason] = useState(''), [basis, setBasis] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [restarted, setRestarted] = useState(false);
  const role = issue.from.split(':')[0];
  const settled = view.state === '已关闭';
  let protocol: { error: string; raw: string } | null = null;
  if (issue.from === 'system' && issue.body) {
    try {
      const value = JSON.parse(issue.body);
      if (typeof value?.error === 'string' && typeof value?.raw === 'string') protocol = value;
    } catch { /* Ordinary issue bodies are free text. */ }
  }
  const recovery = protocol && task.reviewRecovery;
  const canRestart = recovery && recovery.attempt === issue.attempt_id && recovery.thread_id === issue.thread_id && !restarted;
  const act = (run: () => Promise<unknown>) => {
    setBusy(true); setError('');
    void run().then(() => { setAnswer(''); setClosing(false); changed(); }, reason => setError(String(reason))).finally(() => setBusy(false));
  };
  return <article className="record-card issue-card" data-issue-id={issue.id} data-issue-state={view.state} data-issue-blocking={issue.blocking || undefined}>
    <header className="record-heading">
      <strong>{task.name} · 问题 {issue.number}：{issue.title}</strong>
      <span className="record-state" data-tone={view.state === '等你决定' ? 'needs' : settled ? 'quiet' : undefined}>{view.state}</span>
      {issue.blocking && <span className="record-badge">阻塞</span>}
    </header>
    <p className="record-meta">{roles[role] ?? role} 上报 · {time(issue.created_at)}</p>
    {protocol ? <section className="record-body" data-review-protocol-error={protocol.error}>
      <p>{protocol.error === 'review_json'
        ? '审查输出不是可直接解析的 JSON 对象。代码围栏、前后说明或 JSON 语法错误都会被拒绝。'
        : `审查 JSON 的字段不符合协议：${protocol.error}。`}
        这次输出被拒绝，当时任务因此暂停。原文保留如下。</p>
      <details><summary>查看审查原文</summary><pre className="review-original">{protocol.raw}</pre></details>
      {canRestart && <div className="record-actions"><p>将停止并归档旧审查，为这一次交付新开一个干净的审查会话，仍审查同一个候选提交。</p>
        <button type="button" className="primary-button" data-restart-review={recovery.review_id} disabled={busy}
          onClick={() => act(async () => { await window.a2a.restartReview(task.task, recovery.attempt, recovery.review_id); setRestarted(true); })}>为同一次交付新开审查</button></div>}
      {restarted && <p role="status">已为同一次交付新开审查，当前进度请查看任务。旧输出仍保留在这里。</p>}
      {!canRestart && !restarted && <p>这条记录不再提供恢复操作。请由执行主控核对当前任务状态；关闭问题不会恢复或验收任务。</p>}
    </section> : issue.body && <p className="record-body">{issue.body}</p>}
    {view.superseded_by_revision && <div className="record-actions" data-superseded-attempt={view.superseded_by_revision.attempt}>
      <p>上报它的 attempt 已在修订任务卡时作废，任务已按新卡重新派发，这个问题可能已经不成立。它不再计入等你决定。请看上面的原文，确认不再需要处理就关闭；仍需处理的照常答复。</p>
      <div className="record-buttons"><button type="button" className="primary-button" data-confirm-superseded={issue.id} disabled={busy}
        onClick={() => act(() => window.a2a.disposeIssue(task.task, issue.id, 'close', '已随修订失效',
          `上报所在的 attempt ${view.superseded_by_revision!.attempt} 已因修订任务卡作废，任务按新卡重新派发`))}>确认已失效，关闭</button></div>
    </div>}
    {view.answer && <p className="record-reply"><span>答复</span>{view.answer.body}</p>}
    {view.disposition && <p className="record-reply"><span>处置</span>{({ close: '已关闭', dismiss: '不处理', snooze: '稍后再看', forward: '转交构思主控', 'needs-user': '交给你决定', reopen: '重新打开', delivered: '答复已送达' } as Record<string, string>)[view.disposition.action ?? ''] ?? view.disposition.action}
      {view.disposition.reason ? `：${view.disposition.reason}` : ''}</p>}
    {!settled && !view.answer && <form className="record-actions" onSubmit={event => { event.preventDefault(); act(() => window.a2a.answerIssue(task.task, issue.id, answer)); }}>
      <label>答复<textarea value={answer} maxLength={4000} rows={2} disabled={busy} onChange={event => setAnswer(event.target.value)} /></label>
      <div className="record-buttons">
        <button className="primary-button" disabled={busy || !answer.trim()}>发送答复</button>
        <button type="button" className="text-button" disabled={busy} onClick={() => act(() => window.a2a.disposeIssue(task.task, issue.id, 'snooze'))}>稍后再看</button>
        <button type="button" className="text-button" disabled={busy} onClick={() => setClosing(value => !value)} aria-expanded={closing}>关闭…</button>
      </div>
    </form>}
    {closing && <form className="record-actions" onSubmit={event => { event.preventDefault(); act(() => window.a2a.disposeIssue(task.task, issue.id, 'close', reason, basis)); }}>
      <label>为什么关闭<input value={reason} maxLength={1000} disabled={busy} onChange={event => setReason(event.target.value)} /></label>
      <label>依据（看了什么）<input value={basis} maxLength={1000} disabled={busy} onChange={event => setBasis(event.target.value)} /></label>
      <div className="record-buttons"><button className="primary-button" disabled={busy || !reason.trim() || !basis.trim()}>确认关闭</button></div>
    </form>}
    {error && <p role="alert" className="catalog-error">{error}</p>}
  </article>;
}
