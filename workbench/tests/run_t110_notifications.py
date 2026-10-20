"""Private copies + real installed Claude/local fake API + Electron. Python 3.9.

The red candidate removes only the visible notification list. The same native
entry and business assertion must reject it, then accept the unchanged candidate.
No model/vendor calls, screenshots, shared output links or global configuration.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--summary', type=Path, required=True)
    p.add_argument('--electron-dist', type=Path, required=True)
    args = p.parse_args()
    source = Path(__file__).resolve().parents[2]
    output = args.summary.resolve()
    assert not output.exists(), 'Use a fresh summary path'
    root = Path(tempfile.mkdtemp(prefix='t110-native-', dir='/private/tmp')).resolve()
    env = dict(os.environ, LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE'):
        env.pop(key, None)
    report = dict(status='INCOMPLETE', task='T-110', attempt='a1', fixture=str(root), commands=[],
                  model_calls=0, vendor_calls=0, screenshots=[], runs=[])
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, env=env, text=True).strip()
        report['source_head'] = revision
        report['source_changes'] = subprocess.check_output(['git', 'status', '--short'], cwd=source, env=env, text=True).splitlines()
        copy = root / 'candidate'
        copy.mkdir()
        shutil.copytree(source / 'workbench', copy / 'workbench', symlinks=False,
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__'))
        shutil.copytree(source / 'workbench/node_modules', copy / 'workbench/node_modules', symlinks=False)
        # Only this newly created, private test copy receives the executable bit.
        helper = copy / 'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
        helper.chmod(0o755)
        component = copy / 'workbench/app/AppNotifications.tsx'
        original = component.read_text(encoding='utf-8')
        marker = 'notices.map(notice =>'
        assert original.count(marker) == 1
        for label, disabled, mutant in [('red-hidden-notices', False, True), ('green', False, False), ('disabled', True, False)]:
            component.write_text(original.replace(marker, 'notices.slice(0, 0).map(notice =>') if mutant else original, encoding='utf-8')
            summary = root / (label + '.json')
            command = ['/usr/bin/python3', '-B', str(copy / 'workbench/tests/run_t108_native_e2e.py'),
                       '--summary', str(summary), '--electron-dist', str(args.electron_dist.resolve()),
                       '--source-revision', revision, '--notifications'] + (['--disable-notifications'] if disabled else [])
            with (root / (label + '.log')).open('x', encoding='utf-8') as log:
                result = subprocess.run(command, cwd=copy, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
            report['commands'].append(dict(argv=command, exit=result.returncode))
            value = json.loads(summary.read_text(encoding='utf-8'))
            report['runs'].append(dict(label=label, summary=str(summary), result=value))
            if mutant:
                assert result.returncode == 1 and value['status'] == 'INCOMPLETE'
                assert 'One in-app waiting-user notification' in value.get('error', ''), value
                assert not value.get('window_cleanup_error') and not value.get('daemon_cleanup_error') and not value.get('process_cleanup_errors'), value
                report['red_business_rejected'] = True
            else:
                assert result.returncode == 0 and value['status'] == 'PASS', value
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        # Dependencies are disposable build inputs in our private copy. Native
        # fixtures and every failure result remain for evidence archival.
        copied_dependencies = root / 'candidate/workbench/node_modules'
        if copied_dependencies.exists():
            try:
                shutil.rmtree(copied_dependencies)
            except OSError as error:
                report.update(status='INCOMPLETE', dependency_cleanup_error=str(error))
        with output.open('x', encoding='utf-8') as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write('\n')
        print(json.dumps(dict(status=report['status'], summary=str(output), error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
