# T-257：红态与已批准的后台恢复

2026-11-08。本票仍为 INCOMPLETE：已复现缺陷，尚无产品修复或绿态。

真实后台、门禁与交互 Codex 0.167.0 的隔离运行见 `red-controller-diagnostic-02.json`。四条真实请求的回执在首个 Stop 钩子返回前提交，同一 turn 再次触发 UserPromptSubmit、Stop 和原生 task_complete，窗格仍 busy、排队消息未发、reclaim 返回 worker_working。真正工作的两个屏障阶段也均拒绝回收。此次运行退出 1，defect_reproduced 为 true；夹具已记录状态后清理。

诊断入口 `replay-stop-identity.py` 使用已提交测试 `1acebc00d617a04317164370dcfb21c1b21b3308`，只去掉票据未要求的 stop_hook_active=true 限定，以同 turn 且序号晚于续跑 UPS 识别第二个 Stop。它没有改产品或冻结验收，不替代候选的门禁完成检查。原测试首次运行因该多余限定退出 2，原始结果 `red-controller-01.json` 保留。Python 3.9/macOS 的跨进程 monotonic_ns 不能排序，后续测试应使用 UTC 和后台序号。

正式 worker 也触发同一缺陷。attempt `42b3cd31-9194-45ba-85ea-4744b051cfe5`、launch `6b6a329a-5072-416c-a00f-af1b62183969`、thread `3d277255-4396-40d2-8277-c3c939307849`。11:14:01Z 的 stop_not_matched 后已有原生 task_complete；12:25:04Z 主控答复只排入队列，没有贴入或新回合，见 `worker-stop-stalled.json`。worker 没有 submit；HEAD `e9e9f2db8ce6f2c50b453a868c8bcaa026e9fa8b` 只含复现测试和失败证据，没有产品改动。保留为 `keep/T-257-1-a1`。

本轮用户在提问“是否批准现在正常重启 Enchanted 后台、保留现有提交与证据，再经门禁回收旧 attempt 并用 astra xhigh 重派继续修复？”下明确回答：

> 批准重启并经门禁恢复（推荐）

此授权只允许恢复执行环境，不代表修复、验收或敏感变更集成批准。正常 daemon_stop 后核对旧后台 44606、worker 58263/58265 退出；按正式应用启动流程恢复后台，核对主控身份。旧 attempt 经门禁 reclaim；不改库、不手输旧 worker、不使用重叠参数绕过自身回收。

随后将卡修订为 v2，从保留提交导入测试与证据，修正上述开发测试识别，直接依据已有红态做最小修复。worker 和 reviewer 都为 gpt-6-astra xhigh、fast=false。主控负责沙箱外真实检查，worker 不扩大权限；提交前须移除主控创建的 workbench/node_modules 链接本身（目标是主仓库依赖，不得删除目标）。旧主仓库脏日志全部保留。

任务顺序仍为 T-257 → T-249 → T-250，不启动 Claude、不 push。修复候选通过独立审查后，敏感变更仍须用户读证据批准才能集成；两个面板最终用 gpt-6.1-terra Computer Use 加常规测试验收。
