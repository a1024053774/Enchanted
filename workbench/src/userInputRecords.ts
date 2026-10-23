import type { DatabaseSync } from 'node:sqlite';
import type { A2AUserInput } from './contracts/a2aGates.ts';

// The user-input records of one project for the records page (T-133), read as the gate stored them. An input the
// gate turned into a human intervention (a managed attempt's session) carries that event's sequence.
export function userInputRecords(db: DatabaseSync, project: string) {
  const roles = new Map<string, { role: string; preset: string | null; launch: string }>();
  for (const row of db.prepare('SELECT data FROM launch_records ORDER BY rowid').all()) {
    const record = JSON.parse(String(row.data));
    if (record.thread) roles.set(record.thread, { role: record.role, preset: record.preset ?? null, launch: record.id });
  }
  // A prompt from a terminal controller names the role request it was kept under (T-133).
  const requested = new Map<string, string>();
  for (const row of db.prepare("SELECT json_extract(data,'$.role_request') AS id, json_extract(data,'$.role') AS role FROM orchestration_events WHERE type='role_requested'").all())
    requested.set(String(row.id), String(row.role));
  const interventions = new Map<string, number>();
  for (const row of db.prepare("SELECT seq, json_extract(details,'$.input_id') AS input FROM events WHERE type='human_intervention'").all())
    interventions.set(String(row.input), Number(row.seq));
  return db.prepare("SELECT data FROM user_inputs WHERE json_extract(data,'$.target.project')=? ORDER BY rowid").all(project)
    .map(row => JSON.parse(String(row.data)) as A2AUserInput)
    .map(input => {
      const session = roles.get(input.target.thread);
      return { id: input.id, created_at: input.created_at, form: input.form, channel: input.channel, certainty: input.certainty,
        text: input.text, task: input.target.task, attempt: input.target.attempt, thread: input.target.thread,
        launch: session?.launch ?? null, role: input.channel === 'controller-terminal' ? requested.get(input.source_ref?.label ?? '') ?? null
          : session ? session.preset ?? session.role : null,
        intervention: interventions.get(input.id) ?? null, question: input.question ?? null };
    });
}
