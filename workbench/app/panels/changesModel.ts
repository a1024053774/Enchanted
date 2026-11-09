// T-250: the "改动" panel's model, after herdr-gitview (MIT, Copyright (c) 2026 Adam Chmara; its diff view is adapted
// from herdr-reviewr, also MIT). Only its behaviour is followed; its Rust engine is not used. Pure functions: the main
// process (gitHost.ts) runs git with the argv built here and parses the output here; the panel renders the result.
export const UNTRACKED_COUNT_LIMIT = 200;
export const TRUNKS = ['main', 'master', 'trunk', 'develop', 'dev'];
const DIFF_OPTS = ['--no-color', '--no-ext-diff', '--no-textconv'];

export type Group = 'conflict' | 'staged' | 'unstaged';
export type ChangeEntry = { path: string; group: Group; code: string; untracked: boolean; add: number | null; del: number | null; binary: boolean };
export type Counts = Map<string, { add: number; del: number; binary: boolean }>;

// A repository-relative path as git prints it. Never absolute, never a parent or .git segment.
export function safePath(path: unknown): path is string {
  return typeof path === 'string' && path.length > 0 && !path.includes('\0') && !path.startsWith('/')
    && path.split('/').every(part => part && part !== '.' && part !== '..' && part !== '.git');
}
export const literal = (path: string) => `:(top,literal)${path}`;

// git status --porcelain=v2 -z --no-renames --untracked-files=all
export function parseStatusV2(text: string) {
  const conflict: string[] = [], staged: { path: string; code: string }[] = [], unstaged: { path: string; code: string; untracked: boolean }[] = [];
  const fields = text.split('\0');
  for (let i = 0; i < fields.length; i++) {
    const line = fields[i]!;
    if (!line) continue;
    const kind = line[0];
    if (kind === '?') { unstaged.push({ path: line.slice(2), code: '?', untracked: true }); continue; }
    if (kind === '!') continue;
    if (kind === 'u') { conflict.push(line.split(' ').slice(10).join(' ')); continue; }
    if (kind === '1' || kind === '2') {
      const parts = line.split(' ');
      const xy = parts[1]!, path = parts.slice(kind === '1' ? 8 : 9).join(' ');
      if (kind === '2') i++; // the original path follows a rename record
      if (xy[0] !== '.') staged.push({ path, code: xy[0]! });
      if (xy[1] !== '.') unstaged.push({ path, code: xy[1]!, untracked: false });
    }
  }
  return { conflict, staged, unstaged };
}

// git diff --numstat -z: "add\tdel\tpath\0", or "add\tdel\t\0from\0to\0" when the two sides have different paths
// (--no-index against /dev/null); binary files print "-\t-". The count is keyed by the new path.
export function parseNumstat(text: string): Counts {
  const counts: Counts = new Map(), fields = text.split('\0');
  for (let i = 0; i < fields.length; i++) {
    const record = fields[i]!;
    if (!record) continue;
    const [add, del, ...rest] = record.split('\t');
    let path = rest.join('\t');
    if (!path) { path = fields[i + 2] ?? ''; i += 2; }
    if (!path) continue;
    counts.set(path, { add: add === '-' ? 0 : Number(add), del: del === '-' ? 0 : Number(del), binary: add === '-' });
  }
  return counts;
}

export function groupEntries(status: ReturnType<typeof parseStatusV2>, staged: Counts, unstaged: Counts, untracked: Counts): ChangeEntry[] {
  const counted = (counts: Counts, path: string) => {
    const value = counts.get(path);
    return value ? { add: value.add, del: value.del, binary: value.binary } : { add: null, del: null, binary: false };
  };
  return [
    ...status.conflict.map(path => ({ path, group: 'conflict' as const, code: 'U', untracked: false, ...counted(unstaged, path) })),
    ...status.staged.map(({ path, code }) => ({ path, group: 'staged' as const, code, untracked: false, ...counted(staged, path) })),
    ...status.unstaged.map(({ path, code, untracked: u }) => ({ path, group: 'unstaged' as const, code, untracked: u, ...counted(u ? untracked : unstaged, path) })),
  ];
}

export function totals(entries: { add: number | null; del: number | null }[]) {
  return entries.reduce((sum, entry) => ({ add: sum.add + (entry.add ?? 0), del: sum.del + (entry.del ?? 0) }), { add: 0, del: 0 });
}

// The reads of one status refresh.
export const STATUS_ARGS = ['status', '--porcelain=v2', '-z', '--no-renames', '--untracked-files=all'];
export const STAGED_NUMSTAT = ['diff', ...DIFF_OPTS, '--cached', '--no-renames', '--numstat', '-z'];
export const UNSTAGED_NUMSTAT = ['diff', ...DIFF_OPTS, '--no-renames', '--numstat', '-z'];
export const untrackedNumstat = (path: string) => ['diff', '--no-index', ...DIFF_OPTS, '--numstat', '-z', '--', '/dev/null', path];

// Range scope: the work tree against the merge base (untracked files are not part of it, as in git diff <base>).
export const rangeNameStatus = (base: string) => ['diff', ...DIFF_OPTS, '--no-renames', '--name-status', '-z', base];
export const rangeNumstat = (base: string) => ['diff', ...DIFF_OPTS, '--no-renames', '--numstat', '-z', base];
export const commitNameStatus = (hash: string) => ['diff-tree', '-r', '--root', '--no-commit-id', ...DIFF_OPTS, '--no-renames', '--name-status', '-z', hash];
export const commitNumstat = (hash: string) => ['diff-tree', '-r', '--root', '--no-commit-id', ...DIFF_OPTS, '--no-renames', '--numstat', '-z', hash];
export function parseNameStatus(text: string) {
  const fields = text.split('\0'), files: { path: string; code: string }[] = [];
  for (let i = 0; i + 1 < fields.length; i += 2) if (fields[i]) files.push({ code: fields[i]![0]!, path: fields[i + 1]! });
  return files;
}
export const LOG_FORMAT = '--format=%H%x1f%h%x1f%s%x1f%an%x1f%at';
export function parseLog(text: string) {
  return text.split('\0').map(record => record.replace(/^\n/, '')).filter(Boolean).map(record => {
    const [hash, short, subject, author, time] = record.split('\x1f');
    return { hash: hash!, short: short!, subject: subject ?? '', author: author ?? '', time: Number(time) };
  });
}

export type DiffSide = { kind: 'staged' | 'unstaged' | 'untracked' | 'conflict' } | { kind: 'range'; base: string } | { kind: 'commit'; hash: string; parent: string | null };
export const FULL_CONTEXT = 100000;
export function diffArgsFor(path: string, side: DiffSide) {
  const context = `-U${FULL_CONTEXT}`;
  switch (side.kind) {
    case 'staged': return ['diff', ...DIFF_OPTS, '--cached', '--no-renames', context, '--', literal(path)];
    case 'unstaged': case 'conflict': return ['diff', ...DIFF_OPTS, '--no-renames', context, '--', literal(path)];
    case 'untracked': return ['diff', '--no-index', ...DIFF_OPTS, context, '--', '/dev/null', path];
    case 'range': return ['diff', ...DIFF_OPTS, '--no-renames', context, side.base, '--', literal(path)];
    case 'commit': return side.parent ? ['diff', ...DIFF_OPTS, '--no-renames', context, side.parent, side.hash, '--', literal(path)]
      : ['show', ...DIFF_OPTS, '--format=', context, side.hash, '--', literal(path)];
  }
}

// Base detection, after herdr-gitview's detect_base: among the branches HEAD descends from, the one whose merge base
// is closest to HEAD; ties prefer the trunk names, then a local branch, then the name. A branch that contains HEAD
// (merge base == HEAD) is not a base; neither is the current branch nor its own remote copies.
export type BaseCandidate = { name: string; remote: boolean; mergeBase: string; distance: number };
export function excludedFromBase(name: string, remote: boolean, current: string | null) {
  if (!current) return false;
  return remote ? name.endsWith('/' + current) : name === current;
}
export function pickBase(candidates: BaseCandidate[], head: string) {
  const rank = (name: string) => { const short = name.replace(/^[^/]+\//, ''); const index = TRUNKS.indexOf(short); return index < 0 ? TRUNKS.length : index; };
  return candidates.filter(c => c.mergeBase !== head).sort((a, b) => a.distance - b.distance || rank(a.name) - rank(b.name)
    || Number(a.remote) - Number(b.remote) || a.name.localeCompare(b.name))[0] ?? null;
}

// The repository changes the panel asks for. Built here, run by the main process with the argv as is.
export type ChangesAction = { type: 'stage' | 'unstage' | 'discard' | 'commit'; entries?: { path: string; group: Group; untracked: boolean }[]; message?: string };
export function changeCommands(action: ChangesAction, repo: { hasHead: boolean; stagedCount: number }): string[][] {
  const entries = action.entries ?? [];
  if (action.type !== 'commit') {
    if (!entries.length) throw new Error('没有选中文件');
    if (entries.some(entry => !safePath(entry.path))) throw new Error('文件路径不合法');
  }
  const specs = (list: typeof entries) => list.map(entry => literal(entry.path));
  switch (action.type) {
    case 'stage': return [['add', '-A', '--', ...specs(entries)]];
    case 'unstage': return [repo.hasHead ? ['reset', '-q', 'HEAD', '--', ...specs(entries)] : ['rm', '--cached', '-r', '-q', '--', ...specs(entries)]];
    case 'discard': {
      if (entries.some(entry => entry.group === 'conflict')) throw new Error('冲突文件不能直接丢弃：先解决冲突');
      const untracked = entries.filter(entry => entry.untracked), unstaged = entries.filter(entry => !entry.untracked && entry.group === 'unstaged');
      const staged = entries.filter(entry => entry.group === 'staged');
      if (staged.length && !repo.hasHead) throw new Error('还没有提交，已暂存的文件没有可恢复的版本');
      return [
        ...(staged.length ? [['restore', '--source=HEAD', '--staged', '--worktree', '--', ...specs(staged)]] : []),
        ...(unstaged.length ? [['restore', '--worktree', '--', ...specs(unstaged)]] : []),
        ...(untracked.length ? [['clean', '-f', '-q', '--', ...specs(untracked)]] : []),
      ];
    }
    case 'commit': {
      const message = String(action.message ?? '').trim();
      if (!message) throw new Error('提交说明为空');
      // No staged file: commit everything, as herdr-gitview does (git add -A first).
      return [...(repo.stagedCount ? [] : [['add', '-A']]), ['commit', '-q', '-m', message]];
    }
    default: throw new Error('未知的改动操作');
  }
}

// ---- Diff rendering ----
export type DiffLine = { kind: 'add' | 'del' | 'ctx' | 'hunk' | 'meta'; old: number | null; next: number | null; text: string;
  spans?: [number, number] };
export const DIFF_LINE_LIMIT = 20000;
export function parseDiff(text: string): DiffLine[] {
  const lines = text.replace(/\n$/, '').split('\n'), out: DiffLine[] = [];
  let first = lines.findIndex(line => line.startsWith('@@'));
  if (first < 0) return [];
  let old = 0, next = 0, combined = false;
  for (const raw of lines.slice(first, first + DIFF_LINE_LIMIT)) {
    const line = raw.length > 4000 ? raw.slice(0, 4000) + '…' : raw;
    const hunk = /^@@+ -(\d+)(?:,\d+)? .*?\+(\d+)/.exec(line);
    if (hunk) {
      // A conflict shows as a combined diff ("@@@"): two prefix columns, numbered by the work tree side only.
      combined = line.startsWith('@@@'); old = +hunk[1]!; next = +hunk[2]!;
      if (combined) next = +/\+(\d+)(?:,\d+)? @@@/.exec(line)![1]!;
      out.push({ kind: 'hunk', old: null, next: null, text: line }); continue;
    }
    if (line.startsWith('\\')) { out.push({ kind: 'meta', old: null, next: null, text: line }); continue; }
    if (combined) {
      const prefix = line.slice(0, 2), text = line.slice(2);
      if (prefix.includes('-')) out.push({ kind: 'del', old: null, next: null, text });
      else out.push({ kind: prefix.includes('+') ? 'add' : 'ctx', old: null, next: next++, text });
      continue;
    }
    const mark = line[0];
    if (mark === '+') out.push({ kind: 'add', old: null, next: next++, text: line.slice(1) });
    else if (mark === '-') out.push({ kind: 'del', old: old++, next: null, text: line.slice(1) });
    else out.push({ kind: 'ctx', old: old++, next: next++, text: line.slice(1) });
  }
  markWords(out);
  return out;
}

// Word-level emphasis: a run of deleted lines followed by a run of added lines is paired line by line; in each pair
// the part between the common prefix and the common suffix is marked (as herdr-reviewr does).
function markWords(lines: DiffLine[]) {
  for (let i = 0; i < lines.length;) {
    if (lines[i]!.kind !== 'del') { i++; continue; }
    let d = i; while (d < lines.length && lines[d]!.kind === 'del') d++;
    let a = d; while (a < lines.length && lines[a]!.kind === 'add') a++;
    const pairs = Math.min(d - i, a - d);
    for (let k = 0; k < pairs; k++) {
      const before = lines[i + k]!, after = lines[d + k]!;
      let start = 0;
      while (start < before.text.length && start < after.text.length && before.text[start] === after.text[start]) start++;
      let end = 0;
      while (end < before.text.length - start && end < after.text.length - start
        && before.text[before.text.length - 1 - end] === after.text[after.text.length - 1 - end]) end++;
      // Only a partial change is worth marking; a line rewritten from scratch stays plain.
      if (start + end > 0) {
        if (before.text.length - end > start) before.spans = [start, before.text.length - end];
        if (after.text.length - end > start) after.spans = [start, after.text.length - end];
      }
    }
    i = a;
  }
}

// Context folding: a run of more than FOLD context lines keeps KEEP lines at each end and folds the rest.
export const FOLD = 8, KEEP = 3;
export type DiffRow = { line: DiffLine; index: number } | { fold: number; from: number; count: number };
export function foldRows(lines: DiffLine[], open: Set<number>): DiffRow[] {
  const rows: DiffRow[] = [];
  for (let i = 0; i < lines.length;) {
    if (lines[i]!.kind !== 'ctx') { rows.push({ line: lines[i]!, index: i }); i++; continue; }
    let j = i; while (j < lines.length && lines[j]!.kind === 'ctx') j++;
    const atStart = i === 0 || lines[i - 1]!.kind === 'hunk', atEnd = j === lines.length;
    const head = atStart ? 0 : KEEP, tail = atEnd ? 0 : KEEP;
    if (j - i > FOLD && !open.has(i) && j - i - head - tail > 0) {
      for (let k = i; k < i + head; k++) rows.push({ line: lines[k]!, index: k });
      rows.push({ fold: i, from: i + head, count: j - i - head - tail });
      for (let k = j - tail; k < j; k++) rows.push({ line: lines[k]!, index: k });
    } else for (let k = i; k < j; k++) rows.push({ line: lines[k]!, index: k });
    i = j;
  }
  return rows;
}

// ---- Syntax highlighting (small, per line; colors come from the terminal palette) ----
const C_LIKE = new Set(['js', 'mjs', 'cjs', 'jsx', 'ts', 'tsx', 'mts', 'cts', 'java', 'c', 'h', 'cc', 'cpp', 'hpp', 'cs', 'go', 'rs', 'swift', 'kt', 'kts', 'scala', 'dart', 'css', 'scss', 'less', 'php', 'json', 'jsonc']);
const HASH_LIKE = new Set(['py', 'rb', 'sh', 'bash', 'zsh', 'fish', 'yml', 'yaml', 'toml', 'pl', 'r', 'mk', 'cmake', 'conf', 'ini', 'dockerfile', 'makefile']);
const KEYWORDS = new Set(('as async await break case catch class const continue def default defer del delete do elif else enum export extends ' +
  'false fn for from func function go if impl import in interface is let match mod module mut new nil none not null or package pass ' +
  'private protected pub public raise return self static struct super switch this throw true try type typeof use var void where while with yield ' +
  'True False None and lambda then fi done esac local echo').split(' '));
export type Token = { text: string; kind: 'plain' | 'keyword' | 'string' | 'comment' | 'number' };
export function languageOf(path: string) {
  const name = path.split('/').pop()!.toLowerCase();
  const ext = name.includes('.') ? name.split('.').pop()! : name;
  return C_LIKE.has(ext) ? 'c' : HASH_LIKE.has(ext) ? 'hash' : ext === 'md' || ext === 'markdown' ? 'md' : null;
}
export function tokenize(text: string, language: string | null): Token[] {
  if (!language || language === 'md') return [{ text, kind: 'plain' }];
  const comment = language === 'c' ? /^\/\/.*|^\/\*.*?(\*\/|$)/ : /^#.*/;
  const tokens: Token[] = [];
  let rest = text;
  const push = (value: string, kind: Token['kind']) => {
    const last = tokens[tokens.length - 1];
    if (last && last.kind === kind) last.text += value; else tokens.push({ text: value, kind });
  };
  while (rest) {
    let m: RegExpExecArray | null;
    if ((m = comment.exec(rest))) { push(m[0], 'comment'); rest = rest.slice(m[0].length); continue; }
    if ((m = /^(["'`])(?:\\.|(?!\1).)*\1?/.exec(rest))) { push(m[0], 'string'); rest = rest.slice(m[0].length); continue; }
    if ((m = /^\b\d[\d_]*(\.\d+)?([eE][+-]?\d+)?\b|^\b0x[0-9a-fA-F]+\b/.exec(rest))) { push(m[0], 'number'); rest = rest.slice(m[0].length); continue; }
    if ((m = /^[A-Za-z_$][\w$]*/.exec(rest))) { push(m[0], KEYWORDS.has(m[0]) ? 'keyword' : 'plain'); rest = rest.slice(m[0].length); continue; }
    push(rest[0]!, 'plain'); rest = rest.slice(1);
  }
  return tokens;
}

// ---- Tree view ----
export type TreeNode = { name: string; path: string; children: TreeNode[]; entry?: ChangeEntry };
export function buildTree(entries: ChangeEntry[]): TreeNode[] {
  const root: TreeNode = { name: '', path: '', children: [] };
  for (const entry of entries) {
    const parts = entry.path.split('/');
    let node = root;
    parts.forEach((part, index) => {
      const path = parts.slice(0, index + 1).join('/');
      if (index === parts.length - 1) { node.children.push({ name: part, path, children: [], entry }); return; }
      let child = node.children.find(c => !c.entry && c.name === part);
      if (!child) { child = { name: part, path, children: [] }; node.children.push(child); }
      node = child;
    });
  }
  // A folder with one folder inside shows as "a/b".
  const compact = (node: TreeNode): TreeNode => {
    const children = node.children.map(compact);
    if (!node.entry && node.name && children.length === 1 && !children[0]!.entry) return { ...children[0]!, name: node.name + '/' + children[0]!.name };
    return { ...node, children };
  };
  return compact(root).children;
}

export const IMAGE = /\.(png|jpe?g|gif|webp|bmp|ico|svg)$/i;
export const imageType = (path: string) => {
  const ext = path.split('.').pop()!.toLowerCase();
  return ext === 'svg' ? 'image/svg+xml' : ext === 'jpg' ? 'image/jpeg' : ext === 'ico' ? 'image/x-icon' : 'image/' + ext;
};

// ---- Review notes ----
export type Note = { path: string; from: number; to: number; side: 'old' | 'new'; quote: string[]; text: string };
export function notesText(notes: Note[]) {
  return ['审阅备注（' + notes.length + ' 条）：', ...notes.flatMap(note => [
    '', `${note.path}:${note.from === note.to ? note.from : note.from + '-' + note.to}${note.side === 'old' ? '（改动前）' : ''}`,
    ...note.quote.map(line => '> ' + line), note.text.trim(),
  ])].join('\n');
}

// ---- Markdown preview (a small subset rendered as React elements by the panel; no HTML is injected) ----
export type MdBlock = { kind: 'h'; level: number; text: string } | { kind: 'p'; text: string } | { kind: 'li'; text: string; ordered: boolean }
  | { kind: 'code'; text: string } | { kind: 'quote'; text: string } | { kind: 'hr' };
export function markdownBlocks(text: string): MdBlock[] {
  const blocks: MdBlock[] = [], lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!;
    if (/^```/.test(line)) {
      const body: string[] = [];
      for (i++; i < lines.length && !/^```/.test(lines[i]!); i++) body.push(lines[i]!);
      blocks.push({ kind: 'code', text: body.join('\n') }); continue;
    }
    let m: RegExpExecArray | null;
    if ((m = /^(#{1,6})\s+(.*)/.exec(line))) blocks.push({ kind: 'h', level: m[1]!.length, text: m[2]! });
    else if (/^\s*([-*_])\s*\1\s*\1[\s\-*_]*$/.test(line)) blocks.push({ kind: 'hr' });
    else if ((m = /^\s*[-*+]\s+(.*)/.exec(line))) blocks.push({ kind: 'li', text: m[1]!, ordered: false });
    else if ((m = /^\s*\d+[.)]\s+(.*)/.exec(line))) blocks.push({ kind: 'li', text: m[1]!, ordered: true });
    else if ((m = /^>\s?(.*)/.exec(line))) blocks.push({ kind: 'quote', text: m[1]! });
    else if (line.trim()) {
      const last = blocks[blocks.length - 1];
      if (last?.kind === 'p' && lines[i - 1]?.trim()) last.text += ' ' + line.trim(); else blocks.push({ kind: 'p', text: line.trim() });
    }
  }
  return blocks;
}
export type Inline = { text: string; kind: 'plain' | 'code' | 'strong' | 'em' | 'link' };
export function inlineSpans(text: string): Inline[] {
  const out: Inline[] = [], pattern = /`([^`]+)`|\*\*([^*]+)\*\*|\*([^*]+)\*|\[([^\]]+)\]\([^)]*\)/g;
  let last = 0, m: RegExpExecArray | null;
  while ((m = pattern.exec(text))) {
    if (m.index > last) out.push({ text: text.slice(last, m.index), kind: 'plain' });
    out.push(m[1] !== undefined ? { text: m[1], kind: 'code' } : m[2] !== undefined ? { text: m[2], kind: 'strong' }
      : m[3] !== undefined ? { text: m[3], kind: 'em' } : { text: m[4]!, kind: 'link' });
    last = pattern.lastIndex;
  }
  if (last < text.length) out.push({ text: text.slice(last), kind: 'plain' });
  return out;
}
