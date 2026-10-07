#!/usr/bin/env python3
"""Run an already-built test binary with short runtime paths and isolated process state."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--binary', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--filter')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
shutil.copyfile(__file__, args.output / 'runner-used.py')
binary = str(args.binary.resolve())
env = {k: v for k, v in os.environ.items() if not k.startswith(('HERDR_', 'MUSTER_'))}
runtime = Path(tempfile.mkdtemp(prefix='t027-unit-', dir='/tmp'))
env['TMPDIR'] = str(runtime)
listing = subprocess.run([binary, '--list'], env=env, text=True, capture_output=True, check=True)
(args.output / 'test-list.txt').write_text(listing.stdout, encoding='utf-8')
tests = [line.split(': test')[0] for line in listing.stdout.splitlines() if line.endswith(': test')]
groups = sorted(set(test.split('::')[0] for test in tests))
if args.filter:
    groups = [args.filter]
results = []
for group in groups:
    argv = [binary, group + '::' if not args.filter else group, '--test-threads=1', '--nocapture']
    target = args.output / (group.replace('::', '-') + '.log')
    with target.open('w', encoding='utf-8') as stream:
        result = subprocess.run(argv, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=300)
    entry = dict(group=group, argv=argv, exit_code=result.returncode, log=str(target),
                 runtime_tmpdir=str(runtime))
    results.append(entry)
    print(json.dumps(entry), flush=True)
    (args.output / 'results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    # One fresh process per top-level module contains CLI stdout's SIGPIPE policy.
    # Runtime fixtures use /tmp; compiler output, caches and compiler tmp remain on the external disk.
if any(item['exit_code'] != 0 for item in results):
    raise SystemExit(1)
