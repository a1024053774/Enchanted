import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import type { DatabaseSync } from 'node:sqlite';
import { metricsSnapshot } from './metrics.ts';
import { userInputRecords } from './userInputRecords.ts';

// Retrospectives (native-cli spec section 8, T-136). A run is started by the user ("立即复盘") or by the weekly
// schedule; this module prepares its package from the records, names the files the session may write, and imports
// the report and suggestions the session leaves. The session itself runs in an ordinary project terminal (daemon).
export type RetrospectiveSchedule = { enabled: boolean; weekday: number; hour: number; minute: number;
  cli: 'Claude Code' | 'Codex'; model: string; effort: string; effective_from: string };
export type RetrospectiveRun = { id: string; project: string; repo: string; trigger: 'manual' | 'schedule'; scheduled_for: string | null;
  since: string | null; until: string; cli: string; model: string; effort: string; dir: string; package: string; out: string;
  created_at: string; launch?: string | null };
type Suggestion = { id: string; run: string; project: string; number: number; title: string; body: string; kind: string; created_at: string };

// The spec's defaults: every Monday 09:00, Claude Code with Opus 5.5 at medium effort.
const defaults = { enabled: true, weekday: 1, hour: 9, minute: 0, cli: 'Claude Code' as const, model: 'claude-opus-5-5', effort: 'medium' };
const json = (value: unknown) => JSON.parse(String(value));

export class Retrospectives {
  private db: DatabaseSync;
  readonly root: string;
  constructor(db: DatabaseSync, root: string) {
    this.db = db; this.root = join(root, 'retrospectives');
    const appendOnly = (table: string) => `CREATE TRIGGER IF NOT EXISTS ${table}_no_update BEFORE UPDATE ON ${table} BEGIN SELECT RAISE(ABORT,'append only'); END;
      CREATE TRIGGER IF NOT EXISTS ${table}_no_delete BEFORE DELETE ON ${table} BEGIN SELECT RAISE(ABORT,'append only'); END;`;
    db.exec(`CREATE TABLE IF NOT EXISTS retrospective_schedule (seq INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS retrospective_runs (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, project TEXT NOT NULL, data TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS retrospective_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT NOT NULL, type TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS retrospective_suggestions (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, run TEXT NOT NULL, data TEXT NOT NULL);
      ${appendOnly('retrospective_schedule')} ${appendOnly('retrospective_runs')} ${appendOnly('retrospective_events')} ${appendOnly('retrospective_suggestions')}`);
    // The schedule takes effect from the moment it first exists: slots before installation never fire.
    if (!db.prepare('SELECT 1 FROM retrospective_schedule LIMIT 1').get())
      db.prepare('INSERT INTO retrospective_schedule(data) VALUES (?)').run(JSON.stringify({ ...defaults, effective_from: new Date().toISOString() }));
  }

  schedule(): RetrospectiveSchedule {
    return json(this.db.prepare('SELECT data FROM retrospective_schedule ORDER BY seq DESC LIMIT 1').get()!.data);
  }
  saveSchedule(change: Partial<RetrospectiveSchedule>, now = new Date()) {
    const current = this.schedule();
    const next = { ...current, ...change, effective_from: now.toISOString() };
    if (typeof next.enabled !== 'boolean' || ![0, 1, 2, 3, 4, 5, 6].includes(next.weekday) || !Number.isInteger(next.hour) || next.hour < 0 || next.hour > 23 ||
      !Number.isInteger(next.minute) || next.minute < 0 || next.minute > 59 || !['Claude Code', 'Codex'].includes(next.cli) ||
      typeof next.model !== 'string' || !next.model.trim() || typeof next.effort !== 'string' || !next.effort.trim()) throw new Error('invalid_retrospective_schedule');
    this.db.prepare('INSERT INTO retrospective_schedule(data) VALUES (?)').run(JSON.stringify(next));
    return next;
  }

  /** The latest scheduled slot at or before `now` (local time), when it is due for a project and has not run. */
  due(project: string, now: Date) {
    const schedule = this.schedule();
    if (!schedule.enabled) return null;
    const slot = new Date(now);
    slot.setHours(schedule.hour, schedule.minute, 0, 0);
    slot.setDate(slot.getDate() - ((slot.getDay() - schedule.weekday + 7) % 7));
    if (slot > now) slot.setDate(slot.getDate() - 7);
    if (slot < new Date(schedule.effective_from)) return null;
    const ran = this.runs(project).some(run => run.scheduled_for === slot.toISOString());
    return ran ? null : slot.toISOString();
  }

  runs(project?: string): RetrospectiveRun[] {
    return this.db.prepare(`SELECT data FROM retrospective_runs ${project ? 'WHERE project=?' : ''} ORDER BY seq`).all(...(project ? [project] : []))
      .map(row => json(row.data));
  }

  /** Make a run: its range (from the project's last run to now), package, and the one directory the session may write. */
  prepare(project: string, repo: string, selection: { cli: string; model: string; effort: string }, trigger: 'manual' | 'schedule',
    scheduledFor: string | null, now = new Date(), range: { since?: string | null; until?: string | null } = {}): RetrospectiveRun {
    const id = randomUUID();
    const dir = join(this.root, id), out = join(dir, 'out');
    mkdirSync(out, { recursive: true, mode: 0o700 });
    // From the end of the last run that started: a run whose terminal never opened reviewed nothing (review 02).
    const since = range.since !== undefined ? range.since
      : this.runs(project).findLast(run => !this.events(run.id).some(event => event.type === 'start_failed'))?.until ?? null;
    const until = range.until ?? now.toISOString();
    const run: RetrospectiveRun = { id, project, repo, trigger, scheduled_for: scheduledFor, since, until, ...selection, dir,
      package: join(dir, 'package.json'), out, created_at: now.toISOString() };
    writeFileSync(run.package, JSON.stringify(retrospectivePackage(this.db, project, repo, since, until), null, 2) + '\n', { mode: 0o600 });
    this.db.prepare('INSERT INTO retrospective_runs(id,project,data) VALUES (?,?,?)').run(id, project, JSON.stringify(run));
    return run;
  }
  record(run: string, type: string, data: unknown) {
    this.db.prepare('INSERT INTO retrospective_events(run,type,data,created_at) VALUES (?,?,?,?)').run(run, type, JSON.stringify(data), new Date().toISOString());
  }
  events(run: string) {
    return this.db.prepare('SELECT type, data, created_at FROM retrospective_events WHERE run=? ORDER BY seq').all(run)
      .map(row => ({ type: String(row.type), data: json(row.data), created_at: String(row.created_at) }));
  }

  /**
   * A finished session leaves out/report.md and then out/suggestions.json. Once both are there and the suggestions
   * parse, the report goes to the project's findings/ (the data directory when the project has none) and each
   * suggestion becomes a panel entry. Imported once per run.
   */
  importFinished() {
    const imported: string[] = [];
    const failOnce = (run: string, reason: string, error?: string) => {
      if (!this.events(run).some(event => event.type === 'import_failed' && event.data.reason === reason)) this.record(run, 'import_failed', { reason, error });
    };
    for (const run of this.runs()) {
      if (this.events(run.id).some(event => event.type === 'imported')) continue;
      const report = join(run.out, 'report.md'), suggestions = join(run.out, 'suggestions.json');
      if (!existsSync(report) || !existsSync(suggestions)) continue;
      let parsed: unknown;
      // Not JSON yet: the session may still be writing it, so the next check tries again. Recorded once, so a file
      // that stays broken shows on the run instead of leaving it "in progress" without a word.
      try { parsed = JSON.parse(readFileSync(suggestions, 'utf8')); } catch (error) {
        failOnce(run.id, 'suggestions_not_json', String(error));
        continue;
      }
      const list = Array.isArray(parsed) ? parsed : Array.isArray((parsed as any)?.suggestions) ? (parsed as any).suggestions : null;
      if (!list) { failOnce(run.id, 'suggestions_not_a_list'); continue; }
      const findings = join(run.repo, 'findings');
      const destination = existsSync(findings) && statSync(findings).isDirectory()
        ? join(findings, `${run.until.slice(0, 10)}-retrospective-${run.id.slice(0, 8)}.md`) : join(run.dir, 'report.md');
      copyFileSync(report, destination);
      // The suggestions and the "imported" mark go in together, so a failure part-way leaves nothing to duplicate on the next try.
      this.db.exec('BEGIN IMMEDIATE');
      try {
        list.forEach((item: any, index: number) => {
          const title = typeof item?.title === 'string' ? item.title.trim() : '';
          if (!title) return;
          const suggestion: Suggestion = { id: randomUUID(), run: run.id, project: run.project, number: index + 1, title,
            body: typeof item.body === 'string' ? item.body : '', kind: typeof item.kind === 'string' ? item.kind : 'other', created_at: new Date().toISOString() };
          this.db.prepare('INSERT INTO retrospective_suggestions(id,run,data) VALUES (?,?,?)').run(suggestion.id, run.id, JSON.stringify(suggestion));
        });
        this.record(run.id, 'imported', { report: destination, suggestions: list.length });
        this.db.exec('COMMIT');
      } catch (error) { this.db.exec('ROLLBACK'); throw error; }
      imported.push(run.id);
    }
    return imported;
  }

  suggestions(project: string) {
    const decisions = new Map<string, any>();
    for (const row of this.db.prepare("SELECT data FROM retrospective_events WHERE type='suggestion_decided' ORDER BY seq").all()) {
      const data = json(row.data);
      decisions.set(data.suggestion, data);
    }
    return this.db.prepare('SELECT data FROM retrospective_suggestions ORDER BY seq').all().map(row => json(row.data) as Suggestion)
      .filter(item => item.project === project).map(item => ({ ...item, decision: decisions.get(item.id) ?? null }));
  }
  decide(suggestion: string, approved: boolean) {
    const row = this.db.prepare('SELECT data FROM retrospective_suggestions WHERE id=?').get(suggestion);
    if (!row) throw new Error('unknown_suggestion');
    const item = json(row.data) as Suggestion;
    if (this.suggestions(item.project).find(entry => entry.id === suggestion)?.decision) throw new Error('suggestion_already_decided');
    const decision = { suggestion, approved, decided_at: new Date().toISOString() };
    this.record(item.run, 'suggestion_decided', decision);
    return { ...item, decision };
  }
}

/** Everything a retrospective reads for one project and time range, from the records (spec section 8). */
export function retrospectivePackage(db: DatabaseSync, project: string, repo: string, since: string | null, until: string) {
  const inRange = (time: string) => (!since || time >= since) && time < until;
  const tasks = db.prepare('SELECT id, data FROM tasks').all().map(row => json(row.data)).filter(task => task.project_id === project);
  const ids = new Set(tasks.map(task => task.task_id));
  const events = db.prepare('SELECT seq, time, task, attempt, type, details FROM events ORDER BY seq').all()
    .filter(row => ids.has(String(row.task)) && inRange(String(row.time)))
    .map(row => ({ seq: Number(row.seq), time: String(row.time), task: String(row.task), attempt: row.attempt ?? null, type: String(row.type), details: json(row.details) }));
  const touched = new Set(events.map(event => event.task));
  const of = (...types: string[]) => events.filter(event => types.includes(event.type));
  const issues = db.prepare('SELECT data FROM issue_records ORDER BY rowid').all().map(row => json(row.data))
    .filter(record => ids.has(record.task_id) && inRange(record.created_at));
  const launches = db.prepare('SELECT data FROM launch_records ORDER BY rowid').all().map(row => json(row.data))
    .filter(record => record.project === project);
  // Sessions archived during the range, with what was archived by its end (T-136 review 01: not every session ever).
  const archive = db.prepare('SELECT launch, source, file, max(end) AS end FROM trajectory_archive WHERE created_at < ? GROUP BY launch, source HAVING max(created_at) >= ?')
    .all(until, since ?? '')
    .filter(row => launches.some(record => record.id === row.launch))
    .map(row => ({ launch: String(row.launch), role: launches.find(record => record.id === row.launch)?.role ?? null,
      native: String(row.source), archive: String(row.file), archived_bytes: Number(row.end) }));
  return {
    schema: 1, project, repo, since, until, generated_at: new Date().toISOString(),
    tasks: tasks.filter(task => touched.has(task.task_id)).map(task => ({ task: task.task_id, title: task.title ?? null, state: task.state,
      task_type: task.card?.task_type ?? null, complexity: task.card?.complexity ?? null })),
    gate_checks: of('verification_result', 'delivery_rejected', 'rejected', 'rule_check', 'red_check', 'completion_check', 'integration_compare_failed')
      .map(event => ({ time: event.time, task: event.task, type: event.type,
        check: event.details?.repair?.check ?? event.details?.check ?? null,
        result: event.details?.verification?.state ?? event.details?.error ?? event.details?.result?.state ?? null })),
    rejections: of('delivery_rejected').map(event => ({ time: event.time, task: event.task, check: event.details.repair?.check, count: event.details.repair?.count })),
    reviews: of('review_result').map(event => ({ time: event.time, task: event.task, state: event.details.review?.state ?? null,
      verdict: event.details.review?.result?.verdict ?? null, findings: event.details.review?.result?.findings ?? [] })),
    scores: of('score_recorded').map(event => event.details),
    issues: issues.filter(record => record.kind === 'issue').map(record => ({ id: record.id, task: record.task_id, from: record.from,
      title: record.title, blocking: record.blocking, created_at: record.created_at })),
    panel: issues.filter(record => record.kind !== 'issue').map(record => ({ issue: record.issue_id, kind: record.kind, from: record.from,
      action: record.action ?? null, body: record.body, created_at: record.created_at })),
    user_inputs: userInputRecords(db, project).filter(input => inRange(input.created_at)),
    commit_trailers: commitTrailers(repo, since, until),
    metrics: metricsSnapshot(db, { project, since, until }),
    trajectory_archive: archive,
  };
}

// The A2A trailers of the commits in range on the project's branches; commits without them are counted apart.
function commitTrailers(repo: string, since: string | null, until: string) {
  let log = '';
  try {
    log = execFileSync('git', ['-C', repo, 'log', '--all', `--until=${until}`, ...(since ? [`--since=${since}`] : []),
      '--format=%H%x1f%cI%x1f%(trailers:only,unfold)%x1e'], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  } catch (error) { return { error: String(error), commits: [], without_trailers: null }; }
  const commits = log.split('\x1e').map(entry => entry.trim()).filter(Boolean).map(entry => {
    const [commit, time, trailers = ''] = entry.split('\x1f');
    const values = Object.fromEntries(trailers.split('\n').map(line => /^A2A-([A-Za-z-]+):\s*(.*)$/.exec(line.trim())).filter(Boolean)
      .map(match => [match![1], match![2]]));
    return { commit, time, trailers: values };
  });
  return { commits, without_trailers: commits.filter(entry => !Object.keys(entry.trailers).length).length };
}

/** The session's prompt: what to read, the one directory it may write, and the two files it leaves. */
export function retrospectivePrompt(run: RetrospectiveRun, state: string) {
  return [
    `你在为项目 ${run.project} 做一次复盘（${run.since ?? '最早的记录'} 到 ${run.until}）。`,
    `只读：复盘包 ${run.package}（任务、门禁逐项结果与打回原因、审查结论、打分、问题上报、面板问答、用户输入与介入、提交尾注、指标快照、轨迹归档路径），`,
    `项目目录 ${run.repo}，工作台数据目录 ${state}。不要改它们。`,
    `只能写 ${run.out} 这个目录：`,
    `1. 先写中文报告 ${join(run.out, 'report.md')}：范围；这段时间发生了什么；门禁与打回；审查；用户的注意力消耗；模型使用；做得好的与要改的，每条写依据（包里的哪一项）。`,
    `2. 最后写 ${join(run.out, 'suggestions.json')}：JSON 数组，每项 {"title": "...", "body": "...", "kind": "ticket" | "role-card" | "other"}，一条建议一项，没有就写 []。`,
    '写完 suggestions.json 就结束。看板变化只算观察，不写收益结论。',
  ].join('\n');
}

/** The CLI command line: read anything, write only the run's out directory. */
export function retrospectiveArgv(run: RetrospectiveRun, bins: { claude_bin?: string; codex_bin?: string }, prompt: string, session: string) {
  if (run.cli === 'Claude Code') {
    if (!bins.claude_bin) throw new Error('claude_bin_required');
    // The session starts in the project directory, which Claude's sandbox would otherwise let commands write.
    const settings = {
      permissions: { allow: ['Bash', 'Read', 'Glob', 'Grep', `Edit(/${run.out}/**)`], deny: [`Edit(/${run.repo}/**)`] },
      sandbox: { enabled: true, autoAllowBashIfSandboxed: true, allowUnsandboxedCommands: false,
        filesystem: { allowWrite: [run.out], denyWrite: [run.repo] } },
    };
    return [bins.claude_bin, '--session-id', session, '--model', run.model, '--effort', run.effort, '--permission-mode', 'dontAsk',
      '--setting-sources', '', '--strict-mcp-config', '--disallowedTools', 'AskUserQuestion', '--settings', JSON.stringify(settings), prompt];
  }
  if (!bins.codex_bin) throw new Error('codex_bin_required');
  // The out folder is one a2a just created; trusting it for this session only (nothing is saved) skips Codex's trust
  // question, which nobody may be there to answer for a scheduled run.
  return [bins.codex_bin, '--no-alt-screen', '-C', run.out, '-c', `projects={${JSON.stringify(run.out)}={trust_level="trusted"}}`, '-a', 'never', '--sandbox', 'workspace-write', '-m', run.model,
    '-c', `model_reasoning_effort=${JSON.stringify(run.effort)}`, '-c', 'check_for_update_on_startup=false',
    '-c', 'sandbox_workspace_write.network_access=false', prompt];
}
