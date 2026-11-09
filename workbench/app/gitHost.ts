// T-249: the git the side panels run, in the main process. Every command is an argv array for execFile, never a shell
// line. Reads get the no-lock flags and an allowlist of read-only subcommands; repository changes come in as a panel
// action and the argv is built here (commandsFor), so a name starting with "-" never reaches git as an option. A
// directory under the gate's task worktrees (<state>/worktrees/) is read-only: the gate guards its Git metadata.
import { execFile } from 'node:child_process';
import { existsSync, lstatSync, readFileSync, realpathSync, statSync, watch, type FSWatcher } from 'node:fs';
import { isAbsolute, join, relative, sep } from 'node:path';
import { commandsFor, doneText, findArgs, gitError, LATEST_TAG, objectId, parseFound, parseRepoStatus, READ, REF_CHANGE, REPO_STATUS,
  unsearched, type Action, type RepoStatus } from './panels/gitGraphModel.ts';
import { changeCommands, commitNameStatus, commitNumstat, diffArgsFor, excludedFromBase, groupEntries, LOG_FORMAT, parseLog, parseNameStatus,
  parseNumstat, parseStatusV2, pickBase, rangeNameStatus, rangeNumstat, safePath, STAGED_NUMSTAT, STATUS_ARGS, UNSTAGED_NUMSTAT,
  UNTRACKED_COUNT_LIMIT, untrackedNumstat, TRUNKS, type ChangesAction, type DiffSide } from './panels/changesModel.ts';

export type GitResult = { code: number | null; stdout: string; stderr: string };
const env = () => ({ ...process.env, GIT_TERMINAL_PROMPT: '0', GIT_OPTIONAL_LOCKS: '0', GCM_INTERACTIVE: '0', LC_ALL: 'C' });

function exec(file: string, argv: string[], cwd: string, encoding: 'utf8' | 'base64' = 'utf8', environment = env()): Promise<GitResult> {
  return new Promise(resolve => {
    execFile(file, argv, { cwd, env: environment, maxBuffer: 64 * 1024 * 1024, encoding: encoding === 'base64' ? 'buffer' : 'utf8', timeout: 60000 },
      (error, stdout, stderr) => {
        const code = error ? (typeof (error as any).code === 'number' ? (error as any).code : null) : 0;
        resolve({ code, stdout: encoding === 'base64' ? Buffer.from(stdout as any).toString('base64') : String(stdout), stderr: String(stderr) });
      });
  });
}

function directory(dir: unknown) {
  if (typeof dir !== 'string' || !isAbsolute(dir) || !existsSync(dir) || !statSync(dir).isDirectory()) throw new Error('目录不存在：' + String(dir));
  return realpathSync(dir);
}

// The gate keeps every task worktree under <state>/worktrees/<project>/ (gates/core.ts projectWorktrees).
export function managedWorktree(dir: string, state: string) {
  const worktrees = join(state, 'worktrees');
  if (!existsSync(worktrees) || !existsSync(dir)) return false;
  return realpathSync(dir).startsWith(realpathSync(worktrees) + sep);
}

// Accept only the read forms used by the panels. Subcommand names alone are insufficient:
// symbolic-ref can write HEAD, and Git accepts abbreviated --output options.
const READ_OPTIONS: Record<string, readonly string[]> = {
  log: ['-z', '--branches', '--tags', '--remotes', '--ignore-missing', '--date-order', '--decorate=full'],
  status: ['--porcelain=v1', '--porcelain=v2', '--branch', '-z', '--no-renames', '--untracked-files=all', '--untracked-files=normal'],
  show: ['-s', '--no-color', '--no-ext-diff', '--no-textconv'],
  diff: ['-z', '--no-renames', '--no-color', '--no-ext-diff', '--no-textconv', '--name-status', '--numstat'],
  'diff-tree': ['-z', '--root', '--no-commit-id', '-r', '--no-renames', '--no-ext-diff', '--no-textconv', '--name-status', '--numstat'],
  'for-each-ref': ['--format=%(refname:short)'],
  'ls-files': ['--others', '--exclude-standard', '-z'],
};
function readAllowed(argv: string[]) {
  const [command, ...args] = argv;
  if (command === 'diff' && args[0] === '--no-index') return argv.length === 8
    && argv.slice(0, 7).join('\0') === 'diff\0--no-index\0--no-color\0--no-ext-diff\0--no-textconv\0--\0/dev/null';
  if (command === 'remote') return args.length === 0;
  if (command === 'symbolic-ref') return args.join('\0') === '-q\0--short\0HEAD';
  if (command === 'rev-parse') return args.join('\0') === '--verify\0-q\0HEAD';
  if (command === 'hash-object') return args.join('\0') === '-t\0tree\0/dev/null';
  const options = READ_OPTIONS[command!];
  if (!options) return false;
  const separator = args.indexOf('--');
  if (separator >= 0 && !['diff', 'show'].includes(command!)) return false;
  return args.slice(0, separator < 0 ? args.length : separator).every(arg => options.includes(arg)
    || (['log', 'show'].includes(command!) && arg.startsWith('--format='))
    || (command === 'log' && /^-n[1-9]\d*$/.test(arg))
    || (['log', 'show', 'diff', 'diff-tree'].includes(command!) && (arg === 'HEAD' || objectId(arg)))
    || (command === 'for-each-ref' && ['refs/heads', 'refs/tags'].includes(arg)));
}
export async function gitRead(dir: unknown, argv: unknown, encoding: unknown = 'utf8'): Promise<GitResult> {
  const cwd = directory(dir);
  if (!Array.isArray(argv) || !argv.length || argv.some(value => typeof value !== 'string')) throw new Error('Invalid git argv');
  if (!readAllowed(argv)) throw new Error('不允许的只读 git 命令或选项');
  if (encoding !== 'utf8' && encoding !== 'base64') throw new Error('Invalid encoding');
  const noIndex = argv[0] === 'diff' && argv[1] === '--no-index';
  if (noIndex) {
    // This form compares one ordinary repository file with /dev/null. No directories, stdin,
    // pathspecs, metadata or symlink escapes; require the repository root used by the panel.
    const path = argv[7];
    if (!path.startsWith('./') || path.slice(2).split('/').some(part => !part || ['.', '..', '.git'].includes(part)))
      throw new Error('未跟踪文件路径不合法');
    const root = await exec('git', [...READ, 'rev-parse', '--show-toplevel'], cwd);
    if (root.code !== 0 || realpathSync(root.stdout.trim()) !== cwd) throw new Error('未跟踪文件必须从仓库根目录读取');
    const file = join(cwd, path), resolved = realpathSync(file);
    if (!resolved.startsWith(cwd + sep) || relative(cwd, resolved).split(sep).includes('.git') || !lstatSync(file).isFile())
      throw new Error('未跟踪文件必须是仓库内的普通文件');
  }
  const noPrograms = ['log', 'show', 'diff', 'diff-tree'].includes(argv[0]) ? ['--no-ext-diff', '--no-textconv'] : [];
  const result = await exec('git', [...READ, argv[0], ...noPrograms, ...argv.slice(1)], cwd, encoding);
  // --no-index implies --exit-code: 1 with no diagnostic means a successfully read difference.
  return noIndex && result.code === 1 && !result.stderr ? { ...result, code: 0 } : result;
}

export async function repoOf(dir: unknown, state: string) {
  const cwd = directory(dir);
  const top = await exec('git', [...READ, 'rev-parse', '--path-format=absolute', '--show-toplevel', '--git-common-dir', '--git-dir'], cwd);
  const managed = managedWorktree(cwd, state);
  if (top.code !== 0) return { dir: cwd, top: null, commonDir: null, gitDir: null, managed };
  const [root, commonDir, gitDir] = top.stdout.trim().split('\n');
  return { dir: cwd, top: root!, commonDir: commonDir!, gitDir: gitDir!, managed: managed || managedWorktree(root!, state) };
}

async function remotesOf(cwd: string) {
  const listed = await exec('git', [...READ, 'remote'], cwd);
  return listed.code === 0 ? listed.stdout.split('\n').filter(Boolean) : [];
}

async function writable(dir: unknown, state: string) {
  const repo = await repoOf(dir, state);
  if (!repo.top) throw new Error('不是 Git 仓库');
  if (repo.managed) throw new Error('门禁管理的任务 worktree 只读：门禁保护它的 Git 元数据，直接改动算人工介入。');
  return repo;
}

export async function gitAction(dir: unknown, state: string, action: Action, values: Record<string, any>) {
  if (!action || typeof action !== 'object' || typeof action.type !== 'string') throw new Error('Invalid action');
  const repo = await writable(dir, state);
  const commands = commandsFor(action, values ?? {}, { remotes: await remotesOf(repo.top!) });
  const ran: string[][] = [];
  for (const argv of commands) {
    const result = await exec('git', argv, repo.top!);
    if (result.code !== 0) throw new Error(gitError(result));
    ran.push(argv);
  }
  return { text: doneText(action, values ?? {}), argv: ran };
}

// The working directory of a terminal's shell process.
export async function processCwd(pid: number) {
  if (!Number.isSafeInteger(pid) || pid <= 1) throw new Error('Invalid pid');
  const found = await exec('/usr/sbin/lsof', ['-a', '-p', String(pid), '-d', 'cwd', '-Fn'], '/');
  const line = found.stdout.split('\n').find(value => value.startsWith('n/'));
  if (!line) throw new Error('读不到终端的工作目录：' + (found.stderr.trim() || 'lsof 没有输出'));
  return line.slice(1);
}

// Manygit: the repositories under root, each with its status and (optionally) its newest tag.
export async function scanRepos(root: unknown, depth: number, home: string, tags: boolean) {
  const cwd = directory(root);
  if (unsearched(cwd, home)) return { root: cwd, unsearched: true, repos: [] };
  // An unreadable subfolder makes find exit 1; its output still counts.
  const found = await exec('/usr/bin/find', findArgs(cwd, depth), cwd);
  const repos = parseFound(cwd, found.stdout);
  const rows: ((typeof repos)[number] & { status: RepoStatus })[] = [];
  let next = 0;
  await Promise.all(Array.from({ length: 6 }, async () => {
    while (next < repos.length) {
      const repo = repos[next++]!;
      const status = await exec('git', [...READ, ...REPO_STATUS], repo.path);
      const parsed: RepoStatus = status.code === 0 ? parseRepoStatus(status.stdout) : { ...parseRepoStatus(''), error: gitError(status) };
      parsed.hasRemote = (await remotesOf(repo.path)).length > 0;
      if (tags) {
        const tag = await exec('git', [...READ, ...LATEST_TAG], repo.path);
        parsed.tag = tag.code === 0 ? tag.stdout.trim() || null : null;
      }
      rows.push({ ...repo, status: parsed });
    }
  }));
  rows.sort((a, b) => repos.indexOf(a) - repos.indexOf(b));
  return { root: cwd, unsearched: false, repos: rows.map(row => ({ path: row.path, name: row.name, group: row.group, status: row.status })) };
}

// Watches the work tree and the git common dir. A ref change asks for a full refresh, anything else for the status.
// Events come in a burst; one message per 200 ms.
type Watch = { watchers: FSWatcher[]; timer: NodeJS.Timeout | null; refs: boolean };
const watches = new Map<string, Watch>();
let watchSequence = 0;
export function watchRepo(repo: { top: string; commonDir: string; gitDir: string }, send: (change: { id: string; refs: boolean }) => void) {
  const id = String(++watchSequence);
  const entry: Watch = { watchers: [], timer: null, refs: false };
  const note = (refs: boolean) => {
    entry.refs ||= refs;
    entry.timer ??= setTimeout(() => { const value = entry.refs; entry.refs = false; entry.timer = null; send({ id, refs: value }); }, 200);
  };
  const gitDirs = [repo.commonDir, repo.gitDir];
  const add = (root: string, inGit: boolean) => {
    try {
      entry.watchers.push(watch(root, { recursive: true }, (_type, name) => {
        const path = name ? join(root, String(name)) : root;
        const git = inGit ? root : gitDirs.find(dir => path === dir || path.startsWith(dir + sep));
        if (!git) return note(false);
        const inside = relative(git, path);
        if (/(^|\/)(index\.lock|objects\/|logs\/)/.test(inside) && !REF_CHANGE.test(inside)) return note(false);
        note(REF_CHANGE.test(inside));
      }));
    } catch (error) { console.error('Git watch failed:', root, String(error)); }
  };
  add(repo.top, false);
  if (!repo.commonDir.startsWith(repo.top + sep)) add(repo.commonDir, true);
  if (repo.gitDir !== repo.commonDir && !repo.gitDir.startsWith(repo.top + sep)) add(repo.gitDir, true);
  watches.set(id, entry);
  return id;
}
export function unwatchRepo(id: string) {
  const entry = watches.get(id);
  if (!entry) return;
  for (const watcher of entry.watchers) watcher.close();
  if (entry.timer) clearTimeout(entry.timer);
  watches.delete(id);
}

// T-250: the "改动" panel's reads and writes. The panel names what it wants; the argv is built from changesModel.ts
// here, so no argument from the renderer reaches git as an option. Reads run with the no-lock flags.
async function readGit(cwd: string, argv: string[], ok: number[] = [0]) {
  const result = await exec('git', [...READ, ...argv], cwd);
  if (result.code === null || !ok.includes(result.code)) throw new Error(gitError(result));
  return result.stdout;
}
async function headOf(cwd: string) {
  const head = await exec('git', [...READ, 'rev-parse', '--verify', '-q', 'HEAD'], cwd);
  return head.code === 0 ? head.stdout.trim() : null;
}
const revision = (value: unknown) => typeof value === 'string' && objectId(value);

export async function changesStatus(top: string) {
  const status = parseStatusV2(await readGit(top, STATUS_ARGS));
  const staged = parseNumstat(await readGit(top, STAGED_NUMSTAT)), unstaged = parseNumstat(await readGit(top, UNSTAGED_NUMSTAT));
  const untracked = new Map();
  const files = status.unstaged.filter(entry => entry.untracked).slice(0, UNTRACKED_COUNT_LIMIT);
  // --no-index exits 1 when the file differs from /dev/null, which every non-empty file does.
  for (const entry of files) {
    const [value] = parseNumstat(await readGit(top, untrackedNumstat(entry.path), [0, 1])).values();
    // An empty file has no line to count and prints nothing.
    untracked.set(entry.path, value ?? { add: 0, del: 0, binary: false });
  }
  return { head: await headOf(top), entries: groupEntries(status, staged, unstaged, untracked) };
}

export async function detectBase(top: string) {
  const head = await headOf(top);
  if (!head) return { head: null, current: null, base: null, candidates: [] };
  const current = await exec('git', [...READ, 'symbolic-ref', '-q', '--short', 'HEAD'], top);
  const name = current.code === 0 ? current.stdout.trim() : null;
  const refs = (await readGit(top, ['for-each-ref', '--format=%(refname)%00%(refname:short)%00%(symref)', 'refs/heads', 'refs/remotes']))
    .split('\n').filter(Boolean).map(line => line.split('\0')).filter(([, , symref]) => !symref)
    .map(([full, short]) => ({ name: short!, remote: full!.startsWith('refs/remotes/') }))
    .filter(ref => !excludedFromBase(ref.name, ref.remote, name));
  const trunk = (ref: { name: string }) => TRUNKS.includes(ref.name.replace(/^[^/]+\//, ''));
  // Trunk names first, then at most 40 others: each candidate costs two git runs.
  const ordered = [...refs.filter(trunk), ...refs.filter(ref => !trunk(ref)).slice(0, 40)];
  const candidates = [];
  for (const ref of ordered) {
    const base = await exec('git', [...READ, 'merge-base', 'HEAD', 'refs/' + (ref.remote ? 'remotes/' : 'heads/') + ref.name], top);
    if (base.code !== 0) continue;
    const mergeBase = base.stdout.trim();
    const distance = Number((await readGit(top, ['rev-list', '--count', `${mergeBase}..HEAD`])).trim());
    candidates.push({ ...ref, mergeBase, distance });
  }
  const best = pickBase(candidates, head);
  return { head, current: name, base: best, candidates: candidates.filter(c => c.mergeBase !== head).map(c => c.name) };
}

async function mergeBaseWith(top: string, base: unknown) {
  if (typeof base !== 'string' || !base || base.startsWith('-')) throw new Error('基线不合法');
  const found = await exec('git', [...READ, 'merge-base', 'HEAD', base], top);
  if (found.code !== 0) throw new Error('找不到与 ' + base + ' 的合并基点');
  return found.stdout.trim();
}

export type ChangesRequest = { kind: 'status' } | { kind: 'base' } | { kind: 'range'; base: string } | { kind: 'commit'; hash: string }
  | { kind: 'log'; base: string | null } | { kind: 'diff'; path: string; side: DiffSide }
  | { kind: 'blob'; path: string; rev: string } | { kind: 'worktree'; path: string };

export async function changesRead(dir: unknown, state: string, request: ChangesRequest) {
  const repo = await repoOf(dir, state);
  if (!repo.top) throw new Error('不是 Git 仓库');
  const top = repo.top;
  if (!request || typeof request !== 'object') throw new Error('Invalid request');
  switch (request.kind) {
    case 'status': return changesStatus(top);
    case 'base': return detectBase(top);
    case 'range': {
      const mergeBase = await mergeBaseWith(top, request.base);
      const counts = parseNumstat(await readGit(top, rangeNumstat(mergeBase)));
      const files = parseNameStatus(await readGit(top, rangeNameStatus(mergeBase))).map(file => ({ ...file, ...(counts.get(file.path) ?? { add: null, del: null, binary: false }) }));
      return { mergeBase, files };
    }
    case 'commit': {
      if (!revision(request.hash)) throw new Error('提交哈希不合法');
      const parents = (await readGit(top, ['rev-list', '--parents', '-n1', request.hash])).trim().split(' ').slice(1);
      const counts = parseNumstat(await readGit(top, commitNumstat(request.hash)));
      const files = parseNameStatus(await readGit(top, commitNameStatus(request.hash))).map(file => ({ ...file, ...(counts.get(file.path) ?? { add: null, del: null, binary: false }) }));
      return { parent: parents[0] ?? null, files };
    }
    case 'log': {
      const range = request.base ? [`${await mergeBaseWith(top, request.base)}..HEAD`] : ['-n200', 'HEAD'];
      if (!(await headOf(top))) return { commits: [] };
      return { commits: parseLog(await readGit(top, ['log', '-z', LOG_FORMAT, ...range])) };
    }
    case 'diff': {
      if (!safePath(request.path)) throw new Error('文件路径不合法');
      const side = request.side;
      if (side?.kind === 'range' && !revision(side.base)) throw new Error('基线不合法');
      if (side?.kind === 'commit' && (!revision(side.hash) || (side.parent !== null && !revision(side.parent)))) throw new Error('提交哈希不合法');
      return { text: await readGit(top, diffArgsFor(request.path, side), side?.kind === 'untracked' ? [0, 1] : [0]) };
    }
    case 'blob': {
      if (!safePath(request.path) || !(request.rev === 'HEAD' || request.rev === ':0' || revision(request.rev))) throw new Error('Invalid blob');
      const spec = request.rev === ':0' ? ':0:' + request.path : request.rev + ':' + request.path;
      const result = await exec('git', [...READ, 'show', '--no-textconv', spec], top, 'base64');
      return { base64: result.code === 0 ? result.stdout : null };
    }
    case 'worktree': {
      if (!safePath(request.path)) throw new Error('文件路径不合法');
      const file = join(top, request.path);
      if (!existsSync(file)) return { base64: null };
      const resolved = realpathSync(file);
      if (!resolved.startsWith(top + sep) || !lstatSync(resolved).isFile() || statSync(resolved).size > 20 * 1024 * 1024) throw new Error('只能读取仓库内 20 MB 以内的普通文件');
      return { base64: readFileSync(resolved).toString('base64') };
    }
    default: throw new Error('未知的读取');
  }
}

export async function changesAction(dir: unknown, state: string, action: ChangesAction) {
  if (!action || typeof action !== 'object') throw new Error('Invalid action');
  const repo = await writable(dir, state);
  const top = repo.top!;
  const status = action.type === 'commit' ? await changesStatus(top) : null;
  const commands = changeCommands(action, { hasHead: Boolean(await headOf(top)),
    stagedCount: status ? status.entries.filter(entry => entry.group === 'staged').length : 0 });
  if (action.type === 'commit' && status && !status.entries.length) throw new Error('没有可提交的改动');
  for (const argv of commands) {
    const result = await exec('git', argv, top);
    if (result.code !== 0) throw new Error(gitError(result));
  }
  return { argv: commands };
}
