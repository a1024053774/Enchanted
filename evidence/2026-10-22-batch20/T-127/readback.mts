// Test-only (T-127, copied from T-122's): read back the daemon's own records after the GUI run, then stop the daemon.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
const [state, source, out] = process.argv.slice(2);
process.env.A2A_OPERATOR_CREDENTIAL = JSON.parse(readFileSync(join(state, 'desktop-connection.json'), 'utf8')).credential;
const { request } = await import(join(source, 'src/transport.ts'));
const { readOperatorCredential } = await import(join(source, 'src/credentials.ts'));
const operator = readOperatorCredential(state);
const sidebar = await request(state, { command: 'sidebar_snapshot' });
const launches = sidebar.agents.filter((agent: any) => ['worker', 'reviewer'].includes(agent.role));
const records = [];
for (const agent of launches) {
  const { launch } = await request(state, { command: 'launch_show', launch: agent.id }, operator);
  records.push({ id: launch.id, role: launch.role, cli: launch.cli, parent_launch: launch.parent_launch, native_session: launch.native_session,
    model_requested: launch.model_requested, effort_requested: launch.effort_requested, argv: launch.argv });
}
const status = await request(state, { command: 'status', task: 'T-1' }, operator);
const gate = await request(state, { command: 'events', task: 'T-1' }, operator);
const events = (await request(state, { command: 'orchestration_events' })).events
  .filter((e: any) => /^(role_|worker_trust|codex_restricted|codex_folder_trust|worker_startup|launch_failed|native_session_started|pane_native_session|native_turn_facts|relay_|pane_started|turn_submitted)/.test(e.type))
  .map((e: any) => ({ seq: e.seq, type: e.type, launch: e.launch, data: e.type === 'worker_trust_confirm_intent' ? undefined : e.data }));
writeFileSync(out, JSON.stringify({ agents: sidebar.agents, launch_records: records, task: status.task && { state: status.task.state,
  candidate_commit: status.task.candidate_commit, review: status.task.review && { state: status.task.review.state, verdict: status.task.review.result?.verdict } },
  gate_events: gate.events?.map((e: any) => e.type), orchestration_events: events }, null, 2) + '\n');
console.log(JSON.stringify(await request(state, { command: 'daemon_stop' }, operator)));
