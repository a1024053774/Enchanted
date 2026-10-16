# T-087 主控记录

## 开工 #1（2026-10-16 UTC）

依据 assign 20261016T082147Z-ideation-assign-001（ack 20261016T082250Z-executor-ack-001），ticket ready_rev 1，用户原话"T-088 的六条细节和 T-087开工"。只读分析，不改 workbench/。
worktree /Users/luckye/Documents/Code/a2a-wt-t087（exec/t087，基于 main fc362ab44），稀疏检出 workbench/src、hooks、bin、scripts、acceptance、.project-map、.grilling、findings、evidence/2026-10-16-batch16/T-087。
首次 launch-worker（launch-bb8db422295443b2905bd8adff5b9af3）在 herdr agent start 处 exit 1、Codex 未起（记录为 failed）；主控手动同参数 herdr agent start 一次成功，判断为新目录首启超时；因手动启动没有启动记录与 A2A 身份，随即关闭该窗格，经 launch-worker 重新启动：launch-81bf2744649b42f2bc780ace08c32634，agent s16-t087（wF:p4H）。任务卡 task-card-T-087-1.md 经 scripts/dispatch 派发。Codex 会话 2 个（t078、t087）。来源抽查将由另开的不写图会话完成。

## 交付与来源抽查 #2（2026-10-16 UTC）

worker 交付图文档 findings/ticket-gates-graph-2026-10-16.zh-CN.md 与生成脚本 findings/generate_t087_graph.py：34 个点、63 条连接、207 条来源引用存在性检查通过，两次生成 diff 为空，12 条隐式边单列。worker 上报两条 issue：findings/README.md 索引 stale（主控应用其提议补丁，status 0/0）、Codex 沙箱拒写共享 Git 元数据（主控按启动记录写尾注代提交 aba81b52c）；两条均以 disposition close 处理（20261016T084159Z、20261016T084200Z）。
#2：新开 fresh Codex 抽查者 s16-t087-rev（wF:p4J），只写 source-spot-check-01.md，不读作者说明，直接对照 workbench/src/gates/ 核对检查串顺序与拒收码并抽查其他连接与隐式边。Codex 会话 3 个（t078、t087、t087-rev）。
