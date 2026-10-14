#!/usr/bin/env python3
"""Controller-only socket run: kill the mutant first, then prove red and green."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
E = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
assert os.path.ismount('/Volumes/WD-Elements'), 'External dependency volume must be mounted'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
product_revision = '2e2291acfee0e9b4f20c7ff952a5484c4262e20b'
# Later evidence-only commits do not change the tested product.
subprocess.run(['git', 'diff', '--exit-code', product_revision, '--', 'workbench/src', 'workbench/hooks'], cwd=ROOT, check=True)
mutant = Path(tempfile.mkdtemp(prefix='t077-trailer-mutant-', dir='/tmp'))
for folder in ('workbench/src', 'workbench/hooks'):
    shutil.copytree(ROOT / folder, mutant / folder, symlinks=True)
shutil.copyfile(ROOT / 'workbench/package.json', mutant / 'workbench/package.json')
(mutant / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
core = mutant / 'workbench/src/gates/core.ts'
original = core.read_text(encoding='utf-8')
before = 'Object.keys(trailers).length !== required.length ||\n          '
assert original.count(before) == 1
core.write_text(original.replace(before, '', 1), encoding='utf-8')
changed = [str(p.relative_to(ROOT)) for folder in ('workbench/src', 'workbench/hooks') for p in (ROOT / folder).rglob('*')
           if p.is_file() and p.read_bytes() != (mutant / p.relative_to(ROOT)).read_bytes()]
assert changed == ['workbench/src/gates/core.ts']
records = []
for phase, product, selection, counterfactual in [('known-bad', mutant, 'red', True), ('candidate', ROOT, 'both', False)]:
    output = args.output / phase
    argv = ['python3', '-B', str(ROOT / 'workbench/tests/test_conflict_trailer_proofs.py'),
        '--source', str(product), '--input', str(E / 'controlled-trailer-input.json'),
        '--output', str(output.resolve()), '--case', selection] + (['--expect-red'] if counterfactual else [])
    # The child owns cleanup and its per-operation deadlines. Do not kill the
    # client while its detached isolated daemon may still require cleanup.
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    (args.output / (phase + '.console.txt')).write_text(result.stdout + result.stderr, encoding='utf-8')
    receipt = json.loads((output / 'run.json').read_text(encoding='utf-8')) if (output / 'run.json').exists() else None
    records.append({'phase': phase, 'argv': argv, 'exit': result.returncode, 'result': receipt})
    if result.returncode:
        break
    if phase == 'known-bad' and receipt['red_confirmed'] is not True:
        break
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == head
    subprocess.run(['git', 'diff', '--exit-code', product_revision, '--', 'workbench/src', 'workbench/hooks'], cwd=ROOT, check=True)
passed = (len(records) == 2 and all(r['exit'] == 0 for r in records) and
          records[0]['result']['red_confirmed'] is True and records[1]['result']['status'] == 'PASS' and
          (records[1]['result']['tests_run'], records[1]['result']['failures'], records[1]['result']['errors']) == (2, 0, 0))
if passed:
    red = json.loads((args.output / 'candidate/test_extra_trailers_refused/scene.json').read_text(encoding='utf-8'))
    green = json.loads((args.output / 'candidate/test_hook_trailers_integrate/scene.json').read_text(encoding='utf-8'))
    passed = red['C2_source'] == green['C2_source']
oversized = [str(p) for p in args.output.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
report = {'status': 'PASS' if passed and not oversized else 'INCOMPLETE', 'product_revision': product_revision, 'source_commit': head,
    'scope': 'Two controlled CLI proofs; not additional real model evidence', 'real_codex_turns': 0,
    'mutant': {'root': str(mutant), 'changed_files': changed, 'recipe': {'remove_once': before},
               'committed': False, 'source_archives_contain_original_candidate': True},
    'cases': records, 'same_C2_code': passed, 'evidence_over_5MiB': oversized,
    'oversized_action': 'Stop and ask controller to archive; do not commit these files'}
with (args.output / 'run.json').open('x', encoding='utf-8') as f: json.dump(report, f, ensure_ascii=False, indent=2); f.write('\n')
print(json.dumps({'status': report['status'], 'real_codex_turns': 0, 'evidence_over_5MiB': oversized}, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
