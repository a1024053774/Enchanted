#!/usr/bin/env python3
"""T-220 probe: after the private hc core dies, which hc calls start a new one, can a client inside an
Enchanted terminal win that race, and whose environment do terminals on the new core inherit.

Real entry points only: the gates CLI starts the daemon and shell panes; the pinned hc binary the daemon
installed is the only hc used. Every path lives in a disposable /private/tmp fixture whose HOME is the
fixture's own, so a core started with "the user's" XDG defaults writes under the fixture, never under the
real ~/.local/state. No vendor CLI or model is started.

Usage: python3 t220_core_restart_probe.py --output DIR   (DIR must not exist)
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
/usr/bin/python3 - "$T220_DIR/env-$A2A_TERMINAL.json" <<'PY'
import json, os, sys
keys = ['T220_MARKER', 'T220_STARTER', 'HC_SESSION', 'HC_SOCKET', 'HC_TERMINAL_ID', 'XDG_STATE_HOME', 'XDG_CONFIG_HOME',
        'A2A_TERMINAL', 'A2A_PROJECT', 'HOME']
data = {k: os.environ.get(k) for k in keys}
data['A2A_TERMINAL_TOKEN_present'] = bool(os.environ.get('A2A_TERMINAL_TOKEN'))
open(sys.argv[1], 'w').write(json.dumps(data))
PY
( while [[ ! -e $T220_DIR/trigger-$A2A_TERMINAL ]]; do sleep 0.2; done
  T220_STARTER=terminal-agent "$T220_HC" --json ls > "$T220_DIR/agent-$A2A_TERMINAL.out" 2> "$T220_DIR/agent-$A2A_TERMINAL.err"
  echo $? > "$T220_DIR/agent-$A2A_TERMINAL.exit" ) &!
'''

ENV_PROGRAM = r'''
import json, os, sys
keys = ['T220_MARKER', 'T220_STARTER', 'HC_SESSION', 'XDG_STATE_HOME', 'XDG_CONFIG_HOME', 'A2A_TERMINAL', 'HOME']
data = {k: os.environ.get(k) for k in keys}
data['A2A_TERMINAL_TOKEN'] = os.environ.get('A2A_TERMINAL_TOKEN')
open(sys.argv[1], 'w').write(json.dumps(data))
'''


def wait_for(probe, message, seconds=15.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = probe()
        if value:
            return value
        time.sleep(.1)
    raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t220-', dir='/private/tmp'))
    state, home, marks = fixture / 'state', fixture / 'home', fixture / 'marks'
    for d in (state, home, marks):
        d.mkdir()
    (home / '.zshrc').write_text(ZSHRC, encoding='utf-8')
    binary = state / 'hc/bin/herdr-core'
    env = {key: os.environ[key] for key in ('PATH', 'LANG') if key in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TMPDIR='/private/tmp', T220_MARKER='initial-daemon',
               T220_DIR=str(marks), T220_HC=str(binary))
    report = dict(status='INCOMPLETE', command=[sys.executable, *sys.argv], fixture=str(fixture), commands=[],
                  real_model_calls=0, phases={})
    before = user_core_snapshot()
    running, manifest, launches, owned_pids = False, None, [], set()

    def record(argv, run):
        report['commands'].append(dict(argv=[str(a) for a in argv], exit=run.returncode,
                                       stdout=run.stdout[-4000:], stderr=run.stderr[-4000:]))

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
        run = cli('daemon_start', check=False)
        if run.returncode != 0:
            return dict(ok=False, exit=run.returncode, stdout=run.stdout[-2000:], stderr=run.stderr[-2000:])
        running = True
        try:
            wait_for(lambda: request('pane_layout').get('recovering') is False, 'daemon recovery did not finish', 30)
        except Exception as error:
            return dict(ok=False, recovery_error=str(error))
        manifest = json.loads((state / 'hc-runtime.json').read_text(encoding='utf-8'))
        return dict(ok=True, started=json.loads(run.stdout))

    def stop_daemon():
        nonlocal running
        if running:
            cli('daemon_stop', check=False)
            wait_for(lambda: not (state / 'control.sock').exists(), 'daemon did not exit', 20)
            running = False

    def private_env(**extra):
        return dict(env, HC_SESSION=manifest['session'], HC_SOCKET=manifest['socket'],
                    XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'), **extra)

    def hc(*arguments, timeout=15, **extra):
        argv = [str(binary), '--json', *arguments]
        try:
            run = subprocess.run(argv, env=private_env(**extra), capture_output=True, text=True, timeout=timeout,
                                 start_new_session=True)
            record(argv, run)
            return dict(exit=run.returncode, stdout=run.stdout[-2000:], stderr=run.stderr[-2000:])
        except subprocess.TimeoutExpired as error:
            report['commands'].append(dict(argv=[str(a) for a in argv], timeout=timeout))
            return dict(timeout=timeout, stdout=(error.stdout or b'')[-2000:].decode('utf-8', 'replace') if isinstance(error.stdout, bytes) else (error.stdout or '')[-2000:])

    def core_alive():
        # A raw connect never starts a core, unlike any hc client call.
        with socket.socket(socket.AF_UNIX) as probe:
            probe.settimeout(1)
            try:
                probe.connect(manifest['socket'])
                return True
            except OSError:
                return False

    def ps(pid):
        run = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'pid=,ppid=,pgid=,stat=,comm='],
                             capture_output=True, text=True, timeout=5)
        parts = run.stdout.split(None, 4)
        return dict(zip(['pid', 'ppid', 'pgid', 'stat', 'comm'], parts)) if parts else None

    def core_status():
        status = json.loads(hc('server', 'status')['stdout'])
        owned_pids.add(status['pid'])
        for holder in status['holders']:
            owned_pids.add(holder['pid'])
        return status

    def kill_core():
        status = core_status()
        os.kill(status['pid'], signal.SIGKILL)
        wait_for(lambda: not core_alive(), 'core still accepting connections after SIGKILL')
        return status['pid']

    def fixture_processes():
        rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,comm='], text=True).splitlines()
        return [int(r.split(None, 1)[0]) for r in rows
                if len(r.split(None, 1)) == 2 and r.split(None, 1)[1].startswith(str(fixture))]

    try:
        report['phases']['start'] = start_daemon()
        assert report['phases']['start']['ok'], report['phases']['start']
        for project in ('alpha', 'alpha'):
            launch = cli('shell_start', '--project', project, '--cwd', str(home))['launch']
            launches.append(launch)
            owned_pids.add(request('pane_status', thread=launch['thread'])['shell_pid'])
        agent, plain = launches
        wait_for(lambda: all((marks / f"env-{l['id']}.json").exists() for l in launches), 'pane env files missing')
        created = [e for e in request('orchestration_events')['events'] if e['type'] == 'shell_created']
        addresses = {l['id']: next(e['data']['hc_terminal'] for e in created if e.get('launch') == l['id']) for l in launches}
        registry = state / 'hc/state/herdr-core' / manifest['session'] / 'terminals.json'
        agent_token = next(t['restart_env']['A2A_TERMINAL_TOKEN']
                           for t in json.loads(registry.read_text(encoding='utf-8'))['terminals'].values()
                           if t['labels'].get('enchanted_launch') == agent['id'])
        report['phases']['initial'] = dict(
            core=ps(core_status()['pid']), addresses=addresses,
            pane_env={l['id']: json.loads((marks / f"env-{l['id']}.json").read_text()) for l in launches},
            agent_shell=ps(request('pane_status', thread=agent['thread'])['shell_pid']))

        # Phase 1: does the running daemon restart the core by itself, and which hc calls start one?
        first = kill_core()
        time.sleep(5)
        daemon_restarted = core_alive()
        lost = {l['id']: request('pane_status', thread=l['thread']).get('failed') for l in launches}
        if daemon_restarted:
            kill_core()
        calls = {
            'server status': ['server', 'status'],
            'ls': ['ls'],
            'get': ['get', addresses[plain['id']]],
            'read': ['read', addresses[plain['id']]],
            'send': ['send', addresses[plain['id']], 'true'],
            'exec': ['exec', '/usr/bin/true'],
            'events': ['events'],
            'server start': ['server', 'start'],
        }
        outcomes = {}
        for name, arguments in calls.items():
            assert not core_alive()
            result = hc(*arguments, timeout=4 if name == 'events' else 15, T220_STARTER='harness-' + name.replace(' ', '-'))
            started = core_alive()
            outcomes[name] = dict(result=result, started_core=started)
            if started:
                outcomes[name]['core'] = ps(kill_core())
        report['phases']['auto_start'] = dict(killed_pid=first, daemon_restarted_within_5s=daemon_restarted,
                                              panes_after_loss=lost, calls=outcomes)

        # Phase 2: a client inside the agent pane calls hc first.
        assert not core_alive()
        (marks / f"trigger-{agent['id']}").write_text('go')
        wait_for(lambda: (marks / f"agent-{agent['id']}.exit").exists(), 'agent hc call did not finish', 30)
        agent_call = dict(exit=(marks / f"agent-{agent['id']}.exit").read_text().strip(),
                          stdout=(marks / f"agent-{agent['id']}.out").read_text()[-3000:],
                          stderr=(marks / f"agent-{agent['id']}.err").read_text()[-3000:])
        started = core_alive()
        phase2 = dict(agent_call=agent_call, started_core=started)
        if started:
            status = core_status()
            phase2['core'] = ps(status['pid'])
            phase2['agent_shell'] = ps(request('pane_status', thread=agent['thread'])['shell_pid']) if running else None
            probe_file = fixture / 'probe-env.json'
            phase2['probe_run'] = hc('run', '--bg', '--no-parent', '--no-notify', '/usr/bin/python3', '-c', ENV_PROGRAM, str(probe_file))
            wait_for(lambda: probe_file.exists(), 'probe terminal did not write its environment')
            probe = json.loads(probe_file.read_text())
            token = probe.pop('A2A_TERMINAL_TOKEN')
            phase2['probe_env'] = dict(probe, A2A_TERMINAL_TOKEN_present=bool(token),
                                       A2A_TERMINAL_TOKEN_is_agent_pane_token=token == agent_token)
            user_state = home / '.local/state/herdr-core'
            phase2['fixture_home_state'] = sorted(str(p.relative_to(home)) for p in user_state.rglob('*')) if user_state.exists() else []
            phase2['private_state'] = sorted(str(p.relative_to(state)) for p in (state / 'hc/state/herdr-core').rglob('*'))
            listing = json.loads(hc('ls', '--all')['stdout'] or '{}')
            phase2['terminals_known_to_new_core'] = [dict(address=t.get('address'), state=t.get('state'),
                                                          labels=t.get('labels')) for t in listing.get('terminals', [])]
        report['phases']['agent_first'] = phase2

        # Phase 3: what the daemon does with a core somebody else started.
        phase3 = dict()
        run = cli('shell_start', '--project', 'alpha', '--cwd', str(home), check=False)
        phase3['shell_start_on_running_daemon'] = dict(exit=run.returncode, stdout=run.stdout[-1500:], stderr=run.stderr[-1500:])
        if run.returncode == 0:
            launches.append(json.loads(run.stdout)['launch'])
        stop_daemon()
        env['T220_MARKER'] = 'restarted-daemon'
        phase3['restart'] = start_daemon()
        if phase3['restart'].get('ok'):
            phase3['panes_after_restart'] = {l['id']: request('pane_status', thread=l['thread']) for l in launches}
            events = request('orchestration_events')['events']
            phase3['events'] = [dict(type=e['type'], launch=e.get('launch'), data=e.get('data'))
                                for e in events if e['type'].startswith(('hc_', 'shell_'))][-30:]
            run = cli('shell_start', '--project', 'alpha', '--cwd', str(home), check=False)
            phase3['shell_start_after_restart'] = dict(exit=run.returncode, stdout=run.stdout[-1500:], stderr=run.stderr[-1500:])
            if run.returncode == 0:
                fresh = json.loads(run.stdout)['launch']
                launches.append(fresh)
                wait_for(lambda: (marks / f"env-{fresh['id']}.json").exists(), 'new pane env file missing')
                phase3['new_pane_env'] = json.loads((marks / f"env-{fresh['id']}.json").read_text())
        report['phases']['daemon_after_agent_core'] = phase3
        report['status'] = 'OBSERVED'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        cleanup_errors = []
        if running:
            for launch in launches:
                run = cli('shell_close', '--launch', launch['id'], check=False)
                if run.returncode != 0:
                    cleanup_errors.append(f"shell_close {launch['id']}: {run.stdout[-300:]} {run.stderr[-300:]}")
        try:
            stop_daemon()
        except Exception as error:
            cleanup_errors.append(str(error))
        if manifest and binary.exists():
            if core_alive():
                try:
                    core_status()
                except Exception as error:
                    cleanup_errors.append('status before stop: ' + str(error))
                report['core_stop'] = hc('server', 'stop', timeout=20)
        leftovers = sorted(set(fixture_processes()) | {p for p in owned_pids if ps(p)})
        for pid in leftovers:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        report['cleanup'] = dict(killed_leftovers=leftovers, errors=cleanup_errors,
                                 remaining=[p for p in fixture_processes()])
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
        if report['status'] == 'OBSERVED' and not cleanup_errors and not report['cleanup']['remaining']:
            shutil.rmtree(fixture)
    print(json.dumps(dict(status=report['status'], error=report.get('error'), output=str(args.output)), ensure_ascii=False))
    return 0 if report['status'] == 'OBSERVED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
