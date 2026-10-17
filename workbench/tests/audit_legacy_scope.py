"""Require unchanged business assertions from the accepted T-091 task baseline.

The dated T-076 allowed-hunk audit cannot describe later accepted T-077 changes.
This wrapper now compares complete source bytes with the task-card baseline;
there are no allowed methods to mask and no business assertions to rewrite.
"""
import subprocess

BASELINE = '44bbb7828459d81fab0d46069a19d3dd515a7732'
PATHS = (
    'acceptance/test_coop_e2e.py',
    'acceptance/test_run_e2e.py',
    'acceptance/test_recovery_e2e.py',
    'workbench/tests/test_task_cards_e2e.py',
)


def audit(root):
    for name in PATHS:
        before = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=root)
        if (root / name).read_bytes() != before:
            raise RuntimeError('Business assertion source changed from frozen baseline: ' + name)
    return {'baseline': BASELINE, 'paths': list(PATHS), 'assertions_unchanged': True}
