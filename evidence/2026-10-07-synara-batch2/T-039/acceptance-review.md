STATUS: FAIL
TARGET: Synara `fa3fc3352805d00e41c454fa6f810807528de3a9`，分支 `a2a`；冻结清单 `evidence/2026-10-07-synara-batch2/T-039/frozen-manifest.json`

EVIDENCE:
- 合同要求真实 app-server run 完成 `a2a_submit → 独立 oracle → CAS 集成读回 → 回收`：`brief-T-039.md:13-16`、`.project-map/tickets/T-039-real-loop.md:11-19`、`.project-map/specs/synara-m1-2026-10-07.md:80-84`。
- 候选绑定为指定 revision，源码执行且 tracked diff 为空：`candidate-binding.json:2-19`；复核时 `git rev-parse HEAD` 仍为该 revision，`git diff --exit-code HEAD` 返回 0。
- 真实门禁入口 `run` 返回退出码 1、`ok:false`、`identity_conflict`；run 阶段为 `waiting_submit/paused`，`candidate_commit`、`verification`、`integration_intent` 均为空：`run-01.json:4-20`。
- 事件流只到 `run_finished`，没有 submit、oracle 或 integration 事件；原始诊断也记录 `candidate_unsubmitted`、`oracle_and_integration_not_started`、集成引用未改变：`events-01.json:16`、`diagnostic-checks.json:5-8`。
- 绑定原 attempt 的 reclaim 返回 `ok:false`、`run_external_unknown`、退出码 1：`reclaim-01.json:4-19`。原生读回显示 turn 为 `interrupted`，thread/session 未归档：`native-after-interrupt-01.json:82-98,642-650`。
- 独立 oracle 通过外部 subprocess、字面合同期望值和 `unseen-input` sentinel 检查：`frozen-oracle.py:1-55`。它确实拒绝已知坏 fixture：`oracle-known-bad.json:2` 为 `FAIL`，12 个 case 中 10 个失败；这不能替代未发生的 worker 提交闭环。
- 临时隔离边界有证据：服务使用 `/private/tmp` home 且脱离调用者进程组：`server-start.json:7-22`；仅复制 `auth.json`、只放行 `git add/commit`、无 hooks：`isolated-config.json:2-4,44-48`；清理后 homes 不存在、无存活进程组、token 已删除：`cleanup.json:6-25`。
- 无人值守期间两个原生快照均为 `hasPendingApprovals:false`、`hasPendingUserInput:false`、`pendingInteractions:[]`：`native-live-01.json:82-93,212-216`、`native-after-interrupt-01.json:82-98,640-648`。

FINDINGS:
- [P1] `evidence/2026-10-07-synara-batch2/T-039/run-01.json:18` — 真实 run 在 submit 前因 `identity_conflict` 暂停，未达到 accepted，也没有 worker candidate、oracle 或 CAS 集成；应修复 gate attempt 与 provider canonical thread/turn 的身份绑定后，从真实 CLI 重新跑完整闭环。
- [P1] `evidence/2026-10-07-synara-batch2/T-039/reclaim-01.json:17` — gate reclaim 被 `run_external_unknown` 拒绝，原生中断和进程清理不能替代业务回收；应修复 attempt/fence/turn 的外部状态解析，并以成功 reclaim、归档状态和读回事件作为收尾条件。

COUNTEREXAMPLE:
- 已知坏的冻结分页 starter 被独立 oracle 判为 `FAIL`，10/12 case 被拒绝，包括乱序 tie、continuation、边界和非法输入；因此该 oracle 能拒绝已知错误实现。当前证据没有证明任何已提交 worker 实现通过。

LIMITATIONS:
- 隔离 home 删除和临时路径边界已证明，但没有用户 `~/.codex`、Herdr 或既有 Synara 数据的独立前后快照/审计；`versions.json:70` 也明确 Herdr 未连接核实。因此“用户数据无本次写入”只能判为 INCOMPLETE。
- 由于 run 在 submit 前失败，没有成功 accepted run、CAS 引用读回或完整回收证据；无人值守无权限/问题回答仅在已观察到的失败运行和清理截止点成立。
