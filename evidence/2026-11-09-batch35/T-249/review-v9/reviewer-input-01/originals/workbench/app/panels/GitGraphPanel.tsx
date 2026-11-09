// T-249: the Git graph panel, after herdr-git-graph (https://github.com/rabeeh-ta/herdr-git-graph).
// MIT License. Copyright (c) 2026 Rabeeh T A. The full notice is in gitGraphModel.ts.
// A commit table with lanes, the uncommitted row dashed to HEAD, commit details and diffs, the right-click menus with
// a confirmation before every repository change, and the Manygit list when the followed directory is not a repository.
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type Dispatch, type SetStateAction, type MouseEvent as ReactMouseEvent } from 'react';
import { bridge, type PanelHost, type RepoInfo } from './PanelDock';
import { DETAIL_FORMAT, DEPTH, diffArgs, diffRows, dialogFor, fileArgs, initialValues, joinFiles, labelsOf, LANE,
  menuFor, PAD, PAGE, parseDetail, parseRepoStatus, readGraph, readStatus, REPO_STATUS, ROW, syncOf, UNCOMMITTED, validate,
  type Action, type Commit, type DiffRow, type FileChange, type Graph, type MenuItem, type RepoStatus, type Segment, type Target } from './gitGraphModel';

const columnDefaults = { date: 128, author: 120, hash: 76 };
type Columns = typeof columnDefaults;
type FileDiff = { path: string; rows: DiffRow[] | null; text: string };
const columnsKey = 'enchanted.gitGraph.columns';
const readColumns = (): Columns => { try { return { ...columnDefaults, ...JSON.parse(localStorage.getItem(columnsKey) ?? '{}') }; } catch { return columnDefaults; } };
const dateText = (seconds: number | null) => seconds === null ? '' : new Date(seconds * 1000).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
const laneX = (lane: number) => PAD + lane * LANE + LANE / 2;
const READ_ONLY_REASON = '这是门禁管理的任务 worktree：Git 图只读。门禁保护它的 Git 元数据，直接改动算人工介入。';

function check(result: { code: number | null; stdout: string; stderr: string }) {
  if (result.code !== 0) throw new Error((result.stderr || result.stdout).trim() || `git 退出码 ${result.code}`);
  return result.stdout;
}

export function GitGraphPanel({ host }: { host: PanelHost }) {
  const followed = host.directory.dir!;
  // A repository opened from the Manygit list, until the user goes back.
  const [opened, setOpened] = useState<string | null>(null);
  useEffect(() => setOpened(null), [followed]);
  const [repo, setRepo] = useState<RepoInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const target = opened ?? followed;
  useEffect(() => {
    let stopped = false;
    setRepo(null); setError(null);
    host.git.repo(target).then(value => { if (!stopped) setRepo(value); }, failure => { if (!stopped) setError(String(failure)); });
    return () => { stopped = true; };
  }, [target]);
  if (error) return <p className="panel-error" role="alert">{error}</p>;
  if (!repo) return <p className="panel-empty" role="status">正在读取…</p>;
  if (!repo.top) return <Manygit host={host} root={repo.dir} onOpen={setOpened} />;
  return <GraphView key={repo.top} host={host} repo={repo} onBack={opened ? () => setOpened(null) : null} />;
}

function GraphView({ host, repo, onBack }: { host: PanelHost; repo: RepoInfo; onBack: (() => void) | null }) {
  const top = repo.top!;
  const readOnly = repo.managed || host.directory.managed;
  const [all, setAll] = useState(true);
  const [remotes, setRemotes] = useState(true);
  const [limit, setLimit] = useState(PAGE);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [menu, setMenu] = useState<{ x: number; y: number; items: MenuItem[] } | null>(null);
  const [dialog, setDialog] = useState<{ action: Action; values: Record<string, any>; error: string | null; busy: boolean } | null>(null);
  const [diff, setDiff] = useState<FileDiff | null>(null);
  const [columns, setColumns] = useState<Columns>(readColumns);
  const [panelWidth, setPanelWidth] = useState(600);
  const rootRef = useRef<HTMLDivElement>(null);
  useEffect(() => { try { localStorage.setItem(columnsKey, JSON.stringify(columns)); } catch { /* Per-viewer convenience only. */ } }, [columns]);
  useLayoutEffect(() => {
    const element = rootRef.current;
    if (!element) return;
    const observer = new ResizeObserver(() => setPanelWidth(element.clientWidth));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const generation = useRef(0);
  const load = useCallback(async () => {
    const mine = ++generation.current;
    try {
      const next = await readGraph(argv => host.git.read(top, argv), { all, remotes, limit });
      if (mine !== generation.current) return;
      setGraph(next);
      setError(null);
    } catch (failure) { if (mine === generation.current) setError('读不到提交历史：' + String(failure)); }
  }, [top, all, remotes, limit]);
  const loadRef = useRef(load);
  loadRef.current = load;
  useEffect(() => { void load(); }, [load]);
  // Ref changes reload everything; other changes only the status, at most every 1.5 s. A full read every 15 s as well.
  const graphRef = useRef(graph);
  graphRef.current = graph;
  const loadStatus = useCallback(async () => {
    const current = graphRef.current, mine = generation.current;
    if (!current) return;
    try {
      const next = await readStatus(argv => host.git.read(top, argv), current);
      if (mine === generation.current && graphRef.current === current) setGraph(next);
    } catch (failure) { console.error('Git status refresh failed:', String(failure)); }
  }, [top]);
  useEffect(() => {
    let last = 0, pending: ReturnType<typeof setTimeout> | null = null;
    const statusOnly = () => {
      const wait = Math.max(0, last + 1500 - Date.now());
      if (pending) return;
      pending = setTimeout(() => { pending = null; last = Date.now(); void loadStatus(); }, wait);
    };
    const stop = host.git.watch(top, refs => { if (refs) { last = Date.now(); void loadRef.current(); } else statusOnly(); });
    const poll = setInterval(() => void loadRef.current(), 15000);
    return () => { stop(); clearInterval(poll); if (pending) clearTimeout(pending); };
  }, [top, loadStatus]);
  // Esc closes the menu or dialog, then the diff, then the details.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape' || !rootRef.current?.contains(document.activeElement) && document.activeElement !== document.body) return;
      if (menu) setMenu(null); else if (dialog) setDialog(null); else if (diff) setDiff(null); else if (selected) setSelected(null); else return;
      event.preventDefault();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [menu, dialog, diff, selected]);
  const openMenu = (event: ReactMouseEvent, target: Target) => {
    event.preventDefault(); event.stopPropagation();
    if (!graph) return;
    setMenu({ x: Math.min(event.clientX, window.innerWidth - 250), y: Math.min(event.clientY, window.innerHeight - 320), items: menuFor(target, graph.ctx) });
  };
  // The repository's own menu (fetch, pull, push, commit, stash…), as on a Manygit row.
  const openRepoMenu = async (event: ReactMouseEvent) => {
    event.preventDefault(); event.stopPropagation();
    if (!graph) return;
    const x = Math.min(event.clientX, window.innerWidth - 250), y = Math.min(event.clientY, window.innerHeight - 320);
    try {
      const status = parseRepoStatus(check(await host.git.read(top, REPO_STATUS)));
      status.hasRemote = graph.ctx.remotes.length > 0;
      setMenu({ x, y, items: menuFor({ kind: 'repo', status, path: top }, graph.ctx) });
    } catch (failure) { host.notify('读不到仓库状态：' + String(failure), 'error'); }
  };
  const choose = (action: Action) => {
    setMenu(null);
    if (action.type === 'copy') { void bridge().copyText(action.text).then(() => host.notify('已复制：' + action.text)); return; }
    if (action.type === 'showChanges') { host.showPanel('changes'); return; }
    if (readOnly) { host.notify(READ_ONLY_REASON, 'error'); return; }
    setDialog({ action, values: initialValues(action, graph!.ctx), error: null, busy: false });
  };
  const confirm = async () => {
    if (!dialog || !graph) return;
    const problem = validate(dialog.action, dialog.values, graph.ctx);
    if (problem) { setDialog({ ...dialog, error: problem }); return; }
    setDialog({ ...dialog, busy: true, error: null });
    try {
      const done = await host.git.action(top, dialog.action, dialog.values);
      setDialog(null);
      host.notify(done.text);
      await loadRef.current();
    } catch (failure) { setDialog(value => value && { ...value, busy: false, error: String(failure).replace(/^Error: (Error invoking remote method '[^']+': )?(Error: )?/, '') }); }
  };
  const checkoutLabel = (kind: string, name: string) => {
    if (!graph) return;
    if (kind === 'branch' && name !== graph.ctx.current) choose({ type: 'checkout', name });
    else if (kind === 'remote') {
      const branch = name.slice(name.indexOf('/') + 1);
      if (branch === graph.ctx.current) return;
      choose(graph.ctx.branches.includes(branch) ? { type: 'checkout', name: branch } : { type: 'checkoutRemote', name, remote: name.slice(0, name.indexOf('/')), branch });
    }
  };
  const showAuthor = panelWidth >= 560, showHash = panelWidth >= 680;
  const graphWidth = PAD * 2 + LANE * (graph?.width ?? 1);
  const template = `${graphWidth}px minmax(120px, 1fr) ${columns.date}px${showAuthor ? ` ${columns.author}px` : ''}${showHash ? ` ${columns.hash}px` : ''}`;
  const resizer = (column: keyof Columns) => <span className="column-resizer" role="separator" aria-label="拖动调整列宽，双击复原"
    onDoubleClick={() => setColumns(value => ({ ...value, [column]: columnDefaults[column] }))}
    onPointerDown={event => {
      const start = event.clientX, width = columns[column];
      const move = (moved: PointerEvent) => setColumns(value => ({ ...value, [column]: Math.max(48, Math.min(400, width - (moved.clientX - start))) }));
      window.addEventListener('pointermove', move);
      window.addEventListener('pointerup', () => window.removeEventListener('pointermove', move), { once: true });
    }} />;
  const selectedCommit = graph?.commits.find(commit => commit.hash === selected) ?? null;
  return <div className="git-graph" ref={rootRef} data-git-graph data-repo={top} data-read-only={readOnly} tabIndex={-1}>
    <div className="git-toolbar">
      {onBack && <button className="text-button" data-git-back onClick={onBack}>← 仓库列表</button>}
      <div className="segmented" role="group" aria-label="范围">
        <button aria-pressed={all} data-git-scope="all" onClick={() => setAll(true)}>所有分支</button>
        <button aria-pressed={!all} data-git-scope="current" onClick={() => setAll(false)}>当前分支</button>
      </div>
      <label className="git-check"><input type="checkbox" checked={remotes} disabled={!all} data-git-remotes onChange={event => setRemotes(event.target.checked)} />远程分支</label>
      <span className="git-branch" title={top}>{graph ? graph.ctx.current ?? '分离 HEAD' : ''}</span>
      <button className="text-button" data-git-refresh onClick={() => void load()}>刷新</button>
      <button className="text-button" data-git-repo-menu title="抓取、拉取、推送、提交、贮藏" onClick={event => void openRepoMenu(event)}>仓库操作…</button>
    </div>
    {readOnly && <p className="panel-readonly" role="note" data-git-readonly>{READ_ONLY_REASON}</p>}
    {error && <p className="panel-error" role="alert">{error}</p>}
    <div className="git-table" role="table" aria-label="提交" style={{ ['--git-columns' as any]: template }}>
      <div className="git-row git-head" role="row">
        <span role="columnheader">图</span><span role="columnheader">说明</span>
        <span role="columnheader">{resizer('date')}日期</span>
        {showAuthor && <span role="columnheader">{resizer('author')}作者</span>}
        {showHash && <span role="columnheader">{resizer('hash')}提交</span>}
      </div>
      <div className="git-rows" data-git-rows onScroll={event => {
        const element = event.currentTarget;
        if (graph?.more && element.scrollTop + element.clientHeight >= element.scrollHeight - ROW * 4) setLimit(value => value === graph.commits.length - (graph.changes ? 1 : 0) ? value + PAGE : value);
      }}>
        {graph?.commits.map((commit, index) => {
          const row = graph.rows[index]!;
          const labels = labelsOf(commit, remotes);
          return <div key={commit.hash} role="row" className={'git-row' + (commit.hash === selected ? ' selected' : '') + (commit.uncommitted ? ' uncommitted' : '')}
            data-commit-hash={commit.uncommitted ? UNCOMMITTED : commit.hash} data-uncommitted={commit.uncommitted || undefined}
            data-parents={commit.parents.join(' ')} data-lane={row.lane} data-segments={JSON.stringify(row.segments)}
            onClick={() => { setSelected(commit.hash); setDiff(null); }}
            onContextMenu={event => openMenu(event, commit.uncommitted ? { kind: 'uncommitted', staged: graph.staged > 0 } : { kind: 'commit', commit })}>
            <span role="cell" className="git-lanes"><Lanes row={row} width={graphWidth} commit={commit} /></span>
            <span role="cell" className="git-description">
              {labels.map(label => <span key={label.kind + label.parts[0]!.name} className={'git-label ' + label.kind + (label.head ? ' head' : '')}>
                {label.parts.map(part => <span key={part.name} className={'git-label-part ' + part.kind} data-ref-kind={part.kind} data-ref-name={part.name}
                  title={part.name + (part.kind === 'branch' || part.kind === 'remote' ? '（双击检出）' : '')}
                  onDoubleClick={event => { event.stopPropagation(); checkoutLabel(part.kind, part.name); }}
                  onContextMenu={event => part.kind === 'head' ? openMenu(event, { kind: 'commit', commit }) : openMenu(event, { kind: part.kind as 'branch' | 'remote' | 'tag', name: part.name })}>
                  {part.text}</span>)}
              </span>)}
              <span className="git-subject">{commit.subject}</span>
            </span>
            <span role="cell" className="git-date">{dateText(commit.time)}</span>
            {showAuthor && <span role="cell" className="git-author" title={commit.email}>{commit.author}</span>}
            {showHash && <span role="cell" className="git-hash">{commit.uncommitted ? '' : commit.hash.slice(0, 8)}</span>}
          </div>;
        })}
        {graph?.more && <button className="text-button git-more" data-git-more onClick={() => setLimit(value => value + PAGE)}>再加载 {PAGE} 条</button>}
        {graph && !graph.commits.length && <p className="panel-empty">还没有提交。</p>}
      </div>
    </div>
    {selectedCommit && <CommitDetails key={selectedCommit.hash} host={host} top={top} commit={selectedCommit} diff={diff} setDiff={setDiff}
      onSelect={hash => { setSelected(hash); setDiff(null); }} onClose={() => { setSelected(null); setDiff(null); }} />}
    {menu && <div className="pane-menu git-menu" role="menu" aria-label="Git 操作" style={{ left: menu.x, top: menu.y }} data-git-menu
      ref={element => element?.querySelector<HTMLButtonElement>('button:not([aria-disabled="true"])')?.focus()}
      onKeyDown={event => { if (event.key === 'Escape') { event.stopPropagation(); setMenu(null); } }}>
      {readOnly && <p className="pane-menu-note">{READ_ONLY_REASON}</p>}
      {menu.items.map((entry, index) => 'separator' in entry ? <hr key={index} /> :
        <button key={index} role="menuitem" data-git-action={entry.action.type}
          className={entry.action.type.startsWith('delete') || entry.action.type === 'reset' || entry.action.type === 'resetUncommitted' ? 'danger' : undefined}
          aria-disabled={readOnly && entry.writes ? 'true' : undefined} title={readOnly && entry.writes ? READ_ONLY_REASON : undefined}
          onClick={() => { if (!(readOnly && entry.writes)) choose(entry.action); }}>{entry.label}</button>)}
    </div>}
    {menu && <div className="git-menu-backdrop" onClick={() => setMenu(null)} onContextMenu={event => { event.preventDefault(); setMenu(null); }} />}
    {dialog && graph && <ActionDialog spec={dialogFor(dialog.action, graph.ctx)!} dialog={dialog} setValues={values => setDialog({ ...dialog, values, error: null })}
      onCancel={() => setDialog(null)} onConfirm={() => void confirm()} />}
  </div>;
}

function Lanes({ row, width, commit }: { row: { lane: number; segments: Segment[] }; width: number; commit: Commit }) {
  const path = ([fromLane, fromY, toLane, toY]: Segment) => {
    const x1 = laneX(fromLane), y1 = fromY * ROW, x2 = laneX(toLane), y2 = toY * ROW, middle = (y1 + y2) / 2;
    return x1 === x2 ? `M${x1} ${y1}L${x2} ${y2}` : `M${x1} ${y1}C${x1} ${middle} ${x2} ${middle} ${x2} ${y2}`;
  };
  return <svg width={width} height={ROW} aria-hidden="true">
    {row.segments.map((segment, index) => <path key={index} d={path(segment)} className={'lane-line lane-' + (segment[4] % 12)} strokeDasharray={segment[5] ? '3 3' : undefined} data-dashed={segment[5] || undefined} />)}
    <circle cx={laneX(row.lane)} cy={ROW / 2} r={commit.head ? 4.5 : 3.5} className={'lane-dot lane-' + (row.lane % 12) + (commit.uncommitted ? ' open' : '') + (commit.head ? ' head' : '')} />
  </svg>;
}

function CommitDetails({ host, top, commit, diff, setDiff, onSelect, onClose }: { host: PanelHost; top: string; commit: Commit;
    diff: FileDiff | null; setDiff: Dispatch<SetStateAction<FileDiff | null>>;
    onSelect: (hash: string) => void; onClose: () => void }) {
  const [detail, setDetail] = useState<ReturnType<typeof parseDetail> | null>(null);
  const [changes, setChanges] = useState<{ files: FileChange[]; base?: string } | null>(null);
  const files = changes?.files;
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let stopped = false;
    void (async () => {
      try {
        const args = await fileArgs(commit, argv => host.git.read(top, argv));
        const [shown, status, numstat, untracked] = await Promise.all([
          commit.uncommitted ? null : host.git.read(top, ['show', '-s', DETAIL_FORMAT, commit.hash]),
          host.git.read(top, args.status), host.git.read(top, args.numstat),
          commit.uncommitted ? host.git.read(top, ['ls-files', '--others', '--exclude-standard', '-z']) : null]);
        if (stopped) return;
        if (shown) setDetail(parseDetail(check(shown)));
        const changed = joinFiles(check(status), check(numstat));
        if (untracked) for (const path of check(untracked).split('\0').filter(Boolean)) changed.push({ path, status: '?', add: 0, del: 0 });
        setChanges({ files: changed, base: args.base });
      } catch (failure) { if (!stopped) setError(String(failure)); }
    })();
    return () => { stopped = true; };
  }, [commit.hash]);
  const openDiff = async (path: string, status: string) => {
    const loading = { path, rows: null, text: '正在读取 diff…' };
    setDiff(loading);
    try {
      const text = check(await host.git.read(top, diffArgs(commit, path, changes?.base, status)));
      const rows = diffRows(text);
      // A close or a new selection replaces this loading object, so late reads cannot restore it.
      setDiff(current => current === loading ? { path, rows,
        text: status === '?' && !rows && !text.includes('Binary files ') ? '空文件，没有文本内容。' : text } : current);
    } catch (failure) { setDiff(current => current === loading ? { path, rows: null, text: String(failure) } : current); }
  };
  return <section className="git-details" aria-label="提交详情" data-git-details={commit.hash}>
    <header>
      <strong className="git-details-title">{commit.subject}</strong>
      <button className="icon-button" aria-label="关闭详情" onClick={onClose}>✕</button>
    </header>
    {error && <p className="panel-error" role="alert">{error}</p>}
    {diff ? <div className="git-diff" data-git-diff={diff.path}>
      <div className="git-diff-head"><button className="text-button" onClick={() => setDiff(null)}>← 文件</button><code>{diff.path}</code></div>
      {diff.rows ? <pre className="diff-lines">{diff.rows.map((line, index) => <div key={index} className={'diff-line ' + ({ '+': 'add', '-': 'del', '@': 'hunk' }[line.kind] ?? '')}>
        <span className="diff-number">{line.number ?? ''}</span><span>{line.kind === '@' ? line.text : (line.kind || ' ') + line.text}</span></div>)}</pre>
        : <p className="panel-empty">{diff.text || '没有文本改动（可能是二进制文件）。'}</p>}
    </div> : <div className="git-details-body">
      {!commit.uncommitted && <dl className="git-meta">
        <div><dt>提交</dt><dd><code data-detail-hash>{commit.hash}</code></dd></div>
        <div><dt>父提交</dt><dd data-detail-parents={commit.parents.join(' ')}>{commit.parents.length ? commit.parents.map(parent =>
          <button key={parent} className="text-button" onClick={() => onSelect(parent)}><code>{parent.slice(0, 10)}</code></button>) : '无（根提交）'}</dd></div>
        <div><dt>作者</dt><dd>{commit.author} &lt;{commit.email}&gt; · {dateText(commit.time)}</dd></div>
        {detail && <div><dt>提交者</dt><dd>{detail.committer} · {dateText(detail.committed)}</dd></div>}
      </dl>}
      {detail?.body && <pre className="git-body">{detail.body}</pre>}
      <ul className="git-files" aria-label="改动的文件">
        {files?.map(file => <li key={file.path}><button className="git-file" data-git-file={file.path} onClick={() => void openDiff(file.path, file.status)}>
          <span className={'file-status s-' + file.status}>{file.status}</span><span className="file-path">{file.path}</span>
          <span className="file-stat">{file.binary ? '二进制' : <><span className="add">+{file.add}</span> <span className="del">-{file.del}</span></>}</span>
        </button></li>)}
        {files && !files.length && <li className="panel-empty">没有改动的文件。</li>}
      </ul>
    </div>}
  </section>;
}

function ActionDialog({ spec, dialog, setValues, onCancel, onConfirm }: { spec: ReturnType<typeof dialogFor> & {}; dialog: { values: Record<string, any>; error: string | null; busy: boolean; action: Action };
    setValues: (values: Record<string, any>) => void; onCancel: () => void; onConfirm: () => void }) {
  const danger = spec.danger || spec.choice?.options.find(option => option.value === dialog.values[spec.choice!.id])?.danger;
  return <div className="git-dialog-backdrop">
    <form className="git-dialog" role="dialog" aria-modal="true" aria-label={spec.title} data-git-dialog={dialog.action.type}
      onSubmit={event => { event.preventDefault(); onConfirm(); }} onKeyDown={event => { if (event.key === 'Escape') { event.stopPropagation(); onCancel(); } }}>
      <h3>{spec.title}</h3>
      {spec.detail && <p>{spec.detail}</p>}
      {spec.inputs?.map((input, index) => <label key={input.id} className="git-field">{input.label}
        <input autoFocus={index === 0} data-git-input={input.id} value={dialog.values[input.id] ?? ''} onChange={event => setValues({ ...dialog.values, [input.id]: event.target.value })} /></label>)}
      {spec.checks?.map(item => <label key={item.id} className="git-check"><input type="checkbox" data-git-check={item.id} checked={Boolean(dialog.values[item.id])}
        onChange={event => setValues({ ...dialog.values, [item.id]: event.target.checked })} />{item.label}</label>)}
      {spec.choice && <fieldset className="git-choice"><legend>{spec.choice.label}</legend>{spec.choice.options.map(option =>
        <label key={option.value} className={option.danger ? 'danger' : undefined}><input type="radio" name={spec.choice!.id} data-git-choice={option.value}
          checked={dialog.values[spec.choice!.id] === option.value} onChange={() => setValues({ ...dialog.values, [spec.choice!.id]: option.value })} />
          <strong>{option.label}</strong>{option.detail && <span> · {option.detail}</span>}</label>)}</fieldset>}
      {dialog.error && <p className="panel-error" role="alert" data-git-dialog-error>{dialog.error}</p>}
      <footer>
        <button type="button" onClick={onCancel} data-git-cancel>取消</button>
        <button type="submit" className={danger ? 'danger-button' : 'primary-button'} disabled={dialog.busy} data-git-confirm autoFocus={!spec.inputs?.length}>{dialog.busy ? '正在执行…' : spec.confirm}</button>
      </footer>
    </form>
  </div>;
}

type ScannedRepo = { path: string; name: string; group: string; status: RepoStatus };
function Manygit({ host, root, onOpen }: { host: PanelHost; root: string; onOpen: (path: string) => void }) {
  const [depth, setDepth] = useState(DEPTH.default);
  const [tags, setTags] = useState(true);
  const [result, setResult] = useState<{ unsearched: boolean; repos: ScannedRepo[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let stopped = false;
    setResult(null); setError(null);
    host.git.scan(root, depth, tags).then(value => { if (!stopped) setResult(value); }, failure => { if (!stopped) setError(String(failure)); });
    return () => { stopped = true; };
  }, [root, depth, tags, version]);
  const groups = new Map<string, ScannedRepo[]>();
  for (const repo of result?.repos ?? []) groups.set(repo.group, [...groups.get(repo.group) ?? [], repo]);
  return <div className="manygit" data-manygit={root}>
    <div className="git-toolbar">
      <span className="manygit-title">不是 Git 仓库，下面的仓库：</span>
      <label className="git-check">深度 <select value={depth} data-manygit-depth onChange={event => setDepth(Number(event.target.value))}>
        {Array.from({ length: DEPTH.max - DEPTH.min + 1 }, (_, index) => DEPTH.min + index).map(value => <option key={value} value={value}>{value}</option>)}</select></label>
      <label className="git-check"><input type="checkbox" checked={tags} data-manygit-tags onChange={event => setTags(event.target.checked)} />最新标签</label>
      <button className="text-button" onClick={() => setVersion(value => value + 1)}>刷新</button>
    </div>
    {error && <p className="panel-error" role="alert">{error}</p>}
    {!result && !error && <p className="panel-empty" role="status">正在扫描…</p>}
    {result?.unsearched && <p className="panel-empty" data-manygit-unsearched>不扫描家目录、根目录和 /Users/&lt;名字&gt; 这一层。把面板固定或跟随到更具体的目录。</p>}
    {result && !result.unsearched && !result.repos.length && <p className="panel-empty">深度 {depth} 以内没有 Git 仓库。</p>}
    {[...groups].map(([group, repos]) => <section key={group} className="manygit-group" aria-label={group || '当前目录'}>
      <h4>{group || '.'}</h4>
      {repos.map(repo => {
        const sync = syncOf(repo.status);
        return <button key={repo.path} className="manygit-row" data-manygit-repo={repo.path} onClick={() => onOpen(repo.path)} title={repo.path}>
          <span className="manygit-name">{repo.name}</span>
          <span className="manygit-branch">{repo.status.branch ?? (repo.status.detached ? '分离 HEAD' : '')}</span>
          <span className="manygit-dirty" data-dirty={repo.status.dirty}>{repo.status.dirty ? `${repo.status.dirty} 个改动` : ''}</span>
          <span className={'manygit-sync ' + sync.kind}>{sync.text}</span>
          {tags && <span className="manygit-tag">{repo.status.tag ?? ''}</span>}
        </button>;
      })}
    </section>)}
  </div>;
}
