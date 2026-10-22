import { useEffect, useState } from 'react';
import './records.css';

export type UserInputRecord = { id: string; created_at: string; form: string; channel: string; certainty: string; text: string;
  task: string | null; attempt: string | null; thread: string; launch: string | null; role: string | null; intervention: number | null };
const forms: Record<string, string> = { message: '消息', answer: '答复', approval: '批准', denial: '拒绝', choice: '选择', action: '操作', gap: '记录缺口' };
const channels: Record<string, string> = { 'terminal-window': '窗格键入', 'issue-panel': '问题面板', 'thread-message': '会话消息', 'ws-rpc': '界面操作',
  'ui-derived': '界面推断', 'settings-page': '设置页', 'commit-trailer': '提交（缺尾注）' };
const roles: Record<string, string> = { worker: 'worker', reviewer: '审查员', monitor: '监视器', ideation: '构思主控', executor: '执行主控', shell: '项目终端' };
const time = (value: string) => new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
const short = (task: string | null) => task ? task.slice(task.indexOf('+') + 1) : '项目级';
// A key the user pressed in a pane is recorded as its control character; show its name instead of nothing.
const keys: Record<string, string> = { '\r': '回车', '\n': '换行', '\x1b': 'Esc', '\x7f': '退格', '\t': 'Tab', '\x03': 'Ctrl-C' };
const content = (text: string) => keys[text] ? `（按键：${keys[text]}）` : /^[\x00-\x1f\x7f]+$/.test(text)
  ? `（按键：${[...text].map(c => keys[c] ?? '0x' + c.charCodeAt(0).toString(16).padStart(2, '0')).join(' ')}）` : text;

export function RecordsPage({ project }: { project: string | null }) {
  const [records, setRecords] = useState<UserInputRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [task, setTask] = useState(''), [session, setSession] = useState('');
  useEffect(() => {
    setRecords(null); setTask(''); setSession('');
    if (!project) return;
    let mounted = true;
    const load = () => window.a2a.records(project).then((value: UserInputRecord[]) => {
      if (mounted) { setRecords(value); setError(null); }
    }, (reason: unknown) => { if (mounted) setError('记录读取失败：' + String(reason)); });
    void load();
    const timer = setInterval(load, 3000);
    return () => { mounted = false; clearInterval(timer); };
  }, [project]);
  const all = records ?? [];
  const tasks = [...new Set(all.map(record => record.task ?? ''))];
  const sessions = [...new Map(all.filter(record => !task || (record.task ?? '') === task)
    .map(record => [record.thread, record])).values()];
  const rows = all.filter(record => (!task || (record.task ?? '') === task) && (!session || record.thread === session));
  return <div className="records-page user-input-page">
    <div className="records-intro"><h2>用户输入记录</h2>
      <p>你亲手打的字、在面板里的答复和审批都记在这里，主控和后台派发的文字不算。落在受管 worker 会话里的输入记为人工介入。</p></div>
    {error && <p className="catalog-error" role="alert">{error}</p>}
    {!project ? <p className="records-empty">先在左侧选一个项目。</p>
      : records === null && !error ? <p className="records-empty" role="status">正在读取…</p>
      : records !== null && !all.length ? <p className="records-empty">这个项目还没有用户输入记录。</p> : null}
    {!error && all.length > 0 && <>
      <div className="record-filter">
        <label>任务 <select value={task} onChange={event => { setTask(event.target.value); setSession(''); }}>
          <option value="">全部</option>{tasks.map(value => <option key={value} value={value}>{short(value || null)}</option>)}</select></label>
        <label>会话 <select value={session} onChange={event => setSession(event.target.value)}>
          <option value="">全部</option>{sessions.map(record => <option key={record.thread} value={record.thread}>
            {(roles[record.role ?? ''] ?? record.role ?? '未知会话') + ' · ' + short(record.task)}</option>)}</select></label>
        <span className="record-meta">{rows.length} 条，其中人工介入 {rows.filter(record => record.intervention !== null).length} 条</span>
      </div>
      <table className="record-table">
        <thead><tr><th>时间</th><th>任务</th><th>会话</th><th>形态</th><th>来源</th><th>内容</th></tr></thead>
        <tbody>{rows.map(record => <tr key={record.id} data-input-id={record.id} data-intervention={record.intervention !== null || undefined}>
          <td>{time(record.created_at)}</td>
          <td>{short(record.task)}</td>
          <td>{roles[record.role ?? ''] ?? record.role ?? '未知会话'}</td>
          <td>{forms[record.form] ?? record.form}{record.intervention !== null && <span className="record-badge record-intervention">人工介入</span>}</td>
          <td>{channels[record.channel] ?? record.channel}{record.certainty === 'inferred' ? '（推断）' : ''}</td>
          <td className="record-text">{content(record.text)}</td>
        </tr>)}</tbody>
      </table>
    </>}
  </div>;
}
