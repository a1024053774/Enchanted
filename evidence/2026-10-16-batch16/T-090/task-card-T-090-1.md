⟦主控 #1⟧
# 任务卡 T-090-1

你是 T-090 的 worker（执行主控派发）。先读 AGENTS.md、.project-map/roles/worker.md、.project-map/tickets/T-090-review-end-check-worker-boundary.md、.project-map/tickets/T-082-*.md，以及 T-078 worktree 里的诊断（只读）：/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/F4-REVIEW-BOUNDARY-DIAGNOSIS-01.md 与 review-followup-f4-compare-01/。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-090-1 |
| 来源 | T-090 ready_rev 1（ready_by executor，T-004 缺陷级自建） |
| 目标 | 审查结束核对改为：审查开始时绑定 worker 实际 HEAD、分支与干净状态，结束时核对未变；继续核对候选提交号不变、审查目录干净、共享 refs 未变。原验收 test_submit_requires_clean_head_and_cannot_replace_frozen_candidate 在 main 上恢复通过 |
| 非目标 | 不改 acceptance/、冻结 protocol、T-082 的副本/启动参数检查、集成前置；不在测试驱动里 reset worker、跳过回收或伪造 review_reclaimed |
| 修改边界 | 允许：workbench/src/gates/（只限审查开始/结束 worker 边界的绑定与核对）、workbench/tests/、evidence/2026-10-16-batch16/T-090/；禁止：acceptance/、.project-map/（除本卡不改）、AGENTS.md |
| 完成条件 | 红态：修复前该用例在本 worktree 起点失败（review_worker_workspace_changed），保存可复现命令与输出；绿态：修复后通过；反例：审查期间改 worker HEAD、worker 变脏各一条真实入口用例必须仍被拒绝；整组回归：原交付 8、恢复 9、编排 18 与 T-082 启动边界/结束核对/四启动变异全部通过 |
| 任务类型 | 后端逻辑 |
| 复杂度 | M |
| 执行器 | Codex CLI codex-cli 0.162.1，gpt-6.1-sol，xhigh，service_tier default（launch-b4da324aa23d48eda3c1cfcee621a6c5） |
| 起点 | main f08a280bd（exec/t090，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t090：workbench、acceptance、scripts、.project-map、findings、evidence/2026-10-16-batch16） |
| 唯一写入者 | s16-t090，task T-090 attempt a1 |

约束：只在本 worktree 工作；worktree 没有 node_modules——需要依赖时按项目规则用外置盘缓存（/Volumes/WD-Elements），不回退内置盘，不链接或移动构建输出目录；沙箱外命令（安装依赖、受控宿主测试）一律写成脚本交我跑，不请求升级。你可以 git add / git commit 自己的交付（用户规则允许），不 push、不 rebase。证据按 T-088：仓库只留文本摘要与命令，大块原始输出归档外置盘留 *.archive.json 清单。语义拿不准就停下报我。
交付：最后一行写 T-090 READY。
