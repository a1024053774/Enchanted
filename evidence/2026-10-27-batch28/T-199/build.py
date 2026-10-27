"""Copied from evidence/2026-10-27-batch28/T-192/build.py (itself from T-190) to install the T-199 revision into /Applications; only the temp and proof paths differ.
Build the committed release revision with the standard packager in a temporary checkout on the internal disk."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
label = sys.argv[1]
assert label.isalnum()
work = Path('/private/tmp') / ('t199-install-build-' + label)
work.mkdir()
source = work / 'source'
source.mkdir()
proof = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-27-batch28/T-199')
assert proof.is_dir() and proof.stat().st_dev != Path('/Volumes').stat().st_dev
report_path = proof / ('build-' + label + '.json')
assert not report_path.exists()
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
record = {'status': 'INCOMPLETE', 'revision': revision, 'source': str(source),
          'source_scope': ['workbench'], 'commands': []}
env = dict(os.environ, TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp')
for key in ['ELECTRON_RUN_AS_NODE', 'ELECTRON_OVERRIDE_DIST_PATH', 'NODE_OPTIONS', 'NODE_PATH']:
    env.pop(key, None)
try:
    # package.mjs records the source revision (T-122), so the copy is a git checkout: a shallow clone of the
    # committed revision with only workbench checked out. r1 used git archive and stopped there.
    subprocess.run(['git', 'clone', '-q', '--depth', '1', '--no-checkout', '--branch', 'main', 'file://' + str(root), str(source)], check=True)
    subprocess.run(['git', '-C', str(source), 'sparse-checkout', 'set', 'workbench'], check=True)
    subprocess.run(['git', '-C', str(source), 'checkout', '-q', revision], check=True)
    for argv in [
        ['npm', 'ci', '--ignore-scripts', '--cache', str(work / 'npm-cache')],
        ['npm', 'run', 'package:mac', '--', '--slot', 't199install-' + label],
    ]:
        record['commands'].append(argv)
        result = subprocess.run(argv, cwd=source / 'workbench', env=env, capture_output=True, text=True)
        (proof / ('build-' + label + '-' + str(len(record['commands'])) + '.log')).write_text(
            result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'Command failed ({result.returncode}): {argv}')
    record['package'] = json.loads(result.stdout.strip().splitlines()[-1])
    record['status'] = 'PASS'
except BaseException as error:
    record['error'] = str(error)
    raise
finally:
    report_path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record), flush=True)
