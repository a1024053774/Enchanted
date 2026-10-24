# T-170 启动失败的 attempt 无法回收：结果

- 写入者：执行主控（Claude Code）。T-164 第三轮发现，按 T-004 自建；构思主控 answer 20261024T135340Z-ideation-answer-001 要求核对 B a2 现场并裁定。
- 基线：main `6412c5e08`（产品代码与 e3b14d27b 相同）。真实后台、门禁、PTY；Codex 换成编译的替身，重放 B a2 原始终端输出（`b-a2-pty.raw`），`--version` 答 `codex-cli 0.164.0`；不发模型请求。
- 结果见 `CHECKS.json`；运行目录按 T-088 归档（`*.archive.json`）。

## 根因

B a2 的 Codex CLI 在启动时因账号路由超时退出 1，没有原生会话；后台如实记 `launch_failed`，窗格 `failed`、`stopped`。reclaim 先要求 `runtime_identity.native_session !== null`（报 identity_conflict），即使放过这一条，失败窗格 `blocked=true` 又会被 `checkErrorReclaim` 与 `run_blocked` 拒绝。没有任何门禁路径能回收这种 attempt。

## 修改

`workbench/src/gates/core.ts` reclaim：attempt 与实时读数的原生会话都为空、窗格已停止、未在运行、没有回合、错误读数为 provider 已不在且无活动回合时，视为“从未启动”，跳过原生会话与 blocked 检查，照常走停止、归档、清理。其余情况不变。

## 证据

| 项 | 结果 |
| --- | --- |
| 红态（`--revision 6412c5e08`，red-1/2） | 2/2 `red_reproduced`：leader 已观察到、原生会话为空，reclaim 报 identity_conflict，再派发报 already_claimed，与 B a2 一致 |
| 绿态（green-1/2） | 2/2 PASS：reclaim 受理，工作区移除，任务可再派发 |
| 反例（`--scenario hang`，hang-1） | PASS：替身不退出、原生会话为空时 reclaim 仍拒绝，工作区保留 |
| 回归 | T-158 revise-retry、T-146 session-state、T-146 native exit probe 均 PASS |
| 早期无效夹具 | `runs-python-standin`：Python 替身的进程命令是解释器路径，产品认不出 leader（leader_pid 为空），与真实现场不符，作废保留；改为编译替身后重跑 |

## 未覆盖

- 未构造“清空条件之一”的坏实现逐项变异；反例只证明活进程不被回收。
- 未在真实 Codex 账号路由失败下复验（外部故障不可控）。

状态：agy 独立审查 PASS（`review-agy-01.md`，两条 P3：未逐项变异；ticket 待合并后关闭）。

## 后续：dispatch 窗口内失败（2026-10-24，合并后全量回归发现）

合并后 `RUN-MERGE-REGRESSION-11` 满负载下两项 T-170 失败：替身 Codex 在 dispatch 回执前、leader 被观察到之前就退出。dispatch 读到 `blocked` 直接拒绝 `run_blocked`，但它读到的身份只在内存里，没有保存：attempt 停在 `preparing`、`runtime_identity` 为空、任务停在 preparing；reclaim 的 `checkThread` 要求已绑定身份，仍报 identity_conflict。同一缺陷，只是失败更快。第一版修复还要求 `leader_pid` 非空，也挡这种情形。

修改（`core.ts`）：dispatch 读到 blocked 时先把 attempt 与任务记为 claimed 并保存观察到的身份，再拒绝 `run_blocked`；reclaim 的“从未启动”分支不再要求 leader 已被观察到（仍要求窗格已停止、无会话、无回合、provider 不在）。

测试加 `--scenario fast`（替身不停顿立刻退出 1）；dispatch 失败时从 status 读回 attempt；再派发检查改为“门禁接下任务并建了新 attempt”（替身每次都启动失败，所以再派发本身也是 run_blocked，而不是 already_claimed）。

| 项 | 结果（`CHECKS-2.json`） |
| --- | --- |
| 红态 fast，`--revision 121f604e8`（第一版修复） | `red_reproduced`：dispatch run_blocked，reclaim identity_conflict，再派发 already_claimed |
| 红态 fast，`--revision 6412c5e08`（修前） | 同上 |
| 绿态 fast ×2（fast-green2-1/2） | PASS：reclaim 受理、工作区移除、门禁为再派发建新 attempt |
| 绿态 failed（failed-green2-1 及更早 failed-green-*） | PASS |
| 反例 hang（hang-green-*） | PASS：活进程 reclaim 仍拒绝 |
| 探查过程中的中间运行 | fast-red-1～5、fast-green-*：测试逐步改正（读回 attempt、再派发判据）时的运行，保留不删 |

全量回归 `RUN-MERGE-REGRESSION-12`（55 项，加 t170-fast）在候选 c822751c8 上的结果见 merge-wave README。

## 后续二：回归检出缺少现场记录（2026-10-24 更正）

`RUN-MERGE-REGRESSION-12` 在 c822751c8 上 54/55：t170-hang 超时，时间线却是 launch_failed、pane_exit。原因：回归在稀疏检出的 `a2a-merge-check` 里跑，那里没有 `evidence/2026-10-23-batch24/`，测试读的 `b-a2-pty.raw` 不存在，C 替身 `fopen` 失败后立即崩溃退出。因此**更正 merge-wave 11 的说法**：那次两项失败不是“满负载下启动更快”，而是替身因缺文件立即退出。它暴露的产品缺陷是真的（CLI 立即退出时 dispatch 不保存身份、attempt 不可回收），已由 `--scenario fast` 在有记录的检出里确定性复现（红态 2/2），修复不变。

修改（只动测试）：现场记录复制到 `workbench/tests/t170_b_a2_pty.raw`（来源即本目录 `b-a2-pty.raw`），测试开头检查记录存在且含原始报错，缺失即报夹具错误，不再静默变成另一种场景。这是测试自列失败方式第 5 条（把夹具问题算成产品结果）的漏防。

agy 审查（`review-agy-02.md`）PASS，P3 一条（blocked 分支与正常分支的 claimed 保存字面重复）；其“55 项全通”一句不实，已在报告头注明。
