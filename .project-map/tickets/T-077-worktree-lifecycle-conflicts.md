---
id: T-077
title: S3 worktree 生命周期与冲突：命名、清理、隐藏引用、路径交集、冲突回写、重新验收上限
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S3，即第 4 节"worktree 与冲突"与第 3 节第 1、7 步：

1. **命名**：目录 `<项目>/<任务卡号>-a<序号>`，分支 `a2a/<任务卡号>-a<序号>`；验收与审查用的 worktree 加用途与序号，detached。
2. **清理**：按 spec 第 4 节的表：已集成且干净的删目录与分支名、留 `refs/a2a/attempts/<任务卡号>/a<序号>`；打回、撤销、放弃且干净的留隐藏引用、删目录；有未提交改动或状态未知的不删、上报到面板（面板在 S5 之前先写问题上报条目）；验收与审查用的结果存库后删。
3. **路径交集**：认领时允许路径与活跃 attempt 有交集，默认拒绝派发；执行主控要并行须写理由，记下来。
4. **冲突回写**：验收合并出现文本冲突，门禁把冲突信息写回 worker（基于工作分支最新的头重新整理、解决冲突、重跑完成条件后重交，整串连审查重跑）；worker 会话已结束则开新 attempt。程序不替用户在两边改动之间取舍。
5. **重新验收上限**（风险 R8）：CAS 落空时自动重新验收，机械检查在新的 M 上重跑，审查结论在候选不变时沿用；连续超过 3 次交执行主控并上报。
6. **集成时的工作区**：分支被某个工作区检出时在那里快进；会覆盖未提交改动就拒绝并上报，不 stash、不 reset。

## Acceptance

- [x] 检查面同 T-075；冲突与 R8 场景可以用脚本在夹具仓库里制造工作分支的并发提交，至少一个冲突场景由真实 Codex worker 完成整理与重交。
- [x] 清理表的每一行一个正例；"有未提交改动"的不删且有上报；隐藏引用读回存在。
- [x] 路径交集：无理由时拒绝派发；带理由时放行并留记录。
- [x] 冲突：文本冲突写回 worker，重交后整串重跑并集成；会话已结束时开新 attempt。
- [x] R8：连续 CAS 落空到第 4 次时停止自动重新验收并上报；候选不变时审查结论沿用、候选变了时重审。
- [x] 检出工作区有未提交改动时集成被拒，工作区内容不变（读回比对）。
- [x] 8/9/18 三组与 T-075 的正反例不退化。

## 说明

- 只在 /tmp 夹具仓库上做，不碰本仓库与用户的工作区；测试中的后台脱离调用者进程组。
- 与 [T-076](T-076-quality-chain-scoring.md)、[T-078](T-078-controllers-in-workbench.md) 可能改同一批文件，由执行主控安排顺序。
- 授权来源：用户 2026-10-11 在会话"a2a-构思主控"选"S2、S3、S4 三张，缺口并入 (Recommended)"，选项原文含"我写完直接标就绪派出，不再单独给你看切法"；在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## Resolution

**2026-10-14：用户选 C 的两条受控证明 PASS，待主控关闭。** Ticket 保持 open，本 worker 不修改状态或验收复选框。授权为 answer `20261014T011612Z-ideation-answer-001`，主控 #96/#100；完整结果、命令与证据边界见 [RESULTS](../../evidence/2026-10-11-batch13/T-077/RESULTS.md)。产品版本 `2e2291acfee0e9b4f20c7ff952a5484c4262e20b`，本轮未改产品。

冲突写回背景、会话已结束后开新 attempt、真实 Codex worker 整理 C2 并显式重交已由 r3 的原始事件与 Git 证明。r3 九项正确身份外多了 worker 自己用 git commit --trailer 写入的 A2A-Fence/A2A-Spec-Rev，失败归为模型行为，原 run.json 保持 INCOMPLETE，不放宽断言或重写候选。

重交后的验收与集成用两条真实 CLI/门禁/Git 受控证明补齐：十一项 verify 返回 invalid_trailers、rejected 事件齐全且 main 不变；同一份 C2 代码的九项尾注由生产 hook 生成，verify 通过并 integrate，夹具 main=`feaec0b72720c2ce49e88858bc75937f7ca867c9`、task accepted。放过额外尾注的隔离变体先使独立断言失败（1 failure/0 errors），候选两项均通过。PTY/进程事实受控，新增真实模型回合 0，变体源码不提交。

S3 25 项、8/9/18、CAS、cards 及 relay/身份/停机等既有回归见 RESULTS 的版本绑定索引。R8 的审查会话质量串仍由 T-076 负责；本轮没有新增独立模型审查或最新 main 合流复验，不冒称已运行。r1–r3 原失败和审批、预算、日志完整保留；遗留真实证据提交 `ae33ae6cfcfd422f0d8cab9cb5180d93c7b8c479`，本次受控证明提交号以终端回报为准。

**2026-10-14：执行主控验收 PASS，关闭。** 产品内容 `5d0bf1e8`（经变基合入 main `60eb6ac5`，产品与验收文件逐字一致）。证据见 [RESULTS](../../evidence/2026-10-11-batch13/T-077/RESULTS.md) 与 [主控决策](../../evidence/2026-10-11-batch13/T-077/controller-decision-03.md)。

- 合流：变基到含 T-076-2 的 main，`rebase-final-05` 39 个零模型阶段全部按预期（审查目录 4 红 + 候选、R8/T-076 联合路径 3 红 + 候选、S3 25、8/9/18、CAS、cards 15、relay、身份/停机、T-076-2 tracer/wide/审查故障/协议控制/来源冻结、panes）。
- 跨卡遗漏并入本卡：审查 worktree 按 `<task>-a<N>-review-<K>` 命名，结果入库且 reviewer 停止归档后核对身份/HEAD/干净再删并读回；脏/未知保留上报（issue 20261014T023857Z 已修）。
- 冲突反事实：`conflict-red-final-02` 七条红态各在其目标断言失败、前置齐全；候选七项通过。
- 独立审查：01 INCOMPLETE（F1 两条反事实未到达目标）→ 02 F1 已解决、余 1 项分类器标签 P2 → 修正后审查 PASS、0 发现；14 份原始结果离线重分类不变。
- 验收第 1 条按用户选 C（answer `20261014T011612Z`）：真实 Codex worker 完成冲突整理与重交（r3），重交后的验收与集成由两条受控真实入口证明补齐；r3 手写尾注归模型行为。真实模型回合 9/10。
- 打分 `score-ac5390d8033540b485b6f215cc117c3c`（边界 3、工程 2）。
- 未尽：blocking issue `20261011T134711Z-worker:s13-t077-issue-001`（2026-10-11 计划阻塞）须由用户关闭，已转构思主控。
