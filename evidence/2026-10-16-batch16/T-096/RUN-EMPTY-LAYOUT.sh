#!/bin/sh
# 仅由执行主控运行；本 worker 未运行真实 Electron。
# 启动：真实 Claude Code 2.1.302 主控两份，重启后各续接一次（共 4 次）；
# 受控 C receiver 一份（不是真 Codex）；daemon 两个 epoch；Electron 串行三次。
# 模型／假 API POST 预算 0；不传提示词，不登录，不写全局配置，不截屏。
# 每个主控的六个引导键及一次空队列就绪放行仍须逐屏批准；不自动按键。
# 读回后只点击三个“关闭窗格”，正常退出第二个 Electron，再不带 --launch 打开。
# 第三个窗口必须显示空状态、pane_keys=[]、保存集仍空，不新建窗格或输入凭据。
# 原始证据／构建槽只写已挂载外置盘；旧标签拒绝覆盖。正常退出、daemon_stop、
# 写入者退出核对及归档沿用 run_restart.py；退出不明确时保留现场，不重复退出。
# 用法：sh RUN-EMPTY-LAYOUT.sh /绝对路径/claude-2.1.302 本次批准引用 新标签
set -eu
if [ "$#" -ne 3 ]; then
  echo '用法：sh RUN-EMPTY-LAYOUT.sh /绝对路径/claude-2.1.302 本次批准引用 新标签' >&2
  exit 2
fi
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(git -C "$script_dir" rev-parse --show-toplevel)
exec python3 "$script_dir/run_restart.py" \
  --source "$repo" \
  --output "/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/$3" \
  --label "$3" --approval-ref "$2" --claude "$1" --claude-version 2.1.302 \
  --panes 3 --expect restore --startup-wait-seconds 600 --check-close --check-empty-reopen
