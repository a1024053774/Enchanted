import { useEffect, useState } from 'react';
import { attemptStarts, type TaskHistory } from '../src/gates/taskHistory.ts';
import { gateStateNames } from '../src/gateReceipts.ts';
import './records.css';

// T-192: what the gate knows about one task, readable after every pane of it is gone.
type Card = { goal?: string; non_goals?: string[]; paths?: { allow?: string[]; deny?: string[] }; oracle_paths?: string[];
  completion_conditions?: { argv?: string[] }[] };
type Loaded = { task: { task_id: string; title?: string; state: string; card?: Card; current_attempt?: { attempt_id: string; runtime_identity?: { launch?: string } | null } | null }; history: TaskHistory };

const time = (value: string) => new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
const mark = (passed: boolean | null) => passed === null ? null : <span className="record-mark" data-passed={passed}>{passed ? '通过' : '未通过'}</span>;

export function TaskRecord({ task, docked, openSession, busy }: { task: string; docked: boolean; openSession?: (launch: string) => (() => void) | null; busy?: boolean }) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let mounted = true;
    setLoaded(null); setError(null);
    const load = () => window.a2a.taskHistory(task).then((value: Loaded) => { if (mounted) { setLoaded(value); setError(null); } },
      (reason: unknown) => { if (mounted) setError('门禁记录读取失败：' + String(reason)); });
    void load();
    const timer = setInterval(load, 3000);
    return () => { mounted = false; clearInterval(timer); };
  }, [task]);
  if (error) return <p className="catalog-error" role="alert">{error}</p>;
  if (!loaded) return <p className="records-empty" role="status">正在读取门禁记录…</p>;
  const { card = {}, state } = loaded.task;
  const { steps, reviews, score, integration, closed } = loaded.history;
  const attempts = [...new Set(steps.flatMap(step => step.attempt ? [step.attempt] : []))];
  const starts = attemptStarts(steps);
  const body = <>
    {closed && <p className="record-closed">已关闭 · {time(closed.time)} · {closed.reason}</p>}
    <section className="record-section" aria-label="任务卡">
      <h3>任务卡</h3>
      {card.goal && <p className="record-goal">{card.goal}</p>}
      <dl className="record-facts">
        {card.non_goals?.length ? <div><dt>不做</dt><dd>{card.non_goals.join('；')}</dd></div> : null}
        <div><dt>可改路径</dt><dd className="record-mono">{card.paths?.allow?.join('  ') || '无'}</dd></div>
        {card.paths?.deny?.length ? <div><dt>禁改路径</dt><dd className="record-mono">{card.paths.deny.join('  ')}</dd></div> : null}
        {card.oracle_paths?.length ? <div><dt>验收文件</dt><dd className="record-mono">{card.oracle_paths.join('  ')}</dd></div> : null}
        {card.completion_conditions?.map((condition, index) => <div key={index}><dt>完成条件 {index + 1}</dt>
          <dd className="record-mono">{condition.argv?.join(' ')}</dd></div>)}
      </dl>
    </section>
    {(score || integration) && <section className="record-section" aria-label="结果">
      <h3>结果</h3>
      <dl className="record-facts">
        {score && <div><dt>打分</dt><dd>{String(score.data.result ?? '')} · 边界纪律 {String(score.data.boundary_discipline ?? '-')}/3 · 工程品味 {String(score.data.engineering_taste ?? '-')}/3</dd></div>}
        {score?.data.boundary_reason ? <div><dt>边界理由</dt><dd>{String(score.data.boundary_reason)}</dd></div> : null}
        {score?.data.engineering_reason ? <div><dt>工程理由</dt><dd>{String(score.data.engineering_reason)}</dd></div> : null}
        {integration && <div><dt>集成提交</dt><dd className="record-mono">{integration.commit}</dd></div>}
        {integration?.trailers && Object.entries(integration.trailers).map(([key, values]) =>
          <div key={key}><dt>A2A-{key}</dt><dd className="record-mono">{values.join(', ')}</dd></div>)}
      </dl>
    </section>}
    {reviews.length > 0 && <section className="record-section" aria-label="审查报告">
      <h3>审查报告</h3>
      {reviews.map((review, index) => <details key={review.seq} className="record-review" open={index === reviews.length - 1}>
        <summary>第 {index + 1} 次审查 · {review.verdict}{review.findings.length ? ` · ${review.findings.length} 条问题` : ''} · {time(review.time)}
          {review.attempt && <span className="task-meta"> · 第 {attempts.indexOf(review.attempt) + 1} 次执行尝试</span>}</summary>
        <dl className="record-facts">
          {review.findings.map((finding, findingIndex) => <div key={findingIndex}>
            <dt>{finding.path ? `${finding.path}${finding.line ? ':' + finding.line : ''}` : `问题 ${findingIndex + 1}`}</dt>
            <dd>{finding.text}{finding.suggestion && <><br /><span className="record-detail">建议：{finding.suggestion}</span></>}</dd></div>)}
          {Object.entries(review.report).map(([section, text]) => <div key={section}><dt>{section}</dt><dd className="record-report">{text}</dd></div>)}
        </dl>
      </details>)}
    </section>}
    <section className="record-section" aria-label="门禁时间线">
      <h3>门禁时间线</h3>
      {!steps.length ? <p className="records-empty">门禁里还没有这个任务的记录。</p> : <ol className="record-timeline">
        {steps.map((step, index) => {
          const first = starts[index];
          return <li key={step.seq} data-attempt-start={first || undefined}>
            {first && <span className="record-attempt">第 {attempts.indexOf(step.attempt!) + 1} 次执行尝试 · {step.attempt!.slice(0, 8)}</span>}
            <time>{time(step.time)}</time><strong>{step.label}</strong>{mark(step.passed)}
            {step.detail && <span className="record-detail">{step.detail}</span>}
          </li>;
        })}
      </ol>}
    </section>
  </>;
  const launch = loaded.task.current_attempt?.runtime_identity?.launch;
  const open = launch && openSession ? openSession(launch) : null;
  if (docked) return <details className="task-record task-record-docked">
    <summary>门禁记录 · {gateStateNames[state] ?? state} · {steps.length} 步</summary>
    <div className="task-record-body">{body}</div>
  </details>;
  return <div className="task-record task-record-full" aria-label="门禁记录">
    <header><h2>{loaded.task.title ?? task}</h2><span className="task-meta">{gateStateNames[state] ?? state} · {task}</span>
      <p className="task-meta">这个任务没有打开的窗格。下面是门禁里的全部记录；要看会话，从左侧点选或新建终端。</p>
      {open && <p className="record-live">当前执行尝试有 worker 会话。<button className="primary-button" disabled={busy} onClick={open}>打开 worker 会话</button></p>}</header>
    {body}
  </div>;
}
