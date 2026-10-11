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
