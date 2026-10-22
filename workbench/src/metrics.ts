import type { DatabaseSync } from 'node:sqlite';

// The four first metric views (native-cli spec section 8, T-134), computed from the recorded events on each read;
// no counter is stored. A model is the one a turn was observed answering with, never the requested one.
export type MetricsRange = { project?: string | null; since?: string | null; until?: string | null };

const json = (value: unknown) => JSON.parse(String(value));
const roleNames: Record<string, string> = { worker: 'worker', reviewer: '审查员', monitor: '监视器', ideation: '构思主控', executor: '执行主控' };

export function metricsSnapshot(db: DatabaseSync, range: MetricsRange = {}) {
  const inTime = (time: string) => (!range.since || time >= range.since) && (!range.until || time < range.until);
  const inRange = (time: string, project: string | null | undefined) => (!range.project || project === range.project) && inTime(time);
  const taskTypes = new Map<string, string>();
  for (const row of db.prepare('SELECT id, data FROM tasks').all()) taskTypes.set(String(row.id), json(row.data).card?.task_type ?? '未知');

  // 1. Model use: every session the daemon recorded, with the model and effort its turns were observed with. A session
  // counts when it started or had turns in the range, and only its turns in the range are counted (review 01).
  const observed = new Map<string, { models: Set<string>; efforts: Set<string>; turns: number }>();
  const observe = (launch: string, model: unknown, effort: unknown) => {
    const entry = observed.get(launch) ?? { models: new Set(), efforts: new Set(), turns: 0 };
    entry.models.add(typeof model === 'string' && model ? model : 'unknown');
    entry.efforts.add(typeof effort === 'string' && effort ? effort : 'unknown');
    entry.turns++;
    observed.set(launch, entry);
  };
  for (const row of db.prepare("SELECT time, launch, data FROM orchestration_events WHERE type='native_turn_facts' ORDER BY seq").all()) {
    if (!inTime(String(row.time))) continue;
    const data = json(row.data);
    observe(String(row.launch), data.model, data.effort);
  }
  // A Codex turn's facts are in its rollout's turn_context record.
  for (const row of db.prepare("SELECT time, launch, data FROM orchestration_events WHERE type='native_record' AND json_extract(data,'$.record.type')='turn_context' ORDER BY seq").all()) {
    if (!inTime(String(row.time))) continue;
    const payload = json(row.data).record?.payload ?? {};
    observe(String(row.launch), payload.model, payload.effort ?? payload.reasoning_effort);
  }
  // A project terminal counts as a controller session once the user approved its role request (T-119).
  const requested = new Map<string, { launch: string; role: string; cli: string | null }>(), controllers = new Map<string, { role: string; cli: string | null }>();
  for (const row of db.prepare("SELECT type, launch, data FROM orchestration_events WHERE type IN ('role_requested','role_request_decided') ORDER BY seq").all()) {
    const data = json(row.data);
    if (row.type === 'role_requested') requested.set(data.role_request, { launch: String(row.launch), role: data.role,
      cli: data.cli === 'claude' ? 'Claude Code' : data.cli === 'codex' ? 'Codex' : null });
    else if (data.approved && requested.has(data.role_request)) controllers.set(requested.get(data.role_request)!.launch, requested.get(data.role_request)!);
  }
  const sessions = db.prepare('SELECT data FROM launch_records ORDER BY rowid').all().map(row => json(row.data))
    .filter(record => record.role !== 'shell' || controllers.has(record.id))
    .filter(record => (!range.project || record.project === range.project) && (inTime(record.created_at) || observed.has(record.id)))
    .map(record => {
      const facts = observed.get(record.id);
      const controller = controllers.get(record.id);
      const role = controller ? controller.role : record.role === 'controller' ? record.preset : record.role;
      return { launch: record.id, project: record.project, task: record.task, task_type: record.task ? taskTypes.get(record.task) ?? '未知' : null,
        role, role_label: roleNames[role] ?? role ?? '未知', cli: controller ? controller.cli : record.cli ?? null,
        model: facts ? [...facts.models].join(' / ') : 'unknown', effort: facts ? [...facts.efforts].join(' / ') : 'unknown',
        requested_model: record.model_requested ?? null, turns: facts?.turns ?? 0, created_at: record.created_at };
    });
  const byModel = new Map<string, { model: string; task_type: string; sessions: number; turns: number }>();
  for (const session of sessions) {
    const key = session.model + '\u0000' + (session.task_type ?? '项目级');
    const entry = byModel.get(key) ?? { model: session.model, task_type: session.task_type ?? '项目级', sessions: 0, turns: 0 };
    entry.sessions++; entry.turns += session.turns;
    byModel.set(key, entry);
  }

  // Scores: one per attempt that ended (integrated, upgraded or abandoned).
  const scores = db.prepare("SELECT time, details FROM events WHERE type='score_recorded' ORDER BY seq").all()
    .map(row => json(row.details)).filter(score => inRange(score.created_at, score.project));
  const passed = scores.filter(score => score.data?.result === '通过' && score.facts);

  // 2. First-time rate: the first delivery passed every check and nobody intervened.
  const reasons: Record<string, number> = {};
  for (const score of scores) for (const [check, count] of Object.entries(score.facts?.rejections ?? {}))
    reasons[check] = (reasons[check] ?? 0) + Number(count);
  const firstTime = passed.filter(score => score.facts.delivery_rounds === 1 && score.facts.human_interventions === 0 &&
    Object.values(score.facts.rejections ?? {}).every(count => count === 0));

  // 3. The user's attention per integrated task. Every keystroke in a managed pane is its own input record, so an
  // intervention is a turn the user submitted there (Enter), not an input row; a stop is an emergency stop or an Esc.
  const attention = passed.map(score => {
    const forms = db.prepare('SELECT data FROM user_inputs WHERE task=?').all(score.task).map(row => json(row.data))
      .filter(input => input.channel !== 'ui-derived' && input.form !== 'gap').map(input => input.form);
    const orchestration = (type: string, where = '') =>
      Number(db.prepare(`SELECT count(*) AS n FROM orchestration_events WHERE task=? AND type=? ${where}`).get(score.task, type)!.n);
    const gate = (type: string) => Number(db.prepare('SELECT count(*) AS n FROM events WHERE task=? AND type=?').get(score.task, type)!.n);
    return { task: score.task, attempt: score.attempt, task_type: score.facts.task_type,
      answers: forms.filter(form => form === 'answer').length,
      approvals: forms.filter(form => form === 'approval' || form === 'denial').length,
      interventions: orchestration('turn_submit_intent', "AND json_extract(data,'$.source')='user'"),
      stops: gate('emergency_interrupt_intent') + orchestration('terminal_input_write_intent', "AND json_extract(data,'$.data')=char(27)") };
  });

  // 4. Scores by executor and task type.
  const summary = new Map<string, { cli: string; model: string; effort: string; task_type: string; attempts: number; results: Record<string, number>;
    boundary: number[]; taste: number[] }>();
  for (const score of scores) {
    const taskType = score.facts?.task_type ?? taskTypes.get(score.task) ?? '未知';
    const key = [score.cli, score.model, score.effort, taskType].join('\u0000');
    const entry = summary.get(key) ?? { cli: score.cli, model: score.model, effort: score.effort, task_type: taskType, attempts: 0, results: {}, boundary: [], taste: [] };
    entry.attempts++;
    entry.results[score.data.result] = (entry.results[score.data.result] ?? 0) + 1;
    if (typeof score.data.boundary_discipline === 'number') entry.boundary.push(score.data.boundary_discipline);
    if (typeof score.data.engineering_taste === 'number') entry.taste.push(score.data.engineering_taste);
    summary.set(key, entry);
  }
  const mean = (values: number[]) => values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length * 100) / 100 : null;

  return {
    range: { project: range.project ?? null, since: range.since ?? null, until: range.until ?? null },
    model_use: { sessions, by_model: [...byModel.values()] },
    first_time: { integrated: passed.length, first_time: firstTime.length,
      rate: passed.length ? Math.round(firstTime.length / passed.length * 1000) / 1000 : null, rejections: reasons },
    attention,
    scores: [...summary.values()].map(({ boundary, taste, ...entry }) => ({ ...entry,
      boundary_discipline: mean(boundary), engineering_taste: mean(taste) })),
  };
}
