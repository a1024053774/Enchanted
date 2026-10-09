---
id: T-056
title: 用户输入记录覆盖全部范围，观察器改名
type: build
status: open
blocked_by: [T-055]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

让用户在任何会话、任何渠道的输入都被记成数据，并和主控、agent、自动化发出的提示词分开。范围：受管 worker、attach 会话（reviewer/monitor）、普通会话、带角色的主控会话里打的字；对 Codex 异步提问和结构化提问的答复；权限批准与拒绝；界面的停止与中断。每条记录带形态、渠道、目标键（project、task、attempt、thread、turn、message、request）和来源引用，`certainty` 为 `observed`。

现有 `human_intervention` 保留，改为受管 attempt 上"落进该 attempt 的用户输入"的派生事件，带 `input_id`。观察器及相关名字统一改为 `user_input_*`。设计见 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 3 节。

## Acceptance

- [ ] 红态在先：在本票的父修订上，下面覆盖矩阵里除"受管 worker 的消息"外的各项都没有用户输入记录，用例失败；保存输出与重放命令。
- [ ] 覆盖矩阵正例（真实服务，隔离数据目录，每项至少一条）：受管 worker 的消息（既有行为不变）；attach 会话的消息；普通非受管 thread 的消息；带角色的主控会话的消息；Codex 异步提问的答复；结构化提问的答复（`user-input.respond`）；权限批准与拒绝（`approval.respond`）；界面的停止、中断。每条记录含形态、渠道、目标键、来源引用，`certainty` 为 `observed`。
- [ ] 反例：agent、自动化、门禁自己发的消息与命令（dispatch/attach 提示词、automation、`a2a:` 前缀的命令）不产生用户输入；界面自动派生的命令（退出应用时的批量中断、临时线程清理）不被记成用户的明确决定（按 spec 第 3 节的处理）。
- [ ] 观测点：非消息类输入在 WS RPC `dispatchCommand` 入口按枚举的命令类型记录，不改命令契约；发现界面有绕过该入口的路径时，停下发 `needs-decision`，不自行给命令加字段。
- [ ] fail-closed 范围：受管 attempt 的输入记录失败时，所有变更命令照旧被拒（沿用既有行为与测试，只改名字）；其余范围记录失败不阻断业务，恢复后由事件日志重放补齐，补不齐的写 gap 记录；重放不重复。
- [ ] `human_intervention` 保留，改为受管 attempt 上的派生事件，带 `input_id`；界面标记与 AGENTS.md"受管 worker 里直接输入记为人工介入"的规则不变。
- [ ] 改名：`human_input_observer`、`human_inputs`、`recordHumanInput` 等统一改为 `user_input_*` 系列。正式工作台的数据目录里已有旧名的表和历史事件，所以要有幂等的迁移，保留全部历史记录；迁移在一份旧格式夹具库的副本上验证，不碰正式数据目录。既有套件除名字外断言不变并全部通过；README 与界面文案同步。
- [ ] 不使用正则或关键词规则判断内容含义；v1 不产生含义标注。
- [ ] 既有套件（交付 8、恢复 9、编排 18、membership、T-044 的 35 项）、typecheck、lint 通过；对上游文件的改动列清单。

## 说明

- 开工前对照 [T-055](T-055-issue-report-tracer-bullet.md) 的实际结果重读 spec；发现 spec 与已建成的行为不符，停下发 `needs-decision`，不绕开。
- 失败方式清单（处理方式写进 RESULTS）：事件乱序；重复事件；重放与实时交叠；未知命令类型；超大负载（附件只存引用）；迁移中断后重跑；旧库缺少新列。
- 与 [T-057](T-057-issue-panel-completion.md)、[T-058](T-058-server-inbox-capabilities-wake.md) 会改同一批文件，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`。

## Resolution
