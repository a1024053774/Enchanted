---
id: T-049
title: 构思主控与执行主控的分工、层级与权限
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

主控拆成构思主控与执行主控两层后，谁做什么、谁向谁汇报、权限怎么分配？

## Resolution

2026-10-09 grilling 确认。账本 [controller-split-user-input](../../.grilling/controller-split-user-input.md) 的 C11–C13、D5、D7、D13、D17、D18；设计见 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 1 节；用户确认与委托决定见 [基线确认记录](../specs/controller-split-user-input-baseline-2026-10-09.md)。

- **层级**：用户 ⇄ 构思主控 → 执行主控 → worker / reviewer / monitor。用户的话："构思主控是更上层的主控，负责分发任务，任务的监督由运行时执行，待全部完成停下来后再把内容返回给构思主控，然后我看构思主控就可以。"（"运行时主控"于同日改称"执行主控"。）
- **构思主控**：接收想法、澄清、写决定/spec/ticket、标就绪、向执行主控分发任务（assign/revise/cancel/stop）、转述完成报告与待决定事项。不直接派发、验收、集成、回收 worker。
- **执行主控**：执行就绪 ticket，派发、盯进度、审查、验收/集成/回收（全经门禁），没有可执行的就绪 ticket 时才停下并写完成报告。不改目标、规则、术语和他人标就绪的 ticket 正文。
- **执行主控的自主边界**：在已批准范围内（T-004）可以自建缺陷级 ticket 并执行，完成报告里列出；需要用户抉择的才发构思主控。遇到目标、验收、设计级问题，停下该 ticket，简短说明并交构思主控展开，自己继续别的就绪 ticket，不在自己会话里 grill。
- **权限三层，提示词为主**：① 结构底线（不暴露的工具就是没权限；Synara 期用能力预设）；② 提示词与角色卡（脚本重新打印，worker 的卡由派发包装附带）；③ 追加式记录。不做策略引擎，不做按路径或按 ticket 的权限。用户的话："如果真要写死各种权限，这个很难界定，也很难照顾全。"①也要做，不是备用。
- **部署**：Herdr 期两个主控各占一个 pane，靠 [T-052](T-052-controller-handoff-protocol.md) 的协议交接；做能用以后一起挪进 Synara（见 [T-059](T-059-controllers-in-workbench.md)）。
- **术语**：见 CONTEXT.md。2026-10-09 之前文档里无前缀的"主控"指执行主控。

2026-10-10：层级与分工不变；权限分层在第三阶段载体上改为四层，见 [T-071](T-071-permissions-signals-dispatch-data.md)。
