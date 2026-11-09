// T-249: the side panel slot of the project view. An internal registry, not a public mod interface: each panel is
// registered here with an id, a title, an icon and a component, and gets a small host — the directory it follows, the
// theme, git run by the main process as argv (never a shell), opening a file, sending a notice. No third-party code
// is loaded; a public mod interface needs its own decision ticket.
import { useCallback, useEffect, useMemo, useRef, useState, type ComponentType, type ReactNode } from 'react';
import { GitGraphPanel } from './GitGraphPanel';
import { terminalPalettes } from '../terminalPalettes';
import './panels.css';

export type Followed = { dir: string | null; source: 'pane' | 'project' | 'pinned'; managed: boolean; role: string | null; pane: string | null };
export type GitResult = { code: number | null; stdout: string; stderr: string };
export type RepoInfo = { dir: string; top: string | null; commonDir: string | null; gitDir: string | null; managed: boolean };
export type PanelHost = {
  directory: Followed;
  dark: boolean;
  git: {
    repo(dir: string): Promise<RepoInfo>;
    read(dir: string, argv: string[], encoding?: 'utf8' | 'base64'): Promise<GitResult>;
    action(dir: string, action: Record<string, unknown>, values: Record<string, unknown>): Promise<{ text: string; argv: string[][] }>;
    scan(root: string, depth: number, tags: boolean): Promise<any>;
    watch(dir: string, onChange: (refs: boolean) => void): () => void;
  };
  openFile(path: string): Promise<void>;
  notify(text: string, level?: 'info' | 'error'): void;
  showPanel(id: string): void;
};
export type PanelDefinition = { id: string; title: string; icon: ReactNode; Component: ComponentType<{ host: PanelHost }> };

const graphIcon = <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="4" cy="3.5" r="1.6" fill="none" stroke="currentColor" strokeWidth="1.3" /><circle cx="4" cy="12.5" r="1.6" fill="none" stroke="currentColor" strokeWidth="1.3" /><circle cx="12" cy="6" r="1.6" fill="none" stroke="currentColor" strokeWidth="1.3" /><path d="M4 5.1v5.8M12 7.6c0 2.5-3 2.9-7 4" fill="none" stroke="currentColor" strokeWidth="1.3" /></svg>;
export const panels: PanelDefinition[] = [
  { id: 'git-graph', title: 'Git 图', icon: graphIcon, Component: GitGraphPanel },
];

// The preload bridge's panel methods (preload.ts).
type PanelBridge = {
  panelDirectory(key: string | null): Promise<Omit<Followed, 'source'> & { source: 'pane' | 'project' }>;
  gitRepo(dir: string): Promise<RepoInfo>;
  gitRead(dir: string, argv: string[], encoding?: 'utf8' | 'base64'): Promise<GitResult>;
  gitAction(dir: string, action: Record<string, unknown>, values: Record<string, unknown>): Promise<{ text: string; argv: string[][] }>;
  gitScan(root: string, depth: number, tags: boolean): Promise<any>;
  gitWatch(dir: string): Promise<string>; gitUnwatch(id: string): Promise<void>;
  onGitChanged(listener: (change: { id: string; refs: boolean }) => void): () => void;
  openPath(path: string): Promise<void>;
  copyText(text: string): Promise<void>;
};
export const bridge = () => (window as unknown as { a2a: PanelBridge }).a2a;

// One subscription for every watch; each watch id goes to its own listener.
const watchListeners = new Map<string, (refs: boolean) => void>();
let watchSubscribed = false;
function watchRepo(dir: string, onChange: (refs: boolean) => void) {
  if (!watchSubscribed) { watchSubscribed = true; bridge().onGitChanged(change => watchListeners.get(change.id)?.(change.refs)); }
  let id: string | null = null, stopped = false;
  void bridge().gitWatch(dir).then(value => {
    if (stopped) { void bridge().gitUnwatch(value); return; }
    id = value; watchListeners.set(value, onChange);
  }, error => console.error('Git watch failed:', String(error)));
  return () => { stopped = true; if (id) { watchListeners.delete(id); void bridge().gitUnwatch(id); } };
}

const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');
// Lane N's color: the theme's ANSI blue, red, green, magenta, yellow, cyan, then their bright forms.
const laneColors = (dark: boolean) => {
  const p = terminalPalettes[dark ? 'dark' : 'light'];
  return Object.fromEntries([p.blue, p.red, p.green, p.magenta, p.yellow, p.cyan, p.brightBlue, p.brightRed, p.brightGreen,
    p.brightMagenta, p.brightYellow, p.brightCyan].map((color, index) => ['--lane-' + index, color]));
};
const widthKey = 'enchanted.panelWidth', openKey = 'enchanted.panelOpen', panelKey = 'enchanted.panel';
const DEFAULT_WIDTH = 520;
const stored = (key: string) => { try { return localStorage.getItem(key); } catch { return null; } };
const store = (key: string, value: string) => { try { localStorage.setItem(key, value); } catch { /* Per-viewer convenience only. */ } };
export const initialDockOpen = () => stored(openKey) === 'true';
export const saveDockOpen = (open: boolean) => store(openKey, String(open));
const tilde = (path: string, home: string) => path === home || path.startsWith(home + '/') ? '~' + path.slice(home.length) : path;

export function PanelDock({ focusedPane, home, onClose }: { focusedPane: string | null; home: string; onClose: () => void }) {
  const [width, setWidth] = useState(() => Number(stored(widthKey)) || DEFAULT_WIDTH);
  const [active, setActive] = useState(() => panels.some(panel => panel.id === stored(panelKey)) ? stored(panelKey)! : panels[0]!.id);
  const [followed, setFollowed] = useState<Omit<Followed, 'source'> & { source: 'pane' | 'project' } | null>(null);
  const [followError, setFollowError] = useState<string | null>(null);
  const [pinned, setPinned] = useState<Followed | null>(null);
  const [dark, setDark] = useState(darkQuery.matches);
  const [notice, setNotice] = useState<{ text: string; level: 'info' | 'error'; at: number } | null>(null);
  useEffect(() => { const change = () => setDark(darkQuery.matches); darkQuery.addEventListener('change', change); return () => darkQuery.removeEventListener('change', change); }, []);
  useEffect(() => store(widthKey, String(width)), [width]);
  useEffect(() => store(panelKey, active), [active]);
  // A shell can cd at any time; the focused pane's directory is read again every 2 s.
  useEffect(() => {
    let stopped = false;
    const read = () => bridge().panelDirectory(focusedPane).then(value => {
      if (stopped) return;
      setFollowError(null);
      setFollowed(previous => previous && previous.dir === value.dir && previous.source === value.source && previous.managed === value.managed &&
        previous.pane === value.pane ? previous : value);
    }, error => { if (!stopped) setFollowError('读不到跟随的目录：' + String(error)); });
    void read();
    const timer = setInterval(read, 2000);
    return () => { stopped = true; clearInterval(timer); };
  }, [focusedPane]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(value => value === notice ? null : value), notice.level === 'error' ? 8000 : 3000);
    return () => clearTimeout(timer);
  }, [notice]);
  const directory: Followed = pinned ?? (followed ? { ...followed } : { dir: null, source: 'project', managed: false, role: null, pane: null });
  const host = useMemo<PanelHost>(() => ({
    directory, dark,
    git: { repo: dir => bridge().gitRepo(dir), read: (dir, argv, encoding) => bridge().gitRead(dir, argv, encoding),
      action: (dir, action, values) => bridge().gitAction(dir, action, values),
      scan: (root, depth, tags) => bridge().gitScan(root, depth, tags), watch: watchRepo },
    openFile: path => bridge().openPath(path),
    notify: (text, level = 'info') => setNotice({ text, level, at: Date.now() }),
    showPanel: id => { if (panels.some(panel => panel.id === id)) setActive(id); },
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [directory.dir, directory.source, directory.managed, directory.pane, dark]);
  const drag = useRef<{ x: number; width: number } | null>(null);
  const onPointerMove = useCallback((event: PointerEvent) => {
    if (!drag.current) return;
    setWidth(Math.max(320, Math.min(window.innerWidth - 420, drag.current.width + drag.current.x - event.clientX)));
  }, []);
  const stopDrag = useCallback(() => { drag.current = null; window.removeEventListener('pointermove', onPointerMove); }, [onPointerMove]);
  const panel = panels.find(value => value.id === active)!;
  const sourceText = directory.source === 'pinned' ? '已固定' : directory.source === 'pane' ? '跟随聚焦窗格' : '项目主目录';
  return <aside className="panel-dock" aria-label="侧边面板" style={{ width, ...laneColors(dark) }} data-panel-dock data-followed-dir={directory.dir ?? ''}
      data-follow-source={directory.source} data-managed={directory.managed}>
    <div className="panel-resizer" role="separator" aria-orientation="vertical" aria-label="拖动调整面板宽度，双击复原" title="拖动调整宽度，双击复原"
      onPointerDown={event => { drag.current = { x: event.clientX, width }; window.addEventListener('pointermove', onPointerMove); window.addEventListener('pointerup', stopDrag, { once: true }); }}
      onDoubleClick={() => setWidth(DEFAULT_WIDTH)} />
    <header className="panel-dock-header">
      <nav className="panel-tabs" aria-label="面板">
        {panels.map(value => <button key={value.id} data-panel-tab={value.id} aria-pressed={value.id === active} onClick={() => setActive(value.id)}>
          {value.icon}<span>{value.title}</span></button>)}
      </nav>
      <button className="icon-button" aria-label="关闭面板" title="关闭面板" onClick={onClose}>✕</button>
    </header>
    <div className="panel-follow" data-panel-follow>
      <span className="panel-follow-source">{sourceText}</span>
      <span className="panel-follow-dir" title={directory.dir ?? ''}>{directory.dir ? tilde(directory.dir, home) : '没有目录'}</span>
      {pinned ? <button className="text-button" data-panel-unpin onClick={() => setPinned(null)}>取消固定</button>
        : <button className="text-button" data-panel-pin disabled={!directory.dir} onClick={() => setPinned({ ...directory, source: 'pinned' })}>固定</button>}
    </div>
    {followError && !pinned && <p className="panel-error" role="alert">{followError}</p>}
    {notice && <p className={'panel-notice' + (notice.level === 'error' ? ' error' : '')} role={notice.level === 'error' ? 'alert' : 'status'} data-panel-notice={notice.level}>{notice.text}</p>}
    <div className="panel-body">
      {directory.dir ? <panel.Component key={panel.id} host={host} /> : <p className="panel-empty">没有可跟随的目录：先打开项目或聚焦一个终端。</p>}
    </div>
  </aside>;
}
