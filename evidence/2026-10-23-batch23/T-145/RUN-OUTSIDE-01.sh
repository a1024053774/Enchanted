#!/bin/zsh
set -u
# Full run: ./evidence/2026-10-23-batch23/T-145/RUN-OUTSIDE-01.sh
# Bounded local checks only: same command with --bounded (no GUI/daemon/socket).
task_root=${0:A:h:h:h:h}
cd "$task_root" || exit 1
task_output=$(mktemp -d "$task_root/evidence/2026-10-23-batch23/T-145/run-XXXXXX") || exit 1
export PYTHONPYCACHEPREFIX=/private/tmp/t145-pycache
python3 - "$task_root" "$task_output" "${1:-full}" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

root, out, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(root / 'workbench/tests'))
from scripted_claude import source_tree

baseline = 'f8aa846252ddd97008a5e506469ce30024aaacab'
manifest = dict(status='INCOMPLETE', mode=mode, commands=[], checks=[],
                fixture_policy='Temporary source/receiver/runtime evidence retained in /private/tmp; controller archives per T-088')

def run(label, argv, summary, timeout=1200):
    command = list(map(str, argv))
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout)
    (out / (label + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (out / (label + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    manifest['commands'].append(dict(label=label, argv=command, exit_code=result.returncode, summary=str(summary)))
    assert summary.exists(), f'{label}: no summary; inspect stdout/stderr (setup failure is not red evidence)'
    data = json.loads(summary.read_text(encoding='utf-8'))
    return result.returncode, data

def check(name, condition, detail):
    assert condition, f'{name}: {detail}'
    manifest['checks'].append(name)

try:
    manifest['candidate'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    (out / 'candidate.diff').write_text(subprocess.check_output(['git', 'diff', '--', 'workbench/src/panes.ts'], cwd=root, text=True), encoding='utf-8')
    temp = Path(tempfile.mkdtemp(prefix='t145-sources-', dir='/private/tmp'))
    manifest['source_fixtures'] = str(temp)
    old = source_tree(temp / 'baseline', revision=baseline)
    node_test = root / 'workbench/tests/test_t145_protocol_input.mjs'
    summary = out / 'protocol-green.json'
    rc, data = run('protocol-green', ['node', node_test, summary], summary)
    check('bounded_protocol_green', rc == 0 and data['status'] == 'PASS', data)
    summary = out / 'protocol-red.json'
    rc, data = run('protocol-red', ['node', node_test, summary, old], summary)
    check('bounded_baseline_rejected_for_recording_mouse', rc != 0 and 'terminal report must not become user input' in data.get('error', ''), data)
    for name, old_text, new_text, expected in [
        ('record-reports', 'if (!protocolReport) await record(text, control);', 'await record(text, control);', 'terminal report must not become user input'),
        ('drop-reports', 'pane.pty.write(binary ? bytes : data);', 'if (!protocolReport) pane.pty.write(binary ? bytes : data);', 'report bytes must reach PTY unchanged'),
    ]:
        source = source_tree(temp / name, patches=[('src/panes.ts', old_text, new_text)])
        summary = out / ('protocol-mutant-' + name + '.json')
        rc, data = run('protocol-mutant-' + name, ['node', node_test, summary, source], summary)
        check('bounded_mutant_' + name + '_rejected', rc != 0 and expected in data.get('error', ''), data)

    ipc = root / 'workbench/tests/test_t091_pane_ipc.mjs'
    old_summary, new_summary = out / 't091-baseline.json', out / 't091-candidate.json'
    old_rc, old_data = run('t091-baseline', ['node', '--experimental-vm-modules', ipc, old_summary, '--source', old], old_summary)
    new_rc, new_data = run('t091-candidate', ['node', '--experimental-vm-modules', ipc, new_summary], new_summary)
    check('t091_matches_baseline_without_worsening', old_rc == new_rc and old_data.get('status') == new_data.get('status') and
          old_data.get('error') == new_data.get('error') and old_data.get('checks') == new_data.get('checks'),
          dict(baseline=old_data, candidate=new_data))

    if mode != '--bounded':
        test = root / 'workbench/tests/test_t145_mouse_reports_e2e.py'
        for label, options, expected in [
            ('electron-red', ['--revision', baseline], 'mouse_focus_do_not_create_records'),
            ('electron-green', [], None),
            ('electron-mutant-record', ['--mutant', 'record-reports'], 'mouse_focus_do_not_create_records'),
            ('electron-mutant-drop', ['--mutant', 'drop-reports'], '三次移动均到 PTY'),
        ]:
            summary = out / (label + '.json')
            rc, data = run(label, ['python3', test, '--summary', summary, *options], summary)
            if expected:
                check(label + '_expected_contract_failure', rc != 0 and expected in data.get('error', ''), data)
            else:
                check(label + '_all_conditions', rc == 0 and data['status'] == 'PASS', data)
        summary = out / 't133-t134-regression.json'
        rc, data = run('t133-t134-regression', ['python3', root / 'workbench/tests/test_t133_t134_records_metrics_e2e.py', '--summary', summary], summary, timeout=2400)
        check('t133_t134_regression', rc == 0 and data['status'] == 'PASS', data)
        manifest['status'] = 'PASS'
    else:
        manifest['status'] = 'INCOMPLETE'
        manifest['bounded_checks'] = 'PASS'
        manifest['remaining'] = '真实 Electron 红/绿/变异与 T-133/T-134 回归；请在沙箱外不带 --bounded 运行本脚本'
except Exception as error:
    manifest.update(error=str(error), traceback=traceback.format_exc())
finally:
    with (out / 'MANIFEST.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(manifest, ensure_ascii=False))
    print(out)
raise SystemExit(0 if manifest['status'] == 'PASS' or manifest.get('bounded_checks') == 'PASS' else 1)
PY
