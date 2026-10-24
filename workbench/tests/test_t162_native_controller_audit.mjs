// 失败方式：真实主控已经有原生根提示，指标却把未覆盖显示为 0；读到别的会话或用户全局日志。
// 这是既有 T-133 真实 Claude CLI / 本地脚本化接口回归的只读复核，不调用供应商模型。
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync, writeFileSync, mkdirSync, mkdtempSync } from 'node:fs';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { DatabaseSync } from 'node:sqlite';

const { values } = parseArgs({ options: { summary: { type: 'string' }, 'controller-summary': { type: 'string' },
  revision: { type: 'string' }, mutant: { type: 'string' } } });
assert(values.summary && values['controller-summary'], 'Both summary paths are required.');
assert(!(values.revision && values.mutant), 'Select at most one target.');
assert(!existsSync(values.summary), 'Preserve the previous summary.');
const report = { status: 'INCOMPLETE', argv: process.argv, revision: values.revision ?? null, mutant: values.mutant ?? null,
  checks: [], sessions: [], vendor_model_turns: 0 };
let db;
try {
  const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
  let candidate = join(root, 'workbench/src/metrics.ts');
  if (values.revision || values.mutant) {
    let source = values.revision ? execFileSync('git', ['show', values.revision + ':workbench/src/metrics.ts'], { cwd: root, encoding: 'utf8' })
      : readFileSync(candidate, 'utf8');
    if (values.mutant) {
      assert.equal(values.mutant, 'unknown-as-zero', 'Unknown mutant.');
      const old = 'turns: facts?.turns ?? null,';
      assert.equal(source.split(old).length - 1, 1, 'The mutation location must match.');
      source = source.replace(old, 'turns: facts?.turns ?? 0,');
    }
    report.source_fixture = mkdtempSync('/private/tmp/t162-native-audit-');
    candidate = join(report.source_fixture, 'metrics.ts');
    writeFileSync(candidate, source, { flag: 'wx' });
  }
  const { metricsSnapshot } = await import(pathToFileURL(candidate).href);
  const upstream = JSON.parse(readFileSync(values['controller-summary'], 'utf8'));
  assert.equal(upstream.status, 'PASS', 'The controller regression must pass first.');
  const fixture = resolve(upstream.fixture);
  assert(fixture.startsWith('/private/tmp/t133t-'), 'Read only the owned controller fixture.');
  db = new DatabaseSync(join(fixture, 'state/state.sqlite3'), { readOnly: true });
  const metrics = metricsSnapshot(db, { project: 'demo' });
  const requests = db.prepare("SELECT launch,data FROM orchestration_events WHERE type='role_requested' ORDER BY seq").all();
  for (const row of requests) {
    const request = JSON.parse(String(row.data));
    if (!request.native_session) continue;
    const home = resolve(request.native_home);
    assert(home.startsWith(fixture + sep), 'Do not read global CLI state.');
    const projects = join(home, 'projects');
    const files = readdirSync(projects, { withFileTypes: true }).filter(entry => entry.isDirectory())
      .map(entry => join(projects, entry.name, request.native_session + '.jsonl')).filter(existsSync);
    assert.equal(files.length, 1, 'The native session must have one transcript.');
    const prompts = new Set();
    for (const line of readFileSync(files[0], 'utf8').split('\n').filter(Boolean)) {
      const native = JSON.parse(line);
      if (native.type === 'user' && native.promptId && !native.isSidechain && native.sessionId === request.native_session) prompts.add(native.promptId);
    }
    const session = metrics.model_use.sessions.find(item => item.launch === row.launch);
    const passed = prompts.size > 0 && session?.turns === null && session.turn_sources.length === 0;
    report.sessions.push({ launch: row.launch, native_session: request.native_session, native_file: files[0],
      root_prompt_ids: [...prompts], native_root_turns: prompts.size, metric_turns: session?.turns,
      metric_sources: session?.turn_sources, role: request.role });
    report.checks.push({ name: 'native_controller_turns_are_explicitly_uncovered:' + request.role, status: passed ? 'PASS' : 'FAIL' });
  }
  assert(report.sessions.length >= 2, 'Both native controller sessions must be present.');
  report.status = report.checks.every(row => row.status === 'PASS') ? 'PASS' : 'NO_GO';
} catch (error) {
  report.error = String(error.stack ?? error);
} finally {
  db?.close();
  mkdirSync(dirname(resolve(values.summary)), { recursive: true });
  writeFileSync(values.summary, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
}
process.stdout.write(JSON.stringify({ status: report.status, summary: values.summary }) + '\n');
process.exitCode = report.status === 'PASS' ? 0 : 1;
