"""Serial pending/startup/worker checks after the T090 merge; no vendor model."""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

SOURCE = Path(__file__).resolve().parents[4]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(); out = args.output.resolve()
    assert out.parent == BASE and not out.exists()
    suites = [('pending', 'run-pending-checks.py', ['--suite', 'local'], 700),
              ('startup-domain', 'run-startup-receipt-checks.py', ['--suite', 'domain'], 150),
              ('startup-entry', 'run-startup-receipt-checks.py', ['--suite', 'entry'], 420),
              ('worker', 'run-pending-checks.py', ['--suite', 'runtime'], 250)]
    source = json.loads((BASE / 'review-followup-source.json').read_bytes())
    subprocess.run(['git', 'merge-base', '--is-ancestor', source['revision'], 'HEAD'], cwd=SOURCE, check=True)
    assert not subprocess.check_output(['git', 'diff', source['revision'], '--', 'workbench', 'acceptance', 'scripts'], cwd=SOURCE)
    for _, script, _, _ in suites:
        ast.parse((BASE / script).read_text(encoding='utf-8'))
    if args.check_only:
        print(json.dumps({'status': 'PASS', 'scope': 'path/source/AST only; tests not run', 'suites': suites})); return 0
    out.mkdir(); revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()
    record = {'status': 'INCOMPLETE', 'source_revision': revision, 'models': 0, 'stages': []}
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'GIT_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    def save(): (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save()
    try:
        for name, script, extra, timeout in suites:
            argv = [sys.executable, '-B', str(BASE / script), *extra, '--output', str(out / name)]
            row = {'name': name, 'argv': argv, 'status': 'INCOMPLETE'}; record['stages'].append(row); save()
            with (out / (name + '.stdout.bin')).open('xb') as stdout, (out / (name + '.stderr.bin')).open('xb') as stderr:
                child = subprocess.Popen(argv, cwd=SOURCE, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                row['pid'] = child.pid; save(); row['exit_code'] = child.wait(timeout=timeout)
            value = json.loads((out / name / 'result.json').read_bytes())
            assert row['exit_code'] == 0 and value['status'] == 'PASS', ('first failure; no retry', name)
            if name == 'pending': assert len(value['checks']) == 11
            elif name == 'worker': assert value['checks'][0]['assertions'] == 14
            else:
                good = next(item for item in value['runs'] if item['mode'] == 'candidate')
                bad = next(item for item in value['runs'] if item['mode'] == 'm5')
                assert good['checks'] == (15 if name == 'startup-domain' else 14)
                assert good['pre_release_refreshes'] == (7 if name == 'startup-domain' else 6)
                assert bad['exit_code'] != 0
            row['status'] = 'PASS'; save()
        assert revision == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc(), retry=False)
    save(); print(json.dumps({'status': record['status'], 'output': str(out)}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
