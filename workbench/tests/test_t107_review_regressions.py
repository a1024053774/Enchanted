"""Replay F1/F2 against the frozen bad candidate and reject F3 on fixed code."""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--summary', type=Path, required=True)
args = parser.parse_args()
source, output = args.source.resolve(), args.summary.resolve()
assert not output.exists()
root = Path(tempfile.mkdtemp(prefix='t107-review-fixes-', dir='/private/tmp'))
env = dict(os.environ, LC_ALL='C', PYTHONDONTWRITEBYTECODE='1')
revision = '3c3f2e9e189ddf37eeec4091266c8701a2dde33f'
report = dict(status='INCOMPLETE', baseline=revision, source=str(source), root=str(root), model_calls=0, cases=[])


def run(name, command, expected_error=None, escaped_old_oracle=False):
    result_path = root / (name + '.json')
    command = [str(value).replace('REPORT', str(result_path)) for value in command]
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=60)
    (root / (name + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (root / (name + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    observed = json.loads(result_path.read_text(encoding='utf-8'))
    passed = result.returncode == 0 and observed['status'] == 'PASS'
    if expected_error:
        passed = result.returncode == 1 and expected_error in observed.get('error', '') and observed.get('cleanup_complete', True)
    report['cases'].append(dict(name=name, command=command, exit=result.returncode, expected_error=expected_error,
                                pass_evidence=bool(passed), escaped_old_oracle=escaped_old_oracle, observed=observed))
    assert passed, (name, observed)


try:
    baseline = root / 'baseline'
    baseline.mkdir()
    archive = subprocess.check_output(['git', 'archive', revision, 'workbench'], cwd=source)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(baseline)
    daemon_test = source / 'workbench/tests/test_t107_daemon_readonly.mjs'
    for mode, failure in [('identity', 'Auxiliary native start must not release the root question'),
                          ('readonly', 'Sidebar read changed persisted tables or traces')]:
        run('old-' + mode, ['node', '--experimental-vm-modules', daemon_test, 'REPORT', baseline, mode], failure)
        run('fixed-' + mode, ['node', '--experimental-vm-modules', daemon_test, 'REPORT', source, mode])
    mutant = root / 'write-mutant'
    shutil.copytree(source / 'workbench/src', mutant / 'workbench/src')
    module = mutant / 'workbench/src/sidebar.ts'
    text = module.read_text(encoding='utf-8')
    marker = '  const launches = store.launches()'
    assert text.count(marker) == 1
    module.write_text(text.replace(marker, "  store.event('sidebar_read', { source: 'sidebar' });\n" + marker), encoding='utf-8')
    # The original implementation plus this one fault must still pass its
    # original oracle; newer identity requirements must not mask that escape.
    old_module = root / 'old-write-sidebar.ts'
    old_text = (baseline / 'workbench/src/sidebar.ts').read_text(encoding='utf-8')
    assert old_text.count(marker) == 1
    old_module.write_text(old_text.replace(marker, "  store.event('sidebar_read', { source: 'sidebar' });\n" + marker), encoding='utf-8')
    run('old-oracle-write-escaped', ['node', baseline / 'workbench/tests/test_t107_sidebar.mjs', 'REPORT', old_module], escaped_old_oracle=True)
    run('new-oracle-write-rejected', ['node', source / 'workbench/tests/test_t107_sidebar.mjs', 'REPORT', module],
        'Sidebar read changed persisted tables or traces')
    run('daemon-write-rejected', ['node', '--experimental-vm-modules', daemon_test, 'REPORT', mutant, 'readonly'],
        'Sidebar read changed persisted tables or traces')
    run('fixed-projection', ['node', source / 'workbench/tests/test_t107_sidebar.mjs', 'REPORT'])
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = repr(error)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status=report['status'], root=str(root), cases=[dict(name=row['name'], exit=row['exit'], pass_evidence=row['pass_evidence']) for row in report['cases']]), ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
