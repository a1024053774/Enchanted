---
id: T-055
title: 问题上报最薄一刀：worker 上报，用户在面板答复，答复回到 worker 并被记成用户输入
type: build
status: closed
blocked_by: []
claimed_by: s8-t055
supersedes:
ready: yes
ready_by: ideation
ready_rev: 2
---

## What to build

让一个受管 worker 能把"范围外的问题"上报给用户，用户在任务窗口里答复，答复回到 worker，并被记成用户输入。只做穿过所有层的最薄路径：

1. worker 经 MCP 工具 `a2a_raise` 上报一个问题（标题、正文、是否阻塞）。
2. 门禁核心追加存储它；CLI/HTTP 和 `status`/`events` 能读到，执行主控轮询时能看到。
3. 任务窗口里该会话旁出现问题面板，列出这个问题，有回复框和发送键。
4. 用户点发送，worker 的 thread 收到一条来源为 `user` 的消息，格式见 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 4 节。
5. 这次答复被记成用户输入（形态 `answer`，`reply_to` 指向该问题）；受管 attempt 上同时有指向它的 `human_intervention` 派生事件；同一次答复不产生第二组记录。

本票只做受管 worker 与单条答复；多题打包、判断动作、其他会话类型的覆盖留给 [T-056](T-056-user-input-coverage.md)、[T-057](T-057-issue-panel-completion.md)。设计见 spec 第 2、3、4 节。

## Acceptance

- [x] 红态在先：在本票的父修订上，`tools/list` 没有 `a2a_raise`、面板接口不存在，端到端脚本失败；保存输出与重放命令。
- [x] 真实服务端（隔离数据目录）：受管 worker 的凭据在 `tools/list` 里能看到 `a2a_raise`；调用后返回会话内问题号与 id；记录追加存储，重启服务后仍在。
- [x] 反例：未绑定任何 task 的 thread 调用被拒绝；参数里伪造他人的 thread id 被忽略（身份取自凭据）；非活跃 turn 的调用被拒绝（与 `a2a_submit` 同口径）；上报不改变任何门禁业务状态（task、attempt 状态与 fence 前后一致）。
- [x] 读取：`gate` CLI 与 HTTP 都能读出该 task 的上报链（问题 → 答复 → 送达），JSON 可被严格解析；`status`/`events` 里出现问题上报与答复事件，带 task、attempt、thread 绑定。
- [x] 面板：任务窗口里每个会话旁显示该会话的问题（标题、正文、blocking 徽标、回复框、发送键），blocking 的置顶；保存截图。外观由用户判断，本票不宣称外观通过。
- [x] 发送：点发送后 worker thread 里出现一条用户消息，内容逐字等于 spec 第 4 节单条格式的预期串（预期串由需求手写，不从实现输出复制），消息来源字段是 `user`。
- [x] 记录：该次答复产生恰好 1 条形态为 `answer` 的用户输入（`reply_to` = 问题 id），受管 attempt 上有 1 条指向它的 `human_intervention`；不产生形态为 `message` 的重复记录；重放事件日志不增加记录。
- [x] 一次真实 Codex worker 经 MCP 上报并收到答复，证据保存（隔离 `CODEX_HOME`，遵守 AGENTS.md 的真实 Codex 验收规则；额度紧，只用最少的 turn）。无法运行时明确记 INCOMPLETE，不用替身顶替。
- [x] `a2a_raise` 与 `a2a_submit` 同口径免确认（用户 2026-10-09 选 A，逐字：“A，然后你开”）：把 `a2a_raise` 加入网关工具名目录；受管 worker、有效运行身份、活跃 turn、已授权自动批准时不再弹权限提示；非受管会话、非活跃 turn 仍要提示。先红后绿，反例逐条；改动限于该工具名目录，列入上游文件改动清单。上一项的真实 Codex 上报因此要在无人批准的情况下完成。
- [x] 既有套件仍通过（交付 8、恢复 9、编排 18、membership、T-044 的 35 项）；typecheck、lint 通过；对上游文件的改动列清单。
- [x] 不使用正则或关键词规则判断任何内容的含义。

## 说明

- 这是第一条 tracer bullet，目的之一是暴露 spec 的错误：发现 spec 与已建成的行为不符，停下发 `needs-decision`，不绕开。
- 重复计数的做法（面板发送接口在派发消息前登记 `message_id`，记录器跳过已登记的）见 spec 第 3 节；如有更好的做法，写进 RESULTS 并说明理由。
- 与 [T-053](T-053-inbox-script-and-role-cards.md)、[T-054](T-054-dispatch-wrapper-and-session-copy.md) 互不依赖，可并行；改动在 fork `a2a` 分支（`packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a`）。
- 授权来源：`ready_by: ideation`，`ready_rev: 2`（2026-10-09 用户对“a2a_raise 是否免确认”选 A 后，由 1 修订为 2，只增加一项验收；见 inbox 里的 revise 条目）。

## Resolution

2026-10-09 worker：**BLOCKED**，尚未开始实现，待主控决定；ticket 保持 open，待主控关闭。实际 MCP 注册入口为允许目录之外的 `apps/server/src/agentGateway/Layers/AgentGateway.ts`，需要主控批准两处最小接入才能让 `a2a_raise` 出现在正式 `tools/list`。定位证据、拟议差异与未运行检查见 [RESULTS](../../evidence/2026-10-09-batch8/T-055/RESULTS.md)。依据 `ready_rev: 1`，未更改正文或验收条件。

2026-10-09 worker 续轮：**BLOCKED**，已执行主控决定 01 的两处接入，父修订真实 HTTP/MCP 红态与未验收实现已保存（fork `13ec64ce6b6b19b913fe69bfc71dbf49c0f54bb0`）。一次真实 Codex 0.162.0 在 `a2a_raise` 发出 provider 工具批准请求，依决定原样保存并停止；没有批准、没有改 `computerToolPermission.ts`。三包类型检查通过，但上报/答复闭环、既有套件、截图和最终独立审查未完成；Acceptance 保持未勾选。详见 [RESULTS-02](../../evidence/2026-10-09-batch8/T-055/RESULTS-02.md)。ticket 保持 open，待主控决定与关闭。

2026-10-09 ready_rev 2 交接：**INCOMPLETE（工程验收 PASS，最终独立审查待主控决定）**。fork 最终候选 `2330534b2cf906b9d8f0a0b643adb370683d7fe0`；真实 Codex full-access 无人批准上报/接收答复、身份反例、面板/精确消息、一次记录、重启重放、CLI/HTTP 链、35 项与 membership、type/lint/fmt 均有证据。唯一 fresh-context 审查对 `27344e471` 为 FAIL，结束会话转交 P1 已经真实红绿修复；随后补齐原生 archive 幂等回收，最终候选未再独立审查，未自行超出“一次”限制。[RESULTS-03](../../evidence/2026-10-09-batch8/T-055/RESULTS-03.md) 记录版本边界、反例、收尾与未关闭范围外 issue。用户确认 config mtime 变化为外部已知改动。ticket 保持 open，待主控关闭；正文/Acceptance 未改。

2026-10-09 执行主控决定 04 复验：**PASS**，依据 ready_rev 2 对固定 fork `2330534b2cf906b9d8f0a0b643adb370683d7fe0` 与证据 `3bf426f` 完成一次新的 fresh-context 只读独立审查，旧 P1 的 session-ended 转交及 archive 幂等回收均通过，无可复现 P1/P2/P3 违约，原文见 [acceptance-review-final.md](../../evidence/2026-10-09-batch8/T-055/acceptance-review-final.md)，旧 FAIL 原样保留，ticket 仍 open、待主控关闭。

**执行主控关闭（2026-10-09）：PASS，依据 ready_rev 2。** fork 最终候选 `2330534`（分支 `a2a`），证据至 `11774bf`，见 [RESULTS-03](../../evidence/2026-10-09-batch8/T-055/RESULTS-03.md) 与 [最终候选独立审查](../../evidence/2026-10-09-batch8/T-055/acceptance-review-final.md)（PASS）。真实 Codex 0.162.0 在 full-access 下无人批准经 MCP `a2a_raise` 上报成功，用户在面板答复后 worker 收到逐字等于 spec 预期的用户消息，恰 1 条 answer 与 1 条 human_intervention，重启与重放不变，记录表只追加；伪造 thread、未绑定、非活跃 turn、无效凭据均被拒绝且门禁状态不变；35 项既有套件、membership、typecheck/lint/fmt 通过。上游改动：`AgentGateway.ts` 注册两行、`computerToolPermission.ts` 目录一项（用户选 A）。过程保留：两次 BLOCKED（范围、权限提示）、一次逐次人工批准（决定 02，后被决定 03 撤销）、对早期候选 `27344e4` 的审查 FAIL（P1：会话结束未转交，已修复）。范围外发现由 T-061 承接。用户 `config.toml` mtime 在验收期间变化，用户确认为本人或其他已知会话所致。
