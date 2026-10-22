import { appendFileSync, closeSync, existsSync, fstatSync, mkdirSync, openSync, readdirSync, readSync, statSync } from 'node:fs';
import { basename, join } from 'node:path';
import { gzipSync } from 'node:zlib';
import type { DatabaseSync } from 'node:sqlite';

// Trajectory archive (native-cli spec section 8, T-135): the native records of every session the daemon started, and
// of every terminal controller the user approved, copied into the workbench data directory in increments of complete
// lines and compressed, because the CLIs clean their own records up. Each increment is one gzip member appended to the
// session's archive file (a gzip reader reads the concatenation as one stream) and one append-only index row.
// The native files are only read; nothing is written outside the data directory.
type Source = { launch: string; path: string };

export class TrajectoryArchive {
  readonly dir: string;
  private db: DatabaseSync;
  private event: (type: string, data: unknown, launch: string) => void;
  private reported = new Set<string>();
  constructor(db: DatabaseSync, root: string, event: (type: string, data: unknown, launch: string) => void) {
    this.db = db; this.event = event;
    this.dir = join(root, 'archive');
    db.exec(`CREATE TABLE IF NOT EXISTS trajectory_archive (seq INTEGER PRIMARY KEY AUTOINCREMENT, launch TEXT NOT NULL, source TEXT NOT NULL,
        start INTEGER NOT NULL, end INTEGER NOT NULL, file TEXT NOT NULL, stored_bytes INTEGER NOT NULL, created_at TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS trajectory_archive_no_update BEFORE UPDATE ON trajectory_archive BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS trajectory_archive_no_delete BEFORE DELETE ON trajectory_archive BEGIN SELECT RAISE(ABORT,'append only'); END;`);
  }

  /** The native files each archived session has written so far. */
  sources(launch?: string): Source[] {
    const sources: Source[] = [];
    const records = this.db.prepare('SELECT data FROM launch_records ORDER BY rowid').all().map(row => JSON.parse(String(row.data)))
      .filter(record => !launch || record.id === launch);
    for (const record of records) {
      if (record.role === 'shell') continue;
      if (record.cli === 'Claude Code' && record.native_session) {
        // Every Claude hook names the session's transcript; only the one of this launch's own session counts.
        const rows = this.db.prepare("SELECT data FROM orchestration_events WHERE launch=? AND type='hook_received' ORDER BY seq DESC LIMIT 20").all(record.id);
        const path = rows.map(row => { try { return JSON.parse(JSON.parse(String(row.data)).raw_stdin).transcript_path; } catch { return null; } })
          .find(value => typeof value === 'string' && basename(value) === record.native_session + '.jsonl');
        if (path) sources.push({ launch: record.id, path });
      } else if (record.cli === 'Codex' && typeof record.env?.CODEX_HOME === 'string') {
        for (const row of this.db.prepare("SELECT DISTINCT json_extract(data,'$.file') AS file FROM orchestration_events WHERE launch=? AND type='native_record'").all(record.id))
          sources.push({ launch: record.id, path: join(record.env.CODEX_HOME, String(row.file)) });
      }
    }
    // Terminal controllers: only once the user approved the role request that named the native session (T-119).
    const requested = new Map<string, any>();
    for (const row of this.db.prepare("SELECT time, type, launch, data FROM orchestration_events WHERE type IN ('role_requested','role_request_decided') ORDER BY seq").all()) {
      const data = JSON.parse(String(row.data));
      if (row.type === 'role_requested') { requested.set(data.role_request, { ...data, launch: String(row.launch), time: String(row.time) }); continue; }
      const request = requested.get(data.role_request);
      if (!data.approved || !request?.native_session || !request.native_home || (launch && request.launch !== launch)) continue;
      const path = request.cli === 'claude' ? this.claudeTranscript(request.native_home, request.native_session)
        : request.cli === 'codex' ? this.codexRollout(request.native_home, request.native_session, Date.parse(request.time)) : null;
      if (path) sources.push({ launch: request.launch, path });
    }
    return sources;
  }

  private claudeTranscript(home: string, session: string) {
    const projects = join(home, 'projects');
    if (!existsSync(projects)) return null;
    for (const entry of readdirSync(projects, { withFileTypes: true }))
      if (entry.isDirectory() && existsSync(join(projects, entry.name, session + '.jsonl'))) return join(projects, entry.name, session + '.jsonl');
    return null;
  }

  // A Codex rollout lives under sessions/YYYY/MM/DD (local date) from the day the session started.
  private codexRollout(home: string, session: string, since: number) {
    for (const day = new Date(since - 86_400_000); day.getTime() <= Date.now() + 86_400_000; day.setDate(day.getDate() + 1)) {
      const dir = join(home, 'sessions', String(day.getFullYear()), String(day.getMonth() + 1).padStart(2, '0'), String(day.getDate()).padStart(2, '0'));
      if (!existsSync(dir)) continue;
      const found = readdirSync(dir).find(name => name.endsWith(session + '.jsonl'));
      if (found) return join(dir, found);
    }
    return null;
  }

  /** Copy what each source gained since the last increment, up to its last complete line. */
  sweep(launch?: string) {
    for (const source of this.sources(launch)) {
      if (!existsSync(source.path)) continue;
      const last = this.db.prepare('SELECT max(end) AS end FROM trajectory_archive WHERE launch=? AND source=?').get(source.launch, source.path);
      const start = Number(last?.end ?? 0);
      const fd = openSync(source.path, 'r');
      let chunk: Buffer;
      try {
        const size = fstatSync(fd).size;
        if (size < start) {
          // A native file that shrank is not continued from a guessed offset; it is reported once and left.
          const key = `${source.launch}\0${source.path}\0${size}`;
          if (!this.reported.has(key)) { this.reported.add(key); this.event('trajectory_source_truncated', { source: source.path, archived: start, size }, source.launch); }
          continue;
        }
        chunk = Buffer.alloc(size - start);
        let read = 0;
        while (read < chunk.length) {
          const n = readSync(fd, chunk, read, chunk.length - read, start + read);
          if (n === 0) break;
          read += n;
        }
        chunk = chunk.subarray(0, read);
      } finally { closeSync(fd); }
      // A last line without its newline may still be being written; it waits for the next increment.
      const complete = chunk.lastIndexOf(10) + 1;
      if (!complete) continue;
      const dir = join(this.dir, source.launch);
      mkdirSync(dir, { recursive: true });
      const file = join(dir, basename(source.path) + '.gz');
      const member = gzipSync(chunk.subarray(0, complete));
      appendFileSync(file, member);
      this.db.prepare('INSERT INTO trajectory_archive(launch,source,start,end,file,stored_bytes,created_at) VALUES (?,?,?,?,?,?,?)')
        .run(source.launch, source.path, start, start + complete, file, member.length, new Date().toISOString());
    }
  }

  /** What the archive holds: the sessions in the index and the bytes the archive directory takes on disk. */
  usage() {
    const sessions = Number(this.db.prepare('SELECT count(DISTINCT launch) AS n FROM trajectory_archive').get()!.n);
    const size = (path: string): number => !existsSync(path) ? 0 : statSync(path).isDirectory()
      ? readdirSync(path).reduce((sum, name) => sum + size(join(path, name)), 0) : statSync(path).size;
    return { sessions, bytes: size(this.dir), dir: this.dir };
  }
}
