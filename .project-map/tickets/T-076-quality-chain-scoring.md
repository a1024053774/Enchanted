---
id: T-076
title: S2 质量串与打分：独立审查、红态与规则式检查、打回回写，并补 S1 缺口
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S2，在 [T-075](T-075-tracer-bullet-daemon-gate-pane.md) 的 tracer bullet 上加宽第 3 节"一次交付怎么走"的第 4～6 步：

1. **红态与规则式检查**：任务卡写了红态命令才查（候选里的新测试在起点提交上失败、在候选上通过）；规则式检查按项目配置（lint、类型检查等）。
2. **打回回写**：任一检查不过，失败摘要以 `⟦门禁 #序号⟧` 写回 worker 窗格，worker 重交后整串重跑；同一 attempt 连续 3 次打回就停止自动回写，交执行主控。
3. **独立审查**：机械检查全过后，后台新开一个只读的 reviewer 会话（不续接任何会话），附任务卡、候选改动和上一轮问题清单；结论"可合并"或"需修复"加问题清单，绑定候选提交号写回门禁；门禁核对审查会话不是写入会话、是为本次新开的。"需修复"时清单写回 worker。
4. **打分**：集成与放弃命令带打分参数（spec 第 8 节），缺执行主控必填项就拒收；Herdr 期 `records/scores.jsonl` 的格式与之对齐，以便切换时导入。

并入 S1 留下的缺口（T-075 完成报告 `20261011T094922Z-executor-report-001`）：

- **尾注模型为 unknown**：受管 worker 提交的 `A2A-Model`、`A2A-Effort` 要写实际值（例如启动时写进环境变量），不能是 unknown。
- **多回合身份绑定**（上报 `20261011T052530Z`）：回执或打回带来的新回合会让 run/reclaim 按 `attempt.turn_id` 判为身份冲突。区分"原生会话与领导进程身份"和"本次交付的回合绑定"，先取红态；不得为通过而删掉或放宽身份检查。
- **状态表一致性**（spec 第 9 节例外，上报 `20261011T042856Z`）：检查由事件重建的状态与状态表一致；已知 `core.ts` 里 attachment creating 没有对应事件、saveAttachment 与 attached 事件不在同一事务、memberships 与 session_presets 在另库不经 save()。不一致就停下报告，改存储另切片。
- **卡 4 的五类产品变异体**：按 T-075 卡 4 计划补跑，各自在业务断言上失败。

## Acceptance

- [ ] 检查面同 T-075：编排后台命令行入口驱动真实窗格里的真实 Codex worker 与 reviewer，对夹具仓库走完整门禁；证据为命令与输出、库里事件读回、Git 引用读回。
- [ ] 正例：一次"第一次被打回（完成条件或红态不过）→ 自动回写 → worker 修好重交 → 审查可合并 → 带打分集成"的完整流程。
- [ ] 反例，各自在真实入口上被拒且留下事件：红态命令在起点上不失败；规则式检查失败；审查会话是写入会话或续接旧会话；审查结论绑定的提交号与候选不符；缺打分；第 3 次打回后不再自动回写。
- [ ] 尾注：真实 worker 提交的 `A2A-Model`、`A2A-Effort` 与启动记录一致。
- [ ] 多回合：回执回合之后 run 与 reclaim 仍能核对身份；伪造的别的会话仍被拒。先有红态。
- [ ] 一致性检查的结果如实报告（一致 / 哪些表不一致）。
- [ ] 五类变异体各自失败；8/9/18 三组与 T-075 的正反例不退化。

## 说明

- 真实 Codex 按 AGENTS.md 隔离，回合数尽量少；模型按 AGENTS.md 2026-10-11 的规定。
- 与 [T-077](T-077-worktree-lifecycle-conflicts.md)、[T-078](T-078-controllers-in-workbench.md) 都可能改 `workbench/src/gates/` 与 `daemon.ts`，同一文件只给一个写入者，由执行主控安排顺序。
- 授权来源：用户 2026-10-11 在会话"a2a-构思主控"选"S2、S3、S4 三张，缺口并入 (Recommended)"，选项原文含"我写完直接标就绪派出，不再单独给你看切法"；在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## Resolution

T-076-1 完成，待 T-076-2；待主控关闭。保持 open，ready_rev=1。

- 源码提交：`42e2b8ed3caed775133eb3cafff5f4ee5ab68330`；与 fresh-context 只读独立审查快照逐字节一致，审查 PASS。
- 真实受管 worker 的 C=`3f7f0b41ce36b559027d9032473f04adf734d1ee`：Model=gpt-6.1-sol、Effort=xhigh，与启动记录及交付回合原生上下文一致；回执新回合后 run completed/reclaimed。伪造原生会话与领导者仍被拒。真实实验共使用 3/3 回合，不再追加。
- 一致性检查如实报告：完整交付的 tasks/attempts/verifications 一致；membership/session_presets 无法重建；attachment creating 与 active-before-attached 两窗口不一致。主控 #9/#10 已转构思主控另切片，本卡没有修存储，全库报告仍 INCOMPLETE。
- 候选五类变异体各在业务断言失败，两对照通过；8/9/18 回归全部通过，0 failures/errors/skipped。本卡 acceptance diff 为空，保留其他卡的变更。
- 证据、红态/夹具错误、回合账、再生成命令与限制见 [RESULTS](../../evidence/2026-10-11-batch13/T-076/card-1/RESULTS.md)，独立审查见 [REVIEW](../../evidence/2026-10-11-batch13/T-076/card-1/review-01/REVIEW.md)。卡 2 的红态/规则式质量串、打回回写、产品 reviewer 与打分尚未实施，不关闭整票或勾选其验收。

**T-076-1 执行主控验收（2026-10-11）：卡片通过，ticket 仍 open（待 T-076-2）。** 交付提交为 a2a `42e2b8ed`（实现）和 `d95f4171`（证据），实现提交带 9 项尾注。

- **尾注**：真实 worker 提交（outside-real-04）的 `A2A-Model: gpt-6.1-sol`、`A2A-Effort: xhigh` 与启动记录一致。执行主控在夹具仓库中独立读回核对：`main`=M `ecf9a7a`，父提交为 G `935d03c` 和 C `3f7f0b4`。
- **多回合身份**：运行身份（launch、thread、shell、领导进程、原生会话）和交付回合分开记录。回执回合之后，run 以 completed 结束并完成回收。先在起点取得红态，再转绿；伪造身份的反例仍被拒。
- **后台停止**：顺带修复了产品缺陷：有窗格或 run 失败之后，`daemon_stop` 一直返回 daemon_busy。修复后，停止前会等待进行中的请求处理完。反事实已证实测试能抓住这一缺陷。
- **一致性检查**（`workbench/src/stateConsistency.ts`，只读）：
  - tasks、attempts、verifications 三张表：一致；
  - membership 库的 memberships、session_presets：无法用事件重建；
  - attachments 的 creating 窗口与 active 窗口：不一致。

  后两项已报告给构思主控，另开切片改存储；本票不改存储。
- **五类变异体**：在候选上全部按业务断言失败。8/9/18 回归（coop、recovery、run）全部通过，三份断言相对起点没有改动。
- **独立审查**：PASS。
- **真实回合**：用满上限 3/3。real-01 因夹具卡号非法实际使用 0 回合，real-02 因夹具循环等待实际使用 0 回合，real-03 因期限过短使用 1 回合，real-04 通过、使用 2 回合。
- **证据**：有两个文件压缩后仍超过 5 MB，执行主控已移到外置盘（`5060c5ee`），原位置保留指针文件；这两个文件仍留在 Git 历史中。

已打分。

**T-076-2交付（2026-10-13）：PASS，独立审查PASS / LIMITED_GO（仅隔离受管交付）。保持open、ready_rev=1，待主控关闭。**

产品/测试源码提交：`2bc3a1e96b1ecb687e8fae32ebbc5478fa58de88`，绑定s13-t076-2s当前launch、实际gpt-6.1-sol/xhigh及原生会话的9项尾注。交付证据和本Resolution随最终证据提交保存，不push。逐条验收、六类反例、各阶段红绿/变异体、预算与重放命令详见[卡2 RESULTS](../../evidence/2026-10-11-batch13/T-076/card-2/RESULTS.md#主控-92最终交付逐条验收与局限2026-10-13)。Acceptance留给主控核对勾选，本worker不关闭整票。

| Acceptance | 卡2结果与证据 |
| --- | --- |
| 真实入口/检查面 | PASS。outside-real-delivery-02的commands日志指针、bindings、gate-events、events-after-stop、native-sessions、integration及real-delivery-readback-02/run.json；真实worker4回合/reviewer1回合，经过后台CLI/Panes/PTY/B/Git/SQLite。 |
| 首拒→回写→修复→新审查→主控带分集成 | PASS。C1 709a85ba完成条件首拒，⟦门禁 #3⟧自动回写，同attempt重交C2 e08f87cf，新只读reviewer可合并；主控在ready-for-score之后后填3/3，唯一集成M b24ec63e，父提交G 5ce713f5和C2；唯一score_recorded及回收。证据为integration、executor-score、score-payload和独立Git读回。 |
| 六类反例 | PASS（受控实际入口，另有真实边界）。outside-red-02先红；outside-wide-green-01/widened-contracts的red_base_not_failing、red_rules_failing；outside-focused-tracer-01/protocol-controls的writer_cannot_review/reused_native/wrong_candidate/score_required/third_rejection及对应单点变异体。三次上限只有两条修复回写，第三次paused并上报；真实正例缺分为score_required且Git不动。outside-p-review-02实际sentinel EPERM一次，文件/Git未变、主机对照成功。逐案事件位置及层次见RESULTS六类反例表。 |
| 尾注 | PASS。C1/C2九项尾注、bindings和交付turn_context均确认实际gpt-6.1-sol/xhigh；real-delivery-readback-02/run.json。 |
| 多回合 | PASS。卡1先红及真实run/reclaim；卡2同原生会话4回合，ACK零工具、提交绑定1/3回合、原attempt/leader保持，最终回收。outside-legacy-green-06的multiturn/run及伪造身份反例通过；没有放宽身份检查。 |
| 一致性如实报告 | 已报告；全库**INCOMPLETE**。real-delivery-consistency-01.json中tasks/attempts/verifications一致；memberships/session_presets无法重建；空表不代表覆盖，本条真实正例未覆盖attachment中断窗口。沿卡1另切存储决定，不改结构。 |
| 五类变异体与8/9/18、T-075/T-076-1不退化 | PASS（受控）。outside-legacy-green-06共22步均符合预期，coop8/recovery9/run18均0 failures/errors/skipped；五类产品变异体与F10/W07来源反例命中业务断言。批准W01–W07/F01–F14，Recovery9逐字不变；assertion-hunks与最终范围审计可复核。最新default参数另有outside-launch-policy-default-01最小红绿、priority/只读变异体，未宣称重跑全套。 |

独立fresh-context只读交付审查原文：[REPORT](../../evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/REPORT.md)。从ticket/spec独立重建验收，结构风险同审，无确认的可达违规或结构风险；另有16项独立协议输入及C2的8项整数/7项非法类型检查。槽7唯一完整回合，gpt-6.1-sol/xhigh/read-only/never，argv显式default；原生日志未报告实际供应商tier。142个冻结文件首次逐字节读回一致；审查后README/交付文档更新，另仅删除新controlled_quality_pty.ts第13行空行的两个尾随空格（暂存检查失败及diff原样保留）；产品、hooks、acceptance字节不变，测试行为不变，最终核对严格限定差异。

真实累计**7/8**，槽8未用，三组隔离home均已删除、auth未入证据。原真实run.json因48,122,290字节日志归档要求为INCOMPLETE，历史原样保留；archive-real-log-01/run.json为PASS，外置盘逐字节核对一致，本地留pointer，卡目录无>5MB文件。交付核对、地图0 problems/0 stale、diff --check和大小检查收据为delivery-review-readback-01及final-delivery-check-01。

局限：全库一致性与attachment中断窗口如上；P-review在增加显式default之前的冻结版本证明实际只读拒写，当前版本未重做sentinel，default有针对性红绿及真实正例argv证据；受控回归不证明模型理解/审查准确率，良性候选通过不证明可靠性改善；审查快照缺MAP导致其地图检查不可用，主checkout另有实际通过收据；审查未重跑完整可写/socket/模型套件；原生日志实际tier未知。T-077联验/命名/清理/R8、新worker原生记录归属开放issue 20261011T180613Z、T-078及正式工作台切换不在LIMITED_GO结论范围，交主控衔接。待主控关闭。

提交检查补充：当前源码/文档cached检查通过；完整cached检查对原始diff、终端输出、Git消息与冻结快照产生315条空白告警，退出2/INCOMPLETE原样记录，原始字节不清洗。要求的git diff --check、地图、>5MB检查通过。分项收据及解释见RESULTS文末。

最终证据提交前最新检查收据：card-2/final-delivery-check-02/run.json，PASS；7/8真实回合，待主控关闭。
