#!/bin/zsh
set -u
# 在沙箱外执行；每次使用独立目录，保留所有失败现场。
task_root=${0:A:h:h:h:h}
cd "$task_root" || exit 1
task_output=$(mktemp -d "$task_root/evidence/2026-10-23-batch23/T-145-a2/outside01-XXXXXX") || exit 1
export PYTHONPYCACHEPREFIX=/private/tmp/t145-a2-pycache
python3 - "$task_root" "$task_output" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
import traceback

root, out = map(Path, sys.argv[1:])
test = root / 'workbench/tests/test_t145_mouse_reports_e2e.py'
manifest = dict(status='INCOMPLETE', task='T-145-2', attempt='a2', commands=[], checks=[],
                fixture_policy='保留 /private/tmp 中的运行夹具；由执行主控按 T-088 归档。')
try:
    manifest['candidate'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    (out / 'candidate.diff').write_text(subprocess.check_output(
        ['git', 'diff', '--', 'workbench/tests/test_t145_mouse_reports_e2e.py'], cwd=root, text=True), encoding='utf-8')
    for label, driver, options, expected in [
        ('t145-green', test, [], None),
        ('t145-red', test, ['--revision', 'f8aa84625'], 'mouse_focus_do_not_create_records'),
        ('t145-mutant-record', test, ['--mutant', 'record-reports'], 'mouse_focus_do_not_create_records'),
        ('t145-mutant-drop', test, ['--mutant', 'drop-reports'], '三次移动均到 PTY'),
        ('t139-t143-candidate', root / 'workbench/tests/test_t139_t143_views_perf_e2e.py', [], None),
        ('t133-t134-regression', root / 'workbench/tests/test_t133_t134_records_metrics_e2e.py', [], None),
    ]:
        summary = out / (label + '.json')
        command = list(map(str, ['python3', driver, '--summary', summary, *options]))
        entry = dict(label=label, argv=command, summary=str(summary))
        manifest['commands'].append(entry)
        # 独立运行各项，前项失败也保留其余检查的结果。
        with (out / (label + '.stdout.txt')).open('x', encoding='utf-8') as stdout, \
             (out / (label + '.stderr.txt')).open('x', encoding='utf-8') as stderr:
            result = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr)
        entry['exit_code'] = result.returncode
        if not summary.exists():
            entry.update(passed=False, error='未生成摘要；不能当作红态或变异证据')
            continue
        data = json.loads(summary.read_text(encoding='utf-8'))
        entry.update(status=data.get('status'), error=data.get('error'), fixture=data.get('fixture'))
        if expected:
            # 必须越过显示等待和坐标字节检查，排除观察器/注入失败冒充业务红态。
            required = ['receiver_native_identity_bound']
            if 'drop' not in label:
                required += ['motion_bytes_match_coordinates_exactly', 'cli_receives_only_complete_reports']
            entry['passed'] = (result.returncode != 0 and expected in data.get('error', '') and
                               all(name in data.get('checks', []) for name in required) and
                               data.get('cleanup_complete') is True)
        else:
            entry['passed'] = result.returncode == 0 and data.get('status') == 'PASS'
        manifest['checks'].append(dict(name=label, passed=entry['passed']))
    manifest['status'] = 'PASS' if all(row.get('passed') for row in manifest['commands']) else 'INCOMPLETE'
except Exception as error:
    manifest.update(error=str(error), traceback=traceback.format_exc())
finally:
    with (out / 'MANIFEST.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(manifest, ensure_ascii=False))
    print(out)
raise SystemExit(0 if manifest['status'] == 'PASS' else 1)
PY
