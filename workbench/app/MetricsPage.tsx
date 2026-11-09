import { useEffect, useState } from 'react';
import './records.css';

type TurnSource = { sequence: number; type: string; time: string; in_range: boolean; file: string | null; offset: number | null; prompt_id: string | null };
type Session = { launch: string; project: string | null; task: string | null; task_type: string | null; role: string; role_label: string;
  cli: string | null; model: string; effort: string; requested_model: string | null; turns: number | null; turn_sources: TurnSource[] };
type Metrics = {
  model_use: { sessions: Session[]; by_model: { model: string; task_type: string; sessions: number; turns: number | null;
    recorded_turns: number; uncovered_sessions: number }[] };
  first_time: { integrated: number; first_time: number; rate: number | null; rejections: Record<string, number> };
  attention: { task: string; attempt: string; task_type: string; answers: number; approvals: number; interventions: number; stops: number }[];
  scores: { cli: string; model: string; effort: string; task_type: string; attempts: number; results: Record<string, number>;
    boundary_discipline: number | null; engineering_taste: number | null }[];
};
const checks: Record<string, string> = { identity_version: '身份与版本', path_boundary: '路径边界', oracle: '验收文件不被改动', completion: '完成条件',
  red_state: '红态', rule_checks: '规则式检查', independent_review: '独立审查', commit_trailers: '提交尾注' };
const short = (task: string | null) => task ? task.slice(task.indexOf('+') + 1) : '项目级';
const none = <span className="metric-none">无数据</span>;
// T-273: with many sessions the page leads with totals and groups sessions by task. Small data stays fully open,
// as before; past this many sessions only the newest task's group starts open.
const OPEN_ALL_AT = 12;
const sum = (values: Array<number | null>) => values.reduce<number>((total, value) => total + (value ?? 0), 0);
// A date input names a local day; the range runs from the start of the first day to the end of the last.
const day = (value: string, end: boolean) => {
  if (!value) return null;
  const date = new Date(value + 'T00:00:00');
  if (end) date.setDate(date.getDate() + 1);
  return date.toISOString();
};

export function MetricsPage({ project }: { project: string | null }) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [since, setSince] = useState(''), [until, setUntil] = useState('');
  useEffect(() => {
    setMetrics(null);
    if (!project) return;
    let mounted = true;
    const load = () => window.a2a.metrics(project, day(since, false), day(until, true)).then((value: Metrics) => {
      if (mounted) { setMetrics(value); setError(null); }
    }, (reason: unknown) => { if (mounted) setError('指标读取失败：' + String(reason)); });
    void load();
    const timer = setInterval(load, 5000);
    return () => { mounted = false; clearInterval(timer); };
  }, [project, since, until]);
  const sessions = metrics?.model_use.sessions ?? [];
  const byTask = new Map<string, Session[]>();
  for (const row of sessions) byTask.set(row.task ?? '', [...(byTask.get(row.task ?? '') ?? []), row]);
  // Newest task first: the gate numbers tasks in order, so the larger number is the later one.
  const taskGroups = [...byTask.entries()].sort(([a], [b]) => (b ? 1 : 0) - (a ? 1 : 0) || b.localeCompare(a, 'en', { numeric: true }));
  const roleCounts = [...new Set(sessions.map(row => row.role_label))].map(label => `${label} ${sessions.filter(row => row.role_label === label).length}`);
  const rejections = Object.entries(metrics?.first_time.rejections ?? {});
  const rejected = rejections.filter(([, count]) => count > 0).sort(([, a], [, b]) => b - a);
  const uncovered = sessions.filter(row => row.turns === null).length;
  return <div className="records-page metrics-page">
    <div className="records-intro"><h2>指标</h2>
      <p>每次打开都从记录现算，不另存计数。模型取会话里实际观察到的值；看不到的记为 unknown，单独成行。看板上的变化只算观察，不能当成改进的证明。</p></div>
    {project && <div className="record-filter">
      <label>从 <input type="date" value={since} onChange={event => setSince(event.target.value)} /></label>
      <label>到 <input type="date" value={until} onChange={event => setUntil(event.target.value)} /></label>
    </div>}
    {error && <p className="catalog-error" role="alert">{error}</p>}
    {!project ? <p className="records-empty">先在左侧选一个项目。</p>
      : !metrics && !error ? <p className="records-empty" role="status">正在读取…</p> : null}
    {!error && metrics && <>
      <dl className="metric-tiles" data-metric-tiles>
        <div><dt>会话</dt><dd>{sessions.length}</dd><span>{roleCounts.join(' · ') || '—'}</span></div>
        <div><dt>已记录回合</dt><dd>{sum(sessions.map(row => row.turns))}</dd><span>{uncovered ? `另有 ${uncovered} 个会话未覆盖` : '全部会话都有计数来源'}</span></div>
        <div><dt>一次到位率</dt><dd>{metrics.first_time.rate === null ? '—' : Math.round(metrics.first_time.rate * 1000) / 10 + '%'}</dd>
          <span>集成 {metrics.first_time.integrated} 个，一次到位 {metrics.first_time.first_time} 个</span></div>
        <div><dt>打回</dt><dd>{sum(rejections.map(([, count]) => count))}</dd><span>{rejected.length ? rejected.map(([check, count]) => `${checks[check] ?? check} ${count}`).join(' · ') : '没有打回'}</span></div>
      </dl>
      <nav className="metric-jump" aria-label="跳到">
        {[['metric-model-use', '模型使用'], ['metric-first-time', '一次到位率'], ['metric-attention', '注意力'], ['metric-scores', '打分']].map(([id, label]) =>
          <button key={id} type="button" className="text-button" onClick={() => document.getElementById(id)?.scrollIntoView({ block: 'start' })}>{label}</button>)}</nav>
      <section className="metric-section" id="metric-model-use" data-metric="model-use">
        <h3>模型使用</h3>
        <details className="metric-notes"><summary>统计口径</summary>
        <p className="record-body">回合数只统计所选时间内后台采集的 Claude 回合事实和 Codex 回合上下文，按事件时间筛选。
          项目终端主控未接入这些计数来源时显示“未覆盖”；人工输入后的回复、CLI 回执只有被这些来源采集时才计入。Reflect 复盘不在此表中，这不是全局总回合。</p>
        <p className="record-body">0 表示该会话有计数来源，但区间内没有对应记录；“未知”表示汇总中还有未覆盖的会话。展开来源可核对会话、事件序号与原生日志位置。</p></details>
        {!metrics.model_use.sessions.length ? none : <>
          <table className="record-table">
            <thead><tr><th>模型</th><th>任务类型</th><th className="num">会话数</th><th className="num">已记录回合数</th></tr></thead>
            <tbody>{[...metrics.model_use.by_model].sort((a, b) => b.sessions - a.sessions || a.model.localeCompare(b.model)).map(row => <tr key={row.model + row.task_type} data-model={row.model} data-task-type={row.task_type}>
              <td>{row.model}</td><td>{row.task_type}</td><td className="num">{row.sessions}</td><td className="num">{row.turns ?? '未知'}
                {row.uncovered_sessions > 0 && <div className="record-meta">已记录 {row.recorded_turns}；未覆盖 {row.uncovered_sessions} 个会话</div>}</td></tr>)}</tbody>
          </table>
          <h4>按任务看会话（{taskGroups.length} 个任务，最新在前）</h4>
          {taskGroups.map(([taskId, rows], index) => <details key={taskId || 'project'} className="metric-group" data-metric-task={taskId}
            open={sessions.length <= OPEN_ALL_AT || index === 0}>
            <summary><strong>{short(taskId || null)}</strong><span>{rows.length} 个会话</span>
              <span>{[...new Set(rows.map(row => row.role_label))].map(label => `${label} ${rows.filter(row => row.role_label === label).length}`).join(' · ')}</span>
              <span>{rows.every(row => row.turns === null) ? '回合未覆盖' : `回合 ${rows.some(row => row.turns === null) ? '至少 ' : ''}${sum(rows.map(row => row.turns))}`}</span></summary>
          <table className="record-table">
            <thead><tr><th>角色</th><th>CLI</th><th>模型</th><th>强度</th><th className="num">已记录回合数</th><th>计数来源</th></tr></thead>
            <tbody>{rows.map(row => <tr key={row.launch} data-launch={row.launch}>
              <td>{row.role_label}</td><td>{row.cli ?? 'unknown'}</td><td>{row.model}</td><td>{row.effort}</td>
              <td className="num" data-turn-count>{row.turns ?? '未覆盖'}</td>
              <td><details><summary>{row.turn_sources.length ? '查看来源' : '未接入计数来源'}</summary>
                <div className="record-meta">会话 {row.launch}</div>
                {row.turn_sources.map(source => <div key={source.sequence} className="record-meta">
                  #{source.sequence} · {source.type === 'native_turn_facts' ? 'Claude 回合事实' : 'Codex 回合上下文'} · {source.time}
                  {source.in_range ? '（区间内）' : '（区间外，不计入）'}
                  {source.prompt_id && <div>提示 {source.prompt_id}</div>}
                  {source.file && <div>{source.file} · 位置 {source.offset}</div>}
                </div>)}
              </details></td></tr>)}</tbody>
          </table></details>)}
        </>}
      </section>
      <section className="metric-section" id="metric-first-time" data-metric="first-time">
        <h3>一次到位率</h3>
        <p className="record-body">第一次交付就过完整门禁、全程没人介入，才算一次到位。</p>
        <details className="metric-notes"><summary>统计口径</summary>
        <p className="record-body">分母只含所选范围内结果为“通过”且有门禁事实的打分记录。打回原因来自所选范围内已打分的结束 attempt，尚未打分的不计入。</p></details>
        {metrics.first_time.rate === null ? none
          : <p className="metric-figure" data-rate={metrics.first_time.rate}>{Math.round(metrics.first_time.rate * 1000) / 10}%
            <span className="record-meta">（集成 {metrics.first_time.integrated} 个，一次到位 {metrics.first_time.first_time} 个）</span></p>}
        <h4>打回原因</h4>
        {!rejections.length ? none : <>
          {rejected.length > 0 && <ul className="metric-bars">{rejected.map(([check, count]) => <li key={check} data-check={check}>
            <span>{checks[check] ?? check}</span><span className="metric-bar" style={{ width: `${(count / rejected[0][1]) * 100}%` }} aria-hidden="true" />
            <span className="num">{count}</span></li>)}</ul>}
          {rejected.length < rejections.length && <p className="record-meta">
            {rejected.length ? '其余' : '全部'} {rejections.length - rejected.length} 项没有打回：{rejections.filter(([, count]) => !count).map(([check]) => checks[check] ?? check).join('、')}</p>}
        </>}
      </section>
      <section className="metric-section" id="metric-attention" data-metric="attention">
        <h3>你的注意力消耗</h3>
        <p className="record-body">每个集成的任务一行，数的是这个任务全部 attempt 的累计。项目级角色批准/拒绝不摊入某个任务。</p>
        {!metrics.attention.length ? none : <table className="record-table">
          <thead><tr><th>集成的任务</th><th>任务类型</th><th>答题</th><th>审批</th><th>介入</th><th>叫停</th></tr></thead>
          <tbody>{metrics.attention.map(row => <tr key={row.task} data-task={row.task}>
            <td>{short(row.task)}</td><td>{row.task_type}</td><td>{row.answers}</td><td>{row.approvals}</td><td>{row.interventions}</td><td>{row.stops}</td></tr>)}</tbody>
        </table>}
      </section>
      <section className="metric-section" id="metric-scores" data-metric="scores">
        <h3>打分汇总</h3>
        {!metrics.scores.length ? none : <table className="record-table">
          <thead><tr><th>CLI</th><th>模型</th><th>强度</th><th>任务类型</th><th>attempt 数</th><th>结果</th><th>边界纪律</th><th>工程品味</th></tr></thead>
          <tbody>{metrics.scores.map(row => <tr key={[row.cli, row.model, row.effort, row.task_type].join('|')} data-model={row.model} data-task-type={row.task_type}>
            <td>{row.cli}</td><td>{row.model}</td><td>{row.effort}</td><td>{row.task_type}</td><td>{row.attempts}</td>
            <td>{Object.entries(row.results).map(([result, count]) => `${result} ${count}`).join('，')}</td>
            <td>{row.boundary_discipline ?? '无数据'}</td><td>{row.engineering_taste ?? '无数据'}</td></tr>)}</tbody>
        </table>}
      </section>
    </>}
  </div>;
}
