"""Run one real Herdr/Codex task; do not infer success from terminal state."""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent-pane', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    runtime = root / '.runtime' / output.name
    runtime.mkdir(parents=True, exist_ok=False)
    repo = runtime / 'fixture'
    repo.mkdir()
    task = 'pagination-live'
    state = runtime / 'state'
    events = output / 'commands.jsonl'

    def command(argv, cwd=None, expected=0):
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        p = subprocess.run([str(v) for v in argv], cwd=cwd or root,
                           capture_output=True, text=True, timeout=180)
        row = {'started_at': started, 'finished_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'argv': [str(v) for v in argv], 'cwd': str(cwd or root), 'exit': p.returncode,
               'stdout': p.stdout, 'stderr': p.stderr}
        with events.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        if expected is not None and p.returncode != expected:
            raise AssertionError('Unexpected exit {} for {}: {}'.format(p.returncode, argv, p.stderr or p.stdout))
        return p

    def git(*argv):
        return command(['git', '-C', repo, *argv]).stdout.strip()

    def coop(*argv, expected=0):
        p = command([sys.executable, '-B', root / 'coop.py', '--state', state, *argv], expected=expected)
        value = json.loads(p.stdout)
        if expected == 0:
            assert value['ok'] is True, value
        return value

    result = {'status': 'INCOMPLETE', 'task': task, 'runtime': str(runtime),
              'reproduce': 'python3 -B acceptance/live_herdr.py --parent-pane LIVE_PANE --output NEW_OUTPUT_DIRECTORY',
              'claim_scope': 'one actual Herdr/Codex task, independent pagination acceptance, local Git ref'}
    try:
        command(['herdr', 'status', '--json'])
        command(['codex', '--version'])
        git('init', '-b', 'main')
        git('config', 'user.name', 'A2A Isolated Fixture')
        git('config', 'user.email', 'fixture@localhost')
        for name in ('pager.py', 'CONTRACT.md'):
            shutil.copyfile(root / 'fixtures' / 'pagination' / name, repo / name)
        git('add', 'pager.py', 'CONTRACT.md')
        git('commit', '-m', 'test: incomplete pagination task')
        base = git('rev-parse', 'HEAD')
        result['base'] = base
        coop('create', '--task', task, '--repo', str(repo), '--base', base,
             '--oracle', str(root / 'acceptance/pagination_oracle.py'),
             '--instructions', str(repo / 'CONTRACT.md'))
        dispatch = coop('dispatch', '--task', task, '--parent-pane', args.parent_pane,
                        '--name', 'a2a-live-pager')
        (output / 'dispatch.json').write_text(json.dumps(dispatch, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        deadline = time.monotonic() + args.timeout
        observed = None
        last_observe = 0.0
        while time.monotonic() < deadline:
            task_state = coop('status', '--task', task)['task']
            if task_state['state'] != observed:
                observed = task_state['state']
                print('task state:', observed, flush=True)
            if observed == 'submitted':
                break
            if observed in ('failed', 'cancelled', 'revoked', 'unknown', 'dispatch_unknown'):
                raise AssertionError('Task cannot proceed: ' + repr(task_state))
            if time.monotonic() - last_observe >= 30:
                coop('observe', '--task', task, expected=None)
                last_observe = time.monotonic()
            time.sleep(5)
        else:
            raise AssertionError('No explicit submit before bounded task deadline; lifecycle state is not acceptance')
        before = git('rev-parse', 'refs/a2a/integration')
        assert before == base, 'Dispatch or submit changed integration ref without verification'
        rejected = coop('integrate', '--task', task, expected=1)
        assert rejected['ok'] is False
        assert git('rev-parse', 'refs/a2a/integration') == base
        verified = coop('verify', '--task', task)
        (output / 'verification.json').write_text(json.dumps(verified, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        assert coop('status', '--task', task)['task']['state'] == 'verified'
        coop('integrate', '--task', task)
        accepted = git('rev-parse', 'refs/a2a/integration')
        assert accepted != base
        assert coop('status', '--task', task)['task']['state'] == 'accepted'
        coop('integrate', '--task', task)
        assert git('rev-parse', 'refs/a2a/integration') == accepted
        independent = runtime / 'accepted-readback'
        git('worktree', 'add', '--detach', str(independent), accepted)
        oracle = command([sys.executable, '-I', '-B', root / 'acceptance/pagination_oracle.py', independent])
        assert json.loads(oracle.stdout)['status'] == 'PASS'
        coop('reclaim', '--task', task)
        event_data = coop('events', '--task', task)
        (output / 'events.json').write_text(json.dumps(event_data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result.update(status='PASS', accepted_commit=accepted,
                      checks=['explicit_submit', 'unverified_integrate_rejected', 'oracle_pass',
                              'accepted_ref_readback', 'idempotent_integration', 'pane_reclaimed'])
    except (AssertionError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        result['error'] = str(exc)
        # Preserve the process, candidate and state for controller inspection; do not blindly close a pane.
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
