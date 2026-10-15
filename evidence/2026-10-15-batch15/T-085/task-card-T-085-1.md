⟦主控 #14⟧
# 任务卡 T-085-1

你是 T-085 的 worker（执行主控派发）。先读 AGENTS.md、.project-map/roles/worker.md、.project-map/tickets/T-085-daemon-recovery-suite-restart-config.md，以及 evidence/2026-10-15-batch15/T-084/RESULTS.md、independent-review-02.md 第 4 节、regression-03/recovery-baseline/run.json（在主 checkout /Users/luckye/Documents/Code/a2a 下，只读）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-085-1 |
| 来源 | .project-map/tickets/T-085-daemon-recovery-suite-restart-config.md，ready_rev 1（ready_by executor） |
| 目标 | 恢复套件中断用例重启后的 daemon 带上与中断前同一份启动配置（含审查运行时），整套恢复套件 5/5 通过 |
| 非目标 | 不改门禁规则；不伪造审查结果、不跳过 verify；不改尾注夹具（T-086 在做）；不修本套件以外的失败 |
| 修改边界 | 允许：workbench/tests/test_daemon_recovery_e2e.py 及其受控宿主/重启辅助（workbench/tests/ 下）、evidence/2026-10-15-batch15/T-085/；禁止：workbench/src/（如确需改产品 daemon 启动配置持久化，先停下写 needs-decision 报我）、test_worktree_lifecycle_e2e.py、conflict_acceptance_host.ts |
| 完成条件 | 经真实入口跑整套 test_daemon_recovery_e2e.py：5 个用例 failures 0、errors 0；test_daemon_verify_interruption_and_operation_lock 不再出现 review_launch_config_required；重启所用配置可核对地等于中断前那份（证据里给出两份的来源与比对） |
| 红态命令 | 在起点上跑同一套件，复现该用例 review_launch_config_required（其余 4 案在起点应已通过；若不是，先报我） |
| 变异 | 一次性副本里把重启改回空配置，该用例重新失败 |
| 任务类型 | 缺陷修复（测试/恢复） |
| 修复对象 | T-084 范围外发现（main c8d4e5d6 之后） |
| 复杂度 | S |
| 执行器 | Codex CLI codex-cli 0.162.1，gpt-6.1-sol，xhigh，service_tier default（启动记录 launch-209c2887df444a53833d5013f7e8ee85） |
| 起点 | 6ba3bde4174d8e0fc6db65a70a1216fd05c2cdac（exec/t085，worktree /Users/luckye/Documents/Code/a2a-wt-t085，依赖已装，spawn-helper 已 755） |
| 唯一写入者 | s15-t085（wF:p45），task T-085 attempt a1；Herdr 期不经门禁认领，交付由执行主控提交 |

约束：只在 /Users/luckye/Documents/Code/a2a-wt-t085 工作；不 commit、不 push；不写全局配置；不调模型 API；测试的后台进程必须脱离进程组（start_new_session）并清理；临时目录用完即删；需要沙箱外执行（绑定端口等）时写明命令由我跑，不要请求升级。

交付：evidence/2026-10-15-batch15/T-085/RESULTS.md 写清红态、绿态、变异的命令、输出目录与结果；跑 project_map.py status。范围外问题经 scripts/inbox send 上报，不自行处理。最后一行写 T-085 READY。
