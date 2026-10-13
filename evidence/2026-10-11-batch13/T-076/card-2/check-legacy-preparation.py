"""Syntax and scope receipts only. Does not start any test backend or model."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
card = Path(__file__).resolve().parent; root = card.parents[3]
if args.output.exists(): raise RuntimeError('Preserve old evidence; select a new output file.')
result = dict(status='INCOMPLETE', product_status='INCOMPLETE', ready_for_outside=False,
              pending=[], real_codex_turns=0, commands=[])

def command(argv):
    p = subprocess.run(argv, cwd=root, text=True, capture_output=True, timeout=30)
    result['commands'].append(dict(argv=argv, cwd=str(root), exit=p.returncode, stdout=p.stdout, stderr=p.stderr))
    if p.returncode: raise RuntimeError('Static check failed: ' + repr(argv))
    return p.stdout

try:
    result['head'] = command(['git', 'rev-parse', 'HEAD']).strip()
    sys.path.insert(0, str(root / 'workbench/tests'))
    from audit_legacy_scope import audit
    result['approved_assertion_scope'] = audit(root)
    files = sorted(set(command(['git', 'diff', '--name-only', '--', 'workbench', 'acceptance']).splitlines() +
                       command(['git', 'ls-files', '--others', '--exclude-standard', 'workbench/tests']).splitlines()))
    for file in files:
        path = root / file
        if path.suffix == '.py': ast.parse(path.read_text(encoding='utf-8'), filename=file)
        if path.suffix == '.ts': command(['node', '--check', file])
    command(['zsh', '-n', str(card / 'outside-sandbox.sh')])
    command(['node', '--input-type=module', '-e',
             'await Promise.all(["./workbench/tests/controlled_quality_pty.ts","./workbench/tests/legacy_review_runtime.ts"].map(p=>import(p))); console.log("imports only; no runtime constructed")'])
    base = command(['git', 'show', 'a7f4cc3033c16d5888de50d8352da516c941f8e9:workbench/tests/test_task_cards_e2e.py'])
    candidate = (root / 'workbench/tests/test_task_cards_e2e.py').read_text(encoding='utf-8')
    name = 'test_non_fast_forward_git_result_cannot_integrate'
    def method(text):
        node = next(n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef) and n.name == name)
        return ''.join(text.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])
    original = method(base)
    if original.count('a = self.create()') != 1 or method(candidate) != original.replace('a = self.create()', 'a = self.create_managed()', 1):
        raise RuntimeError('F13 changed more than its approved preparation call.')
    result['f13_only_approved_preparation_changed'] = True
    core = (root / 'workbench/src/gates/core.ts').read_text(encoding='utf-8')
    before = '        requireGate(attempt.delivery, "score_provenance_required");'
    if core.count(before) != 1: raise RuntimeError('Provenance mutant does not have one exact target.')
    with tempfile.TemporaryDirectory(prefix='l76-syntax-') as folder:
        path = Path(folder) / 'core.ts'
        path.write_text(core.replace(before, '        // Controlled mutant: omit provenance before CAS.'), encoding='utf-8')
        command(['node', '--check', str(path)])
    result['files_checked'] = files
    for name in ['RESULTS.md', 'assertion-hunks.md', 'HANDOFF-legacy-green-06.md', 'run-review-wait-repair-01/README.md']:
        raw = (card / name).read_bytes()
        if raw.startswith(b'\xef\xbb\xbf') or '\ufffd' in raw.decode('utf-8'):
            raise RuntimeError('Document encoding failed: ' + name)
    command(['git', 'diff', '--check'])
    command(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
    result['oversize_files'] = command(['find', str(card), '-size', '+5M']).splitlines()
    if result['oversize_files']: raise RuntimeError('Oversize evidence requires archival.')
    result['status'] = 'PASS'
    result['ready_for_outside'] = True
except Exception as error:
    result['error'] = repr(error)
with args.output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({k: result[k] for k in ('status', 'product_status', 'ready_for_outside', 'pending')}))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
