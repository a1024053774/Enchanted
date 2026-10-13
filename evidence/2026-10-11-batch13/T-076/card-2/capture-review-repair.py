"""Preserve the measured red readback and the exact reviewer repair diff."""
import argparse
import difflib
import json
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
card = Path(__file__).resolve().parent
root = card.parents[3]
out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
summaries = []
for name in ('outside-reviewer-red-01', 'outside-wide-green-01'):
    report = json.loads((card / name / 'run.json').read_text(encoding='utf-8'))
    if report['status'] != 'PASS' or report['real_codex_turns'] != 0 or report['oversize_files']:
        raise RuntimeError('Controller result does not match the declared checkpoint.')
    steps = []
    for step in report['steps']:
        cases = [{'case': row['case'], 'outcome': row['outcome'], 'failure_id': row.get('failure_id'),
                  'cleanup_failures': row['cleanup_failures']} for row in step['report']['cases']]
        if any(row['cleanup_failures'] or row['outcome'] == 'harness_error' for row in cases):
            raise RuntimeError('Unexpected fixture error in preserved checkpoint.')
        steps.append({'name': step['name'], 'exit': step['exit'], 'cases': cases})
    summaries.append({'path': str(card / name / 'run.json'), 'status': report['status'], 'steps': steps})
files = ['workbench/src/gates/core.ts', 'workbench/src/daemon.ts', 'workbench/src/stateConsistency.ts']
archive = card / 'outside-wide-green-01/candidate-and-harness.tar.gz'
diff = []
with tarfile.open(archive, 'r:gz') as source:
    for name in files:
        before = source.extractfile(name).read()
        after = (root / name).read_bytes()
        for directory, content in (('before', before), ('after', after)):
            target = out / directory / name; target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream: stream.write(content)
        diff.extend(difflib.unified_diff(before.decode('utf-8').splitlines(keepends=True),
                    after.decode('utf-8').splitlines(keepends=True), fromfile='before/' + name, tofile='after/' + name))
with (out / 'reviewer-lifecycle.diff').open('x', encoding='utf-8') as stream: stream.write(''.join(diff))
with (out / 'readback.json').open('x', encoding='utf-8') as stream:
    json.dump({'status': 'PASS', 'product_status': 'INCOMPLETE', 'scope': 'saved checkpoint readback and repair diff only',
               'baseline': str(archive), 'files': files, 'readbacks': summaries}, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print('PASS: preserved checkpoint readback and exact repair diff; dynamic green is pending')
