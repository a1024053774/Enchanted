import type { DatabaseSync } from 'node:sqlite';
import type { RoleRequest } from './roleRequests.ts';

// T-137: every controller a project ever had and the sessions started under it, ended ones included, from the
// records the sidebar uses: a launch record's parent launch and the parent the user chose for a terminal executor.
// A terminal can hold several roles over time, so a session started from a terminal belongs to the role that
// terminal held when the session was created. A worker session shows the score its controller gave the delivery
// it made (the gate's score_recorded names the delivering launch).
export type ReflectNode = { id: string; kind: 'terminal' | 'managed'; launch: string; role: string; role_label: string;
  task: string | null; attempt: string | null; cli: string | null; model: string | null; effort: string | null;
  started_at: string | null; ended_at: string | null; state: string; parent: string | null; score: Record<string, any> | null };

const roleNames: Record<string, string> = { ideation: '构思主控', executor: '执行主控', worker: 'worker', reviewer: '审查员', monitor: '监视器' };
const cliNames: Record<string, string> = { claude: 'Claude Code', codex: 'Codex' };

export function reflectTree(db: DatabaseSync, roleRequests: RoleRequest[], project: string, lifecycle: (record: Record<string, any>) => string): ReflectNode[] {
  const json = (value: unknown) => JSON.parse(String(value));
  const eventTimes = (type: string) => new Map(db.prepare('SELECT launch, max(time) AS time FROM orchestration_events WHERE type=? GROUP BY launch').all(type)
    .map(row => [String(row.launch), String(row.time)]));
  const closed = eventTimes('shell_closed'), archived = eventTimes('pane_archived');
  const scores = new Map<string, Record<string, any>>();
  for (const row of db.prepare("SELECT details FROM events WHERE type='score_recorded' ORDER BY seq").all()) {
    const score = json(row.details);
    if (score.project === project && typeof score.launch_id === 'string') scores.set(score.launch_id, score);
  }
  // Only roles that took effect were controllers.
  const held = roleRequests.filter(row => row.project === project && row.confirmed_at);
  // The latest match: when one role ends and the next starts in the same millisecond, the session belongs to the new one.
  const roleAt = (launch: string, time: string) => held.findLast(row => row.launch === launch && row.confirmed_at! <= time &&
    (row.state !== 'ended' || (row.ended_at ?? closed.get(row.launch) ?? '9999') >= time));
  const nodes: (ReflectNode & { parent_launch: string | null })[] = held.map(row => ({ id: row.id, kind: 'terminal', launch: row.launch,
    role: row.role, role_label: roleNames[row.role] ?? row.role, task: null, attempt: null, cli: row.cli ? cliNames[row.cli] ?? row.cli : null,
    model: null, effort: null, started_at: row.confirmed_at, ended_at: row.state === 'ended' ? row.ended_at ?? closed.get(row.launch) ?? null : null,
    state: row.state === 'ended' ? 'ended' : 'running', parent: null, parent_launch: row.parent_launch, score: null }));
  for (const row of db.prepare('SELECT data FROM launch_records ORDER BY rowid').all()) {
    const record = json(row.data);
    if (record.role === 'shell' || record.project !== project) continue;
    const role = record.role === 'controller' ? record.preset ?? 'controller' : record.role;
    nodes.push({ id: record.id, kind: 'managed', launch: record.id, role, role_label: roleNames[role] ?? role, task: record.task ?? null,
      attempt: record.attempt ?? null, cli: record.cli ?? (record.cli_version?.startsWith('codex-cli ') ? 'Codex' : null),
      model: record.model_requested ?? null, effort: record.effort_requested ?? null, started_at: record.created_at ?? null,
      ended_at: archived.get(record.id) ?? null, state: lifecycle(record), parent: null,
      parent_launch: typeof record.parent_launch === 'string' ? record.parent_launch : null,
      score: record.role === 'worker' ? scores.get(record.id) ?? null : null });
  }
  const ids = new Set(nodes.map(node => node.id));
  return nodes.map(({ parent_launch, ...node }) => {
    // A terminal parent is the role it held when this session started; a managed parent is that launch.
    const parent = parent_launch === null ? null : roleAt(parent_launch, node.started_at ?? '')?.id ?? (ids.has(parent_launch) ? parent_launch : null);
    return { ...node, parent: parent === node.id ? null : parent };
  });
}
