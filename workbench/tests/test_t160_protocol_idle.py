"""T-160 state runner. Failure list and independent expectations are in the TS host.
--revision runs an earlier source; --mutant relaxes reclamation of all unknowns,
or lets a Stop clear a replacement submission. Summaries and fixtures are never overwritten.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import sys

from scripted_claude import ROOT, source_tree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--summary', type=Path, required=True)
target = parser.add_mutually_exclusive_group()
target.add_argument('--revision')
target.add_argument('--mutant', choices=['any-unknown', 'ignore-submission'])
args = parser.parse_args()
assert not args.summary.exists()
root = Path(tempfile.mkdtemp(prefix='t160-idle-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
              fixture=str(root), real_model_turns=0)
patches = {
    'any-unknown': [('src/panes.ts', 'pane.stopped || pane.nativeEnded || pane.state === "idle"',
                    'pane.stopped || pane.nativeEnded || ["idle", "unknown"].includes(pane.state)')],
    'ignore-submission': [('src/panes.ts', 'if (protocolFailure && (pane.active !== active ||',
                           'if (false && (pane.active !== active ||')],
}.get(args.mutant, [])
try:
    source = source_tree(root, args.revision, patches)
    out = root / 'out'
    out.mkdir()
    argv = ['node', str(ROOT / 'workbench/tests/test_t160_protocol_idle.ts'), str(source), str(out)]
    run = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    (root / 'console.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    result = json.loads((out / 'results.json').read_text(encoding='utf-8'))
    report.update(status=result['status'], checks=result['checks'], scope=result['scope'], command=argv, returncode=run.returncode)
except BaseException as error:
    report['error'] = f'{type(error).__name__}: {error}'
args.summary.parent.mkdir(parents=True, exist_ok=True)
with args.summary.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
