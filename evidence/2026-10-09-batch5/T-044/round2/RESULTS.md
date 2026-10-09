# T-044 第二轮交付（2026-10-09）

**PASS（仅限 T-044 与主控决定 01 的本地隔离范围），待主控关闭；M1/发布未验收。** 唯一冻结候选为 Synara fork `90e38b667e224caca75318591fac43e676bf77e3`（parent `808156d63ef8e265a0e2c017fae7851e50a51019`），分支 `a2a`，未 push。本轮授权以 [主控决定 01](../controller-decision-01.md) 为准；首轮 BLOCKED 报告、原始失败与审查原文均保留在上一级目录，未改写。

## 已执行的主控决定

error 会话的原生读回现在明确携带 provider 是否存在、活跃 turn 等事实。门禁核心只在实例不存在、活跃 turn 为空、running 明确为 false、待交互明确为 false，并且原身份匹配时允许回收；仍通过真实 stop、archive 和读回完成记账。待交互包括审批、待答问题和待处理计划。run 观察及等待收尾继续拒绝 error，submit 也不能使用 error 状态；没有把 error 当作完成或交付。

本轮没有启用 provider、调用 app 模型、访问正式工作台目录、改写 apps/*/dist、移动/替换依赖或构建输出、重启正式工作台、操作用户 Herdr、修改 T-045 worktree 或 push。dev 是任务书允许的隔离实例，HOME/CODEX_HOME/Claude 配置与数据位于外置盘。collaboration 独立审查者是受请求的辅助审查，不是 app provider turn；其实际供应商 tier 未验证。

Tracer bullet 经过生产 CLI HTTP → 同一核心 → 真实 Synara 原生线程/消息 → 回收与 membership → dev 界面。Deep modules 的状态写入仍集中在核心；native decoder 只返回事实。Ubiquitous language 沿用 task、attempt、thread、session_id、fence，不把展示角色改成第二套授权或业务状态。

## 两类 18 项失败的根因

**REALITY GATE: PASS（仅限失败分类与夹具修复方向）。** 决策是修产品竞态还是修夹具；原始 CLI/Git/SQLite 与 native 边界时间线保存在 `prior-failures-raw.json`，没有改原现场。

- operation_busy：waiting_submit 从 04:49:36.728 UTC 开始，期限 8 秒；夹具在读取当前身份时调用完整 snapshot，status 花 1.993 秒、events 花 2.935 秒。submit 的实际 native submit-begin 到 04:49:45.110 才发生，已越过期限；此时门禁进入期限清理，互斥锁正确拒绝并发交付，并没有绕过 fence、验收或集成。不能用该迟到交付要求门禁成功。
- KeyError：waiting_submit 从 05:09:11.318 开始；夹具 snapshot 中 events 命令到 05:09:27.255 才返回（15.508 秒）。门禁已于 05:09:19.516 按期限停止/归档旧 thread。夹具随后仍从只包含活跃 thread 的 store 取旧 ID，导致 KeyError；原 thread 保留在 archived 中。

这两例是**夹具把不必要的完整观察串在固定交付窗口里**，不是已证实的产品锁竞态。为了可证伪，用同样的 8 秒 run 输入给 events 观察注入 8.2 秒延迟：原夹具两项重现 KeyError/迟到交付，修复副本两项通过（`slow-observer-red.*`、`slow-observer-green.*`）。没有增加期限、轮询预算或重试失败的交付。

修复只把 `current_attempt()` 改为一次公开 status 读取；所有 18 个测试方法、业务断言、输入、独立分页 oracle 和运行期限保持原样。完整 Git/SQLite/events snapshot 仍在原有业务检查点保存。差异见 `fixture-change.diff`，修复副本为 `test_run_native_e2e.py`；原 T-037 日期记录没有修改。首轮服务测试的 verifying 超时未单独归因，本轮同断言/期限已重跑通过，不称其为上游缺陷。

## 同一冻结候选的证据

上一级目录中的 `round2-*` 为本轮运行，以下路径相对本报告。

| 条件 | 结论 | 证据 |
| --- | --- | --- |
| 新 error 回收合同先红后绿 | PASS | `../round2-positive-error-red.*` 的 CLI 正例被旧候选拒绝；`../round2-http-reclaim-red.jsonl` 的真实 HTTP 正例被拒绝；`../round2-error-positive-final.*` 与 `../round2-http-reclaim-green.jsonl` 转绿 |
| 必须仍拒绝的反例 | PASS（CLI/真实核心与 decoder；原生帧受控） | `error-reclaim-proof.ts`、`../round2-error-negatives-final.*`：worker/reviewer 各 11 情形，含 provider 注册/运行、活跃 turn、running 最新 turn、审批/待答/计划、工作目录/provider/旧 turn 身份不符；任务不变且无 stop/archive 请求。error run 明确返回 run_external_unknown，非 completed，oracle 未调用 |
| 坏候选检验 | PASS | `mutant-error-guard/`、`../round2-error-guard-mutant.*`：移除 error 回收保护后向存在的 provider 发出了 stop，业务断言以“不得产生该副作用”失败，不是 setup/import 崩溃 |
| 35 项 | PASS，18/18 + 17/17 | `../round2-orchestration-final/`、`../round2-delivery-recovery-final/`，完整 argv/env/stdout/stderr/exit/源码与隔离 Git/SQLite/oracle trace 绑定冻结候选 |
| 自动任务/worker/reviewer 与结束历史 | PASS（真实 CLI HTTP、原生读回与 dev UI） | `final-window-02/create.jsonl`、`reclaim.jsonl`、`fixture.json`、`ended-membership.json`；全程 create → dispatch → attach → reclaim，没有 membership 写入。`attach-state-unchanged.json` 证明普通 attach 不替换 attempt；read-native.mjs 经只读公开 RPC 核对原生模型、参数、两份不同指令、error → stopped、归档与消息历史 |
| 截图 | PASS（dev Chrome，非 Electron/发布版） | `../round2-ui-active-02.png/json`、`../round2-ui-ended-clear.png/json`：任务自动出现，worker/reviewer 均已结束，computed opacity=0.55，原生指令历史可见，无会话不可用；仅导航与 Escape 清除悬浮提示，没有响应替换或手动归属修改 |
| attach 无交付/业务推进权限 | PASS（实际 handler/核心权限逻辑；原生 caller 帧受控） | `permission-proof.ts`、`../round2-permission-control-final.*`：同一有效 worker 交付凭据，reviewer active caller 被拒且状态不变，worker active caller 成功正例排除“总是拒绝”；submitted 状态下 reviewer 对其他变更仍被拒。真实签名 Gateway/模型会话认证未在本 ticket 声称通过 |
| T-038 membership | PASS | `../round2-membership-final.jsonl`、`membership-boundaries-final.json`：两任务与角色保存、CAS/重复/未知身份、跨项目、gate project 不一致、trusted origin/OPTIONS、共享任务锁；使用独立 membership 测试项目，未改截图任务归属 |
| attachment/worker 记账恢复 | PASS（CLI/Git/SQLite；native 边界受控） | `../round2-lifecycle-event-final.*`、`../round2-lifecycle-membership-final.*`、`../round2-lifecycle-legacy-final.*`，事件写失败回滚、已持久 ended 后修复 membership、旧 worker 无 reclaimed_at 格式保留标记与删除/重加 |
| fmt/lint/typecheck | PASS | `../round2-fmt-final.*`、`../round2-lint-final.*`、`../round2-typecheck-final.*`；0 lint error，868 既有 warnings |
| 相关 Vitest | PASS | `../round2-core-test-final.*` 1/1，`../round2-service-final.*` 11/11；当前 native error 断言通过真实服务核心拒绝 active error，不再要求 decoder 隐去事实 |
| fresh-context 独立审查 | PASS（本轮批准范围） | [完整审查原文](acceptance-review.md)、review-provenance.json；截止 2026-10-09 06:28:39 UTC，只读核对同候选、独立输入、反例、副作用与实际 UI；没有复用首轮候选结论 |

未重跑完整 workspace suite；当前改动范围的核心、服务、35 个门禁场景与 HTTP/UI 均有本轮证据。没有真实 app 模型调用、供应商实际 tier、性能/可靠性收益、签名 Gateway 验证、Electron 原生、生产发布或 M1 全部完成的结论。

## 夹具失误与现场保留

`final-window` 首次试图在 live server 中只读 SQLite，遇到数据库锁；后续截图/权限命令因它未生成 fixture.json 而失败。原 trace 与失败输出均保留，没有修产品或改断言来绕过；改用已存在的公开 `orchestration.getThreadDetailSnapshot` RPC，在新 label `final-window-02` 完成。原数据与私有目录未移走、链接或覆盖。首轮报告与所有原失败仍在上级目录。

所有隔离 fixture repo/worktree、运行事实和归档保留（retained-fixtures.tar.gz/json，19 个 root）；顶层不登记 gitlink。模型/CLI/启动 argv/受控边界与未知字段沿用上级 `provenance.json`，本轮新增 source/command 记录不把配置当作实际 tier 证据。worker 的真实受管 attempt/session/fence 未提供，保持未知；本报告中的 attempt/fence 都是隔离验收 task 的实际值。自建 dev 全部停止，5817/7777 无监听，cleanup.json 及 stop 进程树记录已保存。

## 复现与交接

在冻结 fork、外置盘挂载时，从 a2a 根目录执行，label 必须全新；先确认隔离 dev health startupReady 与 5817/7777。

```sh
python3 evidence/2026-10-09-batch5/T-044/round2/window-cli.py NEW_LABEL create
python3 evidence/2026-10-09-batch5/T-044/round2/window-cli.py NEW_LABEL reclaim
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance COOP_SCRIPT=/Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch2/T-037/native-entry.py python3 -B evidence/2026-10-09-batch5/T-044/run-acceptance.py NEW_RUN_LABEL /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/round2/test_run_native_e2e.py
PYTHONPATH=/Users/luckye/Documents/Code/a2a/acceptance COOP_NATIVE_ENTRY=/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/cli.ts python3 -B evidence/2026-10-09-batch5/T-044/run-acceptance.py NEW_DELIVERY_LABEL /Users/luckye/Documents/Code/a2a/evidence/2026-10-07-synara-batch1/T-036/native-acceptance/native-suite.py
```

error 拒绝矩阵、permission 与恢复脚本经上级 run-check.py 运行，所有完整命令已经保存。停止仅使用本轮启动记录和当前进程树身份；正式工作台不在清理范围。T-044 保持 open，主控据本轮范围与独立审查决定关闭。
