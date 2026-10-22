import { useEffect, useState } from 'react';
import type { A2AIssueView } from '../src/contracts/a2aGates.ts';
import './records.css';

export type TaskIssues = { task: string; name: string; title: string; issues: A2AIssueView[] };
const roles: Record<string, string> = { worker: 'worker', reviewer: '审查员', monitor: '监视器' };
// The states a user still has to act on come first; the rest keep their reporting order.
const open = new Set(['等你决定', '待判断', '稍后', '已转交']);
const time = (value: string) => new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });

export function IssuesPage({ project }: { project: string | null }) {
  const [tasks, setTasks] = useState<TaskIssues[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  useEffect(() => {
    if (!project) { setTasks([]); setError(null); return; }
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
      : tasks !== null && !rows.length ? <p className="records-empty">这个项目还没有问题上报。</p> : null}
    {!error && rows.map(({ task, view }) => <Issue key={view.issue.id} task={task} view={view} changed={() => setVersion(value => value + 1)} />)}
  </div>;
}

function Issue({ task, view, changed }: { task: TaskIssues; view: A2AIssueView; changed: () => void }) {
  const { issue } = view;
  const [answer, setAnswer] = useState('');
  const [closing, setClosing] = useState(false);
  const [reason, setReason] = useState(''), [basis, setBasis] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const role = issue.from.split(':')[0];
  const settled = view.state === '已关闭';
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
    {issue.body && <p className="record-body">{issue.body}</p>}
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
