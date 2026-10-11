// Runs only as a child of the fixture's actual foreground worker process.
// No operator credential is supplied or copied; capability values stay in env.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

assert.equal(process.env.A2A_ROLE, 'worker');
assert.ok(process.env.A2A_CAPABILITY && process.env.A2A_LAUNCH && process.env.A2A_REQUEST_DIR);
assert.equal(process.env.A2A_OPERATOR_CREDENTIAL, undefined);
const home = process.env.CODEX_HOME;
const batch = process.argv[2];
assert.ok(['1','2'].includes(batch));
const plan = JSON.parse(readFileSync(join(home, 'worker-client-plan-'+batch+'.json'), 'utf8'));
const result = { identity: { role:process.env.A2A_ROLE, launch:process.env.A2A_LAUNCH,
  task:process.env.A2A_TASK, attempt:process.env.A2A_ATTEMPT, session:process.env.A2A_SESSION,
  capability_present:true, operator_credential_present:false }, commands:[] };
for (const item of plan.commands) {
  const argv = [plan.client, '--state', process.env.A2A_STATE, ...item.args];
  const run = spawnSync(process.execPath, argv, { env:process.env, encoding:'utf8', timeout:10000 });
  writeFileSync(join(home, item.name+'.stdout'), run.stdout ?? '', {flag:'wx'});
  writeFileSync(join(home, item.name+'.stderr'), run.stderr ?? '', {flag:'wx'});
  if (run.error || run.signal) throw run.error ?? new Error('Client exited by signal: '+run.signal);
  const response = JSON.parse(run.stdout);
  result.commands.push({ name:item.name, argv, exit:run.status, response });
}
writeFileSync(join(home, 'worker-client-result-'+batch+'.json'), JSON.stringify(result,null,2)+'\n', {flag:'wx'});
