#!/usr/bin/env python3
"""Replay the final contract against the frozen review-05 candidate. No models or Git writes."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

source = Path(__file__).resolve().parents[3]
output = Path(sys.argv[1]).resolve()
assert not output.exists()
revision = 'f533fd16e608cb73f666246700206fe28e21503c'
env = dict(os.environ, LC_ALL='C')
for name in ('GIT_DIR', 'GIT_WORK_TREE'):
    env.pop(name, None)
root = Path(tempfile.mkdtemp(prefix='t108-review05-red-replay-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', revision=revision, fixture=str(root), model_calls=0, vendor_calls=0)
try:
    archive = subprocess.check_output(['git', 'archive', '--format=zip', revision, 'workbench/src', 'workbench/app/main.ts'], cwd=source, env=env)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        for member in bundle.infolist():
            path = root / member.filename
            assert root in path.resolve().parents and not member.filename.startswith('/')
            assert (member.external_attr >> 16) & 0o170000 != 0o120000
            if member.is_dir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(bundle.read(member))
    workbench = root / 'workbench'
    shutil.copytree(source / 'workbench/node_modules', workbench / 'node_modules', symlinks=False)
    (workbench / 'tests').mkdir()
    for name in ('test_t108_questions.mjs', 't108_hook_failure_contracts.mjs', 't108_answer_lifecycle_contracts.mjs',
                 'test_t108_driver.mjs', 't108_questions_driver.mjs', 't108_answer_receipt.mjs'):
        shutil.copy2(source / 'workbench/tests' / name, workbench / 'tests' / name)
    command = ['node', str(workbench / 'tests/test_t108_questions.mjs'), str(root / 'red.json')]
    with (root / 'red.log').open('x', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
    observed = json.loads((root / 'red.json').read_text(encoding='utf-8'))
    assert all(case['status'] == 'PASS' for case in observed['failure_cases'])
    cases = observed['answer_lifecycle_cases']
    failures = [case for case in cases if case['status'] != 'PASS']
    assert result.returncode == 1 and failures
    focused = [case for case in cases if case['name'] in ('early', 'early_stop', 'recorder_refused')]
    assert len(focused) == 3
    for case in focused:
        assert case['status'] != 'PASS' and case.get('error', '').startswith('AssertionError')
        if case['name'] != 'recorder_refused':
            assert case['operation_error'] == 'Error: question_input_changed'
            assert case['answer_keys'] == ['\x1b[B', '\r']
        else:
            assert case['operation_error'] == 'Error: Recorder refused before writing'
            assert case['answer_keys'] == []
        assert case.get('next_error') == case['operation_error']
        assert case['all_keys'] == case['answer_keys']
    driver_command = ['node', str(workbench / 'tests/test_t108_driver.mjs'), str(root / 'driver.json')]
    with (root / 'driver-red.log').open('x', encoding='utf-8') as log:
        driver = subprocess.run(driver_command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
    driver_log = (root / 'driver-red.log').read_text(encoding='utf-8')
    assert driver.returncode == 1 and 'A refused renderer command cannot poison the next request' in driver_log
    assert "'Error: Identity revoked'" in driver_log
    report.update(status='PASS', meaning='Known-bad early answer and poisoned stream rejected by business assertions; not product acceptance',
                  command=command, exit_code=result.returncode, prior_hook_cases=len(observed['failure_cases']),
                  lifecycle_cases=len(cases), focused=focused, driver_command=driver_command, driver_exit_code=driver.returncode)
except Exception as error:
    report['error'] = repr(error)
finally:
    with output.open('x', encoding='utf-8') as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write('\n')
print(json.dumps(report, ensure_ascii=False))
sys.exit(0 if report['status'] == 'PASS' else 1)
