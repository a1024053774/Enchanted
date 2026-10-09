"""Reproduce via the operator gate script against an owned, isolated real HTTP route."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('label')
parser.add_argument('--delay', type=int, default=390)
parser.add_argument('--wait', type=int, default=450)
parser.add_argument('--mode', choices=['complete', 'deadline', 'paused'], default='complete')
parser.add_argument('--idle', type=int)
args = parser.parse_args()
out = Path(__file__).resolve().parent / args.label
out.mkdir()
fork = Path('/Users/luckye/Documents/Code/synara-t045')
volume = Path('/Volumes/WD-Elements')
assert volume.is_mount()
root = volume / 'dev-cache/synara/instances/t047' / args.label
root.mkdir(parents=True)
env = {'PATH': os.environ['PATH'], 'HOME': str(root / 'os-home'), 'SHELL': '/bin/sh',
       'CODEX_HOME': str(root / 'codex'), 'CLAUDE_CONFIG_DIR': str(root / 'claude'),
       'A2A_SYNARA_SLOT': 't047', 'A2A_WORKBENCH_DATA_DIR': str(root),
       'T047_FORK': str(fork), 'T047_ROOT': str(root), 'T047_DELAY': str(args.delay),
       'T047_MODE': args.mode, 'A2A_GATE_BEARER': secrets.token_hex(32)}
for name in ['os-home', 'codex', 'claude']:
    (root / name).mkdir()
if args.idle is not None:
    env['BUN_CONFIG_HTTP_IDLE_TIMEOUT'] = str(args.idle)
wrapper = str(fork / 'a2a/scripts/bun')
argv = [wrapper, 'run', str(Path(__file__).with_name('http-fixture.ts'))]
record = {'argv': sys.argv, 'fixture_argv': argv, 'root': str(root), 'fork': str(fork),
          'base_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip(),
          'start': time.time(), 'mode': args.mode, 'idle_override': args.idle, 'delay': args.delay, 'wait': args.wait}
(out / 'command.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
server_log = (out / 'server.log').open('x')
server = subprocess.Popen(argv, cwd=fork, env=env, stdout=server_log, stderr=subprocess.STDOUT,
                          stdin=subprocess.DEVNULL, start_new_session=True)
record['server_pid'] = server.pid
commands = []

def call(request, label, timeout):
    command = [str(fork / 'a2a/scripts/gate'), json.dumps(request)]
    started = time.monotonic()
    with (out / (label + '-stdout.json')).open('xb') as stdout, (out / (label + '-stderr.txt')).open('xb') as stderr:
        result = subprocess.run(command, cwd=fork, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
    raw = (out / (label + '-stdout.json')).read_bytes()
    try:
        value = json.loads(raw)  # Python's default strict=True rejects raw controls inside strings.
        parse_error = None
    except ValueError as error:
        value, parse_error = None, str(error)
    entry = {'argv': command, 'exit': result.returncode, 'elapsed': time.monotonic() - started,
             'strict_json': parse_error is None, 'parse_error': parse_error}
    commands.append(entry)
    return result.returncode, value

try:
    for _ in range(300):
        if (root / 'ready.json').exists():
            break
        if server.poll() is not None:
            raise RuntimeError('Fixture failed to start; inspect server.log')
        time.sleep(.1)
    ready = json.loads((root / 'ready.json').read_text(encoding='utf-8'))
    record['server_timeouts'] = ready['serverTimeouts']
    # Publish only this test's process identity. No production endpoint is read.
    ps_env = {**os.environ, 'LANG': 'C', 'LC_TIME': 'C', 'LC_CTYPE': 'C'}
    for key in list(ps_env):
        if key.startswith('LC_') and key not in ['LC_TIME', 'LC_CTYPE']:
            del ps_env[key]
    identity = subprocess.check_output(['ps', '-p', str(server.pid), '-o', 'lstart=', '-o', 'command='],
                                       env=ps_env, text=True).strip()
    (root / 'workbench-process.json').write_text(json.dumps({'pid': server.pid, 'identity': identity}), encoding='utf-8')
    (root / 'a2a-gates').mkdir()
    endpoint = root / 'a2a-gates/endpoint.json'
    with endpoint.open('x') as stream:
        json.dump({'origin': ready['origin'], 'desktopPid': server.pid, 'home': str(root), 'token': env['A2A_GATE_BEARER']}, stream)
    endpoint.chmod(0o600)
    create = {'command': 'create', 'task': 'http-proof', 'project': 'http-proof-project',
              **{key: ready[key] for key in ['repo', 'base', 'oracle', 'instructions']}}
    assert call(create, 'create', 30)[0] == 0
    run_exit, receipt = call({'command': 'run', 'task': 'http-proof', 'runtimeMode': 'approval-required',
                              'wait_seconds': args.wait}, 'run', args.wait + 150)
    # A failed client must not be mistaken for a cancelled server run.
    limit = time.monotonic() + max(30, args.delay + 15 - commands[-1]['elapsed'])
    while True:
        events_exit, events = call({'command': 'events', 'task': 'http-proof'}, 'events-' + str(len(commands)), 30)
        assert events_exit == 0 and events is not None
        finished = [event for event in events['events'] if event['type'] == 'run_finished']
        if finished:
            break
        if time.monotonic() >= limit:
            raise RuntimeError('No final server run record')
        time.sleep(5)
    (out / 'events-final.json').write_text(json.dumps(events, ensure_ascii=False) + '\n', encoding='utf-8')
    status_exit, status = call({'command': 'status', 'task': 'http-proof'}, 'status', 30)
    assert status_exit == 0
    record.update(run_exit=run_exit, client_receipt=receipt, server_run=finished[-1]['details'])
    if args.mode == 'complete':
        ref = subprocess.check_output(['git', '-C', ready['repo'], 'rev-parse', 'refs/a2a/integration'], text=True).strip()
        delivery = subprocess.check_output(['git', '-C', ready['repo'], 'show', ref + ':delivery.txt'], text=True)
        assert delivery == 'T047 independently specified delivery\n'
        assert status['task']['state'] == 'accepted'
        assert finished[-1]['details']['outcome'] == 'completed'
        assert finished[-1]['details']['reclaimed'] is True
        result_text = next(event for event in events['events'] if event['type'] == 'verification_result')['details']['result']['stdout']
        assert result_text == 'control: \x00\x01\x1b\t\r\n'
        record['integration_ref'] = ref
        assert run_exit == 0 and receipt['ok'] is True, 'Client must receive the final successful run receipt'
        assert receipt['run']['run_id'] == finished[-1]['details']['run_id']
        assert receipt['run']['attempt_id'] == status['task']['current_attempt']['attempt_id']
    else:
        error = 'run_deadline' if args.mode == 'deadline' else 'run_blocked'
        assert run_exit == 1 and receipt['ok'] is False and receipt['error'] == error
        assert finished[-1]['details']['outcome'] == ('deadline' if args.mode == 'deadline' else 'paused')
        assert status['task']['state'] != 'accepted'
    record['status'] = 'PASS'
except BaseException as error:
    record.update(status='INCOMPLETE', failure=str(error))
    raise
finally:
    record['end'] = time.time()
    record['commands'] = commands
    server.terminate()
    server.wait(timeout=15)
    server_log.close()
    # Credential created by this fixture; never retain it in evidence or Git.
    (root / 'a2a-gates/endpoint.json').unlink(missing_ok=True)
    record['server_exit'] = server.returncode
    (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: record.get(key) for key in ['status', 'failure', 'run_exit', 'start', 'end']}, ensure_ascii=False))
