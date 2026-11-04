"""Copied from evidence/2026-10-26-batch27/T-188/build.py for 0.1.6 (T-248). Differences: temp path, the summary goes to
this directory (2026-11-01 rule: no WD archive), command logs stay in the temporary work directory, and the pinned hc
archive is read from the existing cache (installHc still checks its SHA-256).
Build the committed release revision with the standard packager in a temporary checkout on the internal disk."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
label = sys.argv[1]
assert label.isalnum()
work = Path('/private/tmp') / ('release016-build-' + label)
work.mkdir()
source = work / 'source'
source.mkdir()
proof = Path(__file__).resolve().parent
report_path = proof / ('build-' + label + '.json')
assert not report_path.exists()
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
record = {'status': 'INCOMPLETE', 'revision': revision, 'source': str(source),
          'source_scope': ['workbench'], 'commands': [], 'logs': str(work)}
env = dict(os.environ, TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp',
           ENCHANTED_HC_CACHE_DIR=str(root.parent / 'hc-cache'))
for key in ['ELECTRON_RUN_AS_NODE', 'ELECTRON_OVERRIDE_DIST_PATH', 'NODE_OPTIONS', 'NODE_PATH']:
    env.pop(key, None)
try:
    subprocess.run(['git', 'clone', '-q', '--depth', '1', '--no-checkout', '--branch', 'main', 'file://' + str(root), str(source)], check=True)
    subprocess.run(['git', '-C', str(source), 'sparse-checkout', 'set', 'workbench'], check=True)
    subprocess.run(['git', '-C', str(source), 'checkout', '-q', revision], check=True)
    for argv in [
        ['npm', 'ci', '--ignore-scripts', '--cache', str(work / 'npm-cache')],
        ['npm', 'run', 'package:mac', '--', '--slot', 'release016-' + label],
    ]:
        record['commands'].append(argv)
        result = subprocess.run(argv, cwd=source / 'workbench', env=env, capture_output=True, text=True)
        (work / ('build-' + str(len(record['commands'])) + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
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
