# T-158 继续执行依据

执行主控消息 #36 转述构思主控 answer `20261024T005556Z-ideation-answer-001`，用户 2026-10-24 逐字：“显式 reclaim 后释放 (Recommended)”。

本 worktree 尚未合入 main `fd4ebe236` 的 ticket 改动；按当前会话 #36 的明确指令执行，不修改本地 ticket，也不 rebase。

已确定流程：保存 v2 → revise → 对旧 attempt 显式 reclaim → 正常 dispatch；reclaim 后一次成功，无需交叠参数。旧 attempt 未 reclaim 时仍必须 `path_overlap`。若现有门禁已满足这条流程，红态落在步骤不可发现，使用真实 `a2a help` 和应用内角色说明文本核对。

只涉及以下说明文件：

- `workbench/src/terminalCli.ts` 的帮助输出。
- `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`，应用内主控说明。
- `workbench/roles/worker.md`，worker 遇到改卡需求时交给执行主控处理。
- 必要的 `workbench/README.md` 操作说明。

非目标：不取消路径检查，不自动回收会话，不让 worker 自己 revise 或 reclaim，不改其他任务或全局配置。若真实流程暴露 reclaim 后仍拒绝，才在卡内门禁代码修根因。

验收先走现有生产路径的一条 Tracer bullet：真实后台、门禁、Git、PTY 与 Electron，完成打回、改卡、撤销、回收和重派。沿用 Ubiquitous language 中的 task / attempt / reclaim，不增加第二套路径所有权状态；按 Deep modules 原则复用门禁接口，不为说明改动增加包装 API。

测试先列失败方式，期望独立来自上述裁定。额外哨兵为旧 worktree 留有未提交证据：回收后保留内容，但不继续占路径。受控模型为真实交互 Claude CLI 配本地脚本化接口，供应商模型回合为 0。
