// Codex dark theme seed from Synara 49cae984f, apps/web/src/theme/theme.seed.generated.ts.
// Copyright (c) 2026 T3 Tools Inc. and Emanuele Di Pietro. MIT; see ../LICENSE.synara.
import { createRoot } from 'react-dom/client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';
import './style.css';
import { TerminalScrollToBottom } from './TerminalScrollToBottom';
import { createFocusSafeWriter, ownTerminalQueries } from './terminalOutput.mjs';
import type { EmptyInputDeclaration } from '../src/panes.ts';

type Snapshot = {
  daemon: string;
  pane_key: string;
  input_enabled: boolean;
  window_id?: string;
  task: { task_id: string; title: string; project_id: string; repo: string; state: string;
    current_attempt: { attempt_id: string; state: string } | null; candidate_commit: string | null;
    verification: { state: string } | null; integration_intent: { state: string } | null };
  launch: { id: string; thread: string; attempt: string | null; role: string; preset: string | null; cli_version: string; model_requested: string } | null;
  pane: { launch: string; state: string; lifecycle: string; state_source: string; historical?: boolean; failed: string | null;
    restoration?: { status: string; error: string | null; details: string | null } | null;
    interrupted?: boolean; interruption?: number | null; input_generation?: number; active?: { dispatch: string } | null } | null;
};
type Chunk = { launch: string; start_offset: number; next_offset: number; total_bytes: number; data_base64: string };
type TaskItem = { task_id: string; project_id: string; title: string; state: string };
type ProjectItem = { project_id: string };
type Selection = { task: Snapshot['task'] | null; paneKeys: string[] };
declare global { interface Window { a2a: { readonly paneKeys: readonly string[];
  projects(): Promise<ProjectItem[]>; tasks(project: string): Promise<TaskItem[]>;
  selection(): Promise<Selection>; selectTask(task: string | null): Promise<Selection>;
  snapshot(key: string): Promise<Snapshot>; output(key: string, offset: number): Promise<Chunk>;
  closePane(key: string): Promise<{ ok: boolean }>;
  input(key: string, data: string, encoding?: 'utf8' | 'binary'): Promise<void>; beginComposition(key: string): Promise<void>;
  releaseQueue(key: string, declaration: EmptyInputDeclaration): Promise<{ ok: boolean; error?: string }>;
  observeFocus(key: string, rawSequence: string): Promise<void> } } }
const gateNames: Record<string, string> = { creating: '创建中', ready: '待认领', preparing: '准备中', claimed: '已认领', submitted: '已交付',
  verifying: '验收中', verified: '验收通过', integrating: '集成中', accepted: '已集成', paused: '已暂停', revoked: '已撤销' };
const activityNames: Record<string, string> = { unknown: '未知', idle: '空闲', busy: '忙' };
const lifecycleNames: Record<string, string> = { running: '运行中', interrupted: '已中断', unknown: '未知', ended: '已结束', not_started: '未启动' };
const restoreErrors: Record<string, string> = {
  restore_managed_attempt_requires_reclaim: '受管 worker 未续接；请由执行主控按中断恢复流程回收后重新认领',
  restore_argv_missing: '启动记录缺少完整参数', restore_version_mismatch: 'CLI 版本与启动记录不符',
  restore_session_missing: '原生会话不存在',
};

type PaneStatus = { snapshot: Snapshot | null; error: string | null; connecting: boolean };

function SessionPane({ paneKey, onStatus, onClose }: { paneKey: string; onStatus: (key: string, status: PaneStatus) => void; onClose: (key: string) => void }) {
  const mount = useRef<HTMLDivElement>(null);
  const reconnect = useRef<() => void>(() => {});
  const releaseQueue = useRef<() => void>(() => {});
  const [terminal, setTerminal] = useState<Terminal | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(true);
  const [offset, setOffset] = useState(0);
  const [inputError, setInputError] = useState<string | null>(null);
  const [releasing, setReleasing] = useState(false);
  const [declarationReady, setDeclarationReady] = useState(false);
  const [releaseError, setReleaseError] = useState<string | null>(null);
  const [keyboardFocused, setKeyboardFocused] = useState(false);
  const [closing, setClosing] = useState(false);
  const [closeError, setCloseError] = useState<string | null>(null);
  useEffect(() => { onStatus(paneKey, { snapshot, error, connecting }); }, [paneKey, snapshot, error, connecting, onStatus]);

  useEffect(() => {
    let mounted = true, running = false, cursor = 0, total = 0;
    let boundLaunch: string | null = null;
    let inputFailed = false, releasePending = false;
    let inputVersion = 0, pendingInput = 0;
    let releaseBasis: EmptyInputDeclaration | null = null;
    const admitInput = (operation: () => Promise<void>) => {
      inputVersion++; pendingInput++; releaseBasis = null;
      setDeclarationReady(false); setReleaseError(null);
      void operation().catch(failInput).finally(() => { pendingInput--; });
    };
    const term = new Terminal({ cols: 160, rows: 45, disableStdin: true, cursorBlink: true,
      cursorInactiveStyle: 'none', screenReaderMode: true, scrollback: 10000, fontSize: 11, lineHeight: 1,
      fontFamily: '"SF Mono", "SFMono-Regular", Menlo, monospace',
      theme: { background: '#111111', foreground: '#fcfcfc', selectionBackground: '#0169cc66' } });
    term.open(mount.current!);
    const failInput = (failure: unknown) => {
      inputFailed = true; term.options.disableStdin = true;
      if (mounted) setInputError(`输入尚未确认，已停止发送：${String(failure)}`);
    };
    releaseQueue.current = () => {
      if (releasePending || inputFailed || !releaseBasis) return;
      const declaration = releaseBasis;
      releaseBasis = null; setDeclarationReady(false); setReleaseError(null);
      releasePending = true; setReleasing(true);
      void window.a2a.releaseQueue(paneKey, declaration).then(result => {
        if (!result.ok && mounted) setReleaseError('声明已过期，请处理当前输入框后重新声明。');
        return window.a2a.snapshot(paneKey);
      }).then(value => {
        if (mounted) setSnapshot(value);
      }).catch(failInput).finally(() => {
        releasePending = false;
        if (mounted) setReleasing(false);
      });
    };
    const writeOutput = createFocusSafeWriter(term, (type: string, detail: { raw_sequence: string }) => {
      if (type === 'focus-mode-intercept') void window.a2a.observeFocus(paneKey, detail.raw_sequence).catch(failInput);
    });
    ownTerminalQueries(term, () => {});
    const decoder = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
    term.onData(data => admitInput(() => window.a2a.input(paneKey, data)));
    term.onBinary(data => admitInput(() => window.a2a.input(paneKey, data, 'binary')));
    const beginComposition = () => {
      if (!inputFailed && !term.options.disableStdin) admitInput(() => window.a2a.beginComposition(paneKey));
    };
    const focused = () => setKeyboardFocused(true);
    const blurred = () => setKeyboardFocused(false);
    term.textarea!.addEventListener('compositionstart', beginComposition);
    term.textarea!.addEventListener('focus', focused);
    term.textarea!.addEventListener('blur', blurred);
    setTerminal(term);
    const delay = () => new Promise((resolve) => setTimeout(resolve, 100));
    async function read() {
      if (running || !mounted) return;
      running = true; setConnecting(true); setError(null);
      let nextSnapshot = 0;
      try {
        while (mounted) {
          if (Date.now() >= nextSnapshot) {
            const version = inputVersion, settled = pendingInput === 0;
            const value = await window.a2a.snapshot(paneKey);
            if (!mounted) break;
            if (value.pane_key !== paneKey) throw new Error('窗格路由改变，已停止读取');
            if (boundLaunch && value.launch?.id !== boundLaunch) throw new Error('窗格身份改变，已停止读取');
            if (value.launch) boundLaunch = value.launch.id;
            term.options.disableStdin = inputFailed || !value.input_enabled;
            const p = value.pane;
            releaseBasis = settled && pendingInput === 0 && version === inputVersion && value.input_enabled && value.window_id &&
              value.launch && p?.interrupted && Number.isSafeInteger(p.interruption) && Number.isSafeInteger(p.input_generation)
              ? { statement: '用户声明输入框已空', launch: value.launch.id, window_id: value.window_id,
                  interruption: p.interruption!, input_generation: p.input_generation! } : null;
            setDeclarationReady(Boolean(releaseBasis));
            setSnapshot(value); setConnecting(false);
            nextSnapshot = Date.now() + 1000;
          }
          if (!boundLaunch) { await delay(); continue; }
          const chunk = await window.a2a.output(paneKey, cursor);
          if (!mounted) break;
          const bytes = Uint8Array.from(atob(chunk.data_base64), (char) => char.charCodeAt(0));
          if (chunk.launch !== boundLaunch || chunk.start_offset !== cursor || chunk.next_offset !== cursor + bytes.length ||
              chunk.total_bytes < total || chunk.next_offset > chunk.total_bytes) throw new Error('输出不完整，已停止读取');
          total = chunk.total_bytes;
          if (bytes.length) {
            await writeOutput(decoder.decode(bytes, { stream: true }));
            cursor = chunk.next_offset;
            if (mounted) setOffset(cursor);
          }
          if (cursor === total) await delay();
        }
      } catch (failure) {
        term.options.disableStdin = true;
        if (mounted) { setError(String(failure)); setConnecting(false); }
      } finally { running = false; }
    }
    reconnect.current = () => { void read(); };
    void read();
    return () => {
      mounted = false;
      term.textarea!.removeEventListener('compositionstart', beginComposition);
      term.textarea!.removeEventListener('focus', focused);
      term.textarea!.removeEventListener('blur', blurred);
      term.dispose();
    };
  }, [paneKey]);
  const task = snapshot?.task;
  const pane = snapshot?.pane;
  const historical = Boolean(snapshot?.launch?.attempt && task?.current_attempt?.attempt_id !== snapshot.launch.attempt);
  const role = snapshot?.launch?.role === 'controller'
    ? snapshot.launch.preset === 'ideation' ? '构思主控' : snapshot.launch.preset === 'executor' ? '执行主控' : '主控 · 角色未确认'
    : snapshot?.launch?.role === 'worker' ? '受管 worker' : snapshot?.launch?.role ?? '窗格';
  const inputEnabled = Boolean(snapshot?.input_enabled && !inputError && !error);
  const inputTarget = keyboardFocused && inputEnabled;
  return <section className={'pane' + (inputTarget ? ' pane-focused' : '')} aria-label={role + '交互终端'}
        data-pane-key={paneKey} data-task-id={task?.task_id} data-window-id={snapshot?.window_id}
        data-role={snapshot?.launch?.role} data-preset={snapshot?.launch?.preset ?? ''}
        data-attempt-id={snapshot?.launch?.attempt ?? ''} data-keyboard-focused={keyboardFocused}
        data-input-target={inputTarget} data-launch-id={snapshot?.launch?.id}
        data-thread-id={snapshot?.launch?.thread} data-active-dispatch={pane?.active?.dispatch ?? ''}
        data-input-enabled={inputEnabled}>
        {error && <div className="connection-error" role="alert"><span>{error}</span><button onClick={() => reconnect.current()}>重新连接</button></div>}
        {inputError && <div className="connection-error" role="alert">{inputError}</div>}
        {releaseError && <div className="connection-error" role="alert">{releaseError}</div>}
        {pane?.restoration?.status === 'failed' && <div className="connection-error" role="alert">未恢复：{restoreErrors[pane.restoration.error ?? ''] ?? pane.restoration.error}。启动记录已保留。</div>}
        {closeError && <div className="connection-error" role="alert">{closeError}</div>}
        {pane?.restoration?.status === 'pending' && <div className="connection-error" role="status">正在恢复原生会话…</div>}
        <div className="pane-header"><strong>{role}</strong><span>{snapshot?.launch?.cli_version ?? '读取中'}</span>
          <span className="readonly">{inputEnabled ? '可输入' : '只读'}</span>
          <span className="input-target">{inputTarget ? `正在输入：${role}` : historical ? '历史 attempt · 只读' : '终端未聚焦'}</span>
          <span className="pane-state" data-state={error ? 'unknown' : pane?.state ?? 'unknown'}>{error ? '未知' : activityNames[pane?.state ?? 'unknown'] ?? '未知'}</span>
          <button disabled={!inputEnabled} onClick={() => terminal?.focus()}>进入终端</button>
          <button disabled={closing} onClick={() => {
            setClosing(true); setCloseError(null);
            void window.a2a.closePane(paneKey).then(() => onClose(paneKey)).catch(error => {
              setCloseError('关闭窗格未确认：' + String(error)); setClosing(false);
            });
          }}>关闭窗格</button>
          <button disabled={!snapshot?.input_enabled || !pane?.interrupted || !declarationReady || releasing || Boolean(inputError || error)}
            onClick={() => releaseQueue.current()}>输入框已空，放行</button>
          <span className="pane-identity">{snapshot?.launch ?
            `${snapshot.launch.role}${snapshot.launch.preset ? '/' + snapshot.launch.preset : ''} · task ${task?.task_id} · launch ${snapshot.launch.id}${snapshot.launch.attempt ? ' · attempt ' + snapshot.launch.attempt : ''}`
            : '尚未启动窗格'}</span>
        </div>
        <div className="terminal-scroll" data-output-offset={offset}><div className="terminal-mount" ref={mount} /></div>
        <TerminalScrollToBottom terminal={terminal} />
        <div className="pane-footer"><span>{pane?.interrupted ? '请自行保留、修改或清空草稿；看到输入框空了再声明放行。'
          : snapshot?.launch?.role === 'worker' ? '在此窗格输入会记录为人工介入' : '在此窗格输入会记录为用户输入'}</span><span data-lifecycle={pane?.lifecycle ?? 'unknown'}>执行：{lifecycleNames[pane?.lifecycle ?? 'unknown'] ?? '未知'}</span></div>
      </section>;
}

function Workbench() {
  const [statuses, setStatuses] = useState<Record<string, PaneStatus>>({});
  const [paneKeys, setPaneKeys] = useState([...window.a2a.paneKeys]);
  const [selectedTask, setSelectedTask] = useState<Snapshot['task'] | null>(null);
  const [projects, setProjects] = useState<(ProjectItem & { tasks: TaskItem[] })[]>([]);
  const [loading, setLoading] = useState(true);
  const [navigating, setNavigating] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [navigationError, setNavigationError] = useState<string | null>(null);
  const applySelection = useCallback((value: Selection) => {
    setSelectedTask(value.task); setPaneKeys(value.paneKeys); setStatuses({});
  }, []);
  const refresh = useCallback(async () => {
    setLoading(true); setCatalogError(null);
    try {
      const [rows, current] = await Promise.all([window.a2a.projects(), window.a2a.selection()]);
      const catalog = await Promise.all(rows.map(async row => ({ ...row, tasks: await window.a2a.tasks(row.project_id) })));
      if (current.task && !catalog.some(project => project.tasks.some(task => task.task_id === current.task!.task_id))) {
        applySelection(await window.a2a.selectTask(null));
      } else {
        setSelectedTask(current.task); setPaneKeys(current.paneKeys);
      }
      setProjects(catalog);
    } catch (error) { setCatalogError('读取项目与任务失败：' + String(error)); }
    finally { setLoading(false); }
  }, [applySelection]);
  useEffect(() => { void refresh(); }, [refresh]);
  const selectTask = async (task: string) => {
    if (navigating || loading || task === selectedTask?.task_id) return;
    setNavigating(true); setNavigationError(null);
    try { applySelection(await window.a2a.selectTask(task)); }
    catch (error) { setNavigationError('切换任务失败：' + String(error)); }
    finally { setNavigating(false); }
  };
  const onClose = useCallback((key: string) => {
    setPaneKeys(previous => previous.filter(value => value !== key));
    setStatuses(previous => { const next = { ...previous }; delete next[key]; return next; });
  }, []);
  const onStatus = useCallback((key: string, status: PaneStatus) => {
    setStatuses(previous => ({ ...previous, [key]: status }));
  }, []);
  const states = Object.values(statuses);
  const task = states.find(value => value.snapshot)?.snapshot?.task ?? selectedTask;
  const error = states.some(value => value.error);
  const connecting = states.length < paneKeys.length || states.some(value => value.connecting);
  return <div className="workbench">
    <aside className="sidebar">
      <div className="brand">a2a <span>工作台</span></div>
      <div className="catalog-heading"><span className="nav-label">项目与任务</span>
        <button disabled={loading || navigating} onClick={() => void refresh()}>刷新列表</button></div>
      <div className="catalog-status" role="status">{loading ? '正在读取列表…' : catalogError ? '列表未更新' : `${projects.length} 个项目`}</div>
      {catalogError && <p className="catalog-error" role="alert">{catalogError}</p>}
      <nav className="project-list" aria-label="项目与任务" aria-busy={loading}>
        {projects.map(project => <details className="project-group" key={project.project_id} open>
          <summary className="project-name" data-project-id={project.project_id}>{project.project_id}</summary>
          <ul>{project.tasks.map(item => <li key={item.task_id}>
            <button className="task-row" data-task-option={item.task_id} disabled={loading || navigating}
              aria-current={task?.task_id === item.task_id ? 'page' : undefined} onClick={() => void selectTask(item.task_id)}>
              <span className="task-title">{item.title}</span>
              <span className="task-meta"><span>{item.task_id}</span><span>{gateNames[item.state] ?? item.state}</span></span>
            </button>
          </li>)}</ul>
          {!project.tasks.length && <p className="catalog-status">这个项目还没有任务。</p>}
        </details>)}
        {!loading && !catalogError && !projects.length && <p className="catalog-status">还没有项目。请先通过编排后台创建项目中的任务，再刷新列表。</p>}
      </nav>
      <div className="sidebar-footer">原生 CLI · 本地编排</div>
    </aside>
    <main>
      <header className="task-header">
        <div><div className="eyebrow">{task ? `${task.project_id} / ${task.task_id}` : '项目 / 任务'}</div><h1>{task?.title ?? (loading ? '正在读取项目' : '选择任务')}</h1></div>
        <span className={'connection ' + (error || catalogError ? 'warning' : '')}>{navigating ? '正在切换任务' : loading ? '正在读取后台' : catalogError ? '列表未更新' : error ? '窗格未连接 · 上次记录' : connecting ? '正在连接' : '后台已连接'}</span>
      </header>
      {navigationError && <div className="connection-error" role="alert">{navigationError}</div>}
      <div className={'pane-grid' + (paneKeys.length > 1 ? ' multi' : '')} aria-label="任务会话">
        {!navigating && paneKeys.map(key => <SessionPane key={key} paneKey={key} onStatus={onStatus} onClose={onClose} />)}
        {navigating ? <p className="selection-hint" role="status">正在切换任务…</p> : !task && !paneKeys.length
          ? <div className="selection-hint"><h2>{!loading && !catalogError && !projects.length ? '还没有项目' : '从左侧选择任务'}</h2>
            <p>{!loading && !catalogError && !projects.length ? '请先通过编排后台创建项目中的任务，再刷新列表。' : '选择项目下的任务，查看它的会话和门禁状态。'}</p></div>
          : !paneKeys.length && <p className="selection-hint">当前任务没有打开的窗格。</p>}
      </div>
      {task && <section className="gate" aria-label="门禁状态">
        <div><span className="eyebrow">当前任务门禁</span><strong data-gate-state={task?.state ?? 'unknown'}>{gateNames[task?.state ?? ''] ?? '未知'}</strong></div>
        <dl><div><dt>执行尝试</dt><dd>{task?.current_attempt?.attempt_id.slice(0, 8) ?? '尚未认领'}</dd></div>
          <div><dt>候选提交</dt><dd>{task?.candidate_commit?.slice(0, 10) ?? '尚未交付'}</dd></div>
          <div><dt>验收</dt><dd>{task?.verification?.state ?? '尚未开始'}</dd></div>
          <div><dt>集成</dt><dd>{task?.integration_intent?.state ?? '尚未开始'}</dd></div></dl>
      </section>}
    </main>
  </div>;
}
createRoot(document.getElementById('root')!).render(<Workbench />);
