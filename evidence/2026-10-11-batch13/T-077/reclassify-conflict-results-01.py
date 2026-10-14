#!/usr/bin/env python3
"""Replay saved conflict result inputs without running product scenarios."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
E = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from test_worktree_lifecycle_e2e import classify_conflict_red

# Membership and expected coverage come from controller #132 and the saved run,
# independently of the classifier's tables or returned coverage.
CASES = [
    'test_conflict_active_worker_reworks_and_integrates',
    'test_conflict_ended_session_gets_new_attempt',
    'test_conflict_unknown_session_preserves_scene_and_reports',
    'test_conflict_unknown_delivery_does_not_resend',
    'test_merge_command_error_is_not_text_conflict',
    'test_conflict_rework_still_rejects_forbidden_path',
    'test_conflict_rework_still_rejects_foreign_trailer',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = E / 'outside-conflict-red-final-02'
    records = []
    for phase in ('red', 'candidate'):
        for number, case in enumerate(CASES, 1):
            stage = source / ('red-%02d' % number if phase == 'red' else 'candidate')
            path = stage / ('01-' + case if phase == 'red' else '%02d-%s' % (number, case)) / 'result.json'
            raw = path.read_bytes()
            saved = json.loads(raw)
            value = classify_conflict_red(saved['case'], saved['contracts'], saved['conflict_evidence'],
                tests_run=saved['tests_run'], failures=saved['failures'], errors=saved['errors'], skipped=saved['skipped'])
            expected = 'TARGET_FAILED' if phase == 'red' else 'TARGET_PASSED'
            changed = [key for key in value if value[key] != saved[key]]
            input_unchanged = path.read_bytes() == raw
            passed = (saved['case'] == case and value['target_coverage'] == expected
                      and value['business_red'] is (phase == 'red') and not changed and input_unchanged)
            records.append({'input': str(path.relative_to(ROOT)), 'phase': phase, 'case': case,
                            'counts': {key: saved[key] for key in ('tests_run', 'failures', 'errors', 'skipped')},
                            'expected_coverage': expected, 'saved_coverage': saved['target_coverage'],
                            'new_failure_rule_applies': bool(saved['failures'] and not value['target_failed']),
                            'changed_classification_fields': changed, 'input_bytes_unchanged': input_unchanged,
                            'pass': passed, 'classification': value})
    report = {'status': 'PASS' if all(row['pass'] for row in records) else 'INCOMPLETE',
              'scope': 'offline classification replay only; no product or conflict-final rerun',
              'command': [sys.executable, '-B', *sys.argv], 'cwd': str(Path.cwd()),
              'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'original_evidence_commit': '05ed480bcc9882fb2c8074c4b8ad8c3727d66c2d',
              'input_files': len(records), 'real_codex_turns': 0, 'records': records}
    (args.output / 'fixture-at-run.py').write_bytes((ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py').read_bytes())
    (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for row in records:
        print(json.dumps({key: row[key] for key in ('phase', 'case', 'expected_coverage',
            'new_failure_rule_applies', 'changed_classification_fields', 'input_bytes_unchanged', 'pass')}))
    print(json.dumps({'status': report['status'], 'input_files': len(records), 'real_codex_turns': 0}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
