// Launch contract only; native sandbox, MCP and answer delivery need the E2E run.
// Failure modes: closed network, MCP suppression, project/tool overrides,
// missing approval policy, and reviewer rejection of the new launch contract.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import vm from 'node:vm';
import { resolve } from 'node:path';
const [output, source = '.'] = process.argv.slice(2);
if (!output || existsSync(output)) throw new Error('Fresh summary path required');
const report = { status: 'INCOMPLETE', checks: [] };
try {
  const text = readFileSync(resolve(source, 'workbench/src/panes.ts'), 'utf8');
  const begin = text.indexOf('async function claudeArgv(');
  const end = text.indexOf('\nconst STARTUP_DEADLINE_MS', begin);
  assert.ok(begin >= 0 && end > begin);
  const context = vm.createContext({});
  vm.runInContext(stripTypeScriptTypes(text.slice(begin, end)), context);
  const argv = await context.claudeArgv('/claude', 'signal', 'session',
    { model: 'claude-haiku-5-5', effort: 'low', fast: false }, ['/work', '/requests'], ['/requests'], ['/git'], ['/extra']);
  assert.ok(!argv.includes('--strict-mcp-config'), 'T-141: user MCP must load');
  const settings = JSON.parse(argv[argv.indexOf('--settings') + 1]);
  assert.ok(settings.sandbox.network.allowedDomains.includes('*'), 'T-141: all network hosts');
  assert.equal(settings.sandbox.enabled, true);
  assert.equal(settings.sandbox.allowUnsandboxedCommands, false);
  assert.deepEqual(settings.sandbox.filesystem.denyWrite, ['/git']);
  assert.ok(argv.includes('--add-dir') && argv.includes('/extra'));
  report.checks.push('claude_network_mcp_write_boundary');
  const launch = text.slice(text.indexOf('private async createPane('), text.indexOf('\n  //', text.indexOf('    this.store.launch(record);', text.indexOf('private async createPane('))));
  assert.ok(!launch.includes('network_access=false') && !launch.includes('const networkAccess = "false"'), 'T-141: Codex network closed');
  assert.ok(!launch.includes('features.network_proxy=') && !launch.includes('trust_level='), 'T-141: inherit user trust and tools');
  assert.ok(launch.includes('"-a", "never"'), 'T-141: never wait for native approval');
  report.checks.push('codex_inherits_user_configuration');
  report.status = 'PASS';
} catch (error) { report.error = String(error); }
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(report));
process.exitCode = report.status === 'PASS' ? 0 : 1;
