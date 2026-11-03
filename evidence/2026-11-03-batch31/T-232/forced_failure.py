"""Run test_t216_issue_push_e2e with a deliberate failure right after Fixture.start (the controller Claude Code is live
in the private core), then list fixture processes. Usage: python3 forced_failure.py <summary.json>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'workbench/tests'))
import scripted_claude
import test_t216_issue_push_e2e as t

def fail(self, *a, **k):
    raise RuntimeError('T-232 deliberate failure after start')
scripted_claude.Fixture.card = fail
sys.argv = ['test_t216_issue_push_e2e.py', '--summary', sys.argv[1]]
try:
    t.main()
except RuntimeError as error:
    print('raised as intended:', error)
