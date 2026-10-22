// Copied from T-118 for T-129 (credential read from <state>-credentials after T-126).
// Test-only: register fixture directories through the daemon's operator API,
// the same command the 打开项目目录 dialog sends after the user picks a folder.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
const [state, ...repos] = process.argv.slice(2);
process.env.A2A_OPERATOR_CREDENTIAL = JSON.parse(readFileSync(join(state + '-credentials', 'desktop-connection.json'), 'utf8')).credential;
const { request } = await import('/Users/luckye/Documents/Code/a2a/workbench/src/transport.ts');
const { readOperatorCredential } = await import('/Users/luckye/Documents/Code/a2a/workbench/src/credentials.ts');
const operator = readOperatorCredential(state);
for (const repo of repos) console.log(JSON.stringify(await request(state, { command: 'project_open', repo }, operator)));
console.log(JSON.stringify(await request(state, { command: 'project_open', repo: repos[0] }, operator)));
