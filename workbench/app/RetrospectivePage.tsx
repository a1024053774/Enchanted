import { useEffect, useState } from 'react';
import './records.css';

type Schedule = { enabled: boolean; weekday: number; hour: number; minute: number; cli: string; model: string; effort: string };
type Run = { id: string; trigger: string; since: string | null; until: string; cli: string; model: string; effort: string; created_at: string;
  events: { type: string; data: any; created_at: string }[] };
type Suggestion = { id: string; run: string; number: number; title: string; body: string; kind: string; decision: { approved: boolean } | null };
type Listing = { schedule: Schedule; runs: Run[]; suggestions: Suggestion[] };
const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
const kinds: Record<string, string> = { ticket: '写成 ticket', 'role-card': '改角色卡', other: '其他' };
const time = (value: string | null) => value ? new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '最早';
const pad = (value: number) => String(value).padStart(2, '0');

export function RetrospectivePage({ project }: { project: string | null }) {
  const [listing, setListing] = useState<Listing | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const [selection, setSelection] = useState<{ cli: string; model: string; effort: string } | null>(null);
  const [busy, setBusy] = useState(false), [actionError, setActionError] = useState('');
  useEffect(() => {
    if (!project) return;
    let mounted = true;
    const load = () => window.a2a.retrospectives(project).then((value: Listing) => {
      if (!mounted) return;
      setListing(value); setError(null);
      setSelection(current => current ?? { cli: value.schedule.cli, model: value.schedule.model, effort: value.schedule.effort });
    }, (reason: unknown) => { if (mounted) setError('复盘记录读取失败：' + String(reason)); });
    void load();
    const timer = setInterval(load, 5000);
    return () => { mounted = false; clearInterval(timer); };
  }, [project, version]);
  const act = (run: () => Promise<unknown>) => {
    setBusy(true); setActionError('');
    void run().then(() => setVersion(value => value + 1), reason => setActionError(String(reason))).finally(() => setBusy(false));
  };
  const schedule = listing?.schedule;
  return <div className="records-page retrospective-page">
    <div className="records-intro"><h2>复盘</h2>
      <p>复盘会话在一个普通项目终端里跑，只读代码和记录，只写自己的报告。报告存到项目的 findings/（没有这个目录就存在工作台数据目录）；改进建议列在下面，你批了，构思主控才把它写成 ticket 或改角色卡。</p></div>
    {error && <p className="catalog-error" role="alert">{error}</p>}
    {!project ? <p className="records-empty">先在左侧选一个项目。</p>
      : !listing && !error ? <p className="records-empty" role="status">正在读取…</p> : null}
    {listing && selection && schedule && <>
      <section className="metric-section">
        <h3>立即复盘</h3>
        <form className="record-filter" onSubmit={event => { event.preventDefault(); act(() => window.a2a.startRetrospective(project!, selection)); }}>
          <label>CLI <select value={selection.cli} disabled={busy} onChange={event => setSelection({ ...selection, cli: event.target.value })}>
            <option value="Claude Code">Claude Code</option><option value="Codex">Codex</option></select></label>
          <label>模型 <input value={selection.model} disabled={busy} onChange={event => setSelection({ ...selection, model: event.target.value })} /></label>
          <label>思考强度 <input value={selection.effort} size={8} disabled={busy} onChange={event => setSelection({ ...selection, effort: event.target.value })} /></label>
          <button className="primary-button" data-start-retrospective disabled={busy || !selection.model.trim() || !selection.effort.trim()}>立即复盘</button>
        </form>
        <p className="record-meta">时间范围从这个项目上次复盘到现在。</p>
      </section>
      <section className="metric-section">
        <h3>定期复盘</h3>
        <form className="record-filter" onSubmit={event => event.preventDefault()}>
          <label><input type="checkbox" checked={schedule.enabled} disabled={busy} data-schedule-enabled
            onChange={event => act(() => window.a2a.saveRetrospectiveSchedule({ enabled: event.target.checked }))} />开启</label>
          <label>每 <select value={schedule.weekday} disabled={busy} onChange={event => act(() => window.a2a.saveRetrospectiveSchedule({ weekday: Number(event.target.value) }))}>
            {weekdays.map((name, index) => <option key={index} value={index}>{name}</option>)}</select></label>
          <label><input type="time" value={`${pad(schedule.hour)}:${pad(schedule.minute)}`} disabled={busy} onChange={event => {
            const [hour, minute] = event.target.value.split(':').map(Number);
            if (Number.isInteger(hour) && Number.isInteger(minute)) act(() => window.a2a.saveRetrospectiveSchedule({ hour, minute }));
          }} /></label>
          <span className="record-meta">用 {schedule.cli} · {schedule.model} · {schedule.effort}</span>
        </form>
      </section>
      {actionError && <p className="catalog-error" role="alert">{actionError}</p>}
      <section className="metric-section">
        <h3>改进建议</h3>
        {!listing.suggestions.length ? <p className="metric-none">还没有建议。</p> : listing.suggestions.map(item =>
          <article key={item.id} className="record-card suggestion-card" data-suggestion-id={item.id}
            data-suggestion-state={item.decision ? (item.decision.approved ? 'approved' : 'declined') : 'open'}>
            <header className="record-heading"><strong>{item.number}. {item.title}</strong>
              <span className="record-state" data-tone={item.decision ? 'quiet' : 'needs'}>{item.decision ? (item.decision.approved ? '已批准，交构思主控' : '不采纳') : '等你决定'}</span>
              <span className="record-meta">{kinds[item.kind] ?? item.kind}</span></header>
            {item.body && <p className="record-body">{item.body}</p>}
            {!item.decision && <div className="record-buttons">
              <button className="primary-button" disabled={busy} onClick={() => act(() => window.a2a.decideRetrospectiveSuggestion(item.id, true))}>批准</button>
              <button className="text-button" disabled={busy} onClick={() => act(() => window.a2a.decideRetrospectiveSuggestion(item.id, false))}>不采纳</button>
            </div>}
          </article>)}
      </section>
      <section className="metric-section">
        <h3>复盘记录</h3>
        {!listing.runs.length ? <p className="metric-none">还没有复盘。</p> : <table className="record-table">
          <thead><tr><th>开始</th><th>方式</th><th>范围</th><th>执行</th><th>状态</th><th>报告</th></tr></thead>
          <tbody>{[...listing.runs].reverse().map(run => {
            const imported = run.events.find(event => event.type === 'imported');
            const failed = !imported && run.events.find(event => event.type === 'import_failed');
            return <tr key={run.id} data-run-id={run.id} data-run-state={imported ? 'done' : failed ? 'failed' : 'running'}>
              <td>{time(run.created_at)}</td><td>{run.trigger === 'schedule' ? '定期' : '手动'}</td>
              <td>{time(run.since)} – {time(run.until)}</td><td>{run.cli} · {run.model} · {run.effort}</td>
              <td>{imported ? '已完成' : failed ? `导入失败（${failed.data.reason === 'suggestions_not_json' ? 'suggestions.json 不是合法 JSON' : 'suggestions.json 不是建议列表'}），修好后自动重试` : '进行中'}</td><td className="record-text">{imported?.data.report ?? '—'}</td></tr>;
          })}</tbody>
        </table>}
      </section>
    </>}
  </div>;
}
