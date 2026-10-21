// Codex dark theme seed from Synara 49cae984f, apps/web/src/theme/theme.seed.generated.ts.
// Copyright (c) 2026 T3 Tools Inc. and Emanuele Di Pietro. MIT; see ../LICENSE.synara.
import { createRoot } from 'react-dom/client';
import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import './style.css';
import brandLogo from './brand/logo-on-dark.png';
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
type ProjectItem = { project_id: string; repo: string | null; tasks: TaskItem[]; state: string; state_label: string;
  git: { branch: string | null; upstream: string | null; ahead: number | null; behind: number | null; error: string | null } };
type AgentItem = { id: string; project: string; task: string | null; attempt: string | null; parent: string | null;
  role: string; preset: string | null; role_label: string; cli: string; state: string; state_label: string;
  descendants: { count: number; state: string; state_label: string; counts: { state: string; label: string; count: number }[] } };
type Sidebar = { projects: ProjectItem[]; agents: AgentItem[]; gaps: string[]; notifications: boolean; dockBadges: boolean; notices: AppNotice[] };
const statusIcons: Record<string, string> = { running: '●', waiting_user_answer: '◐', waiting_controller_answer: '◑', idle: '○', ended: '✓', unrestored: '◌', unknown: '?' };
function StatusIcon({ state }: { state: string }) { return <span className="status-icon" aria-hidden="true">{statusIcons[state] ?? '?'}</span>; }

type Layout = string | { direction: 'right' | 'down'; first: Layout; second: Layout };
type Selection = { task: Snapshot['task'] | null; paneKeys: string[]; layout: Layout | null; names: Record<string, string> };
declare global { interface Window { a2a: { readonly paneKeys: readonly string[];
  executionSettings(change?: ExecutionSelection & { role: ExecutionRole }): Promise<Record<ExecutionRole, ExecutionSelection>>;
  flow(): Promise<FlowSnapshot>; sidebar(): Promise<Sidebar>; selectAgent(launch: string): Promise<Selection & { focusKey: string }>; notificationSetting(enabled?: boolean, preference?: 'notifications' | 'dockBadges'): Promise<boolean>;
  projects(): Promise<ProjectItem[]>; tasks(project: string): Promise<TaskItem[]>;
  selection(): Promise<Selection>; selectTask(task: string | null): Promise<Selection>;
  creationRepository(): Promise<{ repo: string; branch: string; card: Record<string, any> } | null>;
  creationSubmit(input: { task: string; project: string; title: string; branch: string; card: string }): Promise<{
    ok: boolean; task?: { task_id: string }; error?: string; details?: unknown; stage?: string; persisted: boolean | 'unknown' }>;
  creationCancel(): Promise<{ ok: boolean; persisted: boolean | 'unknown' }>;
  newTerminal(source?: string): Promise<Selection>;
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
  restore_argv_missing: '启动记录缺少完整参数', restore_version_mismatch: 'CLI 版本与启动记录不符',
  restore_session_missing: '原生会话不存在',
};

type PaneStatus = { snapshot: Snapshot | null; error: string | null; connecting: boolean };

function SessionPane({ paneKey, name, focusRequest, zoomed, onZoom, onAction, onStatus, onClose }: { paneKey: string; name?: string; focusRequest: number; zoomed: boolean; onZoom: () => void; onAction: (key: string, action: { type: string; direction?: string; name?: string }) => Promise<void>; onStatus: (key: string, status: PaneStatus) => void; onClose: (key: string, value: Selection) => void }) {
  const mount = useRef<HTMLDivElement>(null);
  const reconnect = useRef<() => void>(() => {});
  const releaseQueue = useRef<() => void>(() => {});
  const [terminal, setTerminal] = useState<Terminal | null>(null);
  useEffect(() => { if (focusRequest && terminal) terminal.focus(); }, [focusRequest, terminal]);
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
        <div className="pane-header"><strong title={name ?? role}>{name ?? role}</strong>
          {name && <span>{role}</span>}
          <button ref={menuButton} className="pane-menu-trigger" aria-label="窗格菜单" aria-haspopup="menu" aria-expanded={Boolean(menu)} disabled={acting || closing}
            onClick={event => { if (menu) dismissMenu(); else { const rect = event.currentTarget.getBoundingClientRect(); openMenu(rect.left, rect.bottom); } }}>⋯</button><span>{shell ? 'zsh' : snapshot?.launch?.cli_version ?? '读取中'}</span>
          <span className="readonly">{inputEnabled ? '可输入' : '只读'}</span>
          <span className="input-target">{inputTarget ? `正在输入：${role}` : shell && pane?.lifecycle === 'ended' ? '终端已结束 · 只读' : historical ? '历史 attempt · 只读' : '终端未聚焦'}</span>
          <span className="pane-state" data-state={error ? 'unknown' : pane?.state ?? 'unknown'}>{error ? '未知' : shell
            ? lifecycleNames[pane?.lifecycle ?? 'unknown'] ?? '未知' : activityNames[pane?.state ?? 'unknown'] ?? '未知'}</span>
          <button disabled={!inputEnabled} onClick={() => terminal?.focus()}>进入终端</button>
          <button disabled={closing || acting} onClick={closePane}>关闭窗格</button>
          {!shell && snapshot?.launch?.role !== 'reviewer' && <button disabled={!snapshot?.input_enabled || !pane?.interrupted || !declarationReady || releasing || Boolean(inputError || error)}
            onClick={() => releaseQueue.current()}>输入框已空，放行</button>}
          <span className="pane-identity">{snapshot?.launch ?
            shell ? `${snapshot.launch.project ?? '独立终端'} · ${snapshot.launch.worktree ?? ''}` :
              `${snapshot.launch.role}${snapshot.launch.preset ? '/' + snapshot.launch.preset : ''} · task ${task?.task_id} · launch ${snapshot.launch.id}${snapshot.launch.attempt ? ' · attempt ' + snapshot.launch.attempt : ''}`
            : '尚未启动窗格'}</span>
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
        <div className="terminal-scroll" data-output-offset={offset}><div className="terminal-mount" ref={mount} /></div>
        <TerminalScrollToBottom terminal={terminal} />
        <div className="pane-footer"><span>{shell ? '普通终端 · zsh' : pane?.interrupted ? '请自行保留、修改或清空草稿；看到输入框空了再声明放行。'
          : snapshot?.launch?.role === 'reviewer' ? '独立审查 · 只读' : snapshot?.launch?.role === 'worker' ? '在此窗格输入会记录为人工介入' : '在此窗格输入会记录为用户输入'}</span><span data-lifecycle={pane?.lifecycle ?? 'unknown'}>执行：{lifecycleNames[pane?.lifecycle ?? 'unknown'] ?? '未知'}</span></div>
      </section>;
}

function paneRects(tree: Layout | null, x = 0, y = 0, w = 100, h = 100): Record<string, { x: number; y: number; w: number; h: number }> {
  if (!tree) return {};
  if (typeof tree === 'string') return { [tree]: { x, y, w, h } };
  return tree.direction === 'right'
    ? { ...paneRects(tree.first, x, y, w / 2, h), ...paneRects(tree.second, x + w / 2, y, w / 2, h) }
    : { ...paneRects(tree.first, x, y, w, h / 2), ...paneRects(tree.second, x, y + h / 2, w, h / 2) };
}

function CreationForm({ project, onClose, onCreated }: { project: string; onClose: () => void; onCreated: (task: string) => Promise<void> }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [projectName, setProjectName] = useState(project);
  const [repo, setRepo] = useState('');
  const [taskId, setTaskId] = useState('');
  const [branch, setBranch] = useState('');
  const [title, setTitle] = useState('');
  const [goal, setGoal] = useState('');
  const [command, setCommand] = useState('');
  const [remaining, setRemaining] = useState('');
  const [busy, setBusy] = useState(false);
  const [persisted, setPersisted] = useState<boolean | 'unknown'>(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { dialog.current?.showModal(); }, []);
  const choose = async () => {
    setBusy(true); setError(null);
    try {
      const value = await window.a2a.creationRepository();
      if (!value) return;
      setRepo(value.repo); setBranch(value.branch); setTaskId(value.card.id);
      const { goal: _goal, completion_conditions: _commands, ...fields } = value.card;
      setRemaining(JSON.stringify({ ...fields, non_goals: ['不修改目标以外的功能'], paths: { allow: ['.'], deny: ['.git/'] },
        oracle_paths: ['tests/'], executor: { cli: 'Codex', model: 'gpt-6.1-sol', effort: 'xhigh' } }, null, 2));
    } catch (failure) { setError('选择仓库失败：' + String(failure)); }
    finally { setBusy(false); }
  };
  const close = async () => {
    if (busy || persisted === 'unknown') return;
    setBusy(true);
    try { await window.a2a.creationCancel(); onClose(); }
    catch (failure) { setError('关闭表单未确认：' + String(failure)); setBusy(false); }
  };
  const submit = async () => {
    if (busy || persisted) return;
    setBusy(true); setError(null);
    let submitted = false;
    try {
      const fields = JSON.parse(remaining);
      const card = { ...fields, goal, completion_conditions: [{ argv: JSON.parse(command) }] };
      submitted = true;
      const result = await window.a2a.creationSubmit({ task: typeof card.id === 'string' ? card.id : taskId,
        project: projectName, title, branch, card: JSON.stringify(card) });
      setPersisted(result.persisted);
      if (!result.ok) {
        setError(`${result.stage === 'preflight' ? '表单未提交' : '门禁拒收或注册未确认'}（${result.stage}）：${result.error}\n${JSON.stringify(result.details ?? null, null, 2)}`);
        return;
      }
      await onCreated(result.task!.task_id);
    } catch (failure) {
      if (submitted) setPersisted('unknown');
      setError('表单未提交或结果未确认：' + String(failure));
    }
    finally { setBusy(false); }
  };
  return <dialog ref={dialog} className="creation-dialog" aria-labelledby="creation-title" onCancel={event => { event.preventDefault(); void close(); }}>
    <form className="creation-form" onSubmit={event => { event.preventDefault(); void submit(); }} aria-busy={busy}>
      <h2 id="creation-title">新建项目与任务</h2>
      <p>项目随首个任务一起注册，成功后出现在左侧列表。取消草稿不会创建项目或任务。不启动主控，不调用模型。</p>
      <fieldset disabled={busy || Boolean(persisted)}>
        <legend>项目</legend>
        <label>项目名字（项目号）<input data-creation-field="project" required maxLength={128} pattern="[A-Za-z0-9](?:[A-Za-z0-9_.]|-){0,127}" value={projectName} onChange={event => setProjectName(event.target.value)} placeholder="my-project" /></label>
        <small>名字用作列表中的项目号；以英文字母或数字开头，可含点、下划线和短横线，最多 128 字符。</small>
        <div className="repository-choice"><button type="button" onClick={() => void choose()}>选择仓库目录…</button><output data-creation-repo>{repo || '请选择已有 Git 仓库的根目录'}</output></div>
        <label>工作分支<input data-creation-field="branch" required pattern="refs/heads/.+" value={branch} onChange={event => setBranch(event.target.value)} placeholder="refs/heads/main" /></label>
      </fieldset>
      <fieldset disabled={busy || Boolean(persisted)}>
        <legend>任务</legend>
        <label>标题<input data-creation-field="title" required maxLength={240} value={title} onChange={event => setTitle(event.target.value)} /></label>
        <label>目标<textarea data-creation-field="goal" required rows={2} value={goal} onChange={event => setGoal(event.target.value)} /></label>
        <label>完成条件命令<textarea data-creation-field="command" required rows={2} value={command} onChange={event => setCommand(event.target.value)} placeholder={'["python3", "tests/check.py"]'} /></label>
        <small>填写一条 JSON 参数数组，命令须可执行；注册时只校验格式，验收时才运行。</small>
        <label>其余任务卡字段（JSON，可修改）<textarea data-creation-field="card" required rows={15} spellCheck={false} value={remaining} onChange={event => setRemaining(event.target.value)} /></label>
        <small>默认允许修改整个仓库，验收文件为 tests/；请按实际任务修改 paths 和 oracle_paths。source 无 ticket 时为 null；base_commit、writer 由门禁在认领时填写，注册时须为 null。</small>
      </fieldset>
      {error && <pre className="creation-error" role="alert">{error}</pre>}
      {persisted === 'unknown' ? <p role="status">保存或注册结果未知，只读核实未能确认。暂不能取消或重试，请由主控核对门禁记录。</p>
        : persisted && <p role="status">已核实任务卡已保存，当前注册未成功。关闭表单会保留记录；本表单不会自动重试。</p>}
      <div className="creation-actions"><button type="button" disabled={busy || persisted === 'unknown'} onClick={() => void close()}>{persisted === 'unknown' ? '结果未知，暂不能取消' : persisted ? '关闭表单（保留已保存记录）' : '取消'}</button>
        <button disabled={busy || Boolean(persisted) || !repo}>{busy ? '正在处理…' : '确认并注册任务'}</button></div>
    </form>
  </dialog>;
}

function Workbench() {
  const [page, setPage] = useState<'terminal' | 'flow'>('terminal');
  const [statuses, setStatuses] = useState<Record<string, PaneStatus>>({});
  const [paneKeys, setPaneKeys] = useState([...window.a2a.paneKeys]);
  const [layout, setLayout] = useState<Layout | null>(null);
  const [names, setNames] = useState<Record<string, string>>({});
  const [zoom, setZoom] = useState<string | null>(null);
  const [directorySource, setDirectorySource] = useState('home');
  const [selectedTask, setSelectedTask] = useState<Snapshot['task'] | null>(null);
  useEffect(() => { if (!selectedTask && directorySource === 'project') setDirectorySource('home'); }, [selectedTask, directorySource]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [gaps, setGaps] = useState<string[]>([]);
  const [notifications, setNotifications] = useState(true);
  const [dockBadges, setDockBadges] = useState(true);
  const [notices, setNotices] = useState<AppNotice[]>([]);
  const [focusedAgent, setFocusedAgent] = useState<string | null>(null);
  const [collapsedAgents, setCollapsedAgents] = useState<Set<string>>(new Set());
  const [focusRequest, setFocusRequest] = useState({ key: '', version: 0 });
  const sidebarRead = useRef(false);
  const applySidebar = useCallback((value: Sidebar) => {
    setProjects(value.projects); setAgents(value.agents); setGaps(value.gaps); setNotifications(value.notifications);
    setDockBadges(value.dockBadges); setNotices(value.notices);
  }, []);
  const [loading, setLoading] = useState(true);
  const [navigating, setNavigating] = useState(false);
  const [creating, setCreating] = useState(false);
  const [terminalError, setTerminalError] = useState<string | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [navigationError, setNavigationError] = useState<string | null>(null);
  const [creationProject, setCreationProject] = useState<string | null>(null);
  const applySelection = useCallback((value: Selection) => {
    setSelectedTask(value.task); setSelectedProject(value.task?.project_id ?? null); setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names); setZoom(null); setStatuses({});
  }, []);
  const refresh = useCallback(async () => {
    setLoading(true); setCatalogError(null);
    try {
      const current = await window.a2a.selection();
      setSelectedTask(current.task); setSelectedProject(current.task?.project_id ?? null); setPaneKeys(current.paneKeys); setLayout(current.layout); setNames(current.names);
      const sidebar = await window.a2a.sidebar();
      const catalog = sidebar.projects;
      applySidebar(sidebar);
      if (current.task && !catalog.some(project => project.tasks.some(task => task.task_id === current.task!.task_id))) {
        applySelection(await window.a2a.selectTask(null));
      }
      setProjects(catalog);
    } catch (error) { setCatalogError('读取项目与任务失败：' + String(error)); }
    finally { setLoading(false); }
  }, [applySelection, applySidebar]);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    let mounted = true;
    const timer = setInterval(async () => {
      if (sidebarRead.current) return;
      sidebarRead.current = true;
      try { const value = await window.a2a.sidebar(); if (mounted) { applySidebar(value); setCatalogError(null); } }
      catch (error) { if (mounted) { setNotices([]); setCatalogError('侧栏状态未知：' + String(error)); setAgents(rows => rows.map(row => ({ ...row, state: 'unknown', state_label: '未知' }))); setProjects(rows => rows.map(row => ({ ...row, state: 'unknown', state_label: '未知', git: { branch: null, upstream: null, ahead: null, behind: null, error: '读取未确认' } }))); } }
      finally { sidebarRead.current = false; }
    }, 3000);
    return () => { mounted = false; clearInterval(timer); };
  }, [applySidebar]);
  const selectTask = async (task: string | null) => {
    if (navigating || loading || creating || task === (selectedTask?.task_id ?? null)) return;
    setNavigating(true); setNavigationError(null);
    try { applySelection(await window.a2a.selectTask(task)); }
    catch (error) { setNavigationError('切换任务失败：' + String(error)); }
    finally { setNavigating(false); }
  };
  const newTerminal = async () => {
    if (creating || navigating || loading) return;
    setCreating(true); setTerminalError(null);
    try {
      const value = await window.a2a.newTerminal(directorySource);
      setSelectedTask(value.task); setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names); setZoom(null);
      setStatuses(previous => Object.fromEntries(Object.entries(previous).filter(([key]) => value.paneKeys.includes(key))));
    } catch (error) { setTerminalError('新建终端未确认：' + String(error)); }
    finally { setCreating(false); }
  };
  const onClose = useCallback((key: string, value: Selection) => {
    setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names);
    setZoom(value => value === key ? null : value);
    setStatuses(previous => { const next = { ...previous }; delete next[key]; return next; });
  }, []);
  const onStatus = useCallback((key: string, status: PaneStatus) => {
    setStatuses(previous => ({ ...previous, [key]: status }));
  }, []);
  const selectAgent = async (agent: AgentItem) => {
    if (navigating || loading || creating) return;
    setNavigating(true); setNavigationError(null);
    try {
      const value = await window.a2a.selectAgent(agent.id);
      applySelection(value); setFocusedAgent(agent.id); setPage('terminal');
      setFocusRequest(previous => ({ key: value.focusKey, version: previous.version + 1 }));
    } catch (error) { setNavigationError('聚焦会话失败：' + String(error)); }
    finally { setNavigating(false); }
  };
  const projectAgents = agents.filter(agent => agent.project === selectedProject);
  const renderAgents = (rows: AgentItem[], level: number): ReactNode => <ul className="agent-branches">
    {rows.map(agent => <li key={agent.id}>
      <div className="agent-line">
      {agent.descendants.count > 0 ? <button className="agent-toggle" data-agent-toggle={agent.id}
        aria-expanded={!collapsedAgents.has(agent.id)} aria-controls={'agent-children-' + agent.id}
        aria-label={(collapsedAgents.has(agent.id) ? '展开' : '折叠') + agent.role_label + '的子会话'}
        onClick={() => setCollapsedAgents(previous => { const next = new Set(previous); if (next.has(agent.id)) next.delete(agent.id); else next.add(agent.id); return next; })}>
        <span aria-hidden="true">{collapsedAgents.has(agent.id) ? '▸' : '▾'}</span>
      </button> : <span className="agent-toggle-space" aria-hidden="true" />}
      <button className="agent-row" data-agent-launch={agent.id} data-agent-parent={agent.parent ?? ''} data-agent-level={level}
        data-agent-state={agent.state} aria-current={focusedAgent === agent.id ? 'true' : undefined}
        data-descendant-state={collapsedAgents.has(agent.id) ? agent.descendants.state : undefined}
        disabled={loading || navigating || creating} onClick={() => void selectAgent(agent)}>
        <span className="agent-role"><StatusIcon state={agent.state} />{agent.role_label}</span>
        <span className="agent-state">{agent.state_label}</span>
        <span className="agent-meta">{agent.task ?? '任务未知'} · {agent.attempt ? 'attempt ' + agent.attempt : '无 attempt'} · {agent.cli}</span>
        {collapsedAgents.has(agent.id) && <span className="agent-subtree" data-agent-summary={agent.id}>
          <StatusIcon state={agent.descendants.state} />子会话 {agent.descendants.count} · {agent.descendants.counts.map(item => `${item.label} ${item.count}`).join(' · ')}
        </span>}
      </button>
      </div>
      <div id={'agent-children-' + agent.id} hidden={collapsedAgents.has(agent.id)}>{(() => {
        const children = projectAgents.filter(child => child.parent === agent.id);
        const controllers = children.filter(child => child.role === 'controller');
        const tasks = [...new Set(children.filter(child => child.role !== 'controller').map(child => child.task))];
        return <>{controllers.length > 0 && renderAgents(controllers, level + 1)}{tasks.map(task => <div className="agent-task-group" key={task ?? 'unknown'}>
          <div className="agent-task-label">任务 {task ?? '未知'}</div>
          {renderAgents(children.filter(child => child.task === task && child.role !== 'controller'), level + 1)}
        </div>)}</>;
      })()}</div>
    </li>)}
  </ul>;
  const states = Object.values(statuses);
  const task = states.find(value => value.snapshot)?.snapshot?.task ?? selectedTask;
  const error = states.some(value => value.error);
  const connecting = states.length < paneKeys.length || states.some(value => value.connecting);
  return <div className="workbench">
    <aside className="sidebar">
      <div className="brand"><img src={brandLogo} alt="" />Enchanted <span>a2a 内核</span></div>
      <div className="catalog-heading"><span className="nav-label">项目目录</span>
        <button disabled={loading || navigating || creating} onClick={() => void refresh()}>刷新列表</button></div>
      <button className="create-project" disabled={loading || navigating || creating} onClick={() => setCreationProject('')}>新增项目目录</button>
      {catalogError && <p className="catalog-error" role="alert">{catalogError}</p>}
      <nav className="project-list" aria-label="项目目录" aria-busy={loading}>
        {projects.map(project => <button className="project-row" key={project.project_id} data-project-id={project.project_id}
          data-project-state={project.state} aria-current={selectedProject === project.project_id ? 'page' : undefined}
          disabled={loading || navigating || creating} onClick={() => { setSelectedProject(project.project_id); if (project.tasks[0]) void selectTask(project.tasks[0].task_id); }}>
          <span className="project-title"><StatusIcon state={project.state} />{project.project_id}</span>
          <span className="project-git">{project.git.branch === '(detached)' ? '分离 HEAD' : project.git.branch ?? '分支未知'} · {project.git.error ? project.git.error : project.git.upstream
            ? `领先 ${project.git.ahead} / 落后 ${project.git.behind}` : '未设置上游'}</span>
          <span className="project-state">{project.state_label}</span>
          <span className="project-repo">{project.repo ?? '目录未知'}</span>
        </button>)}
        {!loading && !projects.length && <p className="catalog-status">还没有项目。新增项目目录并注册首个任务后，项目会出现在这里。</p>}
      </nav>
      <div className="catalog-heading agent-heading"><span className="nav-label">agent 会话</span></div>
      <nav className="agent-list" aria-label="agent 层级">
        {renderAgents(projectAgents.filter(agent => !agent.parent && agent.role === 'controller' && agent.preset === 'ideation'), 0)}
        {projectAgents.some(agent => !agent.parent && !(agent.role === 'controller' && agent.preset === 'ideation')) && <div className="unassigned-agents">
          <div className="agent-task-label">未归属</div>
          {renderAgents(projectAgents.filter(agent => !agent.parent && agent.role === 'controller' && agent.preset !== 'ideation'), 0)}
          {[...new Set(projectAgents.filter(agent => !agent.parent && agent.role !== 'controller').map(agent => agent.task))].map(task => <div className="agent-task-group" key={task ?? 'unknown'}>
            <div className="agent-task-label">任务 {task ?? '未知'}</div>
            {renderAgents(projectAgents.filter(agent => !agent.parent && agent.role !== 'controller' && agent.task === task), 0)}
          </div>)}
        </div>}
        {!projectAgents.length && <p className="catalog-status">{selectedProject ? '这个项目还没有 agent 启动记录。' : '选择项目，查看已有会话。'}</p>}
      </nav>
      <button className="free-terminals" aria-current={!selectedTask && !selectedProject ? 'page' : undefined} disabled={loading || navigating || creating} onClick={() => { setSelectedProject(null); void selectTask(null); }}>独立终端</button>
      <details className="sidebar-settings"><summary>图例与设置</summary>
        <ExecutionSettings />
        <div className="status-legend">{Object.entries({ running: '运行中', waiting_user_answer: '等待用户回答', waiting_controller_answer: '等待主控回答', idle: '空闲', ended: '已结束', unrestored: '未恢复', unknown: '未知' }).map(([state, label]) => <span key={state}><StatusIcon state={state} />{label}</span>)}</div>
        <NotificationSettings notifications={notifications} dockBadges={dockBadges} onChange={(enabled, preference) => {
          void window.a2a.notificationSetting(enabled, preference).then(value => {
            if (preference === 'notifications') { setNotifications(value); if (!value) setNotices([]); }
            else setDockBadges(value);
          }).catch(error => setCatalogError('通知设置未保存：' + String(error)));
        }} />
        {gaps.map(gap => <p key={gap}>{gap}</p>)}
      </details>
      <div className="sidebar-footer">原生 CLI · 本地编排</div>
    </aside>
    <AppNotifications notices={notices} disabled={loading || navigating || creating} onSelect={launch => {
      const agent = agents.find(row => row.id === launch); if (agent) void selectAgent(agent);
    }} />
    <main>
      <nav className="workspace-pages" aria-label="工作区页面">
        <button aria-current={page === 'terminal' ? 'page' : undefined} onClick={() => setPage('terminal')}>终端</button>
        <button data-flow-tab aria-current={page === 'flow' ? 'page' : undefined} onClick={() => setPage('flow')}>流程</button>
      </nav>
      {page === 'flow' && <FlowPage />}
      <div className="terminal-page" hidden={page !== 'terminal'}>
      <header className="task-header">
        <div><div className="eyebrow">{task ? `${task.project_id} / ${task.task_id}` : '终端工作区'}</div><h1>{task?.title ?? (loading ? '正在读取项目' : '独立终端')}</h1></div>
        <span className={'connection ' + (error || catalogError ? 'warning' : '')}>{navigating ? '正在切换任务' : loading ? '正在读取后台' : catalogError ? '列表未更新' : error ? '窗格未连接 · 上次记录' : connecting ? '正在连接' : '后台已连接'}</span>
      </header>
      {selectedProject && <nav className="task-strip" aria-label="项目任务">
        <button className="create-task" disabled={loading || navigating || creating} onClick={() => setCreationProject(selectedProject)}>新建任务</button>
        {projects.find(project => project.project_id === selectedProject)?.tasks.map(item => <button key={item.task_id} className="task-row" data-task-option={item.task_id}
          disabled={loading || navigating || creating} aria-current={task?.task_id === item.task_id ? 'page' : undefined} onClick={() => void selectTask(item.task_id)}>
          <span className="task-title">{item.title}</span><span className="task-meta">{item.task_id} · {gateNames[item.state] ?? item.state}</span>
        </button>)}
      </nav>}
      {navigationError && <div className="connection-error" role="alert">{navigationError}</div>}
      <div className="pane-toolbar">
        <span role="status">{creating ? '正在创建终端…' : '新建或分屏，打开你自己的 zsh'}</span>
        <label className="directory-choice">工作目录 <select aria-label="终端工作目录" value={directorySource} onChange={event => setDirectorySource(event.target.value)}>
          <option value="home">家目录</option>{selectedTask && <option value="project">项目目录</option>}<option value="choose">选择目录…</option>
        </select></label>
        <button disabled={loading || navigating || creating} onClick={() => void newTerminal()}>新建终端</button>
      </div>
      {terminalError && <div className="connection-error" role="alert">{terminalError}</div>}
      <div className="pane-grid pane-layout" aria-label="终端窗格">
        {!navigating && paneKeys.map(key => {
          const rect = zoom === key ? { x: 0, y: 0, w: 100, h: 100 } : paneRects(layout)[key] ?? { x: 0, y: 0, w: 100, h: 100 };
          return <div className="pane-slot" key={key} hidden={Boolean(zoom && zoom !== key)} style={{ left: rect.x + '%', top: rect.y + '%', width: rect.w + '%', height: rect.h + '%' }}>
            <SessionPane paneKey={key} name={names[key]} focusRequest={focusRequest.key === key ? focusRequest.version : 0} zoomed={zoom === key} onZoom={() => setZoom(value => value === key ? null : key)}
              onAction={async (key, action) => { const value = await window.a2a.paneAction(key, action); setPaneKeys(value.paneKeys); setLayout(value.layout); setNames(value.names); setZoom(null); }} onStatus={onStatus} onClose={onClose} />
          </div>;
        })}
        {navigating ? <p className="selection-hint" role="status">正在切换任务…</p> : !task && !paneKeys.length
          ? <div className="selection-hint"><h2>{!loading && !catalogError && !projects.length ? '打开第一个终端' : '打开终端或选择任务'}</h2>
            <p>{!loading && !catalogError && !projects.length ? '点击“新建终端”，无需先创建项目。' : '选择项目下的任务，查看它的会话和门禁状态。'}</p></div>
          : !paneKeys.length && <p className="selection-hint">当前任务没有打开的窗格。</p>}
      </div>
      {task && <section className="gate" aria-label="门禁状态">
        <div><span className="eyebrow">当前任务门禁</span><strong data-gate-state={task?.state ?? 'unknown'}>{gateNames[task?.state ?? ''] ?? '未知'}</strong></div>
        <dl><div><dt>执行尝试</dt><dd>{task?.current_attempt?.attempt_id.slice(0, 8) ?? '尚未认领'}</dd></div>
          <div><dt>候选提交</dt><dd>{task?.candidate_commit?.slice(0, 10) ?? '尚未交付'}</dd></div>
          <div><dt>验收</dt><dd>{task?.verification?.state ?? '尚未开始'}</dd></div>
          <div><dt>集成</dt><dd>{task?.integration_intent?.state ?? '尚未开始'}</dd></div></dl>
      </section>}
      </div>
    </main>
    {creationProject !== null && <CreationForm project={creationProject} onClose={() => setCreationProject(null)} onCreated={async task => {
      setCreationProject(null); await refresh();
      try { applySelection(await window.a2a.selectTask(task)); }
      catch (failure) { setNavigationError('任务已注册，切换失败：' + String(failure)); }
    }} />}
  </div>;
}
createRoot(document.getElementById('root')!).render(<Workbench />);
