import { closeSync, existsSync, openSync, readFileSync, readSync, readdirSync, statSync } from 'node:fs';
import { basename, join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import type { ShellNativeReport } from './panes.ts';
import type { TrajectoryArchive } from './trajectoryArchive.ts';

// T-195: what "复制深度链接" copies for a session: the CLI's name, the CLI's own session id, and where the CLI keeps the
// session's record. Facts: findings/2026-10-27-native-session-ids.zh-CN.md. An id a2a made up (osc7501:<launch>) is never
// passed off as the CLI's; a session whose current id or record cannot be pinned down is unavailable, with the reason.
export type NativeLink = { available: true; cli: string; session: string; record: string; text: string }
  | { available: false; cli: string | null; reason: string };
// shell: for a project terminal, the CLI in front of it now and the session that same process reported (Panes.shellNative);
// null when the terminal is closed.
export type ShellNative = { cli: string | null; report: ShellNativeReport | null } | null;

const names: Record<string, string> = { claude: 'Claude Code', codex: 'Codex', agy: 'agy', antigravity: 'agy', opencode: 'opencode' };

export function nativeLink(db: DatabaseSync, root: string, archive: TrajectoryArchive, launch: string, home: string, shell: ShellNative): NativeLink {
  const row = db.prepare('SELECT data FROM launch_records WHERE id=?').get(launch);
  if (!row) return { available: false, cli: null, reason: '没有这个会话的启动记录' };
  const record = JSON.parse(String(row.data));
  const userHome = typeof record.env?.HOME === 'string' ? record.env.HOME : home;
  if (record.role === 'shell') return terminalLink(record, userHome, shell);
  // A worker, reviewer or monitor runs the one CLI process the daemon started for it.
  const cli: string | null = names[String(record.cli).toLowerCase()] ?? record.cli ?? null;
  if (cli === 'Claude Code') {
    // The pane is bound to the session the daemon started it in; its hooks for any other session are refused
    // (hook_native_session_mismatch). Every hook comes from this pane's own CLI (launch token), so one naming another
    // session means the CLI left the bound one (a /clear or /resume typed into the pane): which one it is in now is not
    // the pane's to say (T-195 review 2, R5).
    const session: string | null = record.native_session ?? null;
    if (!session) return { available: false, cli, reason: '启动记录里没有会话号' };
    const others = new Set(db.prepare(`SELECT data FROM orchestration_events WHERE launch=? AND type='hook_received'`).all(launch)
      // A hook whose input is not JSON names no session.
      .map(hook => { try { return JSON.parse(JSON.parse(String(hook.data)).raw_stdin).session_id; } catch { return undefined; } })
      .filter(id => typeof id === 'string' && id && id !== session));
    if (others.size) return { available: false, cli, reason: `Claude Code 在这个窗格里换了会话（如 /clear），已不在启动时的会话 ${session}` };
    const file = archive.sources(launch).map(source => source.path).find(path => basename(path) === session + '.jsonl' && existsSync(path))
      ?? claudeRecord(join(userHome, '.claude'), session);
    return file ? linked(cli, session, file) : { available: false, cli, reason: `找不到会话 ${session} 的记录文件（还没写出，或 CLI 已清理）` };
  }
  if (cli === 'Codex') {
    const bound = db.prepare(`SELECT data FROM orchestration_events WHERE launch=? AND type='pane_native_session' ORDER BY seq DESC LIMIT 1`).get(launch);
    const session: string | null = bound ? JSON.parse(String(bound.data)).native_session ?? null : null;
    if (!session) return { available: false, cli, reason: 'Codex 还没报来会话号（第一个回合开始后才有）' };
    // A second root thread of the CLI in this worktree is one the pane never bound: which one is current is not known.
    // Read from Codex's own records, so it holds however the pane's collector was started (T-195 review 2, R4).
    const threads = codexRootThreads(record);
    if (!Array.isArray(threads)) return { available: false, cli, reason: `读不了 Codex 的记录 ${threads.unreadable}，分不出现在是哪个线程` };
    const other = threads.find(id => id !== session);
    if (other) return { available: false, cli, reason: `Codex 在这个工作区开了新线程 ${other}，不是绑定的 ${session}` };
    const file = archive.sources(launch).map(source => source.path).find(path => basename(path).endsWith(session + '.jsonl'));
    return file && existsSync(file) ? linked(cli, session, file) : { available: false, cli, reason: `找不到会话 ${session} 的记录文件（还没写出，或 CLI 已清理）` };
  }
  // opencode and agy workers: one CLI process per pane, so its own last report is this session's.
  if (cli === 'opencode') return opencodeLink(userHome, lastReportedId(join(root, 'traces', launch, 'pty.raw')));
  if (cli === 'agy') return agyLink(userHome, record.worktree);
  return { available: false, cli, reason: `不支持的 CLI：${cli}` };
}

// A project terminal runs whatever the user typed; only the session the CLI process now in front reported is its own.
function terminalLink(record: any, userHome: string, shell: ShellNative): NativeLink {
  if (!shell) return { available: false, cli: null, reason: '终端已关闭' };
  const cli = shell.cli ? names[shell.cli] ?? shell.cli : null;
  if (!cli) return { available: false, cli: null, reason: '这个终端前台没有 Claude Code、Codex、opencode 或 agy' };
  // agy names no session; in a terminal the user can cd anywhere and start it again, and a conversation file it has not
  // written yet cannot be told from an earlier one, so no file there is known to be this run's (T-195 review 2, R3).
  if (cli === 'agy') return { available: false, cli, reason: 'agy 不报会话号，终端里分不出是哪一次会话（受管 agy worker 按工作区可以）' };
  const report = shell.report;
  // opencode reports its session id to the terminal itself, without its process: in a terminal a report cannot be told
  // from one an earlier run of it wrote (T-195 review 3, F1). A managed opencode worker is one process per pane.
  if (cli === 'opencode') return { available: false, cli, reason: 'opencode 的会话号报告不带进程，终端里分不出是哪一次运行（受管 opencode worker 可以）' };
  if (!report) return { available: false, cli, reason: `${cli} 还没报来这次会话的会话号（经 Enchanted 启动、提交一句话后才有${cli === 'Codex' ? '；Codex 须先信任 Enchanted 的钩子' : ''}）` };
  if (cli === 'Claude Code') {
    const file = claudeRecord(report.home ?? join(userHome, '.claude'), report.session);
    return file ? linked(cli, report.session, file) : { available: false, cli, reason: `找不到会话 ${report.session} 的记录文件（还没写出，或 CLI 已清理）` };
  }
  if (cli === 'Codex') {
    const file = codexRecord(report.home ?? join(userHome, '.codex'), report.session);
    return file ? linked(cli, report.session, file) : { available: false, cli, reason: `找不到会话 ${report.session} 的记录文件（还没写出，或 CLI 已清理）` };
  }
  return { available: false, cli, reason: `不支持的 CLI：${cli}` };
}

function opencodeLink(userHome: string, session: string | null): NativeLink {
  const cli = 'opencode';
  if (!session) return { available: false, cli, reason: 'opencode 还没报来会话号（回合开始后才有）' };
  const store = join(userHome, '.local/share/opencode/opencode.db');
  if (!existsSync(store)) return { available: false, cli, reason: '找不到 opencode 的记录库 ' + store };
  const found = readDatabase(store, opencode => Boolean(opencode.prepare('SELECT 1 FROM session_v2 WHERE id=?').get(session)));
  if (!found.ok) return { available: false, cli, reason: `读不了 opencode 的记录库（${found.error}）` };
  if (!found.value) return { available: false, cli, reason: `opencode 记录库里没有会话 ${session}` };
  return linked(cli, session, store, `${store}（session_v2 表）`);
}

// agy reports no session id; each conversation is one file that names its working directory. A managed agy worker runs
// once in a worktree of its own, so a directory exactly one conversation used tells which file is its session, and only
// when every file could be read.
function agyLink(userHome: string, worktree: string): NativeLink {
  const cli = 'agy';
  const directory = join(userHome, '.gemini/antigravity-cli/conversations');
  const workspace = Buffer.from('file://' + encodeURI(worktree));
  const read = existsSync(directory) ? readdirSync(directory).filter(name => name.endsWith('.db')).map(name => ({ name,
    blob: readDatabase(join(directory, name), agy => agy.prepare(`SELECT data FROM trajectory_metadata_blob WHERE id='main'`).get()?.data) })) : [];
  const unread = read.filter(file => !file.blob.ok);
  if (unread.length) return { available: false, cli, reason: `有 ${unread.length} 个 agy 会话记录读不了（${(unread[0]!.blob as { error: string }).error}），分不出是哪一次` };
  const matches = read.filter(({ blob }) => {
    const value = (blob as { value: unknown }).value;
    if (!(value instanceof Uint8Array)) return false;
    const data = Buffer.from(value);
    for (let at = data.indexOf(workspace); at >= 0; at = data.indexOf(workspace, at + 1)) {
      const next = data[at + workspace.length];
      if (next === undefined || !/[A-Za-z0-9._~%/-]/.test(String.fromCharCode(next))) return true;
    }
    return false;
  });
  if (matches.length !== 1) return { available: false, cli, reason: matches.length
    ? `目录 ${worktree} 有 ${matches.length} 个 agy 会话，分不出是哪一次` : `没找到工作目录为 ${worktree} 的 agy 会话` };
  return linked(cli, basename(matches[0]!.name, '.db'), join(directory, matches[0]!.name));
}

function linked(cli: string, session: string, record: string, shown = record): NativeLink {
  return { available: true, cli, session, record, text: `${cli} 会话 ${session}，记录 ${shown}` };
}

// Claude Code keeps a session as <home>/projects/<directory>/<session>.jsonl.
function claudeRecord(home: string, session: string): string | undefined {
  const projects = join(home, 'projects');
  if (!existsSync(projects)) return undefined;
  return readdirSync(projects).map(directory => join(projects, directory, session + '.jsonl')).find(path => existsSync(path));
}

// The root threads Codex started in a managed session's worktree since its launch: the first line (session_meta) of each
// rollout in the day directories from the launch's day on, as the pane's collector reads them (panes.ts).
function codexRootThreads(record: any): string[] | { unreadable: string } {
  const home = record.env?.CODEX_HOME;
  if (typeof home !== 'string') return { unreadable: '（启动记录里没有 CODEX_HOME）' };
  const since = Date.parse(record.created_at), ids: string[] = [];
  for (const day = new Date(since); day.getTime() <= Date.now() + 86_400_000; day.setDate(day.getDate() + 1)) {
    const directory = join(home, 'sessions', String(day.getFullYear()), String(day.getMonth() + 1).padStart(2, '0'), String(day.getDate()).padStart(2, '0'));
    // Any rollout written since the launch may be this worktree's; one that cannot be read, or a day that cannot be looked
    // into, leaves the current thread unknown. Only a day Codex wrote nothing on is skipped (T-195 review 4, R4-F1).
    let names: string[];
    try { names = readdirSync(directory).filter(name => name.endsWith('.jsonl')); }
    catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') continue;
      return { unreadable: `${directory}（${(error as Error).message}）` };
    }
    for (const name of names) {
      const path = join(directory, name);
      let meta: any;
      try {
        if (statSync(path).mtimeMs < since) continue;
        meta = firstRecord(path);
      } catch (error) { return { unreadable: `${path}（${(error as Error).message}）` }; }
      if (meta === undefined) return { unreadable: path };
      if (meta?.type === 'session_meta' && meta.payload?.cwd === record.worktree && meta.payload?.source === 'cli') ids.push(meta.payload.id);
    }
  }
  return ids;
}

// The first JSON line of a rollout, read only as far as its end; undefined when it is not (yet) complete JSON.
function firstRecord(path: string): any {
  const fd = openSync(path, 'r'), chunk = Buffer.alloc(65536), parts: Buffer[] = [];
  try {
    for (let read; (read = readSync(fd, chunk)) > 0;) {
      const end = chunk.subarray(0, read).indexOf(10);
      parts.push(Buffer.from(chunk.subarray(0, end < 0 ? read : end)));
      if (end >= 0) return JSON.parse(Buffer.concat(parts).toString('utf8'));
    }
    return undefined;
  } catch (error) {
    if (error instanceof SyntaxError) return undefined;
    throw error;
  } finally { closeSync(fd); }
}

// Codex keeps a thread as <home>/sessions/<yyyy>/<mm>/<dd>/rollout-<time>-<thread>.jsonl.
function codexRecord(home: string, session: string): string | undefined {
  const sessions = join(home, 'sessions');
  if (!existsSync(sessions)) return undefined;
  return (readdirSync(sessions, { recursive: true }) as string[]).filter(path => path.endsWith(`-${session}.jsonl`)).map(path => join(sessions, path))[0];
}

// The CLIs' own stores, opened read-only. A store that cannot be read is said so, never taken for "not this session".
function readDatabase<T>(path: string, read: (db: DatabaseSync) => T): { ok: true; value: T } | { ok: false; error: string } {
  let db: DatabaseSync | undefined;
  try { db = new DatabaseSync(path, { readOnly: true }); return { ok: true, value: read(db) }; }
  catch (error) { return { ok: false, error: String((error as Error).message ?? error) }; }
  finally { db?.close(); }
}

// The id in the last OSC 7501 report of a pane's CLI that carried one (opencode reports none in its first two).
function lastReportedId(trace: string): string | null {
  if (!existsSync(trace)) return null;
  let id: string | null = null;
  for (const match of readFileSync(trace, 'utf8').matchAll(/\x1b\]7501;([^\x07\x1b]*)(?:\x07|\x1b\\)/g)) {
    const field = match[1]!.split(':').find(entry => entry.startsWith('id='));
    if (field && field.length > 3) id = field.slice(3);
  }
  return id;
}
