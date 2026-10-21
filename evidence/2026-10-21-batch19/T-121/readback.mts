// Test-only: read back the daemon's own records after the GUI run, then stop the daemon.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
const [state, source, out] = process.argv.slice(2);
process.env.A2A_OPERATOR_CREDENTIAL = JSON.parse(readFileSync(join(state, 'desktop-connection.json'), 'utf8')).credential;
const { request } = await import(join(source, 'src/transport.ts'));
const { readOperatorCredential } = await import(join(source, 'src/credentials.ts'));
const operator = readOperatorCredential(state);
const sidebar = await request(state, { command: 'sidebar_snapshot' });
const events = (await request(state, { command: 'orchestration_events' })).events.filter((e: any) => e.type.startsWith('role_'));
writeFileSync(out, JSON.stringify({ agents: sidebar.agents, pending_role_requests: sidebar.role_requests, role_request_events: events }, null, 2) + '\n');
console.log(JSON.stringify(await request(state, { command: 'daemon_stop' }, operator)));
