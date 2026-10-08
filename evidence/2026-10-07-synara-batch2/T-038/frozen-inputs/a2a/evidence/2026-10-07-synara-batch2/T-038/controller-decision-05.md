# T-038 主控决定 05：冻结前先排除我们造成的回归（2026-10-08，Claude Code）

基线上 CUA 用例 PASS、候选上 timeout，Electron 候选空白：两者都可能是本 ticket 的改动造成的，冻结前必须先区分。

1. CUA 用例：在基线 worktree 与候选上各顺序单跑 3 次（不并行，同一机器负载下交替进行），记录每次结果与耗时。基线全过而候选持续失败，按本 ticket 回归处理：先定位是哪处改动（可在临时 worktree 逐步撤回 T-038 提交），修复后再跑；两边都有失败则记为不稳定的上游用例，保留全部日志。
2. Electron 空白：在基线 worktree 用同样的隔离数据目录与启动方式启动一次 Electron，截图。基线正常渲染而候选空白，就是本 ticket 的回归，必须修；基线也空白，记为上游/环境问题，界面证据用 dev Chrome，并写明差别。
3. 以上结果写进 RESULTS 后再冻结候选与独立审查。基线 worktree `synara-t038-baseline` 保留到主控关闭 ticket，结束时登记路径。
