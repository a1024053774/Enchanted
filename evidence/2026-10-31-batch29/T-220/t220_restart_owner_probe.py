#!/usr/bin/env python3
"""T-220 probe 2: who brings a SIGKILLed private core back, how fast, and with whose environment.

run-01 showed the core reappearing within 5 s with no client call from the test. This probe separates the
candidates. Phase holder: the daemon is stopped before the kill, so only the holder (parent of the shells)
and the shells remain. Phase calls: holders and shells are gone too; each hc command then runs against a dead
core, one at a time. Phase race: the daemon runs, the core is killed, and a client inside the pane calls hc at
once. A new core's environment is read from a terminal it launches (`hc run --bg`), and from which state
directory it writes (private XDG versus the fixture HOME's default).

Same boundaries as t220_core_restart_probe.py: real gates CLI, pinned hc, disposable fixture with its own HOME.
Usage: python3 t220_restart_owner_probe.py --output DIR
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import uuid

ROOT = Path('/Users/luckye/Documents/Code/a2a')
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from hc_evidence import assert_public_evidence, user_core_snapshot  # noqa: E402

ZSHRC = r'''PS1='T220% '
( while [[ ! -e $T220_DIR/trigger-$A2A_TERMINAL ]]; do sleep 0.02; done
  T220_STARTER=terminal-agent "$T220_HC" --json ls > "$T220_DIR/agent-$A2A_TERMINAL.out" 2> "$T220_DIR/agent-$A2A_TERMINAL.err"
  echo $? > "$T220_DIR/agent-$A2A_TERMINAL.exit" ) &!
'''

ENV_PROGRAM = r'''
import json, os, sys
keys = ['T220_MARKER', 'T220_STARTER', 'XDG_STATE_HOME', 'A2A_TERMINAL']
data = {k: os.environ.get(k) for k in keys}
data['A2A_TERMINAL_TOKEN_present'] = bool(os.environ.get('A2A_TERMINAL_TOKEN'))
open(sys.argv[1], 'w').write(json.dumps(data))
'''


def wait_for(probe, message, seconds=15.0, step=.1):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = probe()
        if value:
            return value
        time.sleep(step)
    raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t220b-', dir='/private/tmp'))
    state, home, marks = fixture / 'state', fixture / 'home', fixture / 'marks'
    for d in (state, home, marks):
        d.mkdir()
    (home / '.zshrc').write_text(ZSHRC, encoding='utf-8')
    binary = state / 'hc/bin/herdr-core'
    env = {key: os.environ[key] for key in ('PATH', 'LANG') if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TMPDIR='/private/tmp', T220_MARKER='daemon',
               T220_DIR=str(marks), T220_HC=str(binary))
    report = dict(status='INCOMPLETE', command=[sys.executable, *sys.argv], fixture=str(fixture), commands=[],
                  real_model_calls=0, phases={})
    before = user_core_snapshot()
    running, manifest, launches, probes = False, None, [], 0

    def record(argv, run):
        report['commands'].append(dict(argv=[str(a) for a in argv], exit=run.returncode,
                                       stdout=run.stdout[-1500:], stderr=run.stderr[-1500:]))

    def cli(*arguments, check=True):
        argv = ['node', str(ROOT / 'workbench/src/gates/cli.ts'), '--state', str(state), *arguments]
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60, start_new_session=True)
        record(argv, run)
        if check:
            assert run.returncode == 0, run.stdout or run.stderr
            return json.loads(run.stdout)
        return run

    def request(command, **fields):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(20)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=None,
                                                input=dict(command=command, **fields))) + '\n').encode())
            raw = b''
            while b'\n' not in raw:
                part = connection.recv(65536)
                assert part, 'daemon closed before replying'
                raw += part
        return json.loads(raw.split(b'\n')[0])

    def start_daemon():
        nonlocal running, manifest
        env['A2A_OPERATOR_CREDENTIAL'] = str(fixture / ('operator-' + uuid.uuid4().hex + '.json'))
        cli('daemon_start')
        running = True
        wait_for(lambda: request('pane_layout').get('recovering') is False, 'daemon recovery did not finish', 30)
        manifest = json.loads((state / 'hc-runtime.json').read_text(encoding='utf-8'))

    def stop_daemon():
        nonlocal running
        if running:
            cli('daemon_stop', check=False)
            wait_for(lambda: not (state / 'control.sock').exists(), 'daemon did not exit', 20)
            running = False

    def hc(*arguments, timeout=15, **extra):
        private = dict(env, HC_SESSION=manifest['session'], HC_SOCKET=manifest['socket'],
                       XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'), **extra)
        argv = [str(binary), '--json', *arguments]
        try:
            run = subprocess.run(argv, env=private, capture_output=True, text=True, timeout=timeout, start_new_session=True)
            record(argv, run)
            return dict(exit=run.returncode, stdout=run.stdout[-1500:], stderr=run.stderr[-1500:])
        except subprocess.TimeoutExpired:
            report['commands'].append(dict(argv=[str(a) for a in argv], timeout=timeout))
            return dict(timeout=timeout)

    def core_alive():
        with socket.socket(socket.AF_UNIX) as probe:
            probe.settimeout(.5)
            try:
                probe.connect(manifest['socket'])
                return True
            except OSError:
                return False

    def processes():
        rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,command='], text=True).splitlines()
        out = []
        for row in rows:
            parts = row.split(None, 3)
            if len(parts) == 4 and parts[3].startswith(str(binary)):
                out.append(dict(pid=int(parts[0]), ppid=int(parts[1]), pgid=int(parts[2]), command=parts[3]))
        return out

    def status():
        return json.loads(hc('server', 'status')['stdout'])

    def new_core_identity():
        """Environment of the live core, read from a terminal it launches, plus where it keeps state."""
        nonlocal probes
        probes += 1
        target = fixture / f'probe-{probes}.json'
        launched = hc('run', '--bg', '--no-parent', '--no-notify', '/usr/bin/python3', '-c', ENV_PROGRAM, str(target))
        wait_for(lambda: target.exists(), 'probe terminal did not write its environment')
        core_files = {name: (base / 'core.json').stat().st_mtime for name, base in (
            ('private', state / 'hc/state/herdr-core' / manifest['session']),
            ('fixture_home_default', home / '.local/state/herdr-core' / manifest['session'])) if (base / 'core.json').exists()}
        return dict(probe_env=json.loads(target.read_text()), probe_exit=launched.get('exit'), core_json_mtime=core_files)

    def kill_and_watch(seconds=12.0):
        live = status()
        os.kill(live['pid'], signal.SIGKILL)
        killed = time.monotonic()
        wait_for(lambda: not core_alive(), 'core still accepting after SIGKILL', 5, .01)
        back = None
        while time.monotonic() - killed < seconds:
            if core_alive():
                back = round(time.monotonic() - killed, 2)
                break
            time.sleep(.05)
        return dict(killed_pid=live['pid'], holders_before=[h['pid'] for h in live['holders']], reappeared_after_s=back,
                    herdr_processes=processes())

    try:
        start_daemon()
        launch = cli('shell_start', '--project', 'alpha', '--cwd', str(home))['launch']
        launches.append(launch)
        shell_pid = request('pane_status', thread=launch['thread'])['shell_pid']
        report['phases']['initial'] = dict(status=status(), herdr_processes=processes(), shell_pid=shell_pid,
                                           identity=new_core_identity())

        # Phase holder: daemon stopped, holder and shell alive.
        stop_daemon()
        holder_phase = kill_and_watch()
        if holder_phase['reappeared_after_s'] is not None:
            holder_phase['status'] = status()
            holder_phase['identity'] = new_core_identity()
        report['phases']['daemon_stopped'] = holder_phase

        # Does the daemon accept the core the holder brought back?
        env['A2A_OPERATOR_CREDENTIAL'] = str(fixture / ('operator-' + uuid.uuid4().hex + '.json'))
        run = cli('daemon_start', check=False)
        accepted = dict(exit=run.returncode, stdout=run.stdout[-1500:])
        daemon_log = state / 'daemon.stderr.log'
        if run.returncode != 0 and daemon_log.exists():
            accepted['daemon_stderr_tail'] = [line for line in daemon_log.read_text(encoding='utf-8').splitlines()
                                              if 'TOKEN' not in line.upper()][-6:]
        if run.returncode == 0:
            running = True
            stop_daemon()
        report['phases']['daemon_start_on_holder_core'] = accepted

        # Kill the holder's own child core: does the holder bring it back faster than after its parent died?
        live = status()
        os.kill(live['pid'], signal.SIGKILL)
        killed = time.monotonic()
        wait_for(lambda: not core_alive(), 'core still accepting after SIGKILL', 5, .01)
        back = wait_for(lambda: core_alive() and round(time.monotonic() - killed, 2), 'holder did not respawn its child core', 12, .02)
        report['phases']['holder_child_core_killed'] = dict(killed_pid=live['pid'], reappeared_after_s=back,
                                                            herdr_processes=processes())

        # Clear core, holder and shell, then let the daemon start a fresh core and a fresh pane.
        live = status()
        for pid in [h['pid'] for h in live['holders']] + [live['pid']]:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        wait_for(lambda: not core_alive() and not processes(), 'core or holder still alive', 10)
        start_daemon()
        launch = cli('shell_start', '--project', 'alpha', '--cwd', str(home))['launch']
        launches.append(launch)
        shell_pid = request('pane_status', thread=launch['thread'])['shell_pid']
        report['phases']['fresh_daemon'] = dict(status=status(), herdr_processes=processes(), shell_pid=shell_pid)

        # Phase race: daemon running, kill the core, the pane's client calls hc immediately.
        race = dict(panes=request('pane_status', thread=launch['thread']))
        if core_alive():
            live = status()
            trigger = marks / f"trigger-{launch['id']}"
            os.kill(live['pid'], signal.SIGKILL)
            trigger.write_text('go')
            race['killed_pid'] = live['pid']
            wait_for(lambda: (marks / f"agent-{launch['id']}.exit").exists(), 'agent call did not finish', 30)
            race['agent_call'] = dict(exit=(marks / f"agent-{launch['id']}.exit").read_text().strip(),
                                      stderr=(marks / f"agent-{launch['id']}.err").read_text()[-1500:],
                                      stdout_bytes=len((marks / f"agent-{launch['id']}.out").read_text()))
            wait_for(core_alive, 'no core after the race', 15)
            race['status'] = status()
            race['identity'] = new_core_identity()
            race['herdr_processes'] = processes()
            time.sleep(5)
            race['after_5s'] = dict(herdr_processes=processes(), core_alive=core_alive(),
                                    shell_alive=subprocess.run(['/bin/ps', '-p', str(shell_pid)], capture_output=True).returncode == 0,
                                    terminals=json.loads(hc('ls', '--all')['stdout'] or '{}').get('terminals'),
                                    pane=request('pane_status', thread=launch['thread']))
        report['phases']['race'] = race

        # Phase calls: no daemon, no holder, no shell. Which hc commands start a core?
        stop_daemon()
        live = status()
        for pid in [h['pid'] for h in live['holders']] + [live['pid']]:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        wait_for(lambda: not core_alive() and not processes(), 'core or holder still alive', 10)
        time.sleep(3)
        calls = dict(idle_without_holder=dict(reappeared=core_alive()))
        for name, arguments in {'server status': ['server', 'status'], 'ls': ['ls'], 'get': ['get', 't1'],
                                'read': ['read', 't1'], 'send': ['send', 't1', 'true'], 'wait': ['wait', 't1', '--timeout', '1'],
                                'exec': ['exec', '/usr/bin/true'], 'events': ['events'], 'server start': ['server', 'start']}.items():
            assert not core_alive()
            result = hc(*arguments, timeout=4 if name == 'events' else 15)
            started = core_alive()
            calls[name] = dict(result=result, started_core=started)
            if started:
                live = status()
                for pid in [h['pid'] for h in live['holders']] + [live['pid']]:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                wait_for(lambda: not core_alive() and not processes(), 'core still alive after kill', 10)
        report['phases']['calls_without_holder'] = calls
        report['status'] = 'OBSERVED'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        try:
            stop_daemon()
        except Exception as error:
            report['stop_error'] = str(error)
        leftovers = processes()
        for p in leftovers:
            try:
                os.kill(p['pid'], signal.SIGKILL)
            except ProcessLookupError:
                pass
        time.sleep(1)
        report['cleanup'] = dict(killed=leftovers, remaining=processes())
        tokens = set()
        for base in (state / 'hc/state/herdr-core', home / '.local/state/herdr-core'):
            for path in base.glob('*/terminals.json'):
                for terminal in json.loads(path.read_text(encoding='utf-8')).get('terminals', {}).values():
                    if terminal.get('restart_env', {}).get('A2A_TERMINAL_TOKEN'):
                        tokens.add(terminal['restart_env']['A2A_TERMINAL_TOKEN'])
        after = user_core_snapshot()
        report['user_core'] = dict(unchanged=before == after, before=before, after=after)
        if before != after:
            report['status'] = 'NO_GO'
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        report['evidence_boundary'] = assert_public_evidence(args.output, tokens)
        if report['status'] == 'OBSERVED' and not report['cleanup']['remaining']:
            shutil.rmtree(fixture)
    print(json.dumps(dict(status=report['status'], error=report.get('error'), output=str(args.output)), ensure_ascii=False))
    return 0 if report['status'] == 'OBSERVED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
