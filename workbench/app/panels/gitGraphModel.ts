// Git for the Git graph panel: reading the history, the lane layout, the menus and the commands behind them, and
// the Manygit repository list. No Electron or DOM imports, so the main process (which builds and runs the write
// commands) and the renderer share one copy. Commands are argv arrays, never a shell line.
//
// Adapted from herdr-git-graph (mods/git-graph/git.js, lanes.js, repos.js), https://github.com/rabeeh-ta/herdr-git-graph
// MIT License. Copyright (c) 2026 Rabeeh T A.
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
// documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
// persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice
// and this permission notice shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
// WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
// COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
// OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

// Reads write nothing under .git (no index refresh or lock, no fsmonitor cookie), so the folder watch never wakes
// for the panel's own reads. The main process prepends these to every read.
export const READ = ['--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'diff.autoRefreshIndex=false'];
export const STATUS = ['status', '--porcelain=v1', '-z', '--no-renames', '--untracked-files=all'];
export const UNCOMMITTED = '*';
export const PAGE = 300;
export const ROW = 24, LANE = 12, PAD = 6;
const FORMAT = '%H%x00%P%x00%an%x00%ae%x00%at%x00%D%x00%s';
export const objectId = (s: unknown): s is string => typeof s === 'string' && /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(s);
// A name never reaches git as an option: one starting with "-" is refused here and at the dialog.
export const refName = (s: unknown): s is string => typeof s === 'string' && s.length > 0 && !/^[-/]/.test(s)
  && !/[\x00-\x20\x7f~^:?*[\\]/.test(s) && !s.includes('..') && !s.includes('@{')
  && s !== '@' && !s.endsWith('.') && s.split('/').every(p => p && !p.startsWith('.') && !p.endsWith('.lock'));

// full: the complete ref name git printed (refs/heads/x, refs/tags/x, refs/remotes/o/x; HEAD when detached).
export type Ref = { kind: 'branch' | 'tag' | 'remote' | 'detached'; name: string; full: string; head?: boolean };
export type Commit = { hash: string; parents: string[]; author: string; email: string; time: number | null; refs: Ref[];
  subject: string; head: boolean; uncommitted?: boolean; dashed?: boolean };

function checkCommit(commit: Commit) {
  if (!objectId(commit?.hash) || !Array.isArray(commit.parents) || !commit.parents.every(objectId)) throw new Error('Invalid commit identity');
}

export function logArgs({ all, remotes, limit }: { all: boolean; remotes: boolean; limit: number }) {
  // All branches walks local branches, tags, remote branches (with Remotes) and HEAD. Not `--all`: that also walks
  // other tools' private refs, which show up as orphan commits. `--ignore-missing` keeps an empty repository empty.
  const scope = all ? ['--branches', '--tags', ...(remotes ? ['--remotes'] : []), '--ignore-missing', 'HEAD'] : ['--ignore-missing', 'HEAD'];
  return ['log', '-z', ...scope, '--date-order', '--decorate=full', `-n${limit}`, `--format=${FORMAT}`];
}

export function parseRefs(text: string): Ref[] {
  const refs: Ref[] = [];
  for (let name of text ? text.split(', ') : []) {
    const head = name.startsWith('HEAD -> ');
    if (head) name = name.slice(8);
    if (name === 'HEAD') refs.push({ kind: 'detached', name: 'HEAD', full: 'HEAD' });
    else if (name.startsWith('refs/heads/') && refName(name.slice(11))) refs.push({ kind: 'branch', name: name.slice(11), full: name, head });
    else if (name.startsWith('tag: refs/tags/') && refName(name.slice(15))) refs.push({ kind: 'tag', name: name.slice(15), full: name.slice(5) });
    else if (name.startsWith('refs/remotes/') && !name.endsWith('/HEAD') && refName(name.slice(13))) refs.push({ kind: 'remote', name: name.slice(13), full: name });
  }
  return refs;
}

export function parseLog(text: string): Commit[] {
  if (!text) return [];
  const fields = text.split('\0');
  if (fields.pop() !== '' || fields.length % 7 !== 0) throw new Error('Invalid history framing');
  const commits: Commit[] = [];
  for (let i = 0; i < fields.length; i += 7) {
    const [hash, parents, author, email, time, refs, subject] = fields.slice(i, i + 7) as string[];
    const parsed = parseRefs(refs!);
    const commit: Commit = { hash: hash!, parents: parents ? parents.split(' ') : [], author: author!, email: email!, time: Number(time),
      refs: parsed, subject: subject!, head: parsed.some(r => r.head || r.kind === 'detached') };
    checkCommit(commit);
    if (!/^\d+$/.test(time!) || !Number.isSafeInteger(commit.time)) throw new Error('Invalid commit time');
    commits.push(commit);
  }
  return commits;
}

export type StatusEntry = { path: string; status: string; untracked: boolean; staged: boolean };
// `git status --porcelain=v1 -z --no-renames`: one NUL-terminated "XY path" per file.
export function parseStatus(text: string): StatusEntry[] {
  return text.split('\0').filter(Boolean).map(entry => {
    const xy = entry.slice(0, 2), path = entry.slice(3);
    const status = xy === '??' ? 'A' : xy.includes('U') || xy === 'AA' || xy === 'DD' ? 'U' : xy.includes('D') ? 'D' : xy.includes('A') ? 'A' : 'M';
    return { path, status, untracked: xy === '??', staged: status !== 'U' && xy[0] !== ' ' && xy[0] !== '?' };
  });
}

export type Segment = [number, number, number, number, number, boolean];
// Lays commits out on lanes. Commits come newest first, every child before its parents (--date-order). A lane is a
// column waiting for one commit and keeps its column until that commit arrives, so lines bend only where branches
// fork or merge. Each row gets the commit's lane and its segments [fromLane, fromY, toLane, toY, colorLane, dashed],
// with y 0 = top of the row, 0.5 = the dot, 1 = bottom.
export function layoutLanes(commits: Commit[]) {
  const lanes: (string | null)[] = [], dashed: boolean[] = [];
  const free = () => { const i = lanes.indexOf(null); return i < 0 ? lanes.length : i; };
  let width = 1;
  const rows = commits.map(commit => {
    const before = lanes.slice(), wasDashed = dashed.slice(), segments: Segment[] = [];
    let lane = before.indexOf(commit.hash);
    if (lane < 0) { lane = free(); lanes[lane] = commit.hash; dashed[lane] = false; }
    before.forEach((hash, j) => {
      if (hash === null || hash === undefined) return;
      if (hash === commit.hash) {
        segments.push([j, 0, lane, 0.5, j, Boolean(wasDashed[j])]);
        if (j !== lane) { lanes[j] = null; dashed[j] = false; }
      } else segments.push([j, 0, j, 1, j, Boolean(wasDashed[j])]);
    });
    const [first, ...rest] = commit.parents;
    lanes[lane] = first ?? null;
    dashed[lane] = Boolean(first && commit.dashed);
    if (first) segments.push([lane, 0.5, lane, 1, lane, dashed[lane]!]);
    for (const parent of rest) {
      let k = lanes.indexOf(parent);
      if (k < 0) { k = free(); lanes[k] = parent; dashed[k] = Boolean(commit.dashed); }
      segments.push([lane, 0.5, k, 1, k, dashed[k]!]);
    }
    width = Math.max(width, before.length, lanes.length);
    while (lanes.length && lanes[lanes.length - 1] === null) { lanes.pop(); dashed.length = lanes.length; }
    return { lane, segments };
  });
  return { rows, width };
}

// The working tree's changes as the newest row, drawn dashed to HEAD. The lanes above come from the commits alone
// (layoutLanes), so a commit's lane does not depend on whether the work tree is dirty; the uncommitted row sits on
// HEAD's lane (even when another commit uses that lane above HEAD), and its
// dashed line runs down to HEAD's dot. Returns the row and the extra segments for each commit row.
export function uncommittedRow(commits: Commit[], layout: ReturnType<typeof layoutLanes>, changes: number) {
  const headRow = commits.findIndex(commit => commit.head);
  const commit: Commit = { hash: UNCOMMITTED, parents: headRow < 0 ? [] : [commits[headRow]!.hash], uncommitted: true, dashed: true,
    refs: [], head: false, subject: `未提交的改动（${changes} 个文件）`, author: '', email: '', time: null };
  const above = headRow < 0 ? layout.rows : layout.rows.slice(0, headRow);
  const headLane = headRow < 0 ? null : layout.rows[headRow]!.lane;
  const lane = headLane ?? 0;
  const extra: Segment[][] = layout.rows.map(() => []);
  if (headRow >= 0) {
    above.forEach((_, index) => extra[index]!.push([lane, 0, lane, 1, lane, true]));
    extra[headRow]!.push([lane, 0, headLane!, 0.5, lane, true]);
  }
  const segments: Segment[] = headRow < 0 ? [] : [[lane, 0.5, lane, 1, lane, true]];
  return { commit, row: { lane, segments }, extra, width: Math.max(layout.width, lane + 1) };
}

export type GitRead = (argv: string[]) => Promise<{ code: number | null; stdout: string; stderr: string }>;
// history/layout: the commits alone and their lanes, kept so a status-only refresh can redo just the uncommitted row.
export type Graph = { commits: Commit[]; rows: { lane: number; segments: Segment[] }[]; width: number; more: boolean; ctx: Context;
  changes: number; staged: number; history: Commit[]; layout: ReturnType<typeof layoutLanes> };
const output = (result: { code: number | null; stdout: string; stderr: string }) => {
  if (result.code !== 0) throw new Error(gitError(result));
  return result.stdout;
};
// Reads and lays out one page of history. The panel and the command-line entry (gitGraphCli.ts) both call this, with
// a reader that runs git in the main process (gitHost.ts gitRead). `commits` and `rows` start with the uncommitted
// row when the work tree has changes.
export async function readGraph(read: GitRead, { all, remotes, limit }: { all: boolean; remotes: boolean; limit: number }): Promise<Graph> {
  const [log, status, head, current, branches, remoteList] = await Promise.all([
    read(logArgs({ all, remotes, limit: limit + 1 })), read(STATUS), read(['rev-parse', '--verify', '-q', 'HEAD']),
    read(['symbolic-ref', '-q', '--short', 'HEAD']), read(['for-each-ref', '--format=%(refname:short)', 'refs/heads']), read(['remote'])]);
  const parsed = parseLog(output(log));
  const changes = parseStatus(output(status));
  const commits = parsed.slice(0, limit);
  const layout = layoutLanes(commits);
  const ctx: Context = { current: current.code === 0 ? current.stdout.trim() : null, head: head.code === 0 ? head.stdout.trim() : null,
    branches: output(branches).split('\n').filter(Boolean), remotes: output(remoteList).split('\n').filter(Boolean) };
  return withStatus({ more: parsed.length > limit, ctx, history: commits, layout }, changes);
}

// The graph with the work tree's status put in: the uncommitted row and its dashed line, or none.
export function withStatus(graph: Pick<Graph, 'more' | 'ctx' | 'history' | 'layout'>, changes: StatusEntry[]): Graph {
  const { more, ctx, history, layout } = graph;
  const base = { more, ctx, history, layout, changes: changes.length, staged: changes.filter(change => change.staged).length };
  if (!changes.length) return { ...base, commits: history, rows: layout.rows, width: layout.width };
  const extra = uncommittedRow(history, layout, changes.length);
  return { ...base, commits: [extra.commit, ...history], width: extra.width,
    rows: [extra.row, ...layout.rows.map((row, index) => ({ lane: row.lane, segments: [...row.segments, ...extra.extra[index]!] }))] };
}

// Only the status: for a change in the work tree that moved no ref.
export async function readStatus(read: GitRead, graph: Graph) {
  return withStatus(graph, parseStatus(output(await read(STATUS))));
}

export type Label = { kind: string; head?: boolean; parts: { kind: string; name: string; text: string; head?: boolean }[] };
const fit = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s);
export function labelsOf(commit: Commit, remotesShown = true): Label[] {
  const labels: Label[] = [], remotes = remotesShown ? commit.refs.filter(r => r.kind === 'remote') : [], paired = new Set<string>();
  for (const ref of commit.refs) {
    if (ref.kind === 'detached') labels.push({ kind: 'head', head: true, parts: [{ kind: 'head', name: 'HEAD', text: 'HEAD' }] });
    if (ref.kind !== 'branch') continue;
    // A remote branch with the same name rides on its local branch's label.
    const parts: Label['parts'] = [{ kind: 'branch', name: ref.name, text: fit(ref.name, 22), head: ref.head }];
    for (const remote of remotes) {
      const slash = remote.name.indexOf('/');
      if (remote.name.slice(slash + 1) !== ref.name || paired.has(remote.name)) continue;
      paired.add(remote.name);
      parts.push({ kind: 'remote', name: remote.name, text: fit(remote.name.slice(0, slash), 12) });
    }
    labels.push({ kind: 'branch', head: ref.head, parts });
  }
  for (const remote of remotes) if (!paired.has(remote.name)) labels.push({ kind: 'remote', parts: [{ kind: 'remote', name: remote.name, text: fit(remote.name, 22) }] });
  for (const ref of commit.refs) if (ref.kind === 'tag') labels.push({ kind: 'tag', parts: [{ kind: 'tag', name: ref.name, text: fit(ref.name, 22) }] });
  labels.sort((a, b) => Number(Boolean(b.head)) - Number(Boolean(a.head)));
  return labels;
}

export type Action = { type: string; [key: string]: any };
export type MenuItem = { label: string; action: Action; writes: boolean } | { separator: true };
export type Context = { current: string | null; head: string | null; branches: string[]; remotes: string[] };
const shortHash = (hash: string) => hash.slice(0, 8);
const currentName = (ctx: Context) => ctx.current ?? 'HEAD';
const section = (...items: (MenuItem | false | null | undefined | '')[]) => items.filter(Boolean) as MenuItem[];
const READ_ONLY_ACTIONS = new Set(['copy', 'showChanges']);
const item = (label: string, action: Action): MenuItem => ({ label, action, writes: !READ_ONLY_ACTIONS.has(action.type) });
export type Target = { kind: 'uncommitted'; staged: boolean } | { kind: 'branch' | 'remote' | 'tag'; name: string }
  | { kind: 'commit'; commit: Commit } | { kind: 'repo'; status: RepoStatus; path: string };

// The right-click menu for a commit, a label or the uncommitted row: Git Graph's menus, minus what needs VS Code.
export function menuFor(target: Target, ctx: Context): MenuItem[] {
  const cur = currentName(ctx);
  let sections: MenuItem[][];
  if (target.kind === 'repo') sections = repoMenu(target, ctx);
  else if (target.kind === 'uncommitted') {
    sections = [
      section(item('提交…', { type: 'commit', staged: target.staged })),
      section(item('贮藏未提交的改动…', { type: 'stash' })),
      section(item('重置未提交的改动…', { type: 'resetUncommitted' })),
    ];
  } else if (target.kind === 'branch') {
    const name = target.name, current = name === ctx.current;
    sections = [
      section(!current && item('检出分支', { type: 'checkout', name }),
        item('重命名分支…', { type: 'renameBranch', name }),
        !current && item('删除分支…', { type: 'deleteBranch', name })),
      section(!current && item(`合并到 ${cur}…`, { type: 'merge', ref: name, what: `分支 ${name}` }),
        !current && item(`把 ${cur} 变基到这个分支…`, { type: 'rebase', ref: name, what: `分支 ${name}` })),
      section(ctx.remotes.length > 0 && item('推送分支…', { type: 'push', name })),
      section(item('复制分支名', { type: 'copy', text: name })),
    ];
  } else if (target.kind === 'remote') {
    const name = target.name, slash = name.indexOf('/'), remote = name.slice(0, slash), branch = name.slice(slash + 1);
    const local = ctx.branches.includes(branch);
    sections = [
      section(branch !== ctx.current && (local ? item(`检出 ${branch}`, { type: 'checkout', name: branch })
        : item('检出为本地分支…', { type: 'checkoutRemote', name, remote, branch }))),
      section(item(`合并到 ${cur}…`, { type: 'merge', ref: name, what: `远程分支 ${name}` })),
      section(item('删除远程分支…', { type: 'deleteRemoteBranch', name, remote, branch })),
      section(item('复制分支名', { type: 'copy', text: name })),
    ];
  } else if (target.kind === 'tag') {
    const name = target.name;
    sections = [
      section(item('删除标签…', { type: 'deleteTag', name })),
      section(ctx.remotes.length > 0 && item('推送标签…', { type: 'pushTag', name })),
      section(item('复制标签名', { type: 'copy', text: name })),
    ];
  } else {
    const c = target.commit, hash = c.hash, short = shortHash(hash), here = hash === ctx.head, merge = c.parents.length > 1;
    sections = [
      section(item('打标签…', { type: 'addTag', hash, short }), item('新建分支…', { type: 'createBranch', hash, short })),
      section(!here && item('检出到这个提交…', { type: 'checkoutCommit', hash, short }),
        !here && item('Cherry-pick…', { type: 'cherryPick', hash, short, merge }),
        item('Revert…', { type: 'revert', hash, short, merge })),
      section(!here && item(`合并到 ${cur}…`, { type: 'merge', ref: hash, what: `提交 ${short}` }),
        !here && item(`把 ${cur} 变基到这个提交…`, { type: 'rebase', ref: hash, what: `提交 ${short}` }),
        item(`把 ${cur} 重置到这个提交…`, { type: 'reset', hash, short })),
      section(item('复制提交哈希', { type: 'copy', text: hash }), item('复制提交标题', { type: 'copy', text: c.subject })),
    ];
  }
  const out: MenuItem[] = [];
  for (const s of sections.filter(s => s.length)) { if (out.length) out.push({ separator: true }); out.push(...s); }
  return out;
}

function repoMenu(r: { status: RepoStatus; path: string }, ctx: Context): MenuItem[][] {
  const st = r.status, branch = st.branch, remote = ctx.remotes.length > 0;
  const pull = remote && st.upstream && !st.gone && item('拉取（仅快进）…', { type: 'pull', upstream: st.upstream });
  const push = remote && branch && item(st.upstream ? '推送…' : '推送并设上游…', { type: 'push', name: branch });
  const fetch = remote && item('抓取所有远程', { type: 'fetch' });
  const sync = st.behind && !st.ahead ? [pull, fetch, push] : st.ahead && !st.behind ? [push, fetch, pull] : !st.upstream ? [push, fetch] : [fetch, pull, push];
  return [section(...sync),
    st.dirty > 0 ? section(item('提交…', { type: 'commit', staged: st.staged > 0 }), item('贮藏未提交的改动…', { type: 'stash' }),
      item('重置未提交的改动…', { type: 'resetUncommitted' })) : [],
    section(item('复制路径', { type: 'copy', text: r.path }), branch && item('复制分支名', { type: 'copy', text: branch }))];
}

export type DialogSpec = { title: string; detail?: string; confirm: string; danger?: boolean;
  inputs?: { id: string; label: string; value: string; optional?: boolean; text?: boolean }[];
  checks?: { id: string; label: string; value: boolean }[];
  choice?: { id: string; label: string; value: string; options: { value: string; label: string; detail?: string; danger?: boolean }[] } };
const remoteChoice = (ctx: Context) => ({ id: 'remote', label: '远程', value: ctx.remotes.includes('origin') ? 'origin' : ctx.remotes[0]!,
  options: ctx.remotes.map(r => ({ value: r, label: r })) });
const mergeNote = (a: Action) => (a.merge ? ' 这是合并提交：按它对第一个父提交的改动处理。' : '');

// The confirmation every repository change asks first. Only checkout of a local branch has no inputs; it still asks.
export function dialogFor(a: Action, ctx: Context): DialogSpec | null {
  const cur = currentName(ctx);
  switch (a.type) {
    case 'checkout': return { title: '检出分支', detail: `检出 ${a.name}？`, confirm: '检出' };
    case 'checkoutRemote': return { title: '检出远程分支', detail: `新建一个跟踪 ${a.name} 的本地分支并检出。`,
      inputs: [{ id: 'name', label: '本地分支名', value: a.branch }], confirm: '检出' };
    case 'checkoutCommit': return { title: '检出提交', detail: `检出提交 ${a.short}？之后处于分离 HEAD：新提交不属于任何分支，除非再建分支。`, confirm: '检出' };
    case 'createBranch': return { title: '新建分支', detail: `在提交 ${a.short}。`, inputs: [{ id: 'name', label: '分支名', value: '' }],
      checks: [{ id: 'checkout', label: '新建后检出', value: false }], confirm: '新建' };
    case 'addTag': return { title: '打标签', detail: `在提交 ${a.short}。`, inputs: [{ id: 'name', label: '标签名', value: '' },
      { id: 'message', label: '说明（填了就是附注标签）', value: '', optional: true, text: true }], confirm: '打标签' };
    case 'renameBranch': return { title: '重命名分支', detail: `重命名 ${a.name}。`, inputs: [{ id: 'name', label: '新名字', value: a.name }], confirm: '重命名' };
    case 'deleteBranch': return { title: '删除分支', detail: `删除本地分支 ${a.name}？`,
      checks: [{ id: 'force', label: '强制删除（即使没有合并）', value: false }], confirm: '删除', danger: true };
    case 'deleteRemoteBranch': return { title: '删除远程分支', detail: `删除 ${a.remote} 上的 ${a.branch}？这会改动所有人用的远程。`, confirm: '删除', danger: true };
    case 'deleteTag': return { title: '删除标签', detail: `删除本地标签 ${a.name}？`, confirm: '删除', danger: true };
    case 'merge': return { title: '合并', detail: `把 ${a.what} 合并到 ${cur}？`,
      checks: [{ id: 'noff', label: '即使能快进也创建合并提交', value: false }], confirm: '合并' };
    case 'rebase': return { title: '变基', detail: `把 ${cur} 变基到 ${a.what}？`, confirm: '变基', danger: true };
    case 'cherryPick': return { title: 'Cherry-pick', detail: `把提交 ${a.short} 应用到 ${cur} 上？${mergeNote(a)}`, confirm: 'Cherry-pick' };
    case 'revert': return { title: 'Revert', detail: `在 ${cur} 上加一个撤销 ${a.short} 的提交？${mergeNote(a)}`, confirm: 'Revert' };
    case 'reset': return { title: '重置', detail: `把 ${cur} 移到提交 ${a.short}。`, confirm: '重置', danger: true,
      choice: { id: 'mode', label: '方式', value: 'mixed', options: [
        { value: 'soft', label: 'Soft', detail: '保留所有改动，已暂存' },
        { value: 'mixed', label: 'Mixed', detail: '保留所有改动，未暂存' },
        { value: 'hard', label: 'Hard', detail: '丢弃所有改动', danger: true }] } };
    case 'push': return { title: '推送分支', detail: `推送 ${a.name}。`, choice: remoteChoice(ctx),
      checks: [{ id: 'upstream', label: '设为上游', value: true }], confirm: '推送' };
    case 'pushTag': return { title: '推送标签', detail: `推送标签 ${a.name}。`, choice: remoteChoice(ctx), confirm: '推送' };
    case 'commit': return { title: '提交', detail: ctx.current ? `提交到 ${ctx.current}。` : '处于分离 HEAD：提交不属于任何分支，除非再建分支。',
      inputs: [{ id: 'message', label: '提交说明', value: '', text: true }],
      checks: [{ id: 'all', label: '先暂存所有改动（含未跟踪文件）', value: !a.staged }], confirm: '提交' };
    case 'pull': return { title: '拉取', detail: `把 ${cur} 快进到 ${a.upstream}？不能快进时什么都不改。`, confirm: '拉取' };
    case 'stash': return { title: '贮藏未提交的改动', inputs: [{ id: 'message', label: '说明', value: '', optional: true, text: true }],
      checks: [{ id: 'untracked', label: '包含未跟踪文件', value: true }], confirm: '贮藏' };
    case 'resetUncommitted': return { title: '重置未提交的改动', detail: '把工作区重置到 HEAD。', confirm: '重置', danger: true,
      choice: { id: 'mode', label: '方式', value: 'mixed', options: [
        { value: 'mixed', label: 'Mixed', detail: '取消全部暂存，保留改动' },
        { value: 'hard', label: 'Hard', detail: '丢弃已跟踪文件的所有改动', danger: true }] } };
    case 'fetch': return { title: '抓取', detail: '从所有远程抓取（git fetch --all）？', confirm: '抓取' };
    default: return null;
  }
}

export function initialValues(a: Action, ctx: Context) {
  const spec = dialogFor(a, ctx), v: Record<string, any> = {};
  for (const i of spec?.inputs ?? []) v[i.id] = i.value ?? '';
  for (const c of spec?.checks ?? []) v[c.id] = c.value;
  if (spec?.choice) v[spec.choice.id] = spec.choice.value;
  return v;
}

// What is wrong with the typed values, or null.
export function validate(a: Action, v: Record<string, any>, ctx: Context): string | null {
  const spec = dialogFor(a, ctx);
  for (const input of spec?.inputs ?? []) {
    const text = String(v[input.id] ?? '').trim();
    if (input.optional) continue;
    if (!text) return `${input.label}不能为空。`;
    if (input.text) continue; // free text, passed as one argument after its option
    if (text.startsWith('-')) return `${input.label}不能以“-”开头。`;
    if (!refName(text)) return `${input.label}不是合法的 Git 引用名。`;
  }
  if (spec?.choice && !spec.choice.options.some(o => o.value === v[spec.choice!.id])) return `请选择${spec.choice.label}。`;
  return null;
}

// The git commands an action runs, in order. Validates again at the execution boundary (the main process).
export function commandsFor(a: Action, v: Record<string, any> = {}, ctx: Pick<Context, 'remotes'>): string[][] {
  const hashes = ['checkoutCommit', 'createBranch', 'addTag', 'cherryPick', 'revert', 'reset'];
  const names = ['checkout', 'checkoutRemote', 'renameBranch', 'deleteBranch', 'deleteRemoteBranch', 'deleteTag', 'push', 'pushTag'];
  if (hashes.includes(a.type) && !objectId(a.hash)) throw new Error('提交哈希不合法');
  if (names.includes(a.type) && !refName(a.name)) throw new Error('引用名不合法');
  if (['merge', 'rebase'].includes(a.type) && !refName(a.ref)) throw new Error('引用名不合法');
  if (a.type === 'deleteRemoteBranch' && (!refName(a.remote) || !refName(a.branch))) throw new Error('远程分支不合法');
  if (['checkoutRemote', 'createBranch', 'addTag', 'renameBranch'].includes(a.type) && !refName(String(v.name ?? '').trim())) throw new Error('名字不合法（不能以“-”开头）');
  if (['push', 'pushTag'].includes(a.type) && (!refName(v.remote) || !ctx.remotes.includes(v.remote))) throw new Error('远程不合法');
  if (a.type === 'reset' && !['soft', 'mixed', 'hard'].includes(v.mode)) throw new Error('重置方式不合法');
  if (a.type === 'resetUncommitted' && !['mixed', 'hard'].includes(v.mode)) throw new Error('重置方式不合法');
  if (a.type === 'commit' && !String(v.message ?? '').trim()) throw new Error('提交说明为空');
  const name = String(v.name ?? '').trim(), message = String(v.message ?? '').trim();
  switch (a.type) {
    case 'checkout': return [['checkout', a.name]];
    case 'checkoutRemote': return [['checkout', '-b', name, '--track', a.name]];
    case 'checkoutCommit': return [['checkout', '--detach', a.hash]];
    case 'createBranch': return [v.checkout ? ['checkout', '-b', name, a.hash] : ['branch', name, a.hash]];
    case 'addTag': return [message ? ['tag', '-a', name, '-m', message, a.hash] : ['tag', name, a.hash]];
    case 'renameBranch': return [['branch', '-m', a.name, name]];
    case 'deleteBranch': return [['branch', v.force ? '-D' : '-d', a.name]];
    case 'deleteRemoteBranch': return [['push', a.remote, '--delete', a.branch]];
    case 'deleteTag': return [['tag', '-d', a.name]];
    case 'merge': return [['merge', '--no-edit', ...(v.noff ? ['--no-ff'] : []), a.ref]];
    case 'rebase': return [['rebase', a.ref]];
    case 'cherryPick': return [['cherry-pick', ...(a.merge ? ['-m', '1'] : []), a.hash]];
    case 'revert': return [['revert', '--no-edit', ...(a.merge ? ['-m', '1'] : []), a.hash]];
    case 'reset': return [['reset', `--${v.mode}`, a.hash]];
    case 'push': return [['push', ...(v.upstream ? ['--set-upstream'] : []), v.remote, a.name]];
    case 'pushTag': return [['push', v.remote, `refs/tags/${a.name}`]];
    case 'commit': return [...(v.all ? [['add', '--all']] : []), ['commit', '-m', message]];
    case 'pull': return [['pull', '--ff-only', '--quiet']];
    case 'stash': return [['stash', 'push', ...(v.untracked ? ['--include-untracked'] : []), ...(message ? ['-m', message] : [])]];
    case 'resetUncommitted': return [['reset', `--${v.mode}`, 'HEAD']];
    case 'fetch': return [['fetch', '--all']];
    default: throw new Error('未知的 Git 操作');
  }
}

export function doneText(a: Action, v: Record<string, any> = {}) {
  const name = String(v.name ?? '').trim();
  switch (a.type) {
    case 'checkout': return `已检出 ${a.name}`;
    case 'checkoutRemote': return `已检出 ${name}，跟踪 ${a.name}`;
    case 'checkoutCommit': return `已检出 ${a.short}`;
    case 'createBranch': return `已新建分支 ${name}`;
    case 'addTag': return `已给 ${a.short} 打标签 ${name}`;
    case 'renameBranch': return `已把 ${a.name} 改名为 ${name}`;
    case 'deleteBranch': return `已删除分支 ${a.name}`;
    case 'deleteRemoteBranch': return `已删除 ${a.name}`;
    case 'deleteTag': return `已删除标签 ${a.name}`;
    case 'merge': return `已合并${a.what}`;
    case 'rebase': return `已变基到${a.what}`;
    case 'cherryPick': return `已 cherry-pick ${a.short}`;
    case 'revert': return `已 revert ${a.short}`;
    case 'reset': return `已重置到 ${a.short}（${v.mode}）`;
    case 'push': return `已推送 ${a.name} 到 ${v.remote}`;
    case 'pushTag': return `已推送标签 ${a.name} 到 ${v.remote}`;
    case 'commit': return '已提交';
    case 'pull': return `已拉取 ${a.upstream}`;
    case 'stash': return '已贮藏未提交的改动';
    case 'resetUncommitted': return `已重置未提交的改动（${v.mode}）`;
    case 'fetch': return '已抓取';
    default: return '完成';
  }
}

// Git's own words, without its hints.
export function gitError(result: { code: number | null; stdout: string; stderr: string }) {
  const lines = (result.stderr || result.stdout || '').split('\n').map(l => l.trimEnd()).filter(l => l && !l.startsWith('hint:'));
  return lines.slice(-6).join('\n') || `git 退出码 ${result.code}`;
}

// The files a commit changed against its first parent, joined from --name-status and --numstat (renames off).
export async function fileArgs(commit: Commit, read: GitRead) {
  if (commit.uncommitted) {
    const head = await read(['rev-parse', '--verify', '-q', 'HEAD']);
    // An unborn branch has no HEAD. Git's empty tree compares the working tree including staged and
    // unstaged changes; --cached alone would lose unstaged edits. No -w: this does not write an object.
    const base = output(head.code === 1 ? await read(['hash-object', '-t', 'tree', '/dev/null']) : head).trim();
    if (!objectId(base)) throw new Error('Invalid diff base');
    const argv = ['diff', '-z', '--no-renames', '--no-ext-diff', base];
    return { base, status: [...argv, '--name-status'], numstat: [...argv, '--numstat'] };
  }
  checkCommit(commit);
  const range = commit.parents.length ? [commit.parents[0]!, commit.hash] : null;
  const base = range ? ['diff', '-z', '--no-renames', '--no-ext-diff', ...range] : ['diff-tree', '-z', '--root', '--no-commit-id', '-r', '--no-renames', commit.hash];
  return { base: undefined, status: [...base, '--name-status'], numstat: [...base, '--numstat'] };
}

export type FileChange = { path: string; status: string; add: number; del: number; binary?: boolean };
export function joinFiles(statusText: string, numstatText: string): FileChange[] {
  const stats = new Map<string, { add: number; del: number; binary: boolean }>();
  for (const line of numstatText.split('\0').filter(Boolean)) {
    const [a, d, ...path] = line.split('\t');
    stats.set(path.join('\t'), { add: Number(a) || 0, del: Number(d) || 0, binary: a === '-' });
  }
  const fields = statusText.split('\0'), files: FileChange[] = [];
  for (let i = 0; i + 1 < fields.length; i += 2) {
    const status = fields[i]!, path = fields[i + 1]!;
    files.push({ path, status: status[0]!, ...(stats.get(path) ?? { add: 0, del: 0 }) });
  }
  return files;
}

export function diffArgs(commit: Commit, path: string, base?: string, status?: string) {
  const opts = ['--no-color', '--no-ext-diff', '--no-textconv'];
  if (commit.uncommitted && status === '?') return ['diff', '--no-index', ...opts, '--', '/dev/null', './' + path];
  const file = `:(top,literal)${path}`;
  if (commit.uncommitted) {
    if (!objectId(base)) throw new Error('Invalid diff base');
    return ['diff', ...opts, base, '--', file];
  }
  checkCommit(commit);
  if (!commit.parents.length) return ['show', ...opts, '--format=', commit.hash, '--', file];
  return ['diff', ...opts, commit.parents[0]!, commit.hash, '--', file];
}

export type DiffRow = { kind: string; number?: number; text: string };
// Numbers each diff line once.
export function diffRows(text: string): DiffRow[] | null {
  const all = text.replace(/\n$/, '').split('\n'), first = all.findIndex(l => l.startsWith('@@'));
  if (first < 0) return null;
  let old = 0, next = 0;
  return all.slice(first, first + 3000).map(raw => {
    const line = raw.length > 2000 ? raw.slice(0, 2000) + '…' : raw;
    const m = /^@@ -(\d+)(?:,\d+)? \+(\d+)/.exec(line);
    if (m) { old = +m[1]!; next = +m[2]!; return { kind: '@', text: line }; }
    const kind = line[0];
    if (kind === '-') return { kind, number: old++, text: line.slice(1) || ' ' };
    if (kind === '+') return { kind, number: next++, text: line.slice(1) || ' ' };
    if (kind === ' ') { old++; return { kind, number: next++, text: line.slice(1) || ' ' }; }
    return { kind: '', text: line };
  });
}

// `show -s --format=%an%x1f%ae%x1f%cn%x1f%ct%x1f%B <hash>`
export const DETAIL_FORMAT = '--format=%an%x1f%ae%x1f%cn%x1f%ct%x1f%B';
export function parseDetail(text: string) {
  const [author, email, committer, time, ...body] = text.split('\x1f');
  return { author: author ?? '', email: email ?? '', committer: committer ?? '', committed: Number(time), body: body.join('\x1f').replace(/\n+$/, '') };
}

// Manygit: the repositories under a folder that isn't one itself (after github.com/rabeeh-ta/manygit).
export const DEPTH = { min: 1, max: 5, default: 3 };
const PRUNE = ['node_modules', 'vendor', 'venv', '__pycache__', 'dist', 'build', 'target', 'site-packages', 'Library'];
// A home folder, or a folder above one, is not searched: too big to walk, and on macOS walking it asks for Desktop,
// Documents and Downloads.
export function unsearched(cwd: string, home: string | null) {
  const dir = cwd.replace(/[/\\]+$/, '') || '/';
  if (dir === '/' || dir === '/root' || /^\/(home|Users)(\/[^/]+)?$/.test(dir)) return true;
  return Boolean(home) && (dir === home || home!.startsWith(dir + '/'));
}
export const depthOf = (value: unknown) => (Number.isInteger(value) && (value as number) >= DEPTH.min && (value as number) <= DEPTH.max ? value as number : DEPTH.default);
export function findArgs(root: string, depth: number) {
  return ['-H', root, '-mindepth', '1', '-maxdepth', String(depthOf(depth) + 1),
    '(', '-name', '.git', '-print', '-prune', ')', '-o',
    '(', '-type', 'd', '(', '-name', '.*', ...PRUNE.flatMap(n => ['-o', '-name', n]), ')', '-prune', ')'];
}
export type FoundRepo = { path: string; name: string; group: string };
export function parseFound(root: string, stdout: string, max = 500): FoundRepo[] {
  const base = root.replace(/[/\\]+$/, '');
  const paths = [...new Set(stdout.split('\n').filter(l => /[/\\]\.git$/.test(l)).map(l => l.replace(/[/\\]\.git$/, '')))];
  return paths.filter(p => p.startsWith(base + '/')).slice(0, max).map(path => {
    const rel = path.slice(base.length + 1), cut = rel.lastIndexOf('/');
    return { path, name: cut < 0 ? rel : rel.slice(cut + 1), group: cut < 0 ? '' : rel.slice(0, cut) };
  }).sort((a, b) => (a.group === b.group ? a.name.localeCompare(b.name) : a.group.localeCompare(b.group)));
}
export const REPO_STATUS = ['status', '--porcelain=v2', '--branch', '-z', '--no-renames', '--untracked-files=normal'];
export const LATEST_TAG = ['for-each-ref', '--count=1', '--sort=-creatordate', '--format=%(refname:short)', 'refs/tags'];
export type RepoStatus = { branch: string | null; detached: boolean; head: string | null; upstream: string | null; gone: boolean;
  ahead: number; behind: number; dirty: number; staged: number; hasRemote?: boolean; tag?: string | null; error?: string };
export function parseRepoStatus(stdout: string): RepoStatus {
  const s: RepoStatus = { branch: null, detached: false, head: null, upstream: null, gone: false, ahead: 0, behind: 0, dirty: 0, staged: 0 };
  let counted = false;
  for (const rec of stdout.split('\0')) {
    if (!rec) continue;
    if (!rec.startsWith('# ')) { s.dirty++; if (/^[12] [^.]/.test(rec)) s.staged++; continue; }
    const [key, ...rest] = rec.slice(2).split(' '), value = rest.join(' ');
    if (key === 'branch.oid') s.head = /^[0-9a-f]{40,64}$/.test(value) ? value : null;
    else if (key === 'branch.head') { s.detached = value === '(detached)'; s.branch = s.detached ? null : value; }
    else if (key === 'branch.upstream') s.upstream = value;
    else if (key === 'branch.ab') {
      const m = /^\+(\d+) -(\d+)$/.exec(value);
      if (m) { s.ahead = +m[1]!; s.behind = +m[2]!; counted = true; }
    }
  }
  s.gone = Boolean(s.upstream) && !counted;
  return s;
}
export function syncOf(st: RepoStatus | null): { kind: string; text: string } {
  if (!st) return { kind: 'loading', text: '…' };
  if (st.error) return { kind: 'error', text: '!' };
  if (st.detached) return { kind: 'ok', text: '分离' };
  if (!st.upstream) return st.hasRemote ? { kind: 'unpushed', text: '未推送' } : { kind: 'local', text: '无远程' };
  if (st.gone) return { kind: 'gone', text: '上游已删' };
  if (st.ahead && st.behind) return { kind: 'diverged', text: `↑${st.ahead} ↓${st.behind}` };
  if (st.ahead) return { kind: 'ahead', text: `↑${st.ahead}` };
  if (st.behind) return { kind: 'behind', text: `↓${st.behind}` };
  return { kind: 'ok', text: '✓' };
}
// A change under the git directory that moves a ref (a full refresh); anything else refreshes the status only.
export const REF_CHANGE = /(^|\/)(HEAD|packed-refs)$|(^|\/)refs\//;
