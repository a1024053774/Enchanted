"""Offline observer checks only. These inputs are not gate acceptance evidence.

Expectations: needs-fix may complete the lifecycle; missing mutation data must
not become a guessed count; changed shared refs must fail the readback.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for name in ('needs_fix_completed', 'mutation_data_unavailable', 'shared_refs_changed'):
        run = out / name
        run.mkdir()
        candidate = 'a' * 40
        workspace = str(run / 'removed-review')
        worker = str(run / 'worker')
        section = {'mutation_checks': [{'id': 'M1'}, {'id': 'M2'}]}
        if name == 'mutation_data_unavailable':
            section = '变异 M1/M2：仅有文字，无结构化条目'
        result = {'verdict': '需修复', 'report': {'完成条件与变异检查': section}}
        review = {'review_id': 'readback-fixture', 'candidate_commit': candidate, 'workspace': workspace,
                  'candidate_workspace': str(run / 'removed-copy'), 'attempt': {'workspace': worker}, 'result': result}
        initial = {'review': review}
        final = {'candidate_commit': candidate, 'review': review, 'state': 'submitted'}
        events = [{'seq': 1, 'type': 'review_result', 'details': {'review': review}}]
        for path in (workspace, worker):
            for command, value in ((['rev-parse', 'HEAD'], candidate),
                                   (['status', '--porcelain=v1', '--untracked-files=all'], '')):
                events.append({'seq': len(events) + 1, 'type': 'command_result',
                               'details': {'argv': ['git', '-C', path, *command], 'returncode': 0, 'stdout': value}})
        for kind in ('review_candidate_copy_removed', 'review_worktree_removed', 'review_reclaimed'):
            events.append({'seq': len(events) + 1, 'type': kind, 'details': {'review_id': 'readback-fixture'}})
        for filename, value in [('verify.json', {'task': initial}), ('status-final.json', {'task': final}),
                                ('events-final.json', {'events': events})]:
            (run / filename).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        for prefix in ('worker', 'shared'):
            for when in ('before', 'after'):
                (run / f'{prefix}-sentinel-{when}.txt').write_text('unchanged\n', encoding='utf-8')
        for suffix in ('before', 'committed'):
            (run / f'review-sentinel-{suffix}.txt').write_text('tracked\n', encoding='utf-8')
        (run / 'shared-refs-before.txt').write_text('refs/heads/main=baseline\n', encoding='utf-8')
        (run / 'shared-refs-after.txt').write_text('changed\n' if name == 'shared_refs_changed'
                                                 else 'refs/heads/main=baseline\n', encoding='utf-8')
        argv = [sys.executable, '-B', str(Path(__file__).with_name('read_t082_real_result.py')), '--run', str(run), '--round', '2']
        completed = subprocess.run(argv, capture_output=True, text=True)
        value = json.loads((run / 'real-readback.json').read_text(encoding='utf-8'))
        expected = 0 if name == 'needs_fix_completed' else 1
        passed = completed.returncode == expected
        if name == 'mutation_data_unavailable':
            passed = passed and value['mutation_count'] is None
        if name == 'shared_refs_changed':
            passed = passed and value['checks']['shared_refs_unchanged'] is False
        results.append({'case': name, 'argv': argv, 'expected_exit': expected, 'exit': completed.returncode,
                        'passed': passed, 'stdout': completed.stdout, 'stderr': completed.stderr})
    status = 'PASS' if all(row['passed'] for row in results) else 'INCOMPLETE'
    (out / 'run.json').write_text(json.dumps({'status': status, 'scope': 'readback observer only; synthetic receipts',
          'real_codex_turns': 0, 'cases': results}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': status, 'cases': len(results), 'real_codex_turns': 0}))
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
