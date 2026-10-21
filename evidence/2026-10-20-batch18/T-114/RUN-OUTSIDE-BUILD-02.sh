#!/bin/bash
# 由执行主控在沙箱外运行；不安装、不发布、不调用模型；启动构建产物并验证隔离进程退出。
set -euo pipefail
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
python3 - "$ROOT" "${1:-$(date -u +%Y%m%dT%H%M%SZ)}" <<'PY'
import datetime
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess
import sys

root = Path(sys.argv[1])
label = sys.argv[2]
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', label), 'Invalid run label'
assert platform.system() == 'Darwin' and platform.machine() == 'arm64'
slot = 't114-' + label
build = Path('/private/tmp') / ('a2a-build-' + slot)
proof = Path('/private/tmp') / ('t114-build-proof-' + label)
report = root / 'evidence/2026-10-20-batch18/T-114' / ('outside-build-' + label + '.json')
assert not build.exists() and not proof.exists() and not report.exists(), 'Use a new label; preserve earlier runs'
subprocess.run(['git', 'diff', '--quiet'], cwd=root, check=True)
subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=root, check=True)
proof.mkdir()
env = dict(os.environ)
env.update(TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp')
for key in ['ELECTRON_OVERRIDE_DIST_PATH', 'ELECTRON_RUN_AS_NODE', 'npm_config_cache', 'electron_config_cache']:
    env.pop(key, None)
record = {
    'task': 'T-114', 'attempt': 'a1', 'status': 'INCOMPLETE',
    'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source': str(root), 'proof': str(proof), 'build': str(build),
    'spec': '.project-map/tickets/T-114-enchanted-release-and-go-public.md (ready_rev=1)',
    'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'commands': [],
}

def run(argv, cwd=root, capture=False):
    record['commands'].append(argv)
    print('COMMAND:', json.dumps(argv), flush=True)
    result = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, timeout=1800)
    with (proof / 'commands.log').open('a', encoding='utf-8') as log:
        log.write(json.dumps(argv) + '\n' + result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'Exit {result.returncode}: {argv}; see {proof / "commands.log"}')
    return result.stdout if capture else None

try:
    record['node'] = run(['node', '--version'], capture=True).strip()
    record['npm'] = run(['npm', '--version'], capture=True).strip()
    # Install only in this worktree. Package:mac rebuilds the staged node-pty.
    run(['npm', 'ci', '--ignore-scripts', '--cache', str(proof / 'npm-cache')], cwd=root / 'workbench')
    stdout = run(['npm', 'run', 'package:mac', '--', '--slot', slot], cwd=root / 'workbench', capture=True)
    packaged = json.loads(stdout.strip().splitlines()[-1])
    app = build / 'Enchanted.app'
    assert Path(packaged['app']) == app and app.is_dir(), 'Unexpected output path'
    assert sorted(p.name for p in build.iterdir()) == ['Enchanted.app'], 'Intermediate build files remain'
    with (app / 'Contents/Info.plist').open('rb') as source:
        plist = plistlib.load(source)
    expected = {
        'CFBundleName': 'Enchanted', 'CFBundleDisplayName': 'Enchanted',
        'CFBundleIdentifier': 'org.a2a.workbench', 'CFBundleExecutable': 'Enchanted',
    }
    record['plist'] = {key: plist.get(key) for key in expected}
    assert record['plist'] == expected, record['plist']
    assert (app / 'Contents/MacOS/Enchanted').is_file()
    runtime = json.loads((app / 'Contents/Resources/app/package.json').read_text(encoding='utf-8'))
    assert runtime['name'] == 'a2a' and runtime['productName'] == 'Enchanted', runtime
    helpers = sorted((app / 'Contents/Frameworks').glob('* Helper*.app'))
    assert helpers, 'Missing helpers'
    for helper in helpers:
        with (helper / 'Contents/Info.plist').open('rb') as source:
            helper_plist = plistlib.load(source)
        assert helper.name.startswith('Enchanted Helper'), helper
        assert helper_plist['CFBundleExecutable'] == helper.stem, helper_plist
    record['helpers'] = [p.name for p in helpers]
    # The packaged copy must preserve the data-path code, apart from its error title.
    desktop = app / 'Contents/Resources/app/desktop.mjs'
    assert desktop.read_bytes() == (root / 'workbench/app/desktop.mjs').read_bytes()
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)])
    signed = subprocess.run(['/usr/bin/codesign', '-dv', '--verbose=2', str(app)], text=True, capture_output=True, check=True)
    assert 'Signature=adhoc' in signed.stderr, signed.stderr
    record['codesign'] = signed.stderr
    # Keep the app outside the build slot for the controller's install/release steps.
    artifact = proof / 'Enchanted.app'
    app.rename(artifact)
    record['artifact'] = str(artifact)
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(artifact)])
    run(['node', str(root / 'evidence/2026-10-20-batch18/T-114/check-packaged-start.mjs'), str(artifact), str(proof / 'startup.json')])
    record['startup'] = json.loads((proof / 'startup.json').read_text(encoding='utf-8'))
    assert record['startup']['status'] == 'PASS' and record['startup']['cleanup_complete']
    shutil.rmtree(build)
    shutil.rmtree(proof / 'npm-cache')
    record.update(status='PASS', artifact=str(artifact), build_removed=not build.exists(), package=packaged)
except BaseException as error:
    record['status'] = 'NO_GO'
    record['error'] = f'{type(error).__name__}: {error}'
    raise
finally:
    if (proof / 'startup.json').exists():
        record['startup'] = json.loads((proof / 'startup.json').read_text(encoding='utf-8'))
    record['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with report.open('x', encoding='utf-8') as target:
        json.dump(record, target, ensure_ascii=False, indent=2)
        target.write('\n')
    print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)
PY
