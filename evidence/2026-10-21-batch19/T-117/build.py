"""Build one committed candidate using the standard packager in a temporary copy."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

root = Path(__file__).resolve().parents[3]
label = sys.argv[1]
assert label.isalnum()
work = Path('/private/tmp') / ('t117-build-' + label)
work.mkdir()
source = work / 'source'
source.mkdir()
proof = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-21-batch19/T-117')
assert proof.is_dir() and proof.stat().st_dev != Path('/Volumes').stat().st_dev
report_path = proof / ('build-' + label + '.json')
assert not report_path.exists()
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
record = {'status': 'INCOMPLETE', 'revision': revision, 'source': str(source), 'commands': []}
env = dict(os.environ, TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp')
for key in ['ELECTRON_RUN_AS_NODE', 'ELECTRON_OVERRIDE_DIST_PATH', 'NODE_OPTIONS', 'NODE_PATH']:
    env.pop(key, None)
try:
    with (work / 'source.tar').open('wb') as target:
        subprocess.run(['git', 'archive', revision, 'workbench', 'docs'], cwd=root, stdout=target, check=True)
    with tarfile.open(work / 'source.tar') as archive:
        assert all(not member.name.startswith('/') and '..' not in Path(member.name).parts for member in archive)
        archive.extractall(source)
    for argv in [
        ['npm', 'ci', '--ignore-scripts', '--cache', str(work / 'npm-cache')],
        ['npm', 'run', 'package:mac', '--', '--slot', 't117-' + label],
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
