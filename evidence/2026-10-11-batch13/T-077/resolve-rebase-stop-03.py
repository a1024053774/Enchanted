#!/usr/bin/env python3
"""Resolve only the three speed-related files at the approved fourth commit."""
from pathlib import Path
import ast
import json
import re
import subprocess

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
EVIDENCE = ROOT / 'evidence/2026-10-11-batch13/T-077/rebase-stop-03'
HEAD = '0b194a55b260d5ab342e2cd50b9b49674ee25405'
STOP = 'f6bc3ed99c87e6ea20eaf144b6a073266a5decb2'
PATHS = {'workbench/src/panes.ts': 2, 'workbench/tests/run_pane_lifecycle.py': 2,
         'workbench/tests/run_t076_real.py': 1}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert git('rev-parse', 'REBASE_HEAD').decode().strip() == STOP
unmerged = git('diff', '--name-only', '--diff-filter=U', '-z').decode().split('\0')
assert sorted(filter(None, unmerged)) == sorted(PATHS)
assert not EVIDENCE.exists(), 'Preserve an existing stop archive'
resolved = {}
originals = {}
pattern = re.compile(r'^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]+\n', re.M | re.S)
for name, count in PATHS.items():
    current = (ROOT / name).read_text()
    assert len(pattern.findall(current)) == count, name
    content = pattern.sub(lambda match: match[1], current)
    head = git('show', ':2:' + name)
    assert content.encode() == head, f'Unexpected change outside conflicts: {name}'
    if name.endswith('.py'):
        ast.parse(content, filename=name)
        assert head == git('show', 'main:' + name), f'T-076 script differs from main: {name}'
    originals[name] = {'unresolved': current.encode(), 'head': head, 'incoming': git('show', ':3:' + name)}
    resolved[name] = content
for name, versions in originals.items():
    for version, content in versions.items():
        target = EVIDENCE / version / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
for name, content in resolved.items():
    (ROOT / name).write_text(content)
    target = EVIDENCE / 'resolved' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
subprocess.run(['node', '--check', 'workbench/src/panes.ts'], cwd=ROOT, check=True)
status_argv = ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.']
status = subprocess.run(status_argv, cwd=ROOT, text=True, capture_output=True, check=True)
(EVIDENCE / 'project-map-status.txt').write_text(status.stdout + status.stderr)
result = {'status': 'PASS', 'scope': 'conflict_resolution_and_syntax_only',
    'business_regression': 'INCOMPLETE: run after full rebase',
    'head': HEAD, 'rebase_head': STOP, 'conflict_blocks': PATHS,
    'resolved_files_equal_current_head': True,
    'both_python_scripts_equal_main': True, 'service_tier': 'default',
    'git_mutations': False, 'real_model_turns': 0,
    'commands': [['node', '--check', 'workbench/src/panes.ts'],
                 ['Python ast.parse', *[p for p in PATHS if p.endswith('.py')]], status_argv]}
(EVIDENCE / 'preflight.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
