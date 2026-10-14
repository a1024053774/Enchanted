#!/usr/bin/env python3
"""Read frozen inputs and parse the prepared stage; start no host."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
E = ROOT / 'evidence/2026-10-11-batch13/T-077'
spec = importlib.util.spec_from_file_location('conflict_phase', E / 'run-conflict-red-final-01.py')
phase = importlib.util.module_from_spec(spec); spec.loader.exec_module(phase)
phase.guard(); phase.verify_snapshot()
assert not phase.OUT.exists()
sys.path.insert(0, str(ROOT / 'workbench/tests'))
import test_worktree_lifecycle_e2e as fixture
selected = [name for cls, name in fixture.CASES if cls is fixture.ConflictContracts]
assert selected == [case for case, _, _ in phase.CASES]
assert fixture.CONFLICT_TARGET_IDS == {case: target for case, target, _ in phase.CASES}
assert tuple(fixture.CONFLICT_REQUIRED_FACTS) == ('conflict_delivered', 'explicit_resubmitted', 'target_verify_executed')
for path in [ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py',
             E / 'run-conflict-red-final-01.py', E / 'check-conflict-red-final-preparation-01.py',
             E / 'check-conflict-classifier-01.py', E / 'check-recorded-conflict-red-01.py']:
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
argv = ['bash', '-n', str(E / 'outside-sandbox.sh')]
subprocess.run(argv, cwd=ROOT, check=True)
status_argv = ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.']
status = subprocess.run(status_argv, cwd=ROOT, capture_output=True, text=True, check=True)
(phase.PREP / 'project-map-status.txt').write_text(status.stdout + status.stderr, encoding='utf-8')
large = phase.large_files(E); assert not large, large
record = {'status': 'PASS', 'scope': 'static preparation only; not target red/green',
    'product': phase.PRODUCT, 'harness': phase.HARNESS, 'planned_subphases': 8, 'conflict_cases': 7,
    'target_ids_match': True, 'strict_three_receipts_for_all_cases': True,
    'earlier_stage_targets_may_be_not_covered': selected[:5],
    'mutant_syntax_checks': 4, 'commands': [argv, status_argv], 'files_over_5mb': large, 'real_codex_turns': 0}
with (phase.PREP / 'static-checks.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({key: record[key] for key in ('status', 'scope', 'planned_subphases', 'real_codex_turns')}))
