#!/bin/zsh
set -u
cd "${0:A:h}/../../.." || exit 1
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path.cwd()
out = root / 'evidence/2026-10-23-batch23/T-140' / ('outside-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
out.mkdir()
cases = [
    ('driver-red', 'workbench/tests/test_t140_scripted_plan.py', ['--revision', 'f41503eab'], 'unknown working directory'),
    ('driver-green', 'workbench/tests/test_t140_scripted_plan.py', [], None),
    ('red', 'workbench/tests/test_t140_extra_dirs_e2e.py', ['--revision', 'ebbae7bd0'], 'Edit Project menu'),
    ('green', 'workbench/tests/test_t140_extra_dirs_e2e.py', [], None),
    ('mutant-shell', 'workbench/tests/test_t140_extra_dirs_e2e.py', ['--mutant', 'claude-without-shell-write'], 'T-C_shell_boundary'),
    ('mutant-remove', 'workbench/tests/test_t140_extra_dirs_e2e.py', ['--mutant', 'removed-directory-retained'], 'T-RC_shell_boundary'),
    ('regression-t131', 'workbench/tests/test_t131_parallel_workers_e2e.py', [], None),
    ('regression-t137', 'workbench/tests/test_t137_reflect_e2e.py', [], None),
    ('regression-t127', 'workbench/tests/test_t127_codex_home_e2e.py', [], None),
]
results = []
for name, test, extra, expected_failure in cases:
    summary = out / (name + '.json')
    command = ['python3', test, '--summary', str(summary), *extra]
    with (out / (name + '.log')).open('x', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    data = json.loads(summary.read_text(encoding='utf-8')) if summary.exists() else {}
    accepted = (result.returncode != 0 and expected_failure in data.get('error', '')) if expected_failure else result.returncode == 0 and data.get('status') == 'PASS'
    row = dict(name=name, command=command, exit_code=result.returncode, expected_failure=expected_failure,
               status='PASS' if accepted else 'INCOMPLETE', summary=str(summary), error=data.get('error'))
    results.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
    # Screenshots are small deliverable artifacts; the original run/fixture is left for controller archival.
    fixture = Path(data['fixture']) if data.get('fixture') else None
    if fixture and (fixture / 'out').is_dir():
        for screenshot in (fixture / 'out').glob('*.png'):
            shutil.copy2(screenshot, out / (name + '-' + screenshot.name))
result = dict(status='PASS' if all(row['status'] == 'PASS' for row in results) else 'INCOMPLETE', results=results)
(out / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(str(out / 'run.json'), flush=True)
sys.exit(0 if result['status'] == 'PASS' else 1)
PY
