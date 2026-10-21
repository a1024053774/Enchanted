// Codex dark theme seed from Synara 49cae984f, apps/web/src/theme/theme.seed.generated.ts.
// Copyright (c) 2026 T3 Tools Inc. and Emanuele Di Pietro. MIT; see ../LICENSE.synara.
import { createRoot } from 'react-dom/client';
import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import './style.css';
import { FlowPage } from './FlowPage';
import { ExecutionSettings } from './ExecutionSettings';
import type { ExecutionRole, ExecutionSelection } from '../src/executionSettings.ts';
import type { FlowSnapshot } from '../src/flow.ts';
import { TerminalScrollToBottom } from './TerminalScrollToBottom';
import { createFocusSafeWriter, ownTerminalQueries } from './terminalOutput.mjs';
import type { EmptyInputDeclaration } from '../src/panes.ts';
import { AppNotifications, NotificationSettings } from './AppNotifications';
import type { AppNotice } from './notificationCenter.ts';
import { QuestionsPanel } from './QuestionsPanel';
import type { NativeQuestion } from '../src/questions.ts';

type Snapshot = {
  questions?: NativeQuestion[];
  daemon: string;
  pane_key: string;
  input_enabled: boolean;
  window_id?: string;
  task: { task_id: string; title: string; project_id: string; repo: string; state: string;
    current_attempt: { attempt_id: string; state: string } | null; candidate_commit: string | null;
    verification: { state: string } | null; integration_intent: { state: string } | null } | null;
  launch: { id: string; project: string; worktree?: string; thread: string; attempt: string | null; role: string;
    preset: string | null; cli_version: string; model_requested: string } | null;
  pane: { launch: string; state: string; lifecycle: string; state_source: string; historical?: boolean; failed: string | null;
    restoration?: { status: string; error: string | null; details: string | null } | null;
    interrupted?: boolean; interruption?: number | null; input_generation?: number; active?: { dispatch: string } | null } | null;
};
type Chunk = { launch: string; start_offset: number; next_offset: number; total_bytes: number; data_base64: string };
type TaskItem = { task_id: string; project_id: string; title: string; state: string };
type Theme = 'system' | 'light' | 'dark';
type ProjectItem = { project_id: string; repo: string | null; opened?: boolean; tasks: TaskItem[]; state: string; state_label: string;
  git: { branch: string | null; upstream: string | null; ahead: number | null; behind: number | null; error: string | null } };
type AgentItem = { id: string; project: string; task: string | null; attempt: string | null; parent: string | null;
  role: string; preset: string | null; role_label: string; cli: string; state: string; state_label: string; created_at?: string | null; terminal?: boolean;
  descendants: { count: number; state: string; state_label: string; counts: { state: string; label: string; count: number }[] } };
type RoleRequest = { id: string; launch: string; project: string; role: string; role_label: string; cli: string | null; requested_at: string };
type Sidebar = { projects: ProjectItem[]; agents: AgentItem[]; role_requests: RoleRequest[]; gaps: string[]; notifications: boolean; dockBadges: boolean; notices: AppNotice[] };
const glyphs: Record<string, ReactNode> = {
  running: <circle className="glyph-spin" cx="8" cy="8" r="5.6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeDasharray="26 10" />,
  waiting_user_answer: <><circle cx="8" cy="8" r="5.8" fill="none" stroke="currentColor" strokeWidth="1.6" /><circle cx="8" cy="8" r="2.8" fill="currentColor" /></>,
  waiting_controller_answer: <circle cx="8" cy="8" r="5.8" fill="none" stroke="currentColor" strokeWidth="1.6" strokeDasharray="3 2.4" />,
  idle: <path d="M3.8 8.4 6.6 11 12.2 5.2" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />,
  ended: <path d="M10.9 11.6A5 5 0 0 1 6.4 3.1a5.2 5.2 0 1 0 6.6 6.6 5 5 0 0 1-2.1 1.9Z" fill="currentColor" />,
  unrestored: <><circle cx="8" cy="8" r="5.8" fill="none" stroke="currentColor" strokeWidth="1.5" /><path d="M4 12 12 4" stroke="currentColor" strokeWidth="1.5" /></>,
  unknown: <circle cx="8" cy="8" r="2.2" fill="currentColor" />,
};
function StatusIcon({ state }: { state: string }) {
  return <span className="status-icon" data-glyph={state in glyphs ? state : 'unknown'} aria-hidden="true">
    <svg viewBox="0 0 16 16" width="16" height="16">{glyphs[state] ?? glyphs.unknown}</svg></span>;
}
const stateNames: Record<string, string> = { running: '运行中', waiting_user_answer: '等你回答', waiting_controller_answer: '等主控回答', idle: '空闲', ended: '已结束', unrestored: '未恢复', unknown: '未知' };
// Launch time, not last activity: the catalog has no per-turn timestamps.
function since(iso: string | null | undefined, now: number) {
  const seconds = iso ? (now - Date.parse(iso)) / 1000 : NaN;
  if (!Number.isFinite(seconds)) return '';
  if (seconds < 60) return '刚刚';
  if (seconds < 3600) return Math.floor(seconds / 60) + ' 分';
  if (seconds < 86400) return Math.floor(seconds / 3600) + ' 小时';
  return Math.floor(seconds / 86400) + ' 天';
}
const tilde = (path: string | null | undefined, home: string | null) => !path ? '' : home && (path === home || path.startsWith(home + '/')) ? '~' + path.slice(home.length) : path;
const terminalPalettes = {
  light: { background: '#ffffff', foreground: '#1f2328', cursor: '#1f2328', selectionBackground: '#0969da33',
    black: '#24292f', red: '#cf222e', green: '#116329', yellow: '#7d4e00', blue: '#0969da', magenta: '#8250df', cyan: '#1b7c83', white: '#6e7781',
    brightBlack: '#57606a', brightRed: '#a40e26', brightGreen: '#1a7f37', brightYellow: '#633c01', brightBlue: '#218bff', brightMagenta: '#a475f9', brightCyan: '#3192aa', brightWhite: '#8c959f' },
  dark: { background: '#1c1c1f', foreground: '#e6e6ea', cursor: '#e6e6ea', selectionBackground: '#3b82f655',
    black: '#484f58', red: '#ff7b72', green: '#3fb950', yellow: '#d29922', blue: '#58a6ff', magenta: '#bc8cff', cyan: '#39c5cf', white: '#b1bac4',
    brightBlack: '#6e7681', brightRed: '#ffa198', brightGreen: '#56d364', brightYellow: '#e3b341', brightBlue: '#79c0ff', brightMagenta: '#d2a8ff', brightCyan: '#56d4dd', brightWhite: '#f0f6fc' },
};
const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');

type Layout = string | { direction: 'right' | 'down'; first: Layout; second: Layout };
type ProjectView = { project_id: string; repo: string | null };
type Selection = { task: Snapshot['task'] | null; project: ProjectView | null; paneKeys: string[]; layout: Layout | null; names: Record<string, string>; launches?: Record<string, string> };
declare global { interface Window { a2a: { readonly paneKeys: readonly string[]; readonly home: string;
  executionSettings(change?: ExecutionSelection & { role: ExecutionRole }): Promise<Record<ExecutionRole, ExecutionSelection>>;
  flow(): Promise<FlowSnapshot>; sidebar(): Promise<Sidebar>; selectAgent(launch: string): Promise<Selection & { focusKey: string }>; decideRoleRequest(roleRequest: string, approved: boolean): Promise<unknown>; notificationSetting(enabled?: boolean, preference?: 'notifications' | 'dockBadges'): Promise<boolean>;
  projects(): Promise<ProjectItem[]>; tasks(project: string): Promise<TaskItem[]>;
  selection(): Promise<Selection>; selectTask(task: string | null): Promise<Selection>;
  openProject(): Promise<Selection | null>; removeProject(project: string): Promise<Selection>;
  selectProject(project: string | null): Promise<Selection>; theme(theme: Theme): Promise<void>;
  newTerminal(): Promise<Selection>;
  paneAction(key: string, action: { type: string; direction?: string; name?: string }): Promise<Selection>;
  resize(key: string, cols: number, rows: number): Promise<void>;
  snapshot(key: string): Promise<Snapshot>; output(key: string, offset: number): Promise<Chunk>;
  closePane(key: string): Promise<Selection & { ok: boolean }>;
  input(key: string, data: string, encoding?: 'utf8' | 'binary'): Promise<void>; beginComposition(key: string): Promise<void>;
  answer(key: string, question: string, answers: string[]): Promise<unknown>;
  releaseQueue(key: string, declaration: EmptyInputDeclaration): Promise<{ ok: boolean; error?: string }>;
  observeFocus(key: string, rawSequence: string): Promise<void> } } }
const gateNames: Record<string, string> = { creating: '创建中', ready: '待认领', preparing: '准备中', claimed: '已认领', submitted: '已交付',
  verifying: '验收中', verified: '验收通过', integrating: '集成中', accepted: '已集成', paused: '已暂停', revoked: '已撤销' };
const activityNames: Record<string, string> = { unknown: '未知', idle: '空闲', busy: '忙' };
const lifecycleNames: Record<string, string> = { running: '运行中', interrupted: '已中断', unknown: '未知', ended: '已结束', not_started: '未启动' };
const restoreErrors: Record<string, string> = {
  restore_managed_attempt_requires_reclaim: '受管 worker 未续接；请由执行主控按中断恢复流程回收后重新认领',
  restore_argv_missing: '启动记录缺少完整参数',
  restore_session_missing: '原生会话不存在',
};

type PaneStatus = { snapshot: Snapshot | null; error: string | null; connecting: boolean };

function SessionPane({ paneKey, name, home, focusRequest, zoomed, onZoom, onAction, onStatus, onClose }: { paneKey: string; name?: string; home: string | null; focusRequest: number; zoomed: boolean; onZoom: () => void; onAction: (key: string, action: { type: string; direction?: string; name?: string }) => Promise<void>; onStatus: (key: string, status: PaneStatus) => void; onClose: (key: string, value: Selection) => void }) {
  const mount = useRef<HTMLDivElement>(null);
  const reconnect = useRef<() => void>(() => {});
  const releaseQueue = useRef<() => void>(() => {});
  const [terminal, setTerminal] = useState<Terminal | null>(null);
  useEffect(() => { if (focusRequest && terminal) terminal.focus(); }, [focusRequest, terminal]);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(true);
  const [restoring, setRestoring] = useState(true);
  const [offset, setOffset] = useState(0);
  const [inputError, setInputError] = useState<string | null>(null);
  const [releasing, setReleasing] = useState(false);
  const [declarationReady, setDeclarationReady] = useState(false);
  const [releaseError, setReleaseError] = useState<string | null>(null);
  const [keyboardFocused, setKeyboardFocused] = useState(false);
  const [closing, setClosing] = useState(false);
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  const [forwardRightClick, setForwardRightClick] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [draftName, setDraftName] = useState('');
  const [acting, setActing] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const renameInput = useRef<HTMLInputElement>(null);
  const dismissMenu = () => { setMenu(null); menuButton.current?.focus(); };
  useEffect(() => {
    if (!menu) return;
    menuRef.current?.querySelector<HTMLButtonElement>('button')?.focus();
    const dismiss = (event: MouseEvent) => { if (!menuRef.current?.contains(event.target as Node)) setMenu(null); };
    document.addEventListener('mousedown', dismiss);
    return () => document.removeEventListener('mousedown', dismiss);
  }, [menu]);
  useEffect(() => { if (renaming) { renameInput.current?.focus(); renameInput.current?.select(); } }, [renaming]);
  const act = async (action: { type: string; direction?: string; name?: string }) => {
    setMenu(null); setActing(true); setCloseError(null);
    try { await onAction(paneKey, action); setRenaming(false); }
    catch (error) { setCloseError('窗格操作未确认：' + String(error)); }
    finally { setActing(false); menuButton.current?.focus(); }
  };
  const [closeError, setCloseError] = useState<string | null>(null);
  useEffect(() => { onStatus(paneKey, { snapshot, error, connecting }); }, [paneKey, snapshot, error, connecting, onStatus]);

  useEffect(() => {
    let mounted = true, running = false, cursor = 0, total = 0, hidden = true;
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
      cursorInactiveStyle: 'none', screenReaderMode: true, scrollback: 10000, fontSize: 12, lineHeight: 1.15,
      fontFamily: '"SF Mono", "SFMono-Regular", Menlo, monospace',
      theme: terminalPalettes[darkQuery.matches ? 'dark' : 'light'] });
    const followScheme = () => { term.options.theme = terminalPalettes[darkQuery.matches ? 'dark' : 'light']; };
    darkQuery.addEventListener('change', followScheme);
    const fit = new FitAddon(); term.loadAddon(fit);
    term.open(mount.current!);
    let writable = false, dimensions = '';
    const resize = () => {
      if (!mount.current?.clientWidth || !mount.current?.clientHeight) return;
      fit.fit();
      const next = `${term.cols}:${term.rows}`;
      if (writable && dimensions !== next) {
        dimensions = next;
        void window.a2a.resize(paneKey, term.cols, term.rows).catch(failInput);
      }
    };
    const observer = new ResizeObserver(resize); observer.observe(mount.current!);
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
      // First attach and every reconnect replay their backlog hidden until the live end.
      setRestoring(true); hidden = true;
      let nextSnapshot = 0;
      try {
        while (mounted) {
          if (Date.now() >= nextSnapshot) {
            const version = inputVersion, settled = pendingInput === 0;
            const value = await window.a2a.snapshot(paneKey);
            if (!mounted) break;
            if (value.pane_key !== paneKey) throw new Error('窗格路由改变，已停止读取');
            if (boundLaunch && value.launch?.id !== boundLaunch) throw new Error('窗格身份改变，已停止读取');
            // A placeholder that gains its launch replays that launch's backlog hidden too.
            if (value.launch && !boundLaunch) { setRestoring(true); hidden = true; }
            if (value.launch) boundLaunch = value.launch.id;
            term.options.disableStdin = inputFailed || !value.input_enabled;
            writable = value.input_enabled; resize();
            const p = value.pane;
            releaseBasis = settled && pendingInput === 0 && version === inputVersion && value.input_enabled && value.window_id &&
              value.launch && p?.interrupted && Number.isSafeInteger(p.interruption) && Number.isSafeInteger(p.input_generation)
              ? { statement: '用户声明输入框已空', launch: value.launch.id, window_id: value.window_id,
                  interruption: p.interruption!, input_generation: p.input_generation! } : null;
            setDeclarationReady(Boolean(releaseBasis));
            setSnapshot(value); setConnecting(false);
            nextSnapshot = Date.now() + 1000;
          }
          if (!boundLaunch) { setRestoring(false); await delay(); continue; }
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
          // Earlier output is replayed hidden; the pane shows once it reaches the live end.
          if (cursor === total) {
            // Reveal only after xterm has painted the caught-up screen, never its previous paint.
            if (hidden) { await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); hidden = false; }
            if (mounted) setRestoring(false);
            await delay();
          }
        }
      } catch (failure) {
        term.options.disableStdin = true;
        if (mounted) { setError(String(failure)); setConnecting(false); setRestoring(false); }
      } finally { running = false; }
    }
    reconnect.current = () => { void read(); };
    void read();
    return () => {
      mounted = false;
      term.textarea!.removeEventListener('compositionstart', beginComposition);
      term.textarea!.removeEventListener('focus', focused);
      term.textarea!.removeEventListener('blur', blurred);
      darkQuery.removeEventListener('change', followScheme);
      observer.disconnect(); term.dispose();
    };
  }, [paneKey]);
  const task = snapshot?.task;
  const pane = snapshot?.pane;
  const historical = Boolean(snapshot?.launch?.attempt && task?.current_attempt?.attempt_id !== snapshot.launch.attempt);
  const shell = snapshot?.launch?.role === 'shell';
  const role = snapshot?.launch?.role === 'controller'
    ? snapshot.launch.preset === 'ideation' ? '构思主控' : snapshot.launch.preset === 'executor' ? '执行主控' : '主控 · 角色未确认'
    : shell ? '普通终端' : snapshot?.launch?.role === 'worker' ? '受管 worker' : snapshot?.launch?.role === 'reviewer' ? '独立审查' : snapshot?.launch?.role ?? '窗格';
  const inputEnabled = Boolean(snapshot?.input_enabled && !inputError && !error);
  const inputTarget = keyboardFocused && inputEnabled;
  const closePane = () => {
    setMenu(null); setClosing(true); setCloseError(null);
    void window.a2a.closePane(paneKey).then(value => onClose(paneKey, value)).catch(error => {
      setCloseError('关闭窗格未确认：' + String(error)); setClosing(false);
    });
  };
  const openMenu = (x: number, y: number) => setMenu({ x: Math.max(4, Math.min(x, window.innerWidth - 218)), y: Math.max(4, Math.min(y, window.innerHeight - 280)) });
  return <section onContextMenu={event => {
        if (forwardRightClick && (event.target as HTMLElement).closest('.terminal-mount')) { event.preventDefault(); return; }
        event.preventDefault(); event.stopPropagation(); openMenu(event.clientX, event.clientY);
      }} onMouseDownCapture={event => {
        if (event.button === 2 && !forwardRightClick && (event.target as HTMLElement).closest('.terminal-mount')) event.stopPropagation();
      }} className={'pane' + (inputTarget ? ' pane-focused' : '')} aria-label={role + '交互终端'}
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
        <div className="pane-header">
          <strong title={name ?? role}>{name ?? role}</strong>
          {name && <span className="pane-role">{role}</span>}
          <span className="pane-identity" title={snapshot?.launch ? shell ? snapshot.launch.worktree ?? '' :
            `${snapshot.launch.role}${snapshot.launch.preset ? '/' + snapshot.launch.preset : ''} · task ${task?.task_id} · launch ${snapshot.launch.id}${snapshot.launch.attempt ? ' · attempt ' + snapshot.launch.attempt : ''}` : undefined}>{snapshot?.launch ?
            shell ? tilde(snapshot.launch.worktree, home) :
              `${task?.task_id ?? ''}${snapshot.launch.attempt ? ' · attempt ' + snapshot.launch.attempt.slice(0, 8) : ''} · ${snapshot.launch.cli_version}`
            : '尚未启动窗格'}</span>
          <span className="pane-badges" data-lifecycle={pane?.lifecycle ?? 'unknown'}>
            <span className="input-target">{inputTarget ? '正在输入' : shell && pane?.lifecycle === 'ended' ? '终端已结束 · 只读' : historical ? '历史 attempt · 只读' : ''}</span>
            {!inputEnabled && <span className="readonly">只读</span>}
            <span className="pane-state" data-state={error ? 'unknown' : pane?.state ?? 'unknown'}>{error ? '未知' : shell
              ? lifecycleNames[pane?.lifecycle ?? 'unknown'] ?? '未知' : activityNames[pane?.state ?? 'unknown'] ?? '未知'}</span>
          </span>
          {!shell && snapshot?.launch?.role !== 'reviewer' && pane?.interrupted && <button className="release-queue" disabled={!snapshot?.input_enabled || !declarationReady || releasing || Boolean(inputError || error)}
            onClick={() => releaseQueue.current()}>输入框已空，放行</button>}
          <span className="pane-actions">
            <button ref={menuButton} className="icon-button pane-menu-trigger" aria-label="窗格菜单" aria-haspopup="menu" aria-expanded={Boolean(menu)} disabled={acting || closing}
              onClick={event => { if (menu) dismissMenu(); else { const rect = event.currentTarget.getBoundingClientRect(); openMenu(rect.right - 210, rect.bottom + 4); } }}>
              <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="3.5" cy="8" r="1.3" fill="currentColor" /><circle cx="8" cy="8" r="1.3" fill="currentColor" /><circle cx="12.5" cy="8" r="1.3" fill="currentColor" /></svg></button>
            <button className="icon-button pane-close" aria-label={'关闭' + (name ?? role)} title="关闭窗格" disabled={closing || acting} onClick={closePane}><span className="sr-only">关闭窗格</span>
              <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg></button>
          </span>
        </div>
        {menu && <div ref={menuRef} className="pane-menu" role="menu" aria-label="窗格操作" style={{ left: menu.x, top: menu.y }} onKeyDown={event => {
          const items = [...menuRef.current!.querySelectorAll<HTMLButtonElement>('button')];
          const index = items.indexOf(document.activeElement as HTMLButtonElement);
          if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
            event.preventDefault();
            items[event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
          } else if (event.key === 'Escape' || event.key === 'Tab') { if (event.key === 'Escape') event.preventDefault(); dismissMenu(); }
        }}>
          <button role="menuitem" onClick={() => { setDraftName(name ?? role); setRenaming(true); setMenu(null); }}>重命名窗格</button>
          <button role="menuitem" onClick={() => void act({ type: 'split', direction: 'right' })}>向右分屏</button>
          <button role="menuitem" onClick={() => void act({ type: 'split', direction: 'down' })}>向下分屏</button>
          <button role="menuitem" onClick={() => { onZoom(); dismissMenu(); }}>{zoomed ? '还原' : '放大'}</button>
          <button role="menuitemcheckbox" aria-checked={forwardRightClick} onClick={() => { setForwardRightClick(value => !value); dismissMenu(); }}>{forwardRightClick ? '✓ ' : ''}把右键发给窗格</button>
          <button role="menuitem" disabled={closing} onClick={closePane}>关闭窗格</button>
        </div>}
        {renaming && <form className="pane-rename" onSubmit={event => { event.preventDefault(); void act({ type: 'rename', name: draftName }); }}>
          <label>窗格名称 <input ref={renameInput} maxLength={100} value={draftName} onChange={event => setDraftName(event.target.value)} onKeyDown={event => { if (event.key === 'Escape') { setRenaming(false); menuButton.current?.focus(); } }} /></label>
          <button disabled={acting || !draftName.trim()}>保存名称</button><button type="button" onClick={() => { setRenaming(false); menuButton.current?.focus(); }}>取消</button>
        </form>}
        <QuestionsPanel questions={snapshot?.questions ?? []} enabled={inputEnabled} send={(question, answers) => window.a2a.answer(paneKey, question, answers)} />
        <div className="terminal-scroll" data-output-offset={offset} data-restoring={restoring}>{restoring && <div className="terminal-restoring" role="status">正在恢复终端内容…</div>}<div className="terminal-mount" ref={mount} /></div>
        <TerminalScrollToBottom terminal={terminal} />
        {!shell && <div className="pane-footer"><span>{pane?.interrupted ? '请自行保留、修改或清空草稿；看到输入框空了再声明放行。'
          : snapshot?.launch?.role === 'reviewer' ? '独立审查 · 只读' : snapshot?.launch?.role === 'worker' ? '在此窗格输入会记录为人工介入' : '在此窗格输入会记录为用户输入'}</span><span>执行：{lifecycleNames[pane?.lifecycle ?? 'unknown'] ?? '未知'}</span></div>}
      </section>;
}

function paneRects(tree: Layout | null, x = 0, y = 0, w = 100, h = 100): Record<string, { x: number; y: number; w: number; h: number }> {
  if (!tree) return {};
  if (typeof tree === 'string') return { [tree]: { x, y, w, h } };
  return tree.direction === 'right'
    ? { ...paneRects(tree.first, x, y, w / 2, h), ...paneRects(tree.second, x + w / 2, y, w / 2, h) }
    : { ...paneRects(tree.first, x, y, w, h / 2), ...paneRects(tree.second, x, y + h / 2, w, h / 2) };
}

const themeKey = 'enchanted-theme';
function readTheme(): Theme {
  try { const value = localStorage.getItem(themeKey); return value === 'light' || value === 'dark' ? value : 'system'; }
  catch { return 'system'; }
}

function SettingsDialog({ open, onClose, theme, onTheme, notifications, dockBadges, onNotification, gaps }: {
  open: boolean; onClose: () => void; theme: Theme; onTheme: (theme: Theme) => void;
  notifications: boolean; dockBadges: boolean; onNotification: (enabled: boolean, preference: 'notifications' | 'dockBadges') => void; gaps: string[] }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const node = dialog.current!;
    if (open && !node.open) node.showModal();
    if (!open && node.open) node.close();
  }, [open]);
  return <dialog ref={dialog} className="sidebar-settings settings-dialog" aria-labelledby="settings-title"
    onClose={onClose} onCancel={event => { event.preventDefault(); onClose(); }}
    onMouseDown={event => { if (event.target === dialog.current) onClose(); }}>
    <div className="settings-body">
      <header><h2 id="settings-title">设置</h2>
        <button className="icon-button" aria-label="关闭设置" onClick={onClose}><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg></button></header>
      <section aria-labelledby="settings-theme"><h3 id="settings-theme">外观</h3>
        <div className="segmented" role="group" aria-label="外观">
          {([['system', '跟随系统'], ['light', '浅色'], ['dark', '深色']] as const).map(([value, label]) =>
            <button key={value} aria-pressed={theme === value} autoFocus={theme === value} onClick={() => onTheme(value)}>{label}</button>)}
        </div></section>
      <section aria-labelledby="settings-notify"><h3 id="settings-notify">通知</h3>
        <NotificationSettings notifications={notifications} dockBadges={dockBadges} onChange={onNotification} /></section>
      <section aria-labelledby="settings-models"><h3 id="settings-models">主控派发的默认模型</h3>
        <p className="settings-note">主控派发新会话时按角色取这里的模型和思考强度，主控也可以按你在对话里的要求临时改。只影响之后启动的会话；已经打开的终端、正在运行的会话，以及你在终端里自己启动的 claude / codex 都不受影响。</p>
        <ExecutionSettings /></section>
      <section aria-labelledby="settings-legend"><h3 id="settings-legend">状态图标</h3>
        <ul className="status-legend">{Object.entries(stateNames).map(([state, label]) =>
          <li key={state} data-agent-state={state}><StatusIcon state={state} />{label}</li>)}</ul>
        {gaps.map(gap => <p className="settings-note" key={gap}>{gap}</p>)}</section>
    </div>
  </dialog>;
}

function Workbench() {
  const [page, setPage] = useState<'terminal' | 'flow'>('terminal');
  const [statuses, setStatuses] = useState<Record<string, PaneStatus>>({});
  const [paneKeys, setPaneKeys] = useState([...window.a2a.paneKeys]);
  const [layout, setLayout] = useState<Layout | null>(null);
  const [names, setNames] = useState<Record<string, string>>({});
  const [zoom, setZoom] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<Snapshot['task'] | null>(null);
  const [viewProject, setViewProject] = useState<ProjectView | null>(null);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [roleRequests, setRoleRequests] = useState<RoleRequest[]>([]);
  const [launches, setLaunches] = useState<Record<string, string>>({});
  const [deciding, setDeciding] = useState<string | null>(null);
  const [roleRequestError, setRoleRequestError] = useState<string | null>(null);
  const [gaps, setGaps] = useState<string[]>([]);
  const [notifications, setNotifications] = useState(true);
  const [dockBadges, setDockBadges] = useState(true);
  const [notices, setNotices] = useState<AppNotice[]>([]);
  const [focusedAgent, setFocusedAgent] = useState<string | null>(null);
  const [collapsedAgents, setCollapsedAgents] = useState<Set<string>>(new Set());
  const [focusRequest, setFocusRequest] = useState({ key: '', version: 0 });
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sidebarHidden, setSidebarHidden] = useState(false);
  const [theme, setTheme] = useState<Theme>(readTheme);
  const [projectMenu, setProjectMenu] = useState<{ project: ProjectItem; x: number; y: number; opener: HTMLElement } | null>(null);
  const projectMenuRef = useRef<HTMLDivElement>(null);
  const dismissProjectMenu = () => { projectMenu?.opener.focus(); setProjectMenu(null); };
  const [now, setNow] = useState(Date.now());
  const sidebarRead = useRef(false);
  const selectedProject = selectedTask?.project_id ?? viewProject?.project_id ?? null;
  useEffect(() => {
    void window.a2a.theme(theme).catch(error => setCatalogError('外观未切换：' + String(error)));
    try { localStorage.setItem(themeKey, theme); } catch { /* Per-viewer convenience only. */ }
  }, [theme]);
  const applySidebar = useCallback((value: Sidebar) => {
    setProjects(value.projects); setAgents(value.agents); setRoleRequests(value.role_requests ?? []); setGaps(value.gaps); setNotifications(value.notifications);
    setDockBadges(value.dockBadges); setNotices(value.notices); setNow(Date.now());
  }, []);
  const [loading, setLoading] = useState(true);
  const [navigating, setNavigating] = useState(false);
  const [creating, setCreating] = useState(false);
  const [terminalError, setTerminalError] = useState<string | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [navigationError, setNavigationError] = useState<string | null>(null);
  const busy = loading || navigating || creating;
  const busyRef = useRef(busy); busyRef.current = busy;
  const paneKeysRef = useRef(paneKeys); paneKeysRef.current = paneKeys;
  const applySelection = useCallback((value: Selection) => {
    setSelectedTask(value.task); setViewProject(value.project); setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names); setLaunches(value.launches ?? {}); setZoom(null); setStatuses({});
  }, []);
  const refresh = useCallback(async () => {
    setLoading(true); setCatalogError(null);
    try {
      const current = await window.a2a.selection();
      setSelectedTask(current.task); setViewProject(current.project); setPaneKeys(current.paneKeys); setLayout(current.layout); setNames(current.names); setLaunches(current.launches ?? {});
      const sidebar = await window.a2a.sidebar();
      applySidebar(sidebar);
      if (current.task && !sidebar.projects.some(project => project.tasks.some(task => task.task_id === current.task!.task_id))) {
        applySelection(await window.a2a.selectTask(null));
      }
    } catch (error) { setCatalogError('读取项目与任务失败：' + String(error)); }
    finally { setLoading(false); }
  }, [applySelection, applySidebar]);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    let mounted = true;
    const timer = setInterval(async () => {
      if (sidebarRead.current) return;
      sidebarRead.current = true;
      try {
        const value = await window.a2a.sidebar(); if (mounted) { applySidebar(value); setCatalogError(null); }
        // The main process owns the pane set. A change this renderer never saw the reply
        // for (e.g. a close that finished after a crash reload) is picked up here.
        if (!busyRef.current) {
          const current = await window.a2a.selection();
          if (mounted && !busyRef.current && current.paneKeys.join('\0') !== paneKeysRef.current.join('\0')) {
            const live = new Set(current.paneKeys);
            setPaneKeys(current.paneKeys); setLayout(current.layout); setNames(current.names); setLaunches(current.launches ?? {});
            setZoom(key => key !== null && live.has(key) ? key : null);
            setStatuses(rows => Object.fromEntries(Object.entries(rows).filter(([key]) => live.has(key))));
          }
        }
      }
      catch (error) { if (mounted) { setNotices([]); setCatalogError('侧栏状态未知：' + String(error)); setAgents(rows => rows.map(row => ({ ...row, state: 'unknown', state_label: '未知' }))); setProjects(rows => rows.map(row => ({ ...row, state: 'unknown', state_label: '未知', git: { branch: null, upstream: null, ahead: null, behind: null, error: '读取未确认' } }))); } }
      finally { sidebarRead.current = false; }
    }, 3000);
    return () => { mounted = false; clearInterval(timer); };
  }, [applySidebar]);
  const navigate = async (label: string, change: () => Promise<Selection | null>) => {
    if (busy) return;
    setNavigating(true); setNavigationError(null);
    try { const value = await change(); if (value) { applySelection(value); setPage('terminal'); } }
    catch (error) { setNavigationError(label + '失败：' + String(error)); }
    finally { setNavigating(false); }
  };
  const selectTask = (task: string | null) => {
    if (task === (selectedTask?.task_id ?? null) && (task !== null || !viewProject)) return;
    void navigate('切换任务', () => window.a2a.selectTask(task));
  };
  const selectProject = (project: string | null) => {
    if (!selectedTask && project === (viewProject?.project_id ?? null)) { setPage('terminal'); return; }
    setFocusedAgent(null);
    void navigate('切换项目', () => window.a2a.selectProject(project));
  };
  // The main process has already switched; a failed list read must not keep
  // the renderer on the old selection, so it is reported on its own.
  const reloadSidebar = async () => {
    try { applySidebar(await window.a2a.sidebar()); }
    catch (error) { setCatalogError('读取项目与任务失败：' + String(error)); }
  };
  const openProject = () => {
    void navigate('打开项目目录', async () => {
      const value = await window.a2a.openProject();
      if (value) { setFocusedAgent(null); await reloadSidebar(); }
      return value;
    });
  };
  const removeProject = (project: string) => {
    setProjectMenu(null);
    void navigate('移除项目', async () => {
      const value = await window.a2a.removeProject(project);
      await reloadSidebar();
      return value;
    });
  };
  const newTerminal = async () => {
    if (busy) return;
    setCreating(true); setTerminalError(null); setPage('terminal');
    try {
      const value = await window.a2a.newTerminal();
      setSelectedTask(value.task); setViewProject(value.project); setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names); setLaunches(value.launches ?? {}); setZoom(null);
      setStatuses(previous => Object.fromEntries(Object.entries(previous).filter(([key]) => value.paneKeys.includes(key))));
      const added = value.paneKeys.find(key => !paneKeys.includes(key));
      if (added) setFocusRequest(previous => ({ key: added, version: previous.version + 1 }));
    } catch (error) { setTerminalError('新建终端未确认：' + String(error)); }
    finally { setCreating(false); }
  };
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (!event.metaKey || event.altKey || event.ctrlKey) return;
      if (event.key === ',') { event.preventDefault(); setSettingsOpen(true); }
      else if (event.key === 'o' && !event.shiftKey) { event.preventDefault(); openProject(); }
      else if (event.key === 't' && !event.shiftKey) { event.preventDefault(); void newTerminal(); }
      else if (event.key === '\\') { event.preventDefault(); setSidebarHidden(value => !value); }
    };
    window.addEventListener('keydown', shortcut, true);
    return () => window.removeEventListener('keydown', shortcut, true);
  });
  useEffect(() => {
    if (!projectMenu) return;
    projectMenuRef.current?.querySelector<HTMLButtonElement>('button:not(:disabled)')?.focus();
    const dismiss = () => setProjectMenu(null);
    window.addEventListener('mousedown', dismiss);
    return () => window.removeEventListener('mousedown', dismiss);
  }, [projectMenu]);
  const onClose = useCallback((key: string, value: Selection) => {
    setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names); setLaunches(value.launches ?? {});
    setZoom(value => value === key ? null : value);
    setStatuses(previous => { const next = { ...previous }; delete next[key]; return next; });
  }, []);
  const onStatus = useCallback((key: string, status: PaneStatus) => {
    setStatuses(previous => ({ ...previous, [key]: status }));
  }, []);
  const selectAgent = async (agent: AgentItem) => {
    if (busy) return;
    setNavigating(true); setNavigationError(null);
    try {
      const value = await window.a2a.selectAgent(agent.id);
      applySelection(value); setFocusedAgent(agent.id); setPage('terminal');
      setFocusRequest(previous => ({ key: value.focusKey, version: previous.version + 1 }));
    } catch (error) { setNavigationError('聚焦会话失败：' + String(error)); }
    finally { setNavigating(false); }
  };
  const decideRoleRequest = async (roleRequest: RoleRequest, approved: boolean) => {
    setDeciding(roleRequest.id); setRoleRequestError(null);
    try { await window.a2a.decideRoleRequest(roleRequest.id, approved); }
    catch (error) { setRoleRequestError((approved ? '批准' : '拒绝') + '没有生效：' + String(error)); }
    // Refresh either way: a failed decision may mean the request is already gone.
    try { applySidebar(await window.a2a.sidebar()); } catch (error) { setCatalogError('列表未更新：' + String(error)); }
    finally { setDeciding(null); }
  };
  const toggleAgent = (id: string) => setCollapsedAgents(previous => { const next = new Set(previous); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  const renderAgents = (rows: AgentItem[], level: number, scope: AgentItem[]): ReactNode => <ul className="agent-branches">
    {rows.map(agent => <li key={agent.id}>
      <div className="agent-line" style={{ paddingLeft: level * 14 }}>
        {agent.descendants.count > 0 ? <button className="agent-toggle" data-agent-toggle={agent.id}
          aria-expanded={!collapsedAgents.has(agent.id)} aria-controls={'agent-children-' + agent.id}
          aria-label={(collapsedAgents.has(agent.id) ? '展开' : '折叠') + agent.role_label + '的子会话'}
          onClick={() => toggleAgent(agent.id)}>
          <svg viewBox="0 0 16 16" width="10" height="10" aria-hidden="true"><path d={collapsedAgents.has(agent.id) ? 'M6 3.5 10.5 8 6 12.5' : 'M3.5 6 8 10.5 12.5 6'} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button> : <span className="agent-toggle-space" aria-hidden="true" />}
        <button className="agent-row" data-agent-launch={agent.id} data-agent-parent={agent.parent ?? ''} data-agent-level={level}
          data-agent-state={agent.state} aria-current={focusedAgent === agent.id ? 'true' : undefined}
          data-descendant-state={collapsedAgents.has(agent.id) ? agent.descendants.state : undefined}
          title={`${agent.role_label} · ${agent.task ?? '任务未知'} · ${agent.attempt ? 'attempt ' + agent.attempt : '无 attempt'} · ${agent.cli}`}
          disabled={busy} onClick={() => void selectAgent(agent)}>
          <span className="agent-main">
            <span className="agent-role">{agent.role_label}</span>
            <span className="agent-meta">{agent.terminal ? '项目终端' : agent.task ?? '任务未知'} · {agent.cli}</span>
            <span className="sr-only agent-state">{agent.state_label}</span>
          </span>
          <span className="row-time">{since(agent.created_at, now)}</span>
          <StatusIcon state={agent.state} />
          {collapsedAgents.has(agent.id) && <span className="agent-subtree" data-agent-summary={agent.id}>
            子会话 {agent.descendants.count} · {agent.descendants.counts.map(item => `${item.label} ${item.count}`).join(' · ')}
          </span>}
        </button>
      </div>
      <div id={'agent-children-' + agent.id} hidden={collapsedAgents.has(agent.id)}>{(() => {
        const children = scope.filter(child => child.parent === agent.id);
        const controllers = children.filter(child => child.role === 'controller');
        const tasks = [...new Set(children.filter(child => child.role !== 'controller').map(child => child.task))];
        return <>{controllers.length > 0 && renderAgents(controllers, level + 1, scope)}{tasks.map(task => <div className="agent-task-group" key={task ?? 'unknown'}>
          {renderAgents(children.filter(child => child.task === task && child.role !== 'controller'), level + 1, scope)}
        </div>)}</>;
      })()}</div>
    </li>)}
  </ul>;
  const renderProjectAgents = (scope: AgentItem[]) => {
    const roots = scope.filter(agent => !agent.parent && agent.role === 'controller' && agent.preset === 'ideation');
    const loose = scope.filter(agent => !agent.parent && !(agent.role === 'controller' && agent.preset === 'ideation'));
    return <>{renderAgents(roots, 0, scope)}
      {loose.length > 0 && <div className="unassigned-agents">
        {roots.length > 0 && <div className="agent-task-label">未归属</div>}
        {renderAgents(loose.filter(agent => agent.role === 'controller'), 0, scope)}
        {[...new Set(loose.filter(agent => agent.role !== 'controller').map(agent => agent.task))].map(task => <div className="agent-task-group" key={task ?? 'unknown'}>
          {renderAgents(loose.filter(agent => agent.role !== 'controller' && agent.task === task), 0, scope)}
        </div>)}
      </div>}</>;
  };
  const states = Object.values(statuses);
  const task = states.find(value => value.snapshot)?.snapshot?.task ?? selectedTask;
  const error = states.some(value => value.error);
  const connecting = states.length < paneKeys.length || states.some(value => value.connecting);
  const project = projects.find(row => row.project_id === selectedProject);
  const repo = task?.repo ?? viewProject?.repo ?? project?.repo ?? null;
  const home = window.a2a.home;
  const status = navigating ? '正在切换' : creating ? '正在打开终端' : loading ? '正在读取后台' : catalogError ? '列表未更新' : error ? '窗格未连接' : connecting && paneKeys.length ? '正在连接' : '后台已连接';
  const sidebarToggle = <button className="icon-button" aria-label={sidebarHidden ? '显示侧栏' : '隐藏侧栏'} title="显示或隐藏侧栏（⌘\）" aria-pressed={!sidebarHidden} onClick={() => setSidebarHidden(value => !value)}>
    <svg viewBox="0 0 18 16" width="18" height="16" aria-hidden="true"><rect x="1.5" y="1.5" width="15" height="13" rx="3" fill="none" stroke="currentColor" strokeWidth="1.4" /><path d="M6.5 2v12" stroke="currentColor" strokeWidth="1.4" /></svg></button>;
  return <div className="workbench" data-sidebar={sidebarHidden ? 'hidden' : 'shown'}>
    <aside className="sidebar" hidden={sidebarHidden}>
      <div className="sidebar-top">
        {sidebarToggle}
        <button className="icon-button" aria-label="设置" title="设置（⌘,）" onClick={() => setSettingsOpen(true)}>
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="2.2" fill="none" stroke="currentColor" strokeWidth="1.4" /><path d="M8 1.6v1.8M8 12.6v1.8M1.6 8h1.8M12.6 8h1.8M3.5 3.5l1.3 1.3M11.2 11.2l1.3 1.3M3.5 12.5l1.3-1.3M11.2 4.8l1.3-1.3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></svg></button>
        <button className="icon-button create-project" aria-label="打开项目目录" title="打开项目目录（⌘O）" disabled={busy} onClick={openProject}>
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M8 2.5v11M2.5 8h11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg></button>
      </div>
      {catalogError && <p className="catalog-error" role="alert">{catalogError}</p>}
      <nav className="project-list" aria-label="项目目录" aria-busy={loading}>
        {projects.map(item => {
          const scope = agents.filter(agent => agent.project === item.project_id);
          const waiting = scope.filter(agent => agent.state === 'waiting_user_answer').length;
          return <section className="project-group" key={item.project_id}>
            <button className="project-row" data-project-id={item.project_id} data-project-state={item.state}
              aria-current={selectedProject === item.project_id ? 'page' : undefined} disabled={busy}
              title={`${item.repo ?? '目录未知'}\n${item.git.branch === '(detached)' ? '分离 HEAD' : item.git.branch ?? '分支未知'} · ${item.git.error ?? (item.git.upstream ? `领先 ${item.git.ahead} / 落后 ${item.git.behind}` : '未设置上游')}`}
              onClick={() => selectProject(item.project_id)}
              onContextMenu={event => {
                event.preventDefault();
                const box = event.currentTarget.getBoundingClientRect();
                // A keyboard context-menu request has no pointer position; anchor it under the row.
                const pointer = event.clientX || event.clientY;
                setProjectMenu({ project: item, x: pointer ? event.clientX : box.left + 12, y: pointer ? event.clientY : box.bottom, opener: event.currentTarget });
              }}>
              <span className="project-title">{item.project_id}</span>
              <span className="project-count">{scope.length || ''}</span>
              {waiting > 0 && <span className="project-needs">{waiting} 个等你</span>}
              <span className="sr-only project-state">{item.state_label}</span>
            </button>
            {renderProjectAgents(scope)}
          </section>;
        })}
        {!loading && !projects.length && <div className="catalog-status"><p>还没有项目。打开一个目录，在里面开终端，让主控开始干活。</p>
          <button className="text-button" disabled={busy} onClick={openProject}>打开项目目录…</button></div>}
        <section className="project-group">
          <button className="project-row free-terminals" aria-current={!selectedProject ? 'page' : undefined} disabled={busy} onClick={() => selectProject(null)}>
            <span className="project-title">独立终端</span><span className="project-count">家目录</span></button>
        </section>
      </nav>
      <div className="sidebar-footer"><button className="text-button" disabled={busy} onClick={() => void refresh()}>刷新列表</button></div>
    </aside>
    {projectMenu && <div ref={projectMenuRef} className="pane-menu" role="menu" aria-label="项目操作" style={{ left: projectMenu.x, top: projectMenu.y }}
      onMouseDown={event => event.stopPropagation()} onKeyDown={event => {
        const items = [...projectMenuRef.current!.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')];
        const index = items.indexOf(document.activeElement as HTMLButtonElement);
        if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
          event.preventDefault();
          items[event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
        } else if (event.key === 'Escape' || event.key === 'Tab') { if (event.key === 'Escape') event.preventDefault(); dismissProjectMenu(); }
      }}>
      <button role="menuitem" disabled={busy} onClick={() => { setProjectMenu(null); selectProject(projectMenu.project.project_id); }}>打开终端区</button>
      <button role="menuitem" disabled={busy || !projectMenu.project.opened || projectMenu.project.tasks.length > 0}
        title={projectMenu.project.tasks.length ? '项目已有门禁任务，不能移除' : undefined} onClick={() => removeProject(projectMenu.project.project_id)}>从列表移除</button>
    </div>}
    <AppNotifications notices={notices} disabled={busy} onSelect={launch => {
      const agent = agents.find(row => row.id === launch); if (agent) void selectAgent(agent);
    }} />
    <main className="content">
      <header className="task-header">
        {sidebarHidden && <span className="header-toggle">{sidebarToggle}</span>}
        <div className="header-title">
          <h1>{task?.title ?? viewProject?.project_id ?? (loading ? '正在读取项目' : '独立终端')}</h1>
          <span className="eyebrow" title={repo ?? undefined}>{task ? `${task.project_id} / ${task.task_id}` : repo ? tilde(repo, home) : '~'}</span>
        </div>
        <nav className="workspace-pages" aria-label="工作区页面">
          <button aria-current={page === 'terminal' ? 'page' : undefined} onClick={() => setPage('terminal')}>终端</button>
          <button data-flow-tab aria-current={page === 'flow' ? 'page' : undefined} onClick={() => setPage('flow')}>流程</button>
        </nav>
        <span className={'connection ' + (error || catalogError ? 'warning' : '')} role="status">{status}</span>
        <button className="primary-button" disabled={busy} title="新建终端（⌘T）" onClick={() => void newTerminal()}>新建终端</button>
      </header>
      {page === 'flow' && <FlowPage />}
      <div className="terminal-page" hidden={page !== 'terminal'}>
      {project && project.tasks.length > 0 && <nav className="task-strip" aria-label="项目任务">
        <span className="task-strip-label">任务</span>
        {project.tasks.map(item => <button key={item.task_id} className="task-row" data-task-option={item.task_id}
          disabled={busy} aria-current={task?.task_id === item.task_id ? 'page' : undefined} onClick={() => selectTask(item.task_id)}>
          <span className="task-title">{item.title}</span><span className="task-meta">{gateNames[item.state] ?? item.state}</span>
        </button>)}
      </nav>}
      {roleRequests.length > 0 && <div className="role-requests" aria-label="角色申请">
        {roleRequests.map((roleRequest, index) => {
          const key = Object.entries(launches).find(([, launch]) => launch === roleRequest.launch)?.[0];
          const rivals = roleRequests.filter(other => other.id !== roleRequest.id && other.project === roleRequest.project && other.role === roleRequest.role).length;
          const place = key ? (names[key] ? `终端「${names[key]}」` : `第 ${paneKeys.indexOf(key) + 1} 个窗格`) : '一个终端';
          return <div className="role-request" key={roleRequest.id} data-role-request={roleRequest.id} role="alert">
            <span className="role-request-number" aria-label={`申请 ${index + 1}`}>{index + 1}</span>
            <p><strong>{roleRequest.project}</strong> 的{place}里的 {roleRequest.cli ?? 'agent'} 申请成为<strong>{roleRequest.role_label}</strong>
              {!key && <span className="role-request-hint">（这个终端不在当前视图）</span>}
              {rivals > 0 && <span className="role-request-hint">。同一角色另有 {rivals} 个申请，批准其中一个，其余自动拒绝</span>}</p>
            <button className="text-button" disabled={deciding !== null} onClick={() => void decideRoleRequest(roleRequest, false)}>拒绝</button>
            <button className="primary-button" disabled={deciding !== null} onClick={() => void decideRoleRequest(roleRequest, true)}>批准</button>
          </div>;
        })}
        {roleRequestError && <p className="catalog-error" role="alert">{roleRequestError}</p>}
      </div>}
      {navigationError && <div className="connection-error" role="alert">{navigationError}</div>}
      {terminalError && <div className="connection-error" role="alert">{terminalError}</div>}
      <div className="pane-grid pane-layout" aria-label="终端窗格">
        {!navigating && paneKeys.map(key => {
          const rect = zoom === key ? { x: 0, y: 0, w: 100, h: 100 } : paneRects(layout)[key] ?? { x: 0, y: 0, w: 100, h: 100 };
          return <div className="pane-slot" key={key} hidden={Boolean(zoom && zoom !== key)} data-role-request-pending={roleRequests.some(roleRequest => roleRequest.launch === launches[key]) || undefined} data-edge-right={rect.x + rect.w < 99.9} data-edge-bottom={rect.y + rect.h < 99.9}
            style={{ left: rect.x + '%', top: rect.y + '%', width: rect.w + '%', height: rect.h + '%' }}>
            {roleRequests.map((roleRequest, index) => roleRequest.launch === launches[key] &&
              <span className="role-request-tag" key={roleRequest.id}>申请 {index + 1} · {roleRequest.role_label}</span>)}
            <SessionPane paneKey={key} name={names[key]} home={home} focusRequest={focusRequest.key === key ? focusRequest.version : 0} zoomed={zoom === key} onZoom={() => setZoom(value => value === key ? null : key)}
              onAction={async (key, action) => { const value = await window.a2a.paneAction(key, action); setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names); setLaunches(value.launches ?? {}); setZoom(null); }} onStatus={onStatus} onClose={onClose} />
          </div>;
        })}
        {navigating ? <p className="selection-hint" role="status">正在切换…</p> : !paneKeys.length &&
          <div className="selection-hint">
            <h2>{task ? '这个任务没有打开的窗格' : viewProject ? `在 ${viewProject.project_id} 里开一个终端` : '开一个终端'}</h2>
            <p>{task ? '从左侧点选这个任务下的会话，或新建终端。'
              : `终端会在 ${tilde(repo, home) || '家目录'} 下启动。经门禁派发的会话会按项目出现在左侧。`}</p>
            <button className="primary-button" disabled={busy} onClick={() => void newTerminal()}>新建终端</button>
          </div>}
      </div>
      {task && <section className="gate" aria-label="门禁状态">
        <div><span className="gate-label">门禁</span><strong data-gate-state={task?.state ?? 'unknown'}>{gateNames[task?.state ?? ''] ?? '未知'}</strong></div>
        <dl><div><dt>执行尝试</dt><dd>{task?.current_attempt?.attempt_id.slice(0, 8) ?? '尚未认领'}</dd></div>
          <div><dt>候选提交</dt><dd>{task?.candidate_commit?.slice(0, 10) ?? '尚未交付'}</dd></div>
          <div><dt>验收</dt><dd>{task?.verification?.state ?? '尚未开始'}</dd></div>
          <div><dt>集成</dt><dd>{task?.integration_intent?.state ?? '尚未开始'}</dd></div></dl>
      </section>}
      </div>
    </main>
    <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} theme={theme} onTheme={setTheme} gaps={gaps}
      notifications={notifications} dockBadges={dockBadges} onNotification={(enabled, preference) => {
        void window.a2a.notificationSetting(enabled, preference).then(value => {
          if (preference === 'notifications') { setNotifications(value); if (!value) setNotices([]); }
          else setDockBadges(value);
        }).catch(error => setCatalogError('通知设置未保存：' + String(error)));
      }} />
  </div>;
}
createRoot(document.getElementById('root')!).render(<Workbench />);
