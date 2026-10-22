import { useEffect, useState } from 'react';
import './records.css';

type Session = { launch: string; project: string | null; task: string | null; task_type: string | null; role: string; role_label: string;
  cli: string | null; model: string; effort: string; requested_model: string | null; turns: number };
type Metrics = {
  model_use: { sessions: Session[]; by_model: { model: string; task_type: string; sessions: number; turns: number }[] };
  first_time: { integrated: number; first_time: number; rate: number | null; rejections: Record<string, number> };
  attention: { task: string; attempt: string; task_type: string; answers: number; approvals: number; interventions: number; stops: number }[];
  scores: { cli: string; model: string; effort: string; task_type: string; attempts: number; results: Record<string, number>;
    boundary_discipline: number | null; engineering_taste: number | null }[];
};
const checks: Record<string, string> = { identity_version: '身份与版本', path_boundary: '路径边界', oracle: '验收文件不被改动', completion: '完成条件',
  red_state: '红态', rule_checks: '规则式检查', independent_review: '独立审查', commit_trailers: '提交尾注' };
const short = (task: string | null) => task ? task.slice(task.indexOf('+') + 1) : '项目级';
const none = <span className="metric-none">无数据</span>;
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
      <section className="metric-section" data-metric="model-use">
        <h3>模型使用</h3>
        {!metrics.model_use.sessions.length ? none : <>
          <table className="record-table">
            <thead><tr><th>模型</th><th>任务类型</th><th>会话数</th><th>回合数</th></tr></thead>
            <tbody>{metrics.model_use.by_model.map(row => <tr key={row.model + row.task_type} data-model={row.model} data-task-type={row.task_type}>
              <td>{row.model}</td><td>{row.task_type}</td><td>{row.sessions}</td><td>{row.turns}</td></tr>)}</tbody>
          </table>
          <table className="record-table">
            <thead><tr><th>任务</th><th>角色</th><th>CLI</th><th>模型</th><th>强度</th><th>回合数</th></tr></thead>
            <tbody>{metrics.model_use.sessions.map(row => <tr key={row.launch} data-launch={row.launch}>
              <td>{short(row.task)}</td><td>{row.role_label}</td><td>{row.cli ?? 'unknown'}</td><td>{row.model}</td><td>{row.effort}</td><td>{row.turns}</td></tr>)}</tbody>
          </table>
        </>}
      </section>
      <section className="metric-section" data-metric="first-time">
        <h3>一次到位率</h3>
        <p className="record-body">第一次交付就过完整门禁、全程没人介入，才算一次到位。</p>
        {metrics.first_time.rate === null ? none
          : <p className="metric-figure" data-rate={metrics.first_time.rate}>{Math.round(metrics.first_time.rate * 1000) / 10}%
            <span className="record-meta">（集成 {metrics.first_time.integrated} 个，一次到位 {metrics.first_time.first_time} 个）</span></p>}
        <h4>打回原因</h4>
        {!Object.keys(metrics.first_time.rejections).length ? none : <table className="record-table">
          <thead><tr><th>检查项</th><th>打回次数</th></tr></thead>
          <tbody>{Object.entries(metrics.first_time.rejections).map(([check, count]) => <tr key={check} data-check={check}>
            <td>{checks[check] ?? check}</td><td>{count}</td></tr>)}</tbody>
        </table>}
      </section>
      <section className="metric-section" data-metric="attention">
        <h3>你的注意力消耗</h3>
        {!metrics.attention.length ? none : <table className="record-table">
          <thead><tr><th>集成的任务</th><th>任务类型</th><th>答题</th><th>审批</th><th>介入</th><th>叫停</th></tr></thead>
          <tbody>{metrics.attention.map(row => <tr key={row.attempt} data-task={row.task}>
            <td>{short(row.task)}</td><td>{row.task_type}</td><td>{row.answers}</td><td>{row.approvals}</td><td>{row.interventions}</td><td>{row.stops}</td></tr>)}</tbody>
        </table>}
      </section>
      <section className="metric-section" data-metric="scores">
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
