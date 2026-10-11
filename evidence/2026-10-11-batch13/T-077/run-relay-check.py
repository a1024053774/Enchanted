#!/usr/bin/env python3
"""Controller-only socket experiment. No native CLI/model or credentials."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
assert os.path.ismount('/Volumes/WD-Elements'), 'External dependency volume must be mounted'
baseline = subprocess.check_output(['git', 'show', '14b57d22a84bcaebfa91c5051b9909b53a570fac:workbench/src/relay.ts'], cwd=ROOT)
assert baseline == (EVIDENCE / 'relay-scope-red-01/relay-preimage.ts').read_bytes()
assert baseline == subprocess.check_output(['git', 'show', '93094e7be82c21448c460436c360ffb0f75a3412:workbench/src/relay.ts'], cwd=ROOT)
preimage = Path(tempfile.mkdtemp(prefix='t077-relay-preimage-', dir='/tmp'))
for folder in ('workbench/src', 'workbench/hooks'):
    shutil.copytree(ROOT / folder, preimage / folder)
shutil.copyfile(ROOT / 'workbench/package.json', preimage / 'workbench/package.json')
(preimage / 'workbench/node_modules').symlink_to(ROOT / 'workbench/node_modules', target_is_directory=True)
(preimage / 'workbench/src/relay.ts').write_bytes(baseline)
different = [str(p.relative_to(ROOT)) for folder in ('workbench/src', 'workbench/hooks')
             for p in (ROOT / folder).rglob('*') if p.is_file() and p.read_bytes() != (preimage / p.relative_to(ROOT)).read_bytes()]
assert different == ['workbench/src/relay.ts'], different
records = []
for name, product, red in [('preimage', preimage, True), ('candidate', ROOT, False)]:
    out = args.output / name
    argv = ['python3', '-B', str(ROOT / 'workbench/tests/test_relay_conflict_e2e.py'),
            '--source', str(product), '--output', str(out.resolve())] + (['--expect-red'] if red else [])
    # Individual operations and host cleanup have deadlines in the test. Let
    # its cleanup run; killing this client would orphan the detached host.
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    (args.output / (name + '.console.txt')).write_text(p.stdout + p.stderr, encoding='utf-8')
    records.append({'phase': name, 'argv': argv, 'exit': p.returncode,
                    'result': json.loads((out / 'run.json').read_text(encoding='utf-8')) if (out / 'run.json').exists() else None})
    if p.returncode != 0:
        break
passed = (len(records) == 2 and all(row['exit'] == 0 for row in records) and
          records[0]['result']['red_confirmed'] is True and records[1]['result']['status'] == 'PASS')
report = {'status': 'PASS' if passed else 'INCOMPLETE', 'baseline_relay': '14b57d22 = 93094e7b',
          'preimage_root': str(preimage), 'changed_from_preimage': different,
          'real_codex_turns': 0, 'cases': records}
(args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if passed else 1)
