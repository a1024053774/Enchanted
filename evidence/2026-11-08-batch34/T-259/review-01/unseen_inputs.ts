// T-259: real A2AGates -> Panes -> PTY creation, then one failed identity read.
// Oracle: the ticket permits reclaim only for an owned, stopped, unsent preparation.
// Failure modes fixed before implementation: no recovery; a foreign creation/PID/attempt adopted;
// sent/uncertain input reclaimed; busy locks or running panes bypassed; path release before archive;
// restart/repeated reclaim loses provenance; dirty files or original failure removed.
// The compiled CLI stand-in emits only --version and waits. No model/native-session output is invented.
import { mkdirSync, mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { DatabaseSync } from 'node:sqlite';

const [sourceArg, summaryArg, only] = process.argv.slice(2);
if (!sourceArg || !summaryArg) throw new Error('usage: node test_t259_preparing_reclaim.ts SOURCE SUMMARY [SCENARIO]');
const source = resolve(sourceArg), summary = resolve(summaryArg);
if (existsSync(summary)) throw new Error('preserve existing evidence; choose a new summary');
const load = (name: string) => import(pathToFileURL(join(source, 'workbench/src', name)).href);
const { A2AGates } = await load('gates/core.ts');
const { OrchestrationStore } = await load('store.ts');
const { Panes } = await load('panes.ts');
const root = mkdtempSync('/private/tmp/t259-probe-');
const report: any = { status: 'INCOMPLETE', argv: process.argv, source, fixture: root,
  boundary: 'real A2AGates, Panes, PTY, Git, SQLite; compiled CLI stand-in; one injected read failure',
  model_calls: 0, checks: [], errors: [], cleanup: null };
const executable = join(root, 'waiting-cli');
writeFileSync(executable + '.c', '#include <stdio.h>\n#include <string.h>\n#include <unistd.h>\nint main(int n,char**a){if(n==2&&!strcmp(a[1],"--version")){puts("t259-fixture 1");return 0;}for(;;)pause();}\n');
execFileSync('/usr/bin/cc', [executable + '.c', '-o', executable]);
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
const git = (repo: string, args: string[]) => execFileSync('git', ['-C', repo, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
const check = (name: string, passed: unknown, detail?: unknown) => report.checks.push({ name, passed: Boolean(passed), detail });
const cases = ['review-screen-key','review-composition','review-hc-send'];
try {
  for (const name of cases.filter(n => !only || n === only)) {
    const dir = join(root, name); mkdirSync(dir);
    const state = join(dir, 'state'), repo = join(dir, 'repo'), home = join(dir, 'home');
    for (const p of [state, repo, home]) mkdirSync(p);
    git(repo, ['init', '-b', 'main']); git(repo, ['config', 'user.name', 'T259 fixture']); git(repo, ['config', 'user.email', 'fixture@example.invalid']);
    writeFileSync(join(repo, 'check.py'), 'raise SystemExit(0)\n');
    writeFileSync(join(repo, 'note.txt'), 'original\n');
    git(repo, ['add', '.']); git(repo, ['commit', '-m', 'fixture baseline']);
    const role = join(dir, 'role.txt'); writeFileSync(role, 'isolated test; no model');
    const card = { id: 'T-259', source: null, goal: 'Recover a stopped, unsent preparation', non_goals: ['no model execution'],
      paths: { allow: ['note.txt'], deny: [] }, oracle_paths: ['check.py'], completion_conditions: [{ argv: ['/usr/bin/python3', 'check.py'] }],
      red_commands: [], task_type: '测试', repair_target: null, complexity: 'S', executor: { cli: 'Codex', model: 'fixture', effort: 'high' },
      base_commit: null, writer: null };
    const cardFile = join(dir, 'card.json'); writeFileSync(cardFile, JSON.stringify(card));
    const store = new OrchestrationStore(state);
    const originalLaunch = store.launch.bind(store), originalEvent = store.event.bind(store);
    store.launch = (value: any) => {
      const v = { ...value };
      if (name.startsWith('record-')) {
        const key = name.slice(7); v[key] = typeof v[key] === 'number' ? v[key] + 1 : 'foreign-' + v[key];
      }
      originalLaunch(v);
      if (name === 'duplicate-launch') originalLaunch({ ...v, id: 'duplicate-' + v.id });
    };
    store.event = (type: string, data: any, binding: any) => {
      if (type === 'pane_started' && name === 'missing-start') return 0;
      return originalEvent(type, type === 'pane_started' && name === 'wrong-start-shell' ? { ...data, shell_pid: data.shell_pid + 999 } : data, binding);
    };
    let panes = new Panes(state, store, { codex_bin: executable, codex_home: home, role_card: role,
      code_revision: 'fixture-product', role_card_revision: 'fixture-role', hook_authorization: 'test-only', turn_limit: 1 }, () => {});
    let gates = new A2AGates(state, panes);
    let holder: DatabaseSync | undefined;
    let pane: any;
    const requestDirs: string[] = [];
    try {
      for (const input of [
        { command: 'card_save', task: 'demo+T-259', card: cardFile, expected_version: 0 },
        { command: 'create', task: 'demo+T-259', project: 'demo', repo, branch: 'refs/heads/main', card_version: 1 },
      ]) { const result = await gates.call(input); if (!result.ok) throw new Error(JSON.stringify(result)); }
      const read = panes.readThread.bind(panes);
      let inject = true;
      panes.readThread = async (thread: string) => {
        if (inject) { inject = false; throw new SyntaxError('T259 injected failure after real pane creation'); }
        return read(thread);
      };
      const dispatched = await gates.call({ command: 'dispatch', task: 'demo+T-259', runtimeMode: 'workspace-write' });
      const status = await gates.call({ command: 'status', task: 'demo+T-259' });
      const attempt = status.task.current_attempt;
      pane = panes.get(attempt.thread_id); requestDirs.push(pane.record.request_dir);
      const deadline = Date.now() + 5000;
      while (!pane.leader && Date.now() < deadline) { await panes.processInfo(attempt.thread_id); await sleep(10); }
      if (!pane.leader) throw new Error('fixture CLI never became the PTY foreground leader');
      check(name + ': real dispatch failed before binding', dispatched.error === 'gate_failure' && attempt.state === 'preparing' &&
        attempt.runtime_identity === null && pane.pty.pid > 1 && pane.leader > 1, { error: dispatched.error, details: dispatched.details });
      if (name !== 'running') await panes.shutdown(); // Real termination, never a forged stopped flag.
      if (name === 'restart') {
        gates.close();
        panes = new Panes(state, store, {}, () => {});
        await panes.recover('t259-second-daemon');
        gates = new A2AGates(state, panes);
      }
      const before = await panes.readThread(attempt.thread_id);
      if (name.startsWith('live-')) {
        const original = panes.readThread.bind(panes);
        panes.readThread = async (thread: string) => {
          const live = await original(thread), key = name.slice(5);
          if (key === 'launch') live.runtime_identity.launch = 'foreign-launch';
          if (key === 'thread') live.runtime_identity.thread = 'foreign-thread';
          if (key === 'shell') live.runtime_identity.shell_pid += 999;
          if (key === 'leader') live.runtime_identity.leader_pid += 999;
          if (key === 'native') live.runtime_identity.native_session = 'foreign-session';
          if (key === 'turn') live.turn = 'unaccounted-turn';
          if (key === 'provider') live.provider = 'claude';
          if (key === 'workspace') live.workspace = repo;
          return live;
        };
      }
      if (name === 'dirty') writeFileSync(join(attempt.workspace, 'note.txt'), 'preserve this failed attempt\n');
      if (name === 'prompt-intent') (gates as any).event('demo+T-259', 'prompt_intent', { thread: attempt.thread_id }, attempt.attempt_id);
      if (name === 'dispatch-record') store.register(pane.record.id, 'queued but not sent', 'executor');
      const events: Record<string, string> = { 'paste-intent': 'paste_intent', 'input-intent': 'terminal_input_write_intent',
        'turn-intent': 'turn_submit_intent', 'native-record': 'native_record', 'unknown-send': 'dispatch_unknown', 'native-bound': 'pane_native_session' };
      if (events[name]) originalEvent(events[name], { native_session: 'unknown', record: { type: 'event_msg', payload: { type: 'task_started' } } }, pane.record);
      if (name === 'lock') { holder = new DatabaseSync(join(state, 'locks/demo+T-259.sqlite3')); holder.exec('BEGIN IMMEDIATE'); }
      const reviewInputs: Record<string,string> = {'review-screen-key':'controller_screen_key_intent', 'review-composition':'terminal_composition_started', 'review-hc-send':'hc_send_intent'};
      if(reviewInputs[name]) originalEvent(reviewInputs[name], {request_id: 'unseen-review-sentinel-20261108'}, pane.record);
      const effects: string[] = [];
      const stop = panes.stopThread.bind(panes), archive = panes.archiveThread.bind(panes);
      panes.stopThread = async (thread: string) => { effects.push('stop'); if (name === 'stop-fails') throw new Error('injected stop refusal'); await stop(thread); };
      panes.archiveThread = async (thread: string) => { effects.push('archive'); if (name === 'archive-fails') throw new Error('injected archive refusal'); await archive(thread); };
      const result = await gates.call({ command: 'reclaim', task: 'demo+T-259', attempt: attempt.attempt_id });
      holder?.exec('ROLLBACK'); holder?.close(); holder = undefined;
      const after = (await gates.call({ command: 'status', task: 'demo+T-259' })).task;
      const success = ['stopped', 'restart', 'dirty'].includes(name);
      check(name + ': reclaim contract', success ? result.ok : !result.ok, { result, before, effects });
      if (success) {
        check(name + ': old attempt released after confirmed archive', after.state === 'ready' && after.current_attempt === null &&
          effects.join(',') === 'stop,archive' && (await panes.readThread(attempt.thread_id)).archived);
        check(name + ': dirty work preserved / clean work reclaimed', name === 'dirty' ?
          readFileSync(join(attempt.workspace, 'note.txt'), 'utf8') === 'preserve this failed attempt\n' : !existsSync(attempt.workspace));
        const again = await gates.call({ command: 'reclaim', task: 'demo+T-259', attempt: attempt.attempt_id });
        check(name + ': repeated reclaim has no repeated runtime action', again.ok && effects.length === 2);
        const rows = gates.db.prepare('SELECT type,details FROM events WHERE attempt=? ORDER BY seq').all(attempt.attempt_id);
        check(name + ': original error and bound recovery evidence retained', rows.some((r: any) => r.type === 'rejected' && r.details.includes('T259 injected')) &&
          rows.some((r: any) => r.type === 'reclaimed' && r.details.includes(pane.record.id)));
        if (name === 'stopped') {
          // Claim uses the unchanged dispatch path again; the second deliberate read failure is a new attempt.
          const readAgain = panes.readThread.bind(panes);
          panes.readThread = async () => { throw new Error('second creation probe'); };
          const next = await gates.call({ command: 'dispatch', task: 'demo+T-259', runtimeMode: 'workspace-write' });
          panes.readThread = readAgain;
          const newAttempt = (await gates.call({ command: 'status', task: 'demo+T-259' })).task.current_attempt;
          requestDirs.push(panes.get(newAttempt.thread_id).record.request_dir);
          check('stopped: same task can create a new attempt', next.error === 'gate_failure' && newAttempt.attempt_id !== attempt.attempt_id && newAttempt.fence === attempt.fence + 1);
        }
      } else {
        check(name + ': paths and evidence remain reserved', after.current_attempt?.attempt_id === attempt.attempt_id && existsSync(attempt.workspace));
        check(name + ': no unrelated runtime action', ['archive-fails', 'stop-fails'].includes(name) || effects.length === 0);
      }
      check(name + ': no task input was sent', store.db.prepare("SELECT count(*) AS n FROM orchestration_events WHERE type IN ('paste_written','turn_submitted','terminal_input_written')").get().n === 0);
    } catch (error: any) { report.errors.push({ scenario: name, error: String(error), stack: error.stack }); }
    finally {
      holder?.close();
      try { await panes.shutdown(); } catch (error) { report.errors.push({ scenario: name, cleanup: String(error) }); }
      // Confirm fixture process trees have exited before deleting their text-free data.
      for (const record of store.launches()) {
        const started = store.lastEvent(record.id, ['pane_started']);
        if (started) {
          const proc = JSON.parse(execFileSync('/usr/bin/python3', ['-I', '-S', '-B', join(source, 'workbench/src/processSnapshot.py'), String(started.data.shell_pid)], { encoding: 'utf8' }));
          check(name + ': fixture shell stopped ' + record.id, proc.rows.length === 0);
        }
      }
      const manifest = join(state, 'hc-runtime.json');
      if (existsSync(manifest)) {
        const identity = JSON.parse(readFileSync(manifest, 'utf8'));
        const installs = readdirSync(join(state, 'hc'), { withFileTypes: true })
          .filter(e => e.isDirectory() && e.name.startsWith('herdr-core-'));
        for (const install of installs) {
          const binary = join(state, 'hc', install.name, 'herdr-core');
          const stopped = execFileSync(binary, ['server', 'stop'], { encoding: 'utf8', timeout: 15000,
            env: { ...process.env, HC_SESSION: identity.session, HC_SOCKET: identity.socket,
              XDG_STATE_HOME: join(state, 'hc/state'), XDG_CONFIG_HOME: join(state, 'hc/config') } });
          check(name + ': private core stopped', JSON.parse(stopped).stopped === true, identity.session);
        }
        if (dirname(identity.socket).startsWith('/private/tmp/enchanted-hc-')) rmSync(dirname(identity.socket), { recursive: true, force: true });
      }
      gates.close(); store.close();
      for (const p of requestDirs) rmSync(p, { recursive: true, force: true });
    }
  }
  report.status = report.errors.length ? 'INCOMPLETE' : report.checks.every((c: any) => c.passed) ? 'PASS' : 'FAIL';
} finally {
  let bytes = 0, files = 0;
  const visit = (p: string) => { for (const e of readdirSync(p, { withFileTypes: true })) { const f = join(p, e.name); if (e.isDirectory()) visit(f); else { bytes += statSync(f).size; files++; } } };
  visit(root); report.cleanup = { fixture: root, files, bytes, action: 'removed after text results captured' };
  mkdirSync(resolve(summary, '..'), { recursive: true });
  writeFileSync(summary, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  if (!report.errors.some((e: any) => e.cleanup) && report.checks.filter((c: any) => c.name.includes('fixture shell stopped')).every((c: any) => c.passed)) rmSync(root, { recursive: true });
}
console.log(JSON.stringify({ status: report.status, checks: report.checks.length, failed: report.checks.filter((c: any) => !c.passed).map((c: any) => c.name), errors: report.errors, summary }));
process.exitCode = report.status === 'PASS' ? 0 : 1;
