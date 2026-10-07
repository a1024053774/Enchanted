"""Reconcile a dead owned runtime through the original attempt's reclaim CLI."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    prior = Path(__file__).resolve().parent / 'final-runtime-01'
    context = json.loads((prior / 'context.json').read_text(encoding='utf-8'))
    task = json.loads((prior / 'status-paused.json').read_text(encoding='utf-8'))['task']
    attempt = task['current_attempt']
    dispatch = attempt['dispatch']
    env = {k: v for k, v in os.environ.items() if not k.startswith(('HERDR_', 'MUSTER_')) and k not in ('CODEX_HOME', 'CODEX_THREAD_ID')}
    env.update(context['environment'])
    events = (out / 'commands.jsonl').open('a', encoding='utf-8')

    def command(argv, expected=0):
        argv = [str(v) for v in argv]
        p = subprocess.run(argv, env=env, cwd=ROOT, text=True, capture_output=True, timeout=30)
        events.write(json.dumps(dict(argv=argv, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)) + '\n')
        events.flush()
        if expected is not None:
            assert p.returncode == expected, p.stdout or p.stderr
        return p

    def muster(*args):
        return command([context['binary'], '--session', context['session'], *args])

    old_pids = [context['server_pid'], dispatch['shell_pid'], *dispatch.get('agent_pids', [])]
    assert command(['ps', '-p', ','.join(str(v) for v in old_pids), '-o', 'pid=,lstart=,command='], expected=None).returncode == 1, 'Original process still present'
    assert json.loads(muster('status', '--json').stdout)['server']['running'] is False
    directory = Path(context['runtime']) / 'c/muster/sessions' / context['session']
    saved = directory / 'session.json'
    retained = directory / 'session-before-reclaim.json'
    assert saved.is_file() and not retained.exists()
    # All original processes are gone. Retain layout instead of respawning
    # replacement terminals under the old IDs during absence reconciliation.
    saved.rename(retained)
    events.write(json.dumps(dict(action='retain_dead_runtime_layout', source=str(saved), destination=str(retained),
                                reason='Do not respawn replacement occupants under the old pane IDs; original PIDs are absent')) + '\n')
    events.flush()
    argv = [context['binary'], '--session', context['session'], 'server']
    with (out / 'server-stdio.txt').open('x', encoding='utf-8') as stdio:
        server = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=stdio, stderr=stdio, start_new_session=True)
    deadline = time.monotonic() + 20
    while True:
        assert server.poll() is None and time.monotonic() < deadline
        if json.loads(muster('status', '--json').stdout)['server']['running']:
            break
        time.sleep(.2)
    inventory = json.loads(muster('pane', 'list').stdout)['result']['panes']
    assert inventory == [], inventory
    project = json.loads(muster('workspace', 'create', '--cwd', str(ROOT), '--label', 'T-029 previous attempt reclaim',
                                '--env', 'MUSTER_BIN=' + context['binary'], '--no-focus').stdout)['result']
    pane = project['root_pane']['pane_id']
    state = ROOT / '.runtime/final-runtime-01-live_run/state'
    cli = [sys.executable, '-B', str(ROOT / 'coop.py'), '--state', str(state), 'reclaim',
           '--task', task['task_id'], '--attempt', attempt['attempt_id']]
    reply = out / 'reclaim.json'
    shell = shlex.join(cli) + ' > ' + shlex.quote(str(reply)) + ' 2> ' + shlex.quote(str(out / 'reclaim.stderr'))
    muster('pane', 'run', pane, shell)
    deadline = time.monotonic() + 30
    while not reply.exists() or not reply.stat().st_size:
        assert time.monotonic() < deadline
        time.sleep(.2)
    result = json.loads(reply.read_text(encoding='utf-8'))
    assert result['ok'] and result['attempt']['attempt_id'] == attempt['attempt_id'], result
    assert result['attempt']['dispatch']['state'] == 'reclaimed'
    assert result['attempt']['dispatch']['absent_inventory'] and not any(
        p['pane_id'] == dispatch['pane_id'] for p in result['attempt']['dispatch']['absent_inventory'])
    assert result['task']['state'] == 'ready' and result['task']['current_attempt'] is None
    assert Path(attempt['workspace']).is_dir() and retained.exists()
    authority = json.loads(muster('pane', 'list').stdout)['result']['panes']
    assert [p['pane_id'] for p in authority] == [pane], authority
    muster('server', 'stop')
    server.wait(timeout=20)
    (out / 'result.json').write_text(json.dumps(dict(status='PASS', original_attempt=attempt['attempt_id'],
        server_argv=argv, start_new_session=True, initial_inventory=inventory, final_inventory=authority,
        retained_layout=str(retained), reclaim_argv=cli, server_exit=server.returncode), indent=2) + '\n', encoding='utf-8')
    print('PASS: original attempt reclaimed through CLI; history and worktree retained', flush=True)


if __name__ == '__main__':
    main()
