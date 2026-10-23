#!/bin/zsh
# 主控显式传入本轮真实 Codex 运行与 hook 授权文件；不自动重跑。
# 每场最多 worker 2 回合、reviewer 2 回合，两场总预留上限 8 回合。
# 用法：zsh RUN-OUTSIDE-03.sh /绝对路径/本轮授权.md
set -u
script_dir="${0:A:h}"
root="${script_dir:h:h:h}"
authorization="${1:?请传入本轮真实 Codex 回合和启动参数 hook 的授权文件}"
cd "$root" || exit 2
out="$(mktemp -d "$script_dir/outside-03-XXXXXXXX")" || exit 2
python3 -B - "$root" "$out" "$authorization" <<'PY'
import json
from pathlib import Path
import subprocess
import sys

root, out, authorization = map(Path, sys.argv[1:])
authorization = authorization.resolve()
if not authorization.is_file():
    raise SystemExit('授权文件不存在；未启动 CLI')
runner = root / 'workbench/tests/run_worker_delivery.py'
rows = []

def run(name, argv):
    with (out / (name + '.stdout.txt')).open('x', encoding='utf-8') as stdout, \
         (out / (name + '.stderr.txt')).open('x', encoding='utf-8') as stderr:
        p = subprocess.run(list(map(str, argv)), cwd=root, stdout=stdout, stderr=stderr)
    row = {'name': name, 'argv': list(map(str, argv)), 'exit': p.returncode}
    rows.append(row)
    with (out / 'commands.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    return row

base = [sys.executable, '-B', runner, '--turn-authorization', authorization]
# 同一个入口先完成零模型注册检查；失败即停止，不耗费真实模型预算。
registration = run('registration', [*base, '--setup-only', '--summary', out / 'registration.json'])
registered = json.loads((out / 'registration.json').read_text(encoding='utf-8')) if (out / 'registration.json').exists() else {}
if registration['exit'] != 0 or registered.get('status') != 'PASS' or registered.get('registered_task') != 'B-fixture+T-153-1':
    with (out / 'summary.json').open('x', encoding='utf-8') as stream:
        json.dump({'status': 'INCOMPLETE', 'phase': 'registration', 'real_model_turns': 0, 'commands': rows}, stream, ensure_ascii=False, indent=2)
    raise SystemExit('注册检查未通过；未启动真实模型回合')
# 先跑真实原生 CLI 的反事实；启动或超时不算红态。
red = run('repeat-feedback', [*base, '--mutant', 'repeat-feedback', '--summary', out / 'repeat-feedback.json'])
green = run('green', [*base, '--summary', out / 'green.json'])
red_value = json.loads((out / 'repeat-feedback.json').read_text(encoding='utf-8')) if (out / 'repeat-feedback.json').exists() else {}
green_value = json.loads((out / 'green.json').read_text(encoding='utf-8')) if (out / 'green.json').exists() else {}
red_ok = (red['exit'] == 1 and red_value.get('status') == 'NO_GO'
          and red_value.get('outcome') == 'contract_failure'
          and red_value.get('failure_id') == 'STOP-BATCH-ONE-NOTICE'
          and red_value.get('observed_main_turns') == 2 and red_value.get('isolated_home_removed') is True)
green_ok = green['exit'] == 0 and green_value.get('status') == 'PASS' and green_value.get('isolated_home_removed') is True
counted = run('turn-count', [sys.executable, '-B', root / 'evidence/2026-10-23-batch23/T-153/COUNT-OUTSIDE-02.py', '--run', out, '--summary', out / 'turn-count.json'])

# 相关已有回归：CLI 文件转交、relay 去重与拒绝、真实 Git hook 的原生回合事实。
# 原始 sqlite/夹具目录不进仓库；主控统一按 T-088 归档。
import tempfile
raw = Path(tempfile.mkdtemp(prefix='t153-regressions-', dir='/tmp'))
regressions = [
    run('relay-cli', [sys.executable, '-B', root / 'workbench/tests/test_relay_cli.py', '--output', raw / 'relay-cli']),
    run('relay-core', ['node', root / 'workbench/tests/test_relay_core.ts', raw / 'relay-core']),
    run('hook-turn-facts', [sys.executable, '-B', root / 'workbench/tests/test_hook_turn_facts.py', '--source', root, '--output', raw / 'hook-turn-facts']),
]
passed = red_ok and green_ok and counted['exit'] == 0 and all(row['exit'] == 0 for row in regressions)
summary = {'status': 'PASS' if passed else 'INCOMPLETE', 'green': green_ok, 'retained_check_red': red_ok,
           'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
           'authorization': str(authorization), 'maximum_real_turns_reserved': 8,
           'regression_artifacts': str(raw), 'commands': rows,
           'registration': True, 'turn_count': str(out / 'turn-count.json'),
           'raw_artifacts_to_archive': [value.get('fixture') for value in (registered, red_value, green_value) if value.get('fixture')]}
with (out / 'summary.json').open('x', encoding='utf-8') as stream:
    json.dump(summary, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'status': summary['status'], 'summary': str(out / 'summary.json')}, ensure_ascii=False))
raise SystemExit(0 if passed else 1)
PY
