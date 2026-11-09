import { useEffect, useState } from 'react';
import './records.css';

export type UserInputRecord = { id: string; created_at: string; form: string; channel: string; certainty: string; text: string;
  task: string | null; attempt: string | null; thread: string; launch: string | null; role: string | null; intervention: number | null;
  role_request: string | null; role_event: number | null };
const forms: Record<string, string> = { message: '消息', answer: '答复', approval: '批准', denial: '拒绝', choice: '选择', action: '操作', gap: '记录缺口' };
const channels: Record<string, string> = { 'terminal-window': '窗格键入', 'controller-terminal': '主控终端提交', 'issue-panel': '问题面板', 'thread-message': '会话消息', 'ws-rpc': '界面操作',
  'ui-derived': '界面推断', 'settings-page': '设置页', 'commit-trailer': '提交（缺尾注）' };
const roles: Record<string, string> = { worker: 'worker', reviewer: '审查员', monitor: '监视器', ideation: '构思主控', executor: '执行主控', shell: '项目终端' };
const time = (value: string) => new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
const short = (task: string | null) => task ? task.slice(task.indexOf('+') + 1) : '项目级';
// A key the user pressed in a pane is recorded as its control character; show its name instead of nothing.
const keys: Record<string, string> = { '\r': '回车', '\n': '换行', '\x1b': 'Esc', '\x7f': '退格', '\t': 'Tab', '\x03': 'Ctrl-C' };
const content = (text: string) => keys[text] ? `（按键：${keys[text]}）` : /^[\x00-\x1f\x7f]+$/.test(text)
  ? `（按键：${[...text].map(c => keys[c] ?? '0x' + c.charCodeAt(0).toString(16).padStart(2, '0')).join(' ')}）` : text;

// T-179: what the gate answered a session's requests (submit, status, issue). Kept apart from the user's own input.
export type GateReceipt = { key: string; task: string; attempt: string | null; launch: string; role: string | null; command: string | null;
  created_at: string; ok: boolean; summary: string[]; result: unknown };
// Inputs name their launch when known; receipts name the same launch. A missing
// launch is a thread identity, never a guess based on a role label or task name.
const projectScope = ':project:';
const sessionKey = (record: UserInputRecord) => record.launch ? 'launch:' + record.launch : 'thread:' + record.thread;
const compareText = (a: string, b: string) => a < b ? -1 : a > b ? 1 : 0;
type Entry = { id: string; created_at: string; task: string | null; session: string; role: string | null;
  input?: UserInputRecord; receipt?: GateReceipt };
type Session = { id: string; role: string | null; first: string; latest: string; tasks: Set<string | null> };
const newestFirst = (a: { created_at: string; id: string }, b: { created_at: string; id: string }) =>
  Date.parse(b.created_at) - Date.parse(a.created_at) || compareText(a.id, b.id);
const roleName = (role: string | null) => roles[role ?? ''] ?? (role === 'controller' ? '主控' : role) ?? '未知会话';

export function RecordsPage({ project }: { project: string | null }) {
  const [snapshot, setSnapshot] = useState<{ project: string; records: UserInputRecord[]; receipts: GateReceipt[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false), [revision, setRevision] = useState(0);
  const [task, setTask] = useState(''), [session, setSession] = useState('');
  useEffect(() => { setTask(''); setSession(''); }, [project]);
  useEffect(() => {
    if (!project) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      setLoading(true);
      const [inputs, receipts] = await Promise.allSettled([window.a2a.records(project), window.a2a.receipts(project)]);
      if (!active) return;
      if (inputs.status === 'fulfilled' && receipts.status === 'fulfilled') {
        // Publish one coherent pair. An incomplete read must not present a partial
        // session list as the full set, or erase the user's current selection.
        setSnapshot({ project, records: inputs.value, receipts: receipts.value });
        setError(null);
      } else {
        setError([inputs.status === 'rejected' ? '用户输入读取失败：' + String(inputs.reason) : '',
          receipts.status === 'rejected' ? '门禁回执读取失败：' + String(receipts.reason) : ''].filter(Boolean).join('；'));
      }
      setLoading(false);
      // Poll only after this pair finishes. Refresh/unmount cancels publication of
      // an older pair, including a request from the previous project.
      timer = setTimeout(load, 3000);
    };
    void load();
    return () => { active = false; clearTimeout(timer); };
  }, [project, revision]);
  const data = snapshot?.project === project ? snapshot : null;
  const entries: Entry[] = [
    ...(data?.records ?? []).map(input => ({ id: input.id, created_at: input.created_at, task: input.task,
      session: sessionKey(input), role: input.role, input })),
    ...(data?.receipts ?? []).map(receipt => ({ id: receipt.key, created_at: receipt.created_at, task: receipt.task,
      session: 'launch:' + receipt.launch, role: receipt.role, receipt })),
  ].sort(newestFirst);
  const tasks = [...new Set(entries.map(entry => entry.task ?? projectScope))].sort((a, b) =>
    a === projectScope ? -1 : b === projectScope ? 1 : compareText(a, b));
  const inTask = (entry: Entry) => !task || (entry.task ?? projectScope) === task;
  const sessions = new Map<string, Session>();
  for (const entry of entries) {
    const current = sessions.get(entry.session);
    if (!current) sessions.set(entry.session, { id: entry.session, role: entry.role,
      first: entry.created_at, latest: entry.created_at, tasks: new Set([entry.task]) });
    else {
      current.tasks.add(entry.task);
      if (Date.parse(entry.created_at) < Date.parse(current.first)) current.first = entry.created_at;
      // A receipt says "controller"; the linked input may know which controller role.
      if (current.role === null || current.role === 'controller') current.role = entry.role ?? current.role;
    }
  }
  const shortIdentity = (id: string) => {
    const value = id.slice(id.indexOf(':') + 1);
    let length = 8;
    while ([...sessions.keys()].some(other => other !== id &&
      other.slice(other.indexOf(':') + 1).startsWith(value.slice(0, length))) && length < value.length) length += 4;
    return value.slice(0, length) + (length < value.length ? '…' : '');
  };
  const sessionLabel = (id: string) => roleName(sessions.get(id)?.role ?? null) + ' · ' + shortIdentity(id);
  const available = new Set(entries.filter(inTask).map(entry => entry.session));
  const groups = new Map<string, Session[]>();
  for (const item of [...sessions.values()].filter(item => available.has(item.id))) {
    const taskNames = task ? short(task === projectScope ? null : task)
      : [...item.tasks].sort((a, b) => compareText(a ?? '', b ?? '')).map(short).join(' / ');
    const group = taskNames + ' · ' + roleName(item.role);
    groups.set(group, [...(groups.get(group) ?? []), item]);
  }
  const visible = entries.filter(entry => inTask(entry) && (!session || entry.session === session));
  const inputs = visible.filter(entry => entry.input), receipts = visible.filter(entry => entry.receipt);
  const ready = data !== null && error === null;
  const empty = (name: string) => task || session ? '当前筛选下没有' + name + '。' : '这个项目还没有' + name + '。';
  return <div className="records-page user-input-page">
    <div className="records-intro"><h2>记录</h2>
      <p>用户输入与门禁回执分区显示，每区最新在前。</p>
      <details className="records-help"><summary>记录范围</summary><p>你亲手打的字、在面板里的答复和审批都记在用户输入里，主控和后台派发的文字不算。项目终端里只记你批准为主控的 Claude Code 或 Codex 收到的整条提示词，以及你对它提问的答复。落在受管 worker 会话里的输入记为人工介入。</p></details>
    </div>
    {!project ? <p className="records-empty">先在左侧选一个项目。</p> : <>
      <div className="record-filter" aria-label="记录筛选">
        <label>任务 <select aria-label="任务" value={task} disabled={!ready} onChange={event => { setTask(event.target.value); setSession(''); }}>
          <option value="">全部任务</option>{tasks.map(value => <option key={value} value={value}>{short(value === projectScope ? null : value)}</option>)}</select></label>
        <label>会话 <select aria-label="会话" value={session} disabled={!ready} onChange={event => setSession(event.target.value)}>
          <option value="">全部会话</option>{[...groups].sort(([a], [b]) => compareText(a, b)).map(([group, items]) =>
            <optgroup key={group} label={group}>{items.sort((a, b) => Date.parse(b.latest) - Date.parse(a.latest) || compareText(a.id, b.id)).map(item =>
              <option key={item.id} value={item.id}>{sessionLabel(item.id) + ' · 首条记录 ' + time(item.first)}</option>)}</optgroup>)}</select></label>
        <button type="button" onClick={() => { setTask(''); setSession(''); }} disabled={!task && !session}>清空筛选</button>
        <button type="button" onClick={() => setRevision(value => value + 1)} disabled={loading}>刷新</button>
      </div>
      <p className="record-meta records-count" role="status">{loading ? (data ? '正在刷新…' : '正在读取…') : ready
        ? `用户输入 ${inputs.length} 条 · 门禁回执 ${receipts.length} 条 · 人工介入 ${inputs.filter(entry => entry.input!.intervention !== null).length} 条` : '读取未完成。'}</p>
      {error && <p className="catalog-error" role="alert">{error}。请刷新重试。</p>}
      <section className="input-records records-section" aria-label="用户输入" aria-busy={loading}>
        <h3>用户输入</h3>
        {ready && inputs.length === 0 && <p className="records-empty">{empty('用户输入')}</p>}
        {ready && inputs.map(entry => { const record = entry.input!; const text = content(record.text); return <article className="input-record" key={record.id}
          data-input-id={record.id} data-intervention={record.intervention !== null || undefined}>
          <div className="record-meta"><time dateTime={record.created_at}>{time(record.created_at)}</time> · {short(record.task)} · <span title={entry.session}>{sessionLabel(entry.session)}</span></div>
          <div className="record-kind">{forms[record.form] ?? record.form} · {channels[record.channel] ?? record.channel}{record.certainty === 'inferred' ? '（推断）' : ''}
            {record.intervention !== null && <span className="record-badge record-intervention">人工介入</span>}</div>
          <p className="record-preview">{text.length > 160 ? text.slice(0, 160) + '…' : text}</p>
          <details><summary>原文与追溯</summary><pre className="record-original">{record.text}</pre>
            <dl className="record-trace"><dt>记录</dt><dd>{record.id}</dd><dt>会话</dt><dd>{record.thread}</dd>
              {record.launch && <><dt>启动记录</dt><dd>{record.launch}</dd></>}
              {record.attempt && <><dt>执行轮次</dt><dd>{record.attempt}</dd></>}
              {record.intervention !== null && <><dt>人工介入事件</dt><dd>#{record.intervention}</dd></>}
              {record.role_request && <><dt>角色申请</dt><dd>{record.role_request} · 角色事件 #{record.role_event}</dd></>}
            </dl>
          </details>
        </article>; })}
      </section>
      <section className="receipts records-section" aria-label="门禁回执" aria-busy={loading}>
        <h3>门禁回执</h3>
        <p className="records-empty">会话交付、查状态或上报问题后，门禁给它的答复。</p>
        {ready && receipts.length === 0 && <p className="records-empty">{empty('门禁回执')}</p>}
        {ready && receipts.map(entry => { const receipt = entry.receipt!; return <article className="receipt" key={receipt.key} data-receipt-key={receipt.key}
          data-receipt-command={receipt.command ?? ''} data-receipt-ok={receipt.ok}>
          <div className="record-meta"><time dateTime={receipt.created_at}>{time(receipt.created_at)}</time> · {short(receipt.task)} · <span title={entry.session}>{sessionLabel(entry.session)}</span></div>
          <div className="receipt-summary">{receipt.summary.join('\n')}</div>
          <details><summary>完整回执</summary><pre className="receipt-full">{JSON.stringify(receipt.result, null, 2)}</pre></details>
        </article>; })}
      </section>
    </>}
  </div>;
}
