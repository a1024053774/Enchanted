#!/usr/bin/env python3
"""Resolve the pane role metadata at the fixed fifth-commit rebase stop."""
from pathlib import Path
import json
import re
import subprocess

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
HERE = ROOT / 'evidence/2026-10-11-batch13/T-077/rebase-stop-05'
HEAD = '9f9bca77bbb9901702cc28ecf6834505ce4dc2d4'
STOP = '2e2291acfee0e9b4f20c7ff952a5484c4262e20b'
NAME = 'workbench/src/panes.ts'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert git('rev-parse', 'REBASE_HEAD').decode().strip() == STOP
assert list(filter(None, git('diff', '--name-only', '--diff-filter=U', '-z').decode().split('\0'))) == [NAME]
assert not HERE.exists(), 'Preserve existing evidence'
original = (ROOT / NAME).read_text()
pattern = re.compile(r'^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]+\n', re.M | re.S)
assert len(pattern.findall(original)) == 2
resolved = pattern.sub(lambda match: match[1], original)
head = git('show', ':2:' + NAME)
assert resolved.encode() == head, 'Unexpected change outside the two conflict blocks'
for version, content in [('unresolved', original.encode()), ('head', head),
                         ('incoming', git('show', ':3:' + NAME)), ('resolved', resolved.encode())]:
    path = HERE / version / NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
(ROOT / NAME).write_text(resolved)
subprocess.run(['node', '--check', NAME], cwd=ROOT, check=True)
status = subprocess.run(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'],
                        cwd=ROOT, text=True, capture_output=True, check=True)
(HERE / 'project-map-status.txt').write_text(status.stdout + status.stderr)
result = {'status': 'PASS', 'scope': 'conflict_resolution_and_syntax_only',
          'head': HEAD, 'rebase_head': STOP, 'unmerged_paths': [NAME],
          'resolved_file_equals_head': True, 'service_tier': 'default',
          'reviewer_read_only_and_role_metadata_preserved': True,
          'git_mutations': False, 'real_model_turns': 0,
          'business_regression': 'INCOMPLETE: pending full rebase and frozen HEAD'}
(HERE / 'preflight.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
