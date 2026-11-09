// T-250: the "改动" panel, after herdr-gitview (https://github.com/ChmaraX/herdr-gitview). MIT License.
// Copyright (c) 2026 Adam Chmara. Its diff view is adapted from herdr-reviewr (MIT). Only the behaviour is followed:
// grouped file list (conflicts, staged, unstaged; flat or tree) with +/- counts, stage / unstage / discard / commit,
// a diff with syntax colors, word emphasis and folded context, Markdown and image previews, the uncommitted / base
// scopes with this branch's history, and review notes sent to the focused terminal as a paste.
import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactElement } from 'react';
import type { PanelHost, RepoInfo } from './PanelDock';
import { buildTree, foldRows, IMAGE, imageType, inlineSpans, languageOf, markdownBlocks, notesText, parseDiff, tokenize, totals,
  type DiffLine, type DiffSide, type Group, type Note, type TreeNode } from './changesModel';

const READ_ONLY_REASON = '这是门禁管理的任务 worktree：只能查看。门禁保护它的 Git 元数据，暂存、丢弃、提交算人工介入。';
const GROUP_TITLES: Record<string, string> = { conflict: '冲突', staged: '已暂存', unstaged: '未暂存', range: '与基线的差异', commit: '这个提交的改动' };
type ItemGroup = Group | 'range' | 'commit';
type Item = { key: string; path: string; group: ItemGroup; code: string; untracked: boolean; add: number | null; del: number | null; binary: boolean };
type Commit = { hash: string; short: string; subject: string; author: string; time: number };
type BaseInfo = { head: string | null; current: string | null; base: { name: string; mergeBase: string; distance: number } | null; candidates: string[] };
type Shown = { key: string; path: string; loading: boolean; error?: string; lines?: DiffLine[]; before?: string | null; after?: string | null; text?: string | null };
const keyOf = (group: string, path: string) => group + '\0' + path;
const stored = (key: string) => { try { return localStorage.getItem(key); } catch { return null; } };
const store = (key: string, value: string | null) => { try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); } catch { /* Per-viewer convenience only. */ } };
const utf8 = (base64: string) => new TextDecoder().decode(Uint8Array.from(atob(base64), c => c.charCodeAt(0)));

export function ChangesPanel({ host }: { host: PanelHost }) {
  const dir = host.directory.dir!;
  const [repo, setRepo] = useState<RepoInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let stopped = false;
    setRepo(null); setError(null);
    host.git.repo(dir).then(value => { if (!stopped) setRepo(value); }, failure => { if (!stopped) setError(String(failure)); });
    return () => { stopped = true; };
  }, [dir]);
  if (error) return <p className="panel-error" role="alert">{error}</p>;
  if (!repo) return <p className="panel-empty" role="status">正在读取…</p>;
  if (!repo.top) return <p className="panel-empty" data-changes-none>这个目录不是 Git 仓库。</p>;
  return <ChangesView key={repo.top} host={host} repo={repo} />;
}

function ChangesView({ host, repo }: { host: PanelHost; repo: RepoInfo }) {
  const top = repo.top!;
  const readOnly = repo.managed || host.directory.managed;
  const pinKey = 'enchanted.changes.base:' + top;
  const [scope, setScope] = useState<'worktree' | 'base'>('worktree');
  const [tree, setTree] = useState(() => stored('enchanted.changes.tree') === 'true');
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [items, setItems] = useState<Item[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [baseInfo, setBaseInfo] = useState<BaseInfo | null>(null);
  const [pinned, setPinned] = useState<string | null>(() => stored(pinKey));
  const [mergeBase, setMergeBase] = useState<string | null>(null);
  const [history, setHistory] = useState<Commit[] | null>(null);
  const [commit, setCommit] = useState<{ hash: string; short: string; subject: string; parent: string | null } | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [shown, setShown] = useState<Shown | null>(null);
  const [preview, setPreview] = useState(false);
  const [message, setMessage] = useState('');
  const [confirm, setConfirm] = useState<Item[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [help, setHelp] = useState(false);
  const [notes, setNotes] = useState<Note[]>([]);
  const [draft, setDraft] = useState<(Omit<Note, 'text'> & { text: string }) | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => store('enchanted.changes.tree', String(tree)), [tree]);
  useEffect(() => store(pinKey, pinned), [pinned]);

  const baseName = pinned ?? baseInfo?.base?.name ?? null;
  const generation = useRef(0);
  const ignoreUntil = useRef(0);
  const load = useCallback(async () => {
    const mine = ++generation.current;
    try {
      let next: Item[];
      if (commit) {
        const value = await host.changes.read(top, { kind: 'commit', hash: commit.hash });
        next = value.files.map((file: any) => ({ key: keyOf('commit', file.path), path: file.path, group: 'commit', code: file.code, untracked: false, add: file.add, del: file.del, binary: file.binary }));
      } else if (scope === 'base') {
        if (!baseName) { if (mine === generation.current) { setItems([]); setMergeBase(null); setError(null); } return; }
        const value = await host.changes.read(top, { kind: 'range', base: baseName });
        if (mine !== generation.current) return;
        setMergeBase(value.mergeBase);
        next = value.files.map((file: any) => ({ key: keyOf('range', file.path), path: file.path, group: 'range', code: file.code, untracked: false, add: file.add, del: file.del, binary: file.binary }));
      } else {
        const value = await host.changes.read(top, { kind: 'status' });
        next = value.entries.map((entry: any) => ({ ...entry, key: keyOf(entry.group, entry.path) }));
      }
      if (mine !== generation.current) return;
      setItems(next); setError(null);
    } catch (failure) { if (mine === generation.current) setError('读不到改动：' + String(failure)); }
  }, [top, scope, baseName, commit]);
  const loadRef = useRef(load);
  loadRef.current = load;
  useEffect(() => { void load(); }, [load]);
  const loadBase = useCallback(() => host.changes.read(top, { kind: 'base' }).then(setBaseInfo, failure => console.error('Base detection failed:', String(failure))), [top]);
  useEffect(() => { void loadBase(); }, [loadBase]);
  const loadHistory = useCallback(() => host.changes.read(top, { kind: 'log', base: baseName }).then(value => setHistory(value.commits),
    failure => host.notify('读不到提交历史：' + String(failure), 'error')), [top, baseName]);
  const [historyOpen, setHistoryOpen] = useState(false);
  useEffect(() => { if (historyOpen) void loadHistory(); }, [historyOpen, loadHistory]);
  // File events reload the list; the burst our own write causes is skipped (that write reloads at once).
  useEffect(() => {
    const stop = host.git.watch(top, refs => {
      if (Date.now() < ignoreUntil.current) return;
      void loadRef.current();
      if (refs) void loadBase();
    });
    return stop;
  }, [top, loadBase]);

  // The visible rows, in the order j/k walk them.
  const groups = useMemo(() => {
    if (!items) return [];
    const order: ItemGroup[] = commit ? ['commit'] : scope === 'base' ? ['range'] : ['conflict', 'staged', 'unstaged'];
    return order.map(group => ({ group, items: items.filter(item => item.group === group).sort((a, b) => a.path.localeCompare(b.path)) }))
      .filter(entry => entry.items.length);
  }, [items, scope, commit]);
  const visible = useMemo(() => {
    const out: Item[] = [];
    for (const { group, items: list } of groups) {
      if (!tree) { out.push(...list); continue; }
      const walk = (nodes: TreeNode[]) => nodes.forEach(node => {
        if (node.entry) out.push(node.entry as unknown as Item);
        else if (!collapsed.has(group + ':' + node.path)) walk(node.children);
      });
      walk(buildTree(list as any));
    }
    return out;
  }, [groups, tree, collapsed]);
  const current = visible.find(item => item.key === selected) ?? null;
  useEffect(() => {
    if (!items) return;
    if (!selected || !items.some(item => item.key === selected)) setSelected(visible[0]?.key ?? null);
  }, [items, visible]);

  // The diff (or image / Markdown) of the selected file. A late answer for an older selection is dropped.
  const diffGeneration = useRef(0);
  const sideOf = (item: Item): DiffSide => item.group === 'range' ? { kind: 'range', base: mergeBase! }
    : item.group === 'commit' ? { kind: 'commit', hash: commit!.hash, parent: commit!.parent }
    : item.group === 'unstaged' && item.untracked ? { kind: 'untracked' } : { kind: item.group as 'staged' | 'unstaged' | 'conflict' };
  const showItem = useCallback(async (item: Item | null) => {
    const mine = ++diffGeneration.current;
    if (!item) { setShown(null); return; }
    setShown(previous => previous?.key === item.key ? { ...previous, loading: true } : { key: item.key, path: item.path, loading: true });
    try {
      const side = sideOf(item);
      const image = IMAGE.test(item.path), markdown = languageOf(item.path) === 'md';
      const versions = image || markdown ? await readVersions(item, side) : null;
      const lines = image ? [] : parseDiff((await host.changes.read(top, { kind: 'diff', path: item.path, side })).text);
      if (mine !== diffGeneration.current) return;
      setShown({ key: item.key, path: item.path, loading: false, lines, before: versions?.before, after: versions?.after,
        text: markdown && versions?.after ? utf8(versions.after) : null });
    } catch (failure) {
      if (mine === diffGeneration.current) setShown({ key: item.key, path: item.path, loading: false, error: String(failure) });
    }
  }, [top, mergeBase, commit]);
  const readVersions = async (item: Item, side: DiffSide) => {
    const blob = async (rev: string | null) => rev ? (await host.changes.read(top, { kind: 'blob', path: item.path, rev })).base64 as string | null : null;
    const worktree = async () => (await host.changes.read(top, { kind: 'worktree', path: item.path })).base64 as string | null;
    switch (side.kind) {
      case 'staged': return { before: await blob('HEAD'), after: await blob(':0') };
      case 'unstaged': case 'conflict': return { before: await blob(':0'), after: await worktree() };
      case 'untracked': return { before: null, after: await worktree() };
      case 'range': return { before: await blob(side.base), after: await worktree() };
      case 'commit': return { before: await blob(side.parent), after: await blob(side.hash) };
    }
  };
  // Reload the diff when the selection changes, and when the list was reloaded (the file may have changed).
  useEffect(() => { void showItem(current); setDraft(null); }, [current?.key, items]);

  const refresh = async () => { ignoreUntil.current = Date.now() + 800; await load(); };
  const act = async (action: Record<string, unknown>, done: string) => {
    if (readOnly) { host.notify(READ_ONLY_REASON, 'error'); return false; }
    setBusy(true);
    try {
      ignoreUntil.current = Date.now() + 800;
      await host.changes.action(top, action);
      host.notify(done);
      await refresh();
      return true;
    } catch (failure) { host.notify(String(failure).replace(/^Error: /, ''), 'error'); return false; } finally { setBusy(false); }
  };
  const entriesOf = (list: Item[]) => list.map(item => ({ path: item.path, group: item.group, untracked: item.untracked }));
  const writable = !readOnly && scope === 'worktree' && !commit;
  const stage = (item = current) => { if (item && writable && item.group !== 'staged') void act({ type: 'stage', entries: entriesOf([item]) }, '已暂存 ' + item.path); };
  const unstage = (item = current) => { if (item && writable && item.group === 'staged') void act({ type: 'unstage', entries: entriesOf([item]) }, '已取消暂存 ' + item.path); };
  const discard = (item = current) => { if (item && writable && item.group !== 'conflict') setConfirm([item]); };
  const doCommit = async () => {
    if (!message.trim() || busy) return;
    const stagedCount = items?.filter(item => item.group === 'staged').length ?? 0;
    if (await act({ type: 'commit', message }, stagedCount ? '已提交' : '已暂存全部改动并提交')) { setMessage(''); if (historyOpen) void loadHistory(); }
  };
  const sendNotes = async () => {
    if (!notes.length) return;
    try {
      await host.sendToPane(notesText(notes));
      host.notify(`已把 ${notes.length} 条备注发到聚焦的终端（没有按回车，在终端里确认后再发送）`);
      setNotes([]);
    } catch (failure) { host.notify(String(failure).replace(/^Error: /, ''), 'error'); }
  };

  const move = (step: number) => {
    if (!visible.length) return;
    const index = visible.findIndex(item => item.key === selected);
    const next = visible[Math.max(0, Math.min(visible.length - 1, (index < 0 ? 0 : index) + step))]!;
    setSelected(next.key);
    rootRef.current?.querySelector(`[data-change-key="${CSS.escape(next.key)}"]`)?.scrollIntoView({ block: 'nearest' });
  };
  const onKey = (event: ReactKeyboardEvent) => {
    const target = event.target as HTMLElement;
    if (target.closest('textarea, input, select') || event.metaKey || event.ctrlKey || event.altKey) return;
    if (confirm) return;
    const handled = ({
      j: () => move(1), ArrowDown: () => move(1), k: () => move(-1), ArrowUp: () => move(-1), J: () => move(1), K: () => move(-1),
      s: () => stage(), u: () => unstage(), x: () => discard(), c: () => messageRef.current?.focus(),
      t: () => setTree(value => !value), w: () => { setCommit(null); setScope(value => value === 'worktree' ? 'base' : 'worktree'); },
      l: () => setHistoryOpen(value => !value), '?': () => setHelp(value => !value), Escape: () => { if (help) setHelp(false); else if (draft) setDraft(null); else if (commit) setCommit(null); },
    } as Record<string, () => void>)[event.key];
    if (!handled) return;
    event.preventDefault();
    handled();
  };

  const total = totals(items ?? []);
  const toggleFolder = (id: string) => setCollapsed(value => { const next = new Set(value); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  const row = (item: Item, depth = 0, name = item.path) => <div key={item.key} role="option" aria-selected={item.key === selected} tabIndex={-1}
      className={'change-row' + (item.key === selected ? ' selected' : '')} style={{ paddingLeft: 10 + depth * 14 }}
      data-change-key={item.key} data-change-path={item.path} data-change-group={item.group} data-change-code={item.code}
      data-add={item.binary ? '-' : item.add ?? ''} data-del={item.binary ? '-' : item.del ?? ''}
      onClick={() => { setSelected(item.key); rootRef.current?.focus(); }}
      onDoubleClick={() => void host.openFile(top + '/' + item.path).catch(failure => host.notify('打不开：' + String(failure), 'error'))}>
    <span className={'change-code code-' + item.code}>{item.code}</span>
    <span className="change-name" title={item.path}>{name}</span>
    <span className="file-stat">{item.binary ? <span className="muted">二进制</span> : item.add === null ? null
      : <><span className="add">+{item.add}</span> <span className="del">-{item.del}</span></>}</span>
    {writable && <span className="change-actions">
      {item.group !== 'staged' && <button className="text-button" data-changes-stage title="暂存（s）" disabled={busy} onClick={event => { event.stopPropagation(); stage(item); }}>暂存</button>}
      {item.group === 'staged' && <button className="text-button" data-changes-unstage title="取消暂存（u）" disabled={busy} onClick={event => { event.stopPropagation(); unstage(item); }}>取消</button>}
      {item.group !== 'conflict' && <button className="text-button danger" data-changes-discard title="丢弃（x）" disabled={busy} onClick={event => { event.stopPropagation(); discard(item); }}>丢弃</button>}
    </span>}
  </div>;
  const treeRows = (group: ItemGroup, nodes: TreeNode[], depth: number): ReactElement[] => nodes.flatMap(node => {
    if (node.entry) return [row(node.entry as unknown as Item, depth, node.name)];
    const id = group + ':' + node.path, closed = collapsed.has(id);
    return [<button key={id} className="change-folder" style={{ paddingLeft: 10 + depth * 14 }} data-change-folder={node.path} aria-expanded={!closed}
      onClick={() => toggleFolder(id)}>{closed ? '▸' : '▾'} {node.name}/</button>, ...(closed ? [] : treeRows(group, node.children, depth + 1))];
  });

  const stagedCount = items?.filter(item => item.group === 'staged').length ?? 0;
  return <div className="changes" ref={rootRef} tabIndex={0} onKeyDown={onKey} data-changes data-repo={top} data-read-only={readOnly}
      data-scope={commit ? 'commit' : scope} data-base={baseName ?? ''} data-merge-base={mergeBase ?? ''}>
    <div className="git-toolbar">
      <div className="segmented" role="group" aria-label="范围">
        <button aria-pressed={scope === 'worktree' && !commit} data-changes-scope="worktree" onClick={() => { setCommit(null); setScope('worktree'); }}>未提交</button>
        <button aria-pressed={scope === 'base' && !commit} data-changes-scope="base" onClick={() => { setCommit(null); setScope('base'); }}>与基线比较</button>
      </div>
      {scope === 'base' && <label className="changes-base">基线
        <select data-base-select value={baseName ?? ''} onChange={event => setPinned(event.target.value || null)}>
          {!baseName && <option value="">没有找到</option>}
          {baseInfo?.base && <option value={baseInfo.base.name}>{baseInfo.base.name}（自动）</option>}
          {(baseInfo?.candidates ?? []).filter(name => name !== baseInfo?.base?.name).map(name => <option key={name} value={name}>{name}</option>)}
        </select>
        {pinned && <button className="text-button" data-base-unpin onClick={() => setPinned(null)}>取消固定</button>}
      </label>}
      <button className="text-button" aria-pressed={tree} data-changes-tree onClick={() => setTree(value => !value)} title="平铺或目录树（t）">{tree ? '目录树' : '平铺'}</button>
      <button className="text-button" aria-pressed={historyOpen} data-changes-history onClick={() => setHistoryOpen(value => !value)} title="本分支的提交（l）">历史</button>
      <button className="text-button" onClick={() => setHelp(value => !value)} title="全部按键（?）">?</button>
      <span className="changes-total" data-changes-total-add={total.add} data-changes-total-del={total.del}>
        {items ? <>{items.length} 个文件 <span className="add">+{total.add}</span> <span className="del">-{total.del}</span></> : null}</span>
    </div>
    {readOnly && <p className="panel-readonly" data-changes-readonly>{READ_ONLY_REASON}</p>}
    {error && <p className="panel-error" role="alert">{error}</p>}
    {help && <dl className="changes-help" data-changes-help>
      {[['j / k、↑ / ↓', '上下移动，diff 跟着走'], ['J / K', '下一个 / 上一个文件'], ['s / u / x', '暂存 / 取消暂存 / 丢弃（先确认）'], ['c', '写提交说明（Enter 提交，Shift+Enter 换行）'],
        ['t', '平铺或目录树'], ['w', '切换范围：未提交 / 与基线比较'], ['l', '本分支的提交历史'], ['?', '这份按键表'], ['Esc', '关闭备注、提交或这份表'],
        ['单击 / 双击', '选中 / 用系统默认编辑器打开'], ['在 diff 里拖选行', '写审阅备注']].map(([key, what]) => <div key={key}><dt>{key}</dt><dd>{what}</dd></div>)}
    </dl>}
    <div className="changes-main">
      <div className="changes-list" role="listbox" aria-label="改动的文件">
        {historyOpen && <section className="changes-history" data-changes-history-list>
          <h4>本分支的提交{baseName ? `（${baseName} 之后）` : ''}</h4>
          {history === null ? <p className="panel-empty">正在读取…</p> : !history.length ? <p className="panel-empty">没有提交。</p>
            : history.map(entry => <button key={entry.hash} className={'history-row' + (commit?.hash === entry.hash ? ' selected' : '')} data-history-hash={entry.hash}
              onClick={async () => {
                try {
                  const value = await host.changes.read(top, { kind: 'commit', hash: entry.hash });
                  setCommit({ hash: entry.hash, short: entry.short, subject: entry.subject, parent: value.parent });
                } catch (failure) { host.notify(String(failure), 'error'); }
              }}><code>{entry.short}</code> <span>{entry.subject}</span></button>)}
        </section>}
        {commit && <div className="changes-commit-head"><button className="text-button" onClick={() => setCommit(null)}>← 改动</button><code>{commit.short}</code> {commit.subject}</div>}
        {items === null ? <p className="panel-empty" role="status">正在读取…</p>
          : !groups.length ? <p className="panel-empty" data-changes-empty>{scope === 'base' && !baseName ? '没有找到基线分支。' : '没有改动。'}</p>
          : groups.map(({ group, items: list }) => <section key={group} className="change-group" data-changes-group={group}>
            <h4>{GROUP_TITLES[group]} <span className="muted">{list.length}</span></h4>
            {tree ? treeRows(group, buildTree(list as any), 0) : list.map(item => row(item))}
          </section>)}
      </div>
      <DiffView shown={shown} preview={preview} setPreview={setPreview} dark={host.dark} draft={draft} setDraft={setDraft}
        onNote={() => { if (draft?.text.trim()) { setNotes(value => [...value, draft]); setDraft(null); } }} />
    </div>
    {notes.length > 0 && <div className="changes-notes" data-changes-notes={notes.length}>
      <span>{notes.length} 条审阅备注</span>
      <button className="text-button" onClick={() => setNotes([])}>清空</button>
      <button className="primary-button" data-notes-send disabled={!host.directory.pane} title={host.directory.pane ? '发到聚焦的终端' : '先聚焦一个终端'} onClick={() => void sendNotes()}>发到聚焦的终端</button>
    </div>}
    {scope === 'worktree' && !commit && <div className="changes-commit">
      <textarea ref={messageRef} rows={2} value={message} disabled={readOnly || busy} data-changes-message
        placeholder={readOnly ? '只读' : stagedCount ? `提交 ${stagedCount} 个已暂存的文件（Enter 提交，Shift+Enter 换行）` : '没有已暂存的文件：提交时先暂存全部改动（Enter 提交）'}
        onChange={event => setMessage(event.target.value)}
        onKeyDown={event => {
          if (event.key === 'Escape') { (event.target as HTMLElement).blur(); rootRef.current?.focus(); return; }
          if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void doCommit(); }
        }} />
      <button className="primary-button" data-changes-commit disabled={readOnly || busy || !message.trim()} onClick={() => void doCommit()}>提交</button>
    </div>}
    {confirm && <div className="git-dialog-backdrop" onClick={() => setConfirm(null)}>
      <div className="git-dialog" role="dialog" aria-modal="true" data-changes-confirm onClick={event => event.stopPropagation()}>
        <h3>丢弃改动</h3>
        <p>丢弃 {confirm.map(item => item.path).join('、')} 的{confirm[0]!.group === 'staged' ? '已暂存和未暂存' : ''}改动？{confirm.some(item => item.untracked) ? '未跟踪的文件会被删除。' : ''}丢弃后不能恢复。</p>
        <footer>
          <button className="text-button" data-confirm-cancel autoFocus onClick={() => { setConfirm(null); rootRef.current?.focus(); }}>取消</button>
          <button className="danger-button" data-confirm-ok disabled={busy} onClick={async () => {
            const list = confirm; setConfirm(null);
            await act({ type: 'discard', entries: entriesOf(list) }, '已丢弃 ' + list.map(item => item.path).join('、'));
            rootRef.current?.focus();
          }}>丢弃</button>
        </footer>
      </div>
    </div>}
  </div>;
}

type Draft = (Omit<Note, 'text'> & { text: string }) | null;
function DiffView({ shown, preview, setPreview, dark, draft, setDraft, onNote }: { shown: Shown | null; preview: boolean; setPreview: (value: boolean) => void;
    dark: boolean; draft: Draft; setDraft: (value: Draft) => void; onNote: () => void }) {
  const [open, setOpen] = useState<Set<number>>(new Set());
  const [drag, setDrag] = useState<{ anchor: number; head: number } | null>(null);
  const dragging = useRef(false);
  useEffect(() => { setOpen(new Set()); setDrag(null); }, [shown?.key]);
  const lines = shown?.lines ?? [];
  const rows = useMemo(() => foldRows(lines, open), [lines, open]);
  const language = shown ? languageOf(shown.path) : null;
  const finish = () => {
    if (!dragging.current || !drag || !shown) return;
    dragging.current = false;
    const [a, b] = [Math.min(drag.anchor, drag.head), Math.max(drag.anchor, drag.head)];
    const chosen = lines.slice(a, b + 1).filter(line => line.kind === 'add' || line.kind === 'del' || line.kind === 'ctx');
    if (!chosen.length) { setDrag(null); return; }
    const side = chosen.every(line => line.kind === 'del') ? 'old' : 'new';
    const numbers = chosen.map(line => side === 'old' ? line.old : line.next).filter((n): n is number => n !== null);
    setDraft({ path: shown.path, side, from: Math.min(...numbers), to: Math.max(...numbers), quote: chosen.filter(line => side === 'old' || line.kind !== 'del').map(line => line.text), text: '' });
  };
  useEffect(() => {
    const up = () => finish();
    window.addEventListener('pointerup', up);
    return () => window.removeEventListener('pointerup', up);
  });
  if (!shown) return <div className="changes-diff"><p className="panel-empty">选一个文件看 diff。</p></div>;
  const image = IMAGE.test(shown.path);
  const inRange = (index: number) => drag && index >= Math.min(drag.anchor, drag.head) && index <= Math.max(drag.anchor, drag.head);
  const src = (base64: string | null | undefined) => base64 ? `data:${imageType(shown.path)};base64,${base64}` : null;
  return <div className="changes-diff" data-changes-diff={shown.path} data-diff-loading={shown.loading} data-theme-dark={dark}>
    <div className="git-diff-head"><code title={shown.path}>{shown.path}</code>
      {language === 'md' && shown.text !== null && <button className="text-button" aria-pressed={preview} data-diff-preview onClick={() => setPreview(!preview)}>{preview ? 'diff' : '预览'}</button>}
    </div>
    {shown.error ? <p className="panel-error" role="alert">{shown.error}</p>
      : image ? <div className="image-compare" data-image-compare>
        <figure><figcaption>改动前</figcaption>{src(shown.before) ? <img src={src(shown.before)!} alt="改动前" data-image-before /> : <p className="panel-empty">（没有）</p>}</figure>
        <figure><figcaption>改动后</figcaption>{src(shown.after) ? <img src={src(shown.after)!} alt="改动后" data-image-after /> : <p className="panel-empty">（已删除）</p>}</figure>
      </div>
      : preview && shown.text !== null && shown.text !== undefined ? <Markdown text={shown.text} />
      : !lines.length ? <p className="panel-empty">{shown.loading ? '正在读取 diff…' : '没有文本改动（可能是二进制文件或只改了权限）。'}</p>
      : <pre className="diff-lines changes-lines" onPointerLeave={() => undefined}>{rows.map(item => 'fold' in item
        ? <button key={'f' + item.fold} className="diff-fold" data-diff-fold={item.fold} onClick={() => setOpen(value => new Set(value).add(item.fold))}>… 展开 {item.count} 行未改动的内容</button>
        : <div key={item.index} data-diff-line={item.index} data-kind={item.line.kind}
            className={'diff-line ' + item.line.kind + (inRange(item.index) ? ' picked' : '')}
            onPointerDown={event => { if (event.button !== 0 || item.line.kind === 'hunk') return; event.preventDefault(); dragging.current = true; setDrag({ anchor: item.index, head: item.index }); }}
            onPointerEnter={() => { if (dragging.current) setDrag(value => value && { ...value, head: item.index }); }}>
          <span className="diff-number">{item.line.old ?? ''}</span><span className="diff-number">{item.line.next ?? ''}</span>
          <span className="diff-sign">{item.line.kind === 'add' ? '+' : item.line.kind === 'del' ? '-' : ' '}</span>
          <span className="diff-text">{item.line.kind === 'hunk' || item.line.kind === 'meta' ? item.line.text : <Code line={item.line} language={language} />}</span>
        </div>)}</pre>}
    {draft && <div className="note-draft" data-note-draft>
      <span className="muted">{draft.path}:{draft.from === draft.to ? draft.from : `${draft.from}-${draft.to}`}{draft.side === 'old' ? '（改动前）' : ''}</span>
      <textarea autoFocus rows={2} value={draft.text} data-note-text placeholder="写备注（Enter 保存，Esc 取消）" onChange={event => setDraft({ ...draft, text: event.target.value })}
        onKeyDown={event => {
          if (event.key === 'Escape') { setDraft(null); setDrag(null); }
          if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); onNote(); setDrag(null); }
        }} />
      <button className="text-button" data-note-save disabled={!draft.text.trim()} onClick={() => { onNote(); setDrag(null); }}>保存备注</button>
    </div>}
  </div>;
}

// Syntax colors per token; the word emphasis of a changed line is drawn over them.
function Code({ line, language }: { line: DiffLine; language: string | null }) {
  const tokens = tokenize(line.text, language);
  const [start, end] = line.spans ?? [-1, -1];
  const out: ReactElement[] = [];
  let at = 0;
  tokens.forEach((token, t) => {
    const pieces: [string, boolean][] = [];
    for (let i = 0; i < token.text.length;) {
      const marked = at + i >= start && at + i < end;
      let j = i; while (j < token.text.length && (at + j >= start && at + j < end) === marked) j++;
      pieces.push([token.text.slice(i, j), marked]); i = j;
    }
    pieces.forEach(([text, marked], p) => out.push(<span key={t + ':' + p} className={'tok-' + token.kind + (marked ? ' word' : '')}>{text}</span>));
    at += token.text.length;
  });
  return <>{out}</>;
}

function Markdown({ text }: { text: string }) {
  const blocks = markdownBlocks(text);
  const inline = (value: string) => inlineSpans(value).map((span, i) => span.kind === 'code' ? <code key={i}>{span.text}</code>
    : span.kind === 'strong' ? <strong key={i}>{span.text}</strong> : span.kind === 'em' ? <em key={i}>{span.text}</em>
    : span.kind === 'link' ? <u key={i}>{span.text}</u> : <span key={i}>{span.text}</span>);
  return <article className="markdown-preview" data-markdown-preview>{blocks.map((block, i) => {
    switch (block.kind) {
      case 'h': { const H = ('h' + Math.min(6, block.level)) as 'h1'; return <H key={i}>{inline(block.text)}</H>; }
      case 'p': return <p key={i}>{inline(block.text)}</p>;
      case 'li': return <div key={i} className="md-li">{block.ordered ? '·' : '•'} {inline(block.text)}</div>;
      case 'quote': return <blockquote key={i}>{inline(block.text)}</blockquote>;
      case 'code': return <pre key={i}><code>{block.text}</code></pre>;
      case 'hr': return <hr key={i} />;
    }
  })}</article>;
}
