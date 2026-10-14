#!/usr/bin/env python3
"""Independent red oracle over the original controlled real-entry scene.

No daemon is started. Original CLI/daemon/relay/gates events establish that the
review result and reclaim completed; Git and disk are independently read back.
This is recorded-scene red evidence, not a claim of a fresh entry invocation.
"""
import io
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
E = ROOT / 'evidence/2026-10-11-batch13/T-077'
SOURCE = E / 'outside-rebase-final-01/joint-candidate/same_candidate_reuses_review'
OUT = E / 'review-lifecycle-recorded-red-01'
OUT.mkdir(exist_ok=False)
database = json.loads((SOURCE / 'database-readback.json').read_text(encoding='utf-8'))
events = [{**row, 'details': json.loads(row['details'])} for row in database['tables']['events']]
reclaimed = [row for row in events if row['type'] == 'review_reclaimed']
if len(reclaimed) != 1: raise RuntimeError('Scene must have exactly one completed reviewer reclaim')
review_id = reclaimed[0]['details']['review_id']
results = [row for row in events if row['type'] == 'review_result' and row['details']['review']['review_id'] == review_id]
if len(results) != 1: raise RuntimeError('No uniquely bound stored review result')
review = results[0]['details']['review']
task = json.loads(database['tables']['tasks'][0]['data'])
repo, workspace = Path(task['repo']), Path(review['workspace'])
for path in (repo, workspace):
    if not path.resolve().is_relative_to(Path('/tmp').resolve()): raise RuntimeError('Not an isolated temporary scene')
argv = ['git', '-C', str(repo), 'worktree', 'list', '--porcelain', '-z']
p = subprocess.run(argv, capture_output=True, text=True, check=True)
registered = 'worktree ' + str(workspace) in p.stdout.split('\0')
exists = workspace.exists()
state = Path(json.loads((SOURCE / 'fixture.json').read_text(encoding='utf-8'))['host']['root'])
expected_name = str(state / 'worktrees' / task['project_id'] /
                    (task['task_id'] + '-a' + str(review['attempt']['fence']) + '-review-1'))
proof = {'scope': 'recorded controlled real-entry scene; read-only current Git/disk oracle',
    'source': str(SOURCE), 'review': review, 'result_event': results[0], 'reclaimed_event': reclaimed[0],
    'command': argv, 'stdout': p.stdout, 'directory_exists': exists, 'git_registered': registered,
    'expected': {'directory_exists': False, 'git_registered': False, 'workspace': expected_name},
    'real_codex_turns': 0}
with (OUT / 'readback.json').open('x', encoding='utf-8') as handle:
    json.dump(proof, handle, ensure_ascii=False, indent=2); handle.write('\n')


class StoredReviewCleanup(unittest.TestCase):
    def test_result_and_reclaim_leave_no_review_workspace(self):
        self.assertEqual((exists, registered), (False, False),
                         'Spec section 4: stored result and confirmed reviewer reclaim must remove the review worktree')


stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite([
    StoredReviewCleanup('test_result_and_reclaim_leave_no_review_workspace')]))
(OUT / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
red = len(result.failures) == 1 and not result.errors and exists and registered
report = {'status': 'PASS' if red else 'INCOMPLETE', 'scope': proof['scope'],
    'red_confirmed': red, 'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
    'review_id': review_id, 'directory_exists': exists, 'git_registered': registered, 'real_codex_turns': 0}
with (OUT / 'run.json').open('x', encoding='utf-8') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
print(json.dumps(report))
raise SystemExit(0 if red else 1)
