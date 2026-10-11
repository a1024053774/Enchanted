#!/bin/zsh
# T-075-4 / 主控 #36：red-01 已确认，checks 阶段仍是 0 个模型回合。
# red 不启动 Electron；checks 启动自己的 Electron 并截图，不复制 auth，不装 hooks。
# 主控 #37：window 阶段只复跑窗口；Electron 可执行文件改用解析后的真实路径。
# 主控 #38：驱动追加阶段记录；harness 保存原始 stdout/stderr，超时杀掉自有进程组。
# 主控 #39：bisect 先跑 ready 的三组对照；仅预期矩阵成立后才继续完整窗口检查。
# 主控 #40：live 只放行一个 gpt-6.1-sol/xhigh/Fast 请求的生命周期回合，不自动重试。
# run_pane_lifecycle.py 的 turn_limit=1；全卡预算文件为同目录 turn-budget.jsonl，上限4。
# UserPromptSubmit / Stop / PermissionRequest 沿用决定01逐次批准，具体 -c 值和完整 argv
# 写入 lifecycle/launch-record.json。真实验证以PTY字节增长为准，不要求工具输出标记。
# 决定02 / 主控 #41：累计已用1/4，下一轮最多再1个，预算保护上限暂收紧为累计2。
# live 先跑离线中文/跨块/不读屏夹具；通过后以trace字节增长和ps验真实生命周期。
# 主控 #42：live-02 在参数解析处失败、未用新回合；live-03 修正负游标参数并逐命令保存原始输出。
# 主控 #43：live-03 用了一个回合，累计2/4；live-04 最多再1个，预算保护上限为累计3。
# live-04 先验证固定高水位和普通/备用屏幕切换，再进入真实回合，不用固定延时判断补回完成。
# 后续真实阶段单独交接，获批参数为 gpt-6.1-sol / xhigh / Fast 请求 / -a never。
# 全卡最多 4 个主回合；不得把重复执行这个包装器当作追加回合授权。
# 已批准的三个 hook：UserPromptSubmit、Stop、PermissionRequest，timeout=10。
# 后续完整 argv 将由 launch_records 读回，命令模板为：
# <node绝对路径> <repo>/workbench/src/gates/cli.ts --state <隔离state> signal --launch <launch-id>
# 分别经 -c hooks.UserPromptSubmit / hooks.Stop / hooks.PermissionRequest 传入。
set -eu
TASK_EVIDENCE="${0:A:h}"
TASK_LABEL="${1:?用法：zsh outside-sandbox.sh 唯一标签 阶段}"
TASK_PHASE="${2:?第二参数为 red / checks / window / bisect / offline / live，例如 live-04 live}"
exec python3 -B "$TASK_EVIDENCE/run_outside.py" --label "$TASK_LABEL" --phase "$TASK_PHASE"
