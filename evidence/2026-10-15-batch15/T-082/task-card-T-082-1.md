⟦主控 #27⟧
# 任务卡 T-082-1

你是 T-082 的 worker（执行主控派发）。先读 AGENTS.md、.project-map/roles/worker.md、.project-map/tickets/T-082-reviewer-oracle-sufficiency-mutation.md、.project-map/proposals/gate-hardening-2026-10-14.md（D3）、.project-map/roles/reviewer.md，以及 T-080/T-076 的相关 ticket。旧证据只在主 checkout /Users/luckye/Documents/Code/a2a/evidence/ 下只读查看（本 worktree 是稀疏检出，不含历史 evidence，不要 checkout 它们）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-082-1 |
| 来源 | .project-map/tickets/T-082-reviewer-oracle-sufficiency-mutation.md，ready_rev 1（ready_by ideation）；开工依据用户 2026-10-15 选"先开 T-082"（answer 20261015T155839Z-ideation-answer-001） |
| 目标 | 门禁发给 reviewer 的审查请求含完成条件够格审查与 2～5 个变异要求；reviewer 在门禁新建的一次性候选副本里 workspace-write、断网、/tmp 与 $TMPDIR 不额外可写；门禁核对启动边界与结束后各项不变并删副本 |
| 非目标 | 不建变异平台；不保证模型行为（真实交付审查只如实记录）；不改 T-078 的转交/调用者身份逻辑；不改证据存放方式（T-088 未定） |
| 修改边界 | 允许：workbench/src/panes.ts（审查启动参数）、workbench/src/gates/core.ts（审查请求、启动核对、副本建立与清理）、相关类型、workbench/tests/、README 中对应说明、evidence/2026-10-15-batch15/T-082/；禁止：.project-map/roles/（构思主控已改）、全局配置、用户 ~/.codex |
| 完成条件 | 票据 Acceptance 七条逐条；红态先于修复；拒收参数四种（旧只读 argv、工作目录不是副本、网络开、/tmp 可写）各先见红；结束核对的作废变体；回归 T-076 质量串与 T-077 套件 |
| 红态命令 | 在起点上证明审查请求不含完成条件审查与变异要求，reviewer 写审查目录被拒（沿用 T-076 只读证明，保存读回） |
| 任务类型 | 后端逻辑 |
| 修复对象 | 不适用 |
| 复杂度 | L |
| 执行器 | Codex CLI codex-cli 0.162.1，gpt-6.1-sol，xhigh，service_tier default（启动记录 launch-a6aca9f0379b4363b678e21e1c54bf98） |
| 起点 | 451be8462c85fd08b997cb85453188a8e5751c9d（exec/t082，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t082，依赖已装，spawn-helper 已 755） |
| 唯一写入者 | s15-t082（wF:p49），task T-082 attempt a1；Herdr 期不经门禁认领，交付由执行主控提交 |

约束：
- 只在本 worktree 工作；不 commit、不 push；不写全局配置；后台进程脱离进程组并清理。
- 真实 Codex 回合合计不超过 4（边界证明 + 交付审查），按 AGENTS.md"真实 Codex 验收"规则：/tmp 下隔离 CODEX_HOME，只复制 auth.json，副本不入证据与 Git，结束删整个 home；hook 安装须主控逐次批准。真实回合与沙箱外命令一律写成确切脚本交我运行，不要请求升级，不要自己启动真实 Codex。
- 一次性副本与临时目录只解出必要路径（不要 git archive 整个仓库，evidence 约 4 GB 会写满内置盘）；用完删除。
- 与 T-078 重叠 core.ts/panes.ts：T-078 只碰转交/调用者身份；谁先合入谁先走，另一方变基重跑。你不要改 T-078 的那部分。
- 证据单文件 >5 MB 的压缩或放外置盘，仓库只留摘要与路径；整体规模尽量小。
- 目标、验收、设计级问题停下写 needs-decision（scripts/inbox send），范围外问题照常上报。

交付：evidence/2026-10-15-batch15/T-082/RESULTS.md 写清每条 Acceptance 的命令、输出目录、结果；跑 project_map.py status。先给我一个分阶段计划（tracer bullet：先打通一个最薄的"请求含必查项 + 副本建立/清理 + 启动核对"切片）和需要我跑的第一批命令，再推进。最后一行写 T-082 PLAN READY。
