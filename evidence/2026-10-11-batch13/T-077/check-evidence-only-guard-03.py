#!/usr/bin/env python3
"""Check the actual runner guard's evidence-only commit boundary locally."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
E = ROOT / 'evidence/2026-10-11-batch13/T-077'
OUT = E / 'evidence-only-guard-check-03'; OUT.mkdir(exist_ok=False)
tree = ast.parse((E / 'run-rebase-final-03.py').read_text(encoding='utf-8'))
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'guard')
code = compile(ast.Module(body=[function], type_ignores=[]), 'run-rebase-final-03.py#guard-only', 'exec')
temporary = Path(tempfile.mkdtemp(prefix='t077-guard-03-', dir='/tmp'))
prefix = str(E.relative_to(ROOT)) + '/'
cases = [
    ('ticket-evidence-only', [prefix + 'run-rebase-final-03.py', prefix + 'result.json'], {}, 0, True),
    ('source-after-evidence', [prefix + 'result.json', 'workbench/src/gates/core.ts'], {}, 0, False),
    ('unrelated-evidence', ['evidence/other-ticket/result.json'], {}, 0, False),
    ('non-descendant', [], {}, 1, False),
    ('dirty-tests', [], {'workbench/tests': b'changed'}, 0, False),
    ('dirty-product', [], {'workbench/src': b'changed'}, 0, False),
]
results = []
for name, changed, dirty, ancestry, allowed in cases:
    def git(*args):
        if args == ('rev-parse', 'HEAD'): return b'evidence-commit\n'
        if args[:3] == ('diff', '--name-only', '-z'): return b'\0'.join(p.encode() for p in changed)
        if args == ('branch', '--show-current'): return b'exec/t077\n'
        if args[:2] == ('rev-parse', '--git-path'): return str(temporary / args[2]).encode()
        if args[0] == 'diff': return dirty.get(args[-1], b'')
        raise AssertionError(args)
    namespace = {'ROOT': ROOT, 'E': E, 'REVISION': 'candidate', 'Path': Path, 'git': git,
        'subprocess': SimpleNamespace(run=lambda *a, **k: SimpleNamespace(returncode=ancestry)),
        'os': SimpleNamespace(path=SimpleNamespace(ismount=lambda path: True))}
    exec(code, namespace)
    error = None
    try: namespace['guard']()
    except RuntimeError as caught: error = str(caught)
    actual = error is None
    assert actual == allowed, (name, error)
    results.append({'case': name, 'expected_allowed': allowed, 'allowed': actual, 'error': error})
report = {'status': 'PASS', 'scope': 'runner guard only; no gate/model', 'real_codex_turns': 0, 'cases': results}
with (OUT / 'run.json').open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(report, ensure_ascii=False))
