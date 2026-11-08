"""T-253 审查 01 P2 的后台一侧：t253_shutdown_host.ts 起真实编排后台（serve、门禁、存储、私有 hc core），
把一个夹具窗格交给后台自己的“窗格得知会话号”回调，窗格读取是脚本化的；不起 CLI、PTY 子进程、钩子或模型。

两个场景，期望来自审查 01 P2 与票据（绑定被拒要记下，attempt 保持未绑定）：
- stop_while_binding：绑定还在读窗格时发 daemon_stop。期望后台等这次绑定收尾、记下 native_session_bind_failed
  （daemon_stopping）、门禁没有 runtime_bound、以 0 退出。
- record_write_fails：绑定被拒，而这条记录本身写不进去。期望后台不退出、在 stderr 报 event_write_failed，
  之后照常 daemon_stop、以 0 退出。
- binding_outlives_stop（T-254）：停止开始后窗格读取 30 秒才返回。期望来自 T-254 票据与用户要求（“这个应该设置一个
  合理的上限”）：停止最多等 10 秒，到期在关库前记一条 native_session_bind_abandoned，然后关库、删 daemon.pid；
  读取返回后不再写任何记录，stderr 没有 event_write_failed，以 0 退出，门禁没有 runtime_bound。
另外两个场景也查：daemon.pid 已删；stop_while_binding 关库后 3 秒内退出（等绑定的计时器已清）。

--revision 从 Git 取该版产品源码；--mutant 在当前源码副本上打 MUTANTS 里的变异；都不给时用当前工作区源码。
摘要写到 --summary；通过时删除夹具目录，失败时保留并在摘要里写明。
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

from scripted_claude import ROOT, source_tree, stop_fixture_core

DAEMON = 'src/daemon.ts'
MUTANTS = {
    # Shutdown closes the stores without waiting for bindings still in flight.
    'shutdown-skips-bindings': ((DAEMON, '    await Promise.all([...bindings]);\n', ''),),
    # A refusal whose record cannot be written is left to throw inside the catch.
    'bind-record-unguarded': ((DAEMON,
        '      try { store.event("native_session_bind_failed", data, pane.record); }\n'
        '      catch (recordError) {\n'
        '        // As panes.recordFailure: the failed write is reported on stderr and marks the user-input observer failed.\n'
        '        const reason = `event_write_failed: ${String(recordError)}; original native_session_bind_failed: ${data.error}`;\n'
        '        console.error(JSON.stringify({ error: "event_write_failed", launch: pane.record.id, reason }));\n'
        '        panes.onEventWriteFailed(reason);\n'
        '      }\n',
        '      store.event("native_session_bind_failed", data, pane.record);\n'),),
    # T-254: the stop waits as long as the binding takes (a bound far beyond the scenario's 30 s read).
    'stop-wait-unbounded': ((DAEMON, 'const BINDING_STOP_WAIT_MS = 10_000;\n', 'const BINDING_STOP_WAIT_MS = 600_000;\n'),),
    # T-254: a binding past the bound is not marked, so its late refusal is written into the closed stores.
    'abandon-unmarked': ((DAEMON, '      binding.abandoned = true;\n', ''),),
    # T-254: a binding past the bound is left unbound without a record.
    'abandon-unrecorded': ((DAEMON,
        '      store.event("native_session_bind_abandoned", { native_session: binding.native_session,\n'
        '        waited_ms: Date.now() - waitStarted }, binding.record);\n', ''),),
    # T-254: the bound's timer outlives a wait that ended in time, holding the stopped daemon for 10 s.
    'timer-kept': ((DAEMON, '    clearTimeout(timer);\n', ''),),
}
HOST = Path(__file__).resolve().parent / 't253_shutdown_host.ts'


def wait(condition, host, seconds, message):
    deadline = time.monotonic() + seconds
    while not condition():
        if host.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError(message)
        time.sleep(0.02)


def scenario(source, name, keep):
    root = Path(tempfile.mkdtemp(prefix='t253-stop-', dir='/tmp')).resolve()
    state, control = root / 'state', root / 'control'
    control.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.update(A2A_OPERATOR_CREDENTIAL=str(root / 'operator.json'),
               ENCHANTED_HC_CACHE_DIR=os.environ.get('ENCHANTED_HC_CACHE_DIR', str(ROOT.parent / 'hc-cache')))
    cli = ['node', str(source / 'workbench/src/gates/cli.ts'), '--state', str(state)]
    report = dict(scenario=name, fixture=str(root), checks=[], failed=[], observed={})
    check = lambda label, ok, detail=None: (report['checks'].append(dict(name=label, ok=bool(ok), detail=detail)),
                                            None if ok else report['failed'].append(label))
    out, err = (root / 'host.stdout.txt').open('wb'), (root / 'host.stderr.txt').open('wb')
    host = subprocess.Popen(['node', str(HOST), str(source), str(state), str(control), str(control / 'ready.json'), name],
                            cwd=str(ROOT / 'workbench'), env=env, stdout=out, stderr=err, start_new_session=True)
    try:
        wait(lambda: (control / 'ready.json').exists(), host, 30, 'host did not reach ready')
        if name in ('stop_while_binding', 'binding_outlives_stop'):
            wait(lambda: (control / 'bind-entered').exists(), host, 10, 'the binding did not reach the pane read')
        else:
            wait(lambda: (control / 'host.jsonl').exists() and 'record_refused' in (control / 'host.jsonl').read_text(),
                 host, 10, 'the refusal record was not attempted')
            time.sleep(1.0)
            report['observed']['alive_after_refused_record'] = host.poll() is None
            check('daemon_survives_failed_record', host.poll() is None, host.poll())
        stop = subprocess.run([*cli, 'daemon_stop'], env=env, capture_output=True, text=True, timeout=30)
        report['observed']['stop'] = dict(exit=stop.returncode, stdout=stop.stdout[-2000:], stderr=stop.stderr[-2000:])
        try:
            host.wait(timeout=45 if name == 'binding_outlives_stop' else 30)
            report['observed']['host_exit_at'] = datetime.now(timezone.utc).isoformat()
        except subprocess.TimeoutExpired:
            report['observed']['host_timeout'] = True
    except RuntimeError as error:
        report['error'] = str(error)
    finally:
        if host.poll() is None:
            host.kill(); host.wait()
        out.close(); err.close()
        try:
            report['observed']['hc_cleanup'] = stop_fixture_core(state, root, env)
        except AssertionError as error:
            report['observed']['hc_cleanup_error'] = str(error)
            report['failed'].append('hc_cleanup')
    stderr = (root / 'host.stderr.txt').read_text(errors='replace')
    report['observed'].update(host_exit=host.returncode, host_stderr=stderr[-4000:],
                              host_notes=[json.loads(line) for line in (control / 'host.jsonl').read_text().splitlines()]
                              if (control / 'host.jsonl').exists() else [])
    events, gate_events = [], []
    if (state / 'state.sqlite3').exists():
        # Read after the host has exited (or been killed); a read-only open of a WAL database without its -shm fails.
        with contextlib.closing(sqlite3.connect(state / 'state.sqlite3')) as db:
            events = [dict(type=t, launch=l, data=json.loads(d)) for t, l, d in
                      db.execute("SELECT type, launch, data FROM orchestration_events WHERE type IN "
                                 "('native_session_bind_failed','native_session_bind_abandoned','daemon_stopped') ORDER BY seq")]
            gate_events = [t for (t,) in db.execute("SELECT type FROM events WHERE type='runtime_bound'")]
    report['observed'].update(orchestration_events=events, runtime_bound=gate_events)
    stop = report['observed'].get('stop', {})
    check('stop_accepted', stop.get('exit') == 0 and '"ok": true' in stop.get('stdout', '').replace('"ok":true', '"ok": true'), stop)
    check('host_exit_zero', host.returncode == 0, host.returncode)
    check('nothing_bound', gate_events == [], gate_events)
    check('pid_removed', not (state / 'daemon.pid').exists())
    notes = report['observed']['host_notes']
    at = lambda note: next((datetime.fromisoformat(n['at'].replace('Z', '+00:00')) for n in notes if n['name'] == note), None)
    exit_at = report['observed'].get('host_exit_at')
    exit_at = datetime.fromisoformat(exit_at) if exit_at else None
    failures = [e for e in events if e['type'] == 'native_session_bind_failed' and e['launch'] == 't253-launch']
    abandoned = [e for e in events if e['type'] == 'native_session_bind_abandoned' and e['launch'] == 't253-launch']
    write_failures = [json.loads(line) for line in stderr.splitlines() if line.startswith('{"error":"event_write_failed"')]
    if name == 'stop_while_binding':
        check('bind_failure_recorded', len(failures) == 1 and failures[0]['data'].get('error') == 'daemon_stopping', failures)
        closed_at = at('gates_closed')
        lag = (exit_at - closed_at).total_seconds() if exit_at and closed_at else None
        report['observed']['exit_after_close_seconds'] = lag
        check('exits_soon_after_close', lag is not None and lag <= 3, lag)
    elif name == 'binding_outlives_stop':
        stop_at, closed_at = at('stop_seen'), at('gates_closed')
        took = (closed_at - stop_at).total_seconds() if stop_at and closed_at else None
        report['observed']['close_after_stop_seconds'] = took
        check('stores_closed_within_bound', took is not None and took <= 15, took)
        check('abandon_recorded', len(abandoned) == 1 and abandoned[0]['data'].get('native_session') == 'codex-fixture-session'
              and isinstance(abandoned[0]['data'].get('waited_ms'), int) and abandoned[0]['data']['waited_ms'] >= 9900, abandoned)
        returned = [n for n in notes if n['name'] == 'read_returned']
        check('late_read_ran_after_close', len(returned) == 1 and returned[0].get('after') == 'gates_closed', returned)
        check('nothing_written_after_close', failures == [] and write_failures == [], dict(failures=failures, stderr=write_failures))
    else:
        check('write_failure_reported', any(row.get('launch') == 't253-launch' for row in write_failures), write_failures)
    report['status'] = 'FAIL' if report['failed'] or report.get('error') else 'PASS'
    if report['status'] == 'PASS' and not keep:
        shutil.rmtree(root, ignore_errors=True)
        report['fixture_deleted'] = True
    return report


def main():
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    summary = args.summary.resolve()
    summary.parent.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix='t253-src-', dir='/tmp')) if args.revision or args.mutant else None
    source = source_tree(fixture, args.revision, MUTANTS.get(args.mutant, ())) if fixture else ROOT
    runs = [scenario(source, name, keep=False) for name in ('stop_while_binding', 'record_write_fails', 'binding_outlives_stop')]
    report = dict(status='PASS' if all(run['status'] == 'PASS' for run in runs) else 'FAIL', argv=sys.argv,
                  revision=args.revision, mutant=args.mutant, source_fixture=str(fixture) if fixture else None,
                  failed=[f"{run['scenario']}:{name}" for run in runs for name in run['failed']] +
                         [f"{run['scenario']}:error" for run in runs if run.get('error')], scenarios=runs)
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if fixture and report['status'] == 'PASS':
        shutil.rmtree(fixture, ignore_errors=True)
    print(report['status'], ','.join(report['failed']))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
