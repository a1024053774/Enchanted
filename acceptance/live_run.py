"""One real run command, followed by independent Git/oracle/pane readback."""
import argparse
import os
import datetime
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent-pane', required=True)
    parser.add_argument('--muster-bin', default=os.environ.get('MUSTER_BIN'),
                        help='Explicit absolute path to the Muster executable')
    parser.add_argument('--fixture-repo', required=True)
    parser.add_argument('--existing-state', help='Absolute state directory of a reclaimed registered task')
    parser.add_argument('--output', required=True)
    parser.add_argument('--wait-seconds', type=int, default=600)
    args = parser.parse_args()
    if not args.muster_bin or not Path(args.muster_bin).is_absolute():
        parser.error('--muster-bin or MUSTER_BIN must give an absolute executable path')
    os.environ['MUSTER_BIN'] = args.muster_bin
    root = Path(__file__).resolve().parents[1]
    repo = Path(args.fixture_repo).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    if args.existing_state and not Path(args.existing_state).is_absolute():
        parser.error('--existing-state must be absolute')
    state = Path(args.existing_state).resolve() if args.existing_state else root / '.runtime' / output.name / 'state'
    if not args.existing_state:
        state.parent.mkdir(parents=True, exist_ok=False)
    task = 'automatic-pagination'
    result = {'status': 'INCOMPLETE', 'task': task, 'state': str(state), 'repo': str(repo)}

    def command(argv, timeout=60):
        argv = [str(v) for v in argv]
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        p = subprocess.run(argv, cwd=root, text=True, capture_output=True, timeout=timeout)
        with (output / 'commands.jsonl').open('a', encoding='utf-8') as log:
            log.write(json.dumps({'started': started, 'finished': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                  'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr},
                                 ensure_ascii=False) + '\n')
        if p.returncode:
            raise AssertionError('Command failed (exit {}): {}. Raw output is in commands.jsonl'.format(p.returncode, argv))
        return p.stdout

    def cli(*argv, timeout=60):
        data = json.loads(command([sys.executable, '-B', root / 'coop.py', '--state', state, *argv], timeout))
        assert data['ok'] is True, data
        return data

    try:
        assert (repo / '.git').is_dir(), 'Use a prepared isolated fixture repository'
        assert not command(['git', '-C', repo, 'status', '--porcelain']).strip()
        for name in ('pager.py', 'CONTRACT.md'):
            assert (repo / name).read_bytes() == (root / 'fixtures/pagination' / name).read_bytes()
        base = command(['git', '-C', repo, 'rev-parse', 'HEAD']).strip()
        result['base'] = base
        result['product_commit'] = command(['git', 'rev-parse', 'HEAD']).strip()
        result['product_diff'] = command(['git', 'diff', '--', 'coop.py'])
        assert not result['product_diff'], 'Freeze product source before real acceptance'
        parent = json.loads(command([args.muster_bin, 'pane', 'get', args.parent_pane]))['result']['pane']
        workspace_id = parent['workspace_id']
        before = json.loads(command([args.muster_bin, 'pane', 'list', '--workspace', workspace_id]))
        before_ids = {p['pane_id'] for p in before['result']['panes']}
        assert args.parent_pane in before_ids
        prior_fence = None
        if args.existing_state:
            registered = cli('status', '--task', task)['task']
            assert registered['state'] == 'ready' and registered['current_attempt'] is None
            assert registered['candidate_commit'] is None
            assert Path(registered['repo']).resolve() == repo and registered['base_commit'] == base
            assert Path(registered['oracle']).read_bytes() == (root / 'acceptance/pagination_oracle.py').read_bytes()
            assert Path(registered['instructions']).read_bytes() == (repo / 'CONTRACT.md').read_bytes()
            prior_fence = registered['fence']
            prior_events = cli('events', '--task', task)['events']
            (output / 'events-before.json').write_text(json.dumps(prior_events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        else:
            cli('create', '--task', task, '--repo', repo, '--base', base,
                '--oracle', root / 'acceptance/pagination_oracle.py', '--instructions', repo / 'CONTRACT.md')
        # This is the only workflow-driving call. The test never calls verify/integrate/reclaim.
        outcome = cli('run', '--task', task, '--parent-pane', args.parent_pane,
                      '--name', 'a2a-auto-pager', '--wait-seconds', args.wait_seconds,
                      timeout=args.wait_seconds + 240)
        (output / 'run.json').write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        assert outcome['run']['run_id'] and outcome['run']['attempt_id']
        assert outcome['run']['outcome'] == 'completed'
        current = cli('status', '--task', task)['task']
        assert current['state'] == 'accepted'
        if prior_fence is not None:
            assert current['current_attempt']['fence'] > prior_fence
        accepted = command(['git', '-C', repo, 'rev-parse', 'refs/a2a/integration']).strip()
        assert accepted != base
        assert command(['git', '-C', repo, 'rev-parse', 'HEAD']).strip() == base
        checked = state.parent / ('independent-readback-' + output.name)
        command(['git', '-C', repo, 'worktree', 'add', '--detach', checked, accepted])
        oracle = json.loads(command([sys.executable, '-I', '-B', root / 'acceptance/pagination_oracle.py', checked]))
        assert oracle['status'] == 'PASS' and all(v['pass'] for v in oracle['cases'])
        owned_pane = current['current_attempt']['dispatch']['pane_id']
        assert owned_pane not in before_ids, 'Run must own a newly created pane'
        after = json.loads(command([args.muster_bin, 'pane', 'list', '--workspace', workspace_id]))
        after_ids = {p['pane_id'] for p in after['result']['panes']}
        assert before_ids <= after_ids, 'A pre-existing pane was closed'
        assert owned_pane not in after_ids, 'Owned pane still exists after claimed completion'
        events = cli('events', '--task', task)
        if prior_fence is not None:
            assert events['events'][:len(prior_events)] == prior_events, 'Earlier attempt events changed'
        (output / 'events.json').write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result.update(status='PASS', accepted_commit=accepted, run_id=outcome['run']['run_id'],
                      attempt_id=outcome['run']['attempt_id'], oracle_cases=len(oracle['cases']),
                      checks=['one_run_call', 'explicit_submission', 'authoritative_ref',
                              'independent_oracle', 'parent_preserved', 'owned_pane_reclaimed'])
    except (AssertionError, OSError, KeyError, ValueError, subprocess.TimeoutExpired) as exc:
        result['error'] = str(exc)
        # Preserve the program's state and owned pane for explicit controller diagnosis.
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
