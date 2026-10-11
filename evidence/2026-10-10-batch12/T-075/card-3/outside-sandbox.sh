#!/bin/zsh
# 决定 05 / 主控31：B 修复后复验一次，一个交付回合 + 一个回执回合，累计最多7/10。
# 用户原话与来源见 feedback-turn-authorization-05.md。模型 gpt-6.1-sol xhigh Fast。
# 三个 hook 经 controller-decision-01 第 3 节批准；不装第四个 hook。
# 具体 hook 命令由启动记录固定为：
# <node绝对路径> <repo>/workbench/src/gates/cli.ts --state <隔离state> signal --launch <launch-id>
# 经 -c hooks.UserPromptSubmit / hooks.Stop / hooks.PermissionRequest 传入，timeout=10。
# 完整展开后的 argv、启动环境和 hook_authorization 从 state.sqlite3 的 launch_records 读回。
set -eu
TASK_ROOT="${0:A:h:h:h:h:h}"
TASK_EVIDENCE="${0:A:h}"
TASK_LABEL="${1:?用法：outside-sandbox.sh 唯一标签，例如 b-06}"
TASK_SCOPE="${2:-all}"
if [[ "$TASK_SCOPE" != all && "$TASK_SCOPE" != checks && "$TASK_SCOPE" != probe ]]; then
  print -u2 '第二参数只允许 all / checks / probe'
  exit 2
fi
if [[ "$TASK_LABEL" != [a-zA-Z0-9]* || "$TASK_LABEL" == *[^a-zA-Z0-9_-]* ]]; then
  print -u2 '标签只能含字母、数字、下划线和短横线'
  exit 2
fi
cd "$TASK_ROOT"
TASK_OUT="$TASK_EVIDENCE/outside-$TASK_LABEL"
mkdir "$TASK_OUT"
git rev-parse HEAD > "$TASK_OUT/source-head.txt"
git diff -- workbench/ > "$TASK_OUT/source.diff"
tar -czf "$TASK_OUT/workbench-source.tar.gz" --exclude=node_modules --exclude=__pycache__ --exclude=.DS_Store workbench
if [[ "$TASK_SCOPE" != probe ]]; then
  python3 -B workbench/tests/test_relay_cli.py --output "$TASK_OUT/relay-cli" > "$TASK_OUT/relay-cli.stdout.txt" 2> "$TASK_OUT/relay-cli.stderr.txt"
  node workbench/tests/test_relay_core.ts "$TASK_OUT/relay-core" > "$TASK_OUT/relay-core.stdout.txt" 2> "$TASK_OUT/relay-core.stderr.txt"
  # 旧 14 项断言原样继承，只适配后台生命周期与既有 Git 故障注入。
  python3 workbench/tests/test_daemon_gates_e2e.py --output "$TASK_OUT/gates" > "$TASK_OUT/gates.stdout.txt" 2> "$TASK_OUT/gates.stderr.txt"
fi
# 进入真实阶段前要求外置盘挂载，隔离 home 只复制 auth.json，固定 CLI 版本。
# pane_release 是本脚本执行者（executor）的显式 action，先核对 ps 的前台领导进程。
if [[ "$TASK_SCOPE" != checks ]]; then
  # 产品直接运行 B，不装代理、不放行socket。CLI 写本 attempt 的 /tmp 请求目录；
  # Stop 经同一 CLI 转交，回执先登记再注入；仅一次交付和一次回执，不追加修复回合。
  python3 -B workbench/tests/run_worker_delivery.py --output "$TASK_OUT/delivery" > "$TASK_OUT/delivery.stdout.txt" 2> "$TASK_OUT/delivery.stderr.txt"
fi
