#!/bin/bash
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t103
summary=${1:?传入本轮通过的 run-*-summary.json 路径}
contracts=${2:?传入本轮通过的 contracts-*-summary.json 路径}
test "$(git branch --show-current)" = exec/t103
test "$(git rev-parse HEAD)" = cc18d93dbbcf2ee641dc92befe68e5b0609b4807
/usr/bin/python3 -B - "$summary" "$contracts" <<'PY'
import json, subprocess, sys
from pathlib import Path
value=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert value['status']=='PASS', '真实验证未通过，停止提交'
assert value['source_files'], '缺少运行时源码快照'
archive=Path(value['archive'])/'source-snapshot'
for name in value['source_files']:
    assert Path(name).read_bytes()==(archive/name).read_bytes(), '源码与通过候选不符：'+name
print('通过候选源码逐字节核对完成')
contracts=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
assert contracts['status']=='PASS', '两处扩充合同尚未通过，停止提交'
assert contracts['accepted_e2e_archive']==value['archive'], '合同验证与已通过真实旅程不匹配'
assert len(contracts['checks'])==4 and all(check['status']=='PASS' for check in contracts['checks'])
assert contracts['source_files'], '缺少合同测试源码快照'
for name in contracts['source_files']:
    # 主控 #17 授权只修提交脚本；产品、测试及其余脚本仍逐字节核对。
    # 旧提交脚本不是产品／测试输入，原副本与修订说明保留在证据中。
    if name=='evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-03-COMMIT.sh':
        continue
    assert Path(name).read_bytes()==(Path(contracts['archive'])/'source-snapshot'/name).read_bytes(), '合同源码与通过候选不符：'+name
print('基线、候选与变异合同证据及源码核对完成')
allowed=set(value['source_files']) | set(contracts['source_files'])
staged=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode('utf-8').split('\0')
for name in filter(None, staged):
    assert name in allowed or name.startswith('evidence/2026-10-19-batch17/T-103/'), '暂存区有本票范围外文件：'+name
    assert Path(name).read_bytes()==subprocess.check_output(['git','show',':'+name]), '暂存内容与工作区不一致：'+name
print('已保留并核对本票暂存内容；不清空暂存区')
PY
# 复现该 worker 已有的逐会话 hook 环境；由原 hook 自动写尾注。
export A2A_PROJECT=a2a A2A_TASK=T-103 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=4ff6af88-2671-4679-929b-3600d21a4f61
export A2A_LAUNCH=launch-e2e8f3f912194346bc6568291e17e048
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a1527f-d852-78b2-a13b-c5e266daeb0d
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
git add --sparse workbench/README.md workbench/app/main.ts workbench/app/preload.ts \
  workbench/app/renderer.tsx workbench/app/start.mjs workbench/app/style.css \
  workbench/src/daemon.ts workbench/src/gates/cli.ts workbench/src/gates/core.ts \
  workbench/tests/run_t103_picker.py workbench/tests/t103_picker_driver.mjs workbench/tests/test_t103_driver_startup.mjs \
  workbench/tests/test_t103_keyboard_entry.mjs \
  workbench/tests/test_t091_pane_ipc.mjs workbench/tests/test_electron_e2e.py \
  evidence/2026-10-19-batch17/T-103
git diff --cached --check
git commit -m '工作台支持选择现有项目与任务' \
  -m "真实旅程证据：$summary" \
  -m "基线、候选及变异合同证据：$contracts"
git show -s --format=full HEAD
