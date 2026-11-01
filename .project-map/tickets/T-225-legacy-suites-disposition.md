---
id: T-225
title: 门禁与质量串的 17 个旧套件怎么处置，受管窗格换 hc 之前先恢复哪些
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## Question

T-222 已查清 17 个旧套件守的契约、哪些检查还有别的测试守、哪些没人守（[报告](../../evidence/2026-10-31-batch29/T-222/REPORT.md) 第 3～5 节）。处置照 T-154 先例由用户定。要定的：

1. 17 个文件怎么处置。
   - A 全部迁移：守护最完整，旧测试工具改造量最大。
   - B 全部标历史：最快，但多数检查从此没人守。
   - C 按报告逐个拆分：安全、交付、冲突路径先迁，重复部分和固定旧版本的重建脚本另列。要维护一份逐项迁移清单。
   - 研究建议 C。
2. 报告第 5 节的 P0-1～P0-6，是否作为受管窗格换 hc 之前的基线。
   - A 先在现有运行时迁好并取得基线，再换 hc：出错时分得清是旧测试还是新运行时，多一个前置阶段。
   - B 与受管窗格切片同票迁：起步快，两类错误会混在一起。
   - C 只跑正向交付：成本最低，但不能说边界检查在 hc 上重新证明过。
   - 研究建议 A，以检查为单位，不要求每个文件全量翻新。
3. 尾注四字段和缺启动记录的拒收矩阵，先迁 `test_bad_worker_e2e.py` 还是 `test_t084_trailer_record.py`。研究建议先迁 bad-worker，t084 独有的 unknown、事实与卡上请求分开等项继续登记。
4. `test_task_cards_e2e.py` 与 `test_daemon_gates_e2e.py` 怎样避免两个入口。研究建议业务检查只在后台入口跑（DaemonCards），旧的无后台执行方式标历史，共享 helper 保留。
5. 运行条件挡住的两个：
   - `test_worktree_lifecycle_e2e.py`：研究建议改条件（不再依赖 sparse checkout 里没展开的旧记录文件）并迁当前路径，旧 baseline 重建单列；
   - `test_t082_parent_launch_e2e.py`：研究建议整份标历史，或把固定 START 的重建与现行 workspace、tmp 反例拆开；只去掉外置盘检查不足以让它成为现行回归。
6. 新发现的 `test_relay_scope.ts` 失效（夹具任务 id 不带项目），并入后续 relay 冲突迁移，还是单开一张小票。

## Resolution

用户 2026-11-01 在执行主控会话里回答“T-225、T-226 都按研究建议定吗？”：“都按建议”。

- 第 1 项：选 C，按报告逐个拆分。安全、交付、冲突路径先迁，重复部分和固定旧版本的重建脚本另列，维护一份逐项迁移清单。
- 第 2 项：选 A。P0-1～P0-6 先在现有运行时迁好、取得基线，再把受管窗格换到 hc；以检查为单位，不要求每个文件全量翻新。
- 第 3 项：先迁 `test_bad_worker_e2e.py`；`test_t084_trailer_record.py` 独有的 unknown、事实与卡上请求分开等项继续登记。
- 第 4 项：业务检查只在后台入口（DaemonCards）跑，旧的无后台执行方式标历史，共享 helper 保留。
- 第 5 项前半：`test_worktree_lifecycle_e2e.py` 改条件（不再依赖 sparse checkout 里没展开的旧记录文件），迁当前路径，旧 baseline 重建单列。
- 未随“都按建议”定下的两处，研究给的都是二选一，切片时随迁移清单再请用户选：
  - 第 5 项后半：`test_t082_parent_launch_e2e.py` 整份标历史，还是把固定 START 的重建与现行 workspace、tmp 反例拆开；
  - 第 6 项：`test_relay_scope.ts` 的失效并入后续 relay 冲突迁移，还是单开小票。
