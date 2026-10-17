"""Sequential isolated reader checks; never target the A15 scene."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE.parents[2]
TESTS = SOURCE / 'workbench/tests'


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    cases = [
        ('screen-parent-red', TESTS / 'test_t078_output_paging.py', ['--entry-only', '--ps-mode', 'real', '--p1-script', BASE / '09b-a15-e4-screen-diagnosis-01/run_t078_p1.py'], 1),
        ('screen-green', TESTS / 'test_t078_output_paging.py', ['--ps-mode', 'real'], 0),
        ('one-page-mutant', TESTS / 'test_t078_output_paging.py', ['--entry-only', '--one-page-mutant', '--ps-mode', 'real'], 1),
        ('permission-green', TESTS / 'test_t078_output_paging.py', ['--entry', 'permission', '--ps-mode', 'real'], 0),
        ('phase-parent-red', TESTS / 'test_t078_phase_capture.py', ['--module', BASE / '09b-a15-e4-screen-diagnosis-01/t078_09b_phase_driver.py'], 1),
        ('phase-green', TESTS / 'test_t078_phase_capture.py', [], 0),
        ('recovery-green', TESTS / 'test_t078_permission_recovery.py', [], 0),
        ('recovery-mutant', TESTS / 'test_t078_permission_recovery.py', ['--omit-prefix-check'], 1),
        ('frozen-reader-scope', TESTS / 'test_t078_frozen_reader.py', [], 0),
    ]
    for name, script, argv, expected in cases:
        command = [sys.executable, '-B', str(script), *map(str, argv), '--output', str((args.output / name).resolve())]
        run = subprocess.run(command, cwd=SOURCE, capture_output=True, timeout=60)
        (args.output / (name + '.stdout.txt')).write_bytes(run.stdout); (args.output / (name + '.stderr.txt')).write_bytes(run.stderr)
        report_file = args.output / name / ('result.json' if name.startswith('phase-') else 'results.json')
        contract = False
        if report_file.is_file():
            observed = json.loads(report_file.read_bytes())
            if expected == 0:
                contract = observed['status'] == 'PASS'
            elif name == 'screen-parent-red':
                contract = all(row['observed_error'] == "RuntimeError('screen_exceeds_review_limit')" for row in observed['cases'])
            elif name == 'one-page-mutant':
                contract = all(row['exit_code'] == 0 and row['status'] == 'INCOMPLETE' and row['observed_error'] is None for row in observed['cases'])
            elif name == 'phase-parent-red':
                contract = observed['actual_bytes'] == 65536 and observed['expected_bytes'] == 155701 and observed['offsets'] == [0]
            elif name == 'recovery-mutant':
                contract = any(row['fault'] == 'prefix' and row['error'] is None and row['status'] == 'INCOMPLETE' for row in observed['cases'])
        rows.append({'name': name, 'argv': command, 'expected_exit': expected, 'observed_exit': run.returncode, 'contract_verified': contract})
        if run.returncode != expected or not contract:
            break
    report = {'status': 'PASS' if len(rows) == len(cases) and all(x['expected_exit'] == x['observed_exit'] and x['contract_verified'] for x in rows) else 'INCOMPLETE',
              'cases': rows, 'scope': 'Isolated output transport fixtures and real identity of own foreground Python; no A15 API/daemon/CLI/window/key', 'scene_actions': 0}
    (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'cases': len(rows), 'scene_actions': 0})); return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
