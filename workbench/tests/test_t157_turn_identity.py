"""T-157 identity-state runner; failure modes and oracle precede the TS host.
This is isolated state evidence only. Electron/CLI evidence uses the separate e2e.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from scripted_claude import ROOT, source_tree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--summary', type=Path, required=True)
target = parser.add_mutually_exclusive_group()
target.add_argument('--revision')
target.add_argument('--mutant', choices=['ignore-turn', 'swallow-input', 'delay-input'])
args = parser.parse_args()
assert not args.summary.exists(), 'Preserve existing evidence'
root = Path(tempfile.mkdtemp(prefix='t157-identity-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant, fixture=str(root), vendor_model_turns=0)
patches = {
    'ignore-turn': [('src/panes.ts', 'pane.claudePromptId === turn, "worker_not_active"', 'true, "worker_not_active"')],
    'swallow-input': [('src/panes.ts', 'pane.pty.write(binary ? bytes : data);', '/* mutant: input swallowed */')],
    'delay-input': [('src/panes.ts', 'pane.pty.write(binary ? bytes : data);',
                     'while (pane.stopInProgress) await new Promise(resolve => setTimeout(resolve, 10));\n        pane.pty.write(binary ? bytes : data);')],
}.get(args.mutant, [])
try:
    source = source_tree(root, args.revision, patches)
    out = root / 'out'
    out.mkdir()
    command = ['node', str(ROOT / 'workbench/tests/test_t157_turn_identity.ts'), str(source), str(out)]
    run = subprocess.run(command, capture_output=True, text=True, timeout=15)
    (root / 'console.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    report.update(command=command, returncode=run.returncode)
    result = json.loads((out / 'results.json').read_text(encoding='utf-8'))
    report.update(result)
except Exception as error:
    report['error'] = f'{type(error).__name__}: {error}'
args.summary.parent.mkdir(parents=True, exist_ok=True)
with args.summary.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
