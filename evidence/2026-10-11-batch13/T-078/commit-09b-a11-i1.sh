#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

base = Path('evidence/2026-10-11-batch13/T-078')
before = 'cbf75d61'
check_only = '--check-only' in sys.argv[1:]
allow = json.loads((base / '09b-a11-i1-allowlist.json').read_bytes())
future = {str(base / '09b-a11-i1-ownership-preflight-01.json')}


def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()


assert git('rev-parse', 'HEAD').startswith(before), git('rev-parse', 'HEAD')
assert not git('diff', '--cached', '--name-only')
rows = []
unowned = []
for item in subprocess.check_output(
        ['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all']).decode().split('\0'):
    if not item:
        continue
    path = item[3:]
    owner = next((entry for entry in allow if path == entry or path.startswith(entry + '/')), None)
    rows.append({'path': path, 'status': 'PASS' if owner else 'INCOMPLETE', 'allowlist_entry': owner})
    if owner is None:
        unowned.append(path)
assert not unowned, ('Unowned work; no mutation', unowned)
missing = [entry for entry in allow if entry not in future and not Path(entry).exists()]
assert not missing, ('Allowlist path missing before git add', missing)

p1 = base / '09b-a11-b1-ideation-p1-01'
input_data = json.loads((p1 / 'input.json').read_bytes())
launch_result = json.loads((base / '09b-a11-b1-ideation-01/result.json').read_bytes())
manifest = json.loads((p1 / '09b-a11-b1-ideation-01/process-manifest.json').read_bytes())
assert launch_result['status'] == 'PASS' and launch_result['spawned'] is True
assert launch_result['p1_spawned'] is True and launch_result['cli_spawned'] is True
assert launch_result['p1_result'].endswith('/09b-a11-b1-ideation-01/result.json')
assert manifest['launch'] == input_data['launch'] and manifest['session'] == input_data['session']
assert manifest['cli']['pid'] > 0 and manifest['shell_pid'] > 0
nested = json.loads((p1 / '09b-a11-b1-ideation-01/result.json').read_bytes())
assert nested['phase'] == 'launch' and nested['real_vendor_model_turns'] == 0

onboard = json.loads((base / '09b-a11-b1-onboard-materials-01/static-check.json').read_bytes())
assert onboard['status'] == 'PASS' and onboard['messages_expected'] == 0 and onboard['api_requests_expected'] == 0
assert onboard['screen_steps'] == 6 and onboard['screen_reads'] == 7 and onboard['keys_per_step'] == 1
commands = (base / '09b-a11-b1-onboard-materials-01/ONBOARD-COMMANDS.txt').read_text(encoding='utf-8')
assert commands.count('--phase screen') == 7 and commands.count('--phase key') == 6
assert '--launch-label 09b-a11-b1-ideation-01' in commands and 'security-notice-text.txt' in commands
assert '--purpose onboarding-notice' in commands and 'ideation-s7-Enter-02.json' in commands
assert 'a11-ideation-s9-screen-02' in commands and 'a11-ideation-s13-screen-02' in commands
assert (base / '09b-a11-b1-exec-approvals/ideation-s7-Enter-02.json').is_file()

i1 = base / '09b-a11-i1-materials-01'
i1_static = json.loads((i1 / 'static-check.json').read_bytes())
i1_approval = json.loads((i1 / 'approval.json').read_bytes())
assert i1_static['status'] == 'PASS' and i1_static['messages_expected'] == 2 and i1_static['permission_screens_expected'] == 1
assert i1_static['tool'] == 'I_SEND_STOP' and i1_static['launch_status'] == 'NO_GO'
assert i1_approval['approved_by'] is None and i1_approval['approval_ref'] is None
assert i1_approval['launch'] == input_data['launch'] and i1_approval['session'] == input_data['session']
assert i1_approval['target_binding']['attempt_id']
commands_i1 = (i1 / 'I1-COMMAND.txt').read_text(encoding='utf-8')
assert '--protocol' in commands_i1 and '--protocol-phase dispatch' in commands_i1
assert 'pane_output --launch' in commands_i1 and 't078_09b_i1_permission.py' in commands_i1
assert 'permission-approval.json' in commands_i1 and 'permission=True' in Path('workbench/tests/t078_09b_i1_permission.py').read_text(encoding='utf-8')
api_green = json.loads((i1 / 'api-green.json').read_bytes())
assert api_green['status'] == 'PASS' and api_green['I1']['messages_used'] == 2 and api_green['I1']['second']['settlement'] is True
for mutant in ['tool_id', 'entry_id', 'target', 'seq', 'role', 'text']:
    red = json.loads((i1 / f'api-red-{mutant}.json').read_bytes())
    assert red['status'] == 'PASS' and red['decision'] == '409'
assert json.loads((i1 / 'protocol-materials.json').read_bytes())['launch'] == 'NO_GO'
flow = json.loads((i1 / 'permission-oracle-green.json').read_bytes())
assert flow['status'] == 'PASS' and flow['messages'] == 2 and flow['enter_form'] == 'action'
for name in ['permission-red-early-enter.json', 'permission-red-screen-changed.json', 'permission-red-wrong-dispatch.json']:
    assert json.loads((i1 / name).read_bytes())['status'] == 'PASS'
for source in ['workbench/tests/t078_09b_i1_driver.py', 'workbench/tests/t078_09b_i1_permission.py', 'workbench/tests/test_t078_09b_i1_permission_flow.py']:
    assert Path(source).is_file()
subprocess.run(['git', 'diff', '--check'], check=True)

ownership = base / '09b-a11-i1-ownership-preflight-01.json'
if check_only:
    print(json.dumps({'status': 'PASS', 'mode': 'check-only', 'head': git('rev-parse', 'HEAD'),
                      'cached_paths': 0, 'checked_paths': len(rows), 'unowned': unowned,
                      'b1_result': str(base / '09b-a11-b1-ideation-01/result.json'),
                      'onboard': str(base / '09b-a11-b1-onboard-materials-01'),
                      'i1_materials': str(i1), 'launch': 'NO_GO'}, ensure_ascii=False))
    raise SystemExit(0)

ownership.write_text(json.dumps({'status': 'PASS', 'checked_paths': len(rows),
                                 'unowned': unowned, 'entries': rows}, ensure_ascii=False,
                                indent=2) + '\n', encoding='utf-8')
with (base / 'RESULTS.md').open('a', encoding='utf-8') as fh:
    fh.write('\n## A-11 ideation B1 onboarding and protocol I1 materials\n\n'
             'A-11 ideation B1 process launch PASS：实际 process manifest 保留于 `09b-a11-b1-ideation-p1-01/09b-a11-b1-ideation-01/`，真实 vendor model turns=0。onboarding 材料逐屏单键、security notice 原文、trust ArrowDown→Enter 和 0 Messages 断言已冻结；本轮未发 onboarding 按键。\n'
             'Protocol I1 材料绑定本次 launch/session/target binding，先由 dispatch phase 停在 PermissionRequest 并保存 screen.bin，再由独立 permission phase 通过 Electron window 入口核对完整 Bash 命令、一次性 Yes/Enter，随后完成 tool_result 第二条 Messages、实际 Stop/relay wake 独立读回；离线 shared-core green 与工具 ID/entry/target/seq/role/text、早按键/屏幕变化/错误 dispatch 反例随包保留。I1 approval 留空，executor B1 未启动，未发送 I1。\n')
paths = [
    base / '09b-a11-i1-allowlist.json', base / '09b-a11-b1-ideation-01',
    base / '09b-a11-b1-ideation-p1-01/09b-a11-b1-ideation-01',
    base / '09b-a11-b1-onboard-materials-01', base / 'a11-i1-prompt.txt',
    base / '09b-a11-i1-materials-01', base / '09b-a11-i1-permission-oracle-01',
    base / '09b-a11-i1-permission-early-enter-red-01', base / '09b-a11-i1-permission-screen-changed-red-01',
    base / '09b-a11-i1-permission-wrong-dispatch-red-01', base / '09b-a11-i1-ownership-preflight-01.json',
    base / 'commit-09b-a11-i1.sh', base / 'RESULTS.md',
    Path('workbench/tests/t078_09b_i1_driver.py'), Path('workbench/tests/t078_09b_i1_permission.py'),
    Path('workbench/tests/test_t078_09b_i1_permission_flow.py'),
]
subprocess.run(['git', 'add', '--', *map(str, paths)], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze A11 onboarding and protocol I1 materials'], check=True)
assert not git('status', '--porcelain')
print(json.dumps({'status': 'PASS', 'commit': git('rev-parse', 'HEAD'), 'launch': 'NO_GO'}, ensure_ascii=False))
PY
