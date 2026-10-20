"""Merge main on exec/t112, install the reviewed three-file resolution, commit.
Shared-worktree invocation is run by the controller outside the worker sandbox.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import traceback

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
source, summary = args.source.resolve(), args.summary.resolve()
assert not summary.exists(), 'Preserve previous results'
inputs = source / 'evidence/2026-10-20-batch18/T-112/merge-main-resolutions-13'
manifest = json.loads((inputs / 'manifest.json').read_text())
env = {key: value for key, value in os.environ.items()
       if key not in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE')}
env['LC_ALL'] = 'C'
report = dict(status='INCOMPLETE', source=str(source), tested_parents=manifest, commands=[])
def git(*argv, exits=(0,)):
    command = ['git', *argv]
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True)
    report['commands'].append(dict(argv=command, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
    assert result.returncode in exits, report['commands'][-1]
    return result.stdout.strip()
try:
    assert git('branch', '--show-current') == 'exec/t112'
    assert git('rev-parse', 'HEAD') == manifest['ours'], 'Branch moved since resolution was tested'
    git('rev-parse', '--quiet', '--verify', 'MERGE_HEAD', exits=(1,))
    git('diff', '--quiet', '--cached')
    git('diff', '--quiet', '--', 'workbench', 'scripts/launch-worker')
    git('merge-base', '--is-ancestor', manifest['main'], 'main')
    # New main documentation may advance; production/test changes need a new resolution.
    git('diff', '--quiet', manifest['main'], 'main', '--', 'workbench', 'scripts/launch-worker')
    report['main'] = git('rev-parse', 'main')
    git('merge', '--no-commit', '--no-ff', 'main', exits=(1,))
    assert git('diff', '--name-only', '--diff-filter=U').splitlines() == manifest['conflicts'], 'Unexpected merge conflicts; leave state for inspection'
    for name in manifest['conflicts']:
        content = (inputs / name).read_bytes()
        assert not any(marker in content for marker in (b'<<<<<<<', b'=======', b'>>>>>>>'))
        (source / name).write_bytes(content)
    git('add', '--sparse', '--', *manifest['conflicts'], 'evidence/2026-10-20-batch18/T-112')
    assert not git('diff', '--name-only', '--diff-filter=U')
    git('diff', '--check', '--cached')
    git('commit', '-m', 'Merge main into exec/t112; 保留应用内通知与执行设置')
    report['commit'] = git('rev-parse', 'HEAD')
    report['parents'] = git('show', '-s', '--format=%P', 'HEAD').split()
    assert report['parents'] == [manifest['ours'], report['main']]
    report['status'] = 'PASS'
except Exception as error:
    report.update(error=str(error), traceback=traceback.format_exc())
finally:
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], commit=report.get('commit'), error=report.get('error')), ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
