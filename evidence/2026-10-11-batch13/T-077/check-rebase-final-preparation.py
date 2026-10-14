#!/usr/bin/env python3
"""Static preparation checks only. No sockets, model, PTY or process signals."""
import ast
import json
from pathlib import Path
import subprocess
import tempfile
import sys

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
E = ROOT / 'evidence/2026-10-11-batch13/T-077'
sys.path.insert(0, str(E))
import importlib.util
spec = importlib.util.spec_from_file_location('final_phase', E / 'run-rebase-final-01.py')
phase = importlib.util.module_from_spec(spec); spec.loader.exec_module(phase)
phase.guard(); phase.verify_snapshot()
commands = []
for path in (ROOT / 'workbench/tests').glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
for name in ('run-rebase-final-01.py', 'check-rebase-final-preparation.py'):
    ast.parse((E / name).read_text(encoding='utf-8'), filename=name)
for name in ('conflict_acceptance_host.ts', 'relay_conflict_host.ts', 'trailer_conflict_host.ts',
             'controlled_quality_pty.ts', 'test_conflict_panes.ts', 'test_relay_scope.ts'):
    argv = ['node', '--check', str(ROOT / 'workbench/tests' / name)]
    subprocess.run(argv, cwd=ROOT, check=True); commands.append(argv)
argv = ['bash', '-n', str(E / 'outside-sandbox.sh')]
subprocess.run(argv, cwd=ROOT, check=True); commands.append(argv)
core = (ROOT / 'workbench/src/gates/core.ts').read_text(encoding='utf-8')
temp = Path(tempfile.mkdtemp(prefix='t077-final-syntax-', dir='/tmp'))
for name, (before, after) in phase.RECIPES.items():
    assert core.count(before) == 1, name
    path = temp / (name + '.ts'); path.write_text(core.replace(before, after, 1), encoding='utf-8')
    argv = ['node', '--check', str(path)]
    subprocess.run(argv, cwd=ROOT, check=True); commands.append(argv)

def checks(text):
    return [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(text))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and (n.func.attr == 'check' or n.func.attr.startswith('assert'))]

protected = ['workbench/tests/test_quality_chain_e2e.py', 'workbench/tests/test_quality_tracer_e2e.py',
             'workbench/tests/test_quality_widen_e2e.py', 'workbench/tests/test_native_final_read.ts',
             'workbench/tests/test_pane_dispatch_state.ts']
for name in protected:
    original = subprocess.check_output(['git', 'show', phase.REVISION + ':' + name], cwd=ROOT).decode('utf-8')
    actual = (ROOT / name).read_text(encoding='utf-8')
    assert checks(original) == checks(actual) if name.endswith('.py') else original == actual, name
acceptance = list((ROOT / 'acceptance').glob('test_*.py'))
for path in acceptance:
    assert path.read_bytes() == subprocess.check_output(['git', 'show', phase.REVISION + ':' + str(path.relative_to(ROOT))], cwd=ROOT)
status_argv = ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.']
status = subprocess.run(status_argv, cwd=ROOT, capture_output=True, text=True, check=True)
(phase.PREP / 'project-map-status.txt').write_text(status.stdout + status.stderr, encoding='utf-8')
large = phase.large_files(E)
assert not large, large
record = {'status': 'PASS', 'scope': 'syntax_and_frozen_input_checks_only',
    'business_red_green': 'INCOMPLETE: controller outside phase not run', 'revision': phase.REVISION,
    'real_codex_turns': 0, 'product_source_unchanged': True,
    't076_business_check_asts_unchanged': protected, 'acceptance_files_byte_unchanged': [str(p.relative_to(ROOT)) for p in acceptance],
    'mutants_syntax_only': list(phase.RECIPES), 'commands': commands,
    'files_over_5mb': large, 'issue': '20261014T023857Z-worker:s13-t077s-issue-001'}
with (phase.PREP / 'static-checks.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({k: record[k] for k in ('status', 'scope', 'revision', 'real_codex_turns')}))
