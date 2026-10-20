#!/usr/bin/env python3
"""Replay the final contract against the frozen review-04 candidate. No models or Git writes."""
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
revision = 'f3a4a5416213e912076437cfd8ce6f69a0e3091f'
env = dict(os.environ, LC_ALL='C')
for name in ('GIT_DIR', 'GIT_WORK_TREE'):
    env.pop(name, None)
root = Path(tempfile.mkdtemp(prefix='t108-review04-red-replay-', dir='/private/tmp'))
report = dict(status='INCOMPLETE', revision=revision, fixture=str(root), model_calls=0, vendor_calls=0)
try:
    archive = subprocess.check_output(['git', 'archive', '--format=zip', revision, 'workbench/src'], cwd=source, env=env)
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
    for name in ('test_t108_questions.mjs', 't108_hook_failure_contracts.mjs'):
        shutil.copy2(source / 'workbench/tests' / name, workbench / 'tests' / name)
    command = ['node', str(workbench / 'tests/test_t108_questions.mjs'), str(root / 'red.json')]
    with (root / 'red.log').open('x', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
    observed = json.loads((root / 'red.json').read_text(encoding='utf-8'))
    failures = [case for case in observed['failure_cases'] if case['status'] != 'PASS']
    assert result.returncode == 1 and failures
    assert all(case.get('error', '').startswith('AssertionError') for case in failures)
    expected = ['permission_self_no_content', 'permission_forged_command_current',
                'permission_forged_command_after_bash_current', 'permission_forged_copied_id_command_current',
                'permission_forged_copied_id_empty_current', 'permission_forged_matching_questions_command_current',
                'permission_forged_matching_questions_other_parameter_current',
                'permission_forged_unknown_question_field_current', 'permission_forged_unknown_option_field_current']
    assert all(any(case['name'] == name and case.get('observed') == 'waiting_user_answer' for case in failures) for name in expected)
    report.update(status='PASS', meaning='Known-bad product rejected by business assertions; this is red-state proof, not product acceptance',
                  command=command, exit_code=result.returncode, cases=len(observed['failure_cases']), rejected=len(failures),
                  focused=[dict(name=c['name'], observed=c.get('observed'), error=c['error']) for c in failures if c['name'] in expected])
except Exception as error:
    report['error'] = repr(error)
finally:
    with output.open('x', encoding='utf-8') as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write('\n')
print(json.dumps(report, ensure_ascii=False))
sys.exit(0 if report['status'] == 'PASS' else 1)
