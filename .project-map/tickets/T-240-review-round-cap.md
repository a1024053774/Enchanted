---
id: T-240
title: 审查轮数设上限；同一条不变式再被打破时，改为写不变式并系统搜索
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

审查是为每次交付新开的只读会话（T-070），但轮数没有上限，执行主控一直审到通过为止。[T-229](T-229-worker-input-final-text-only.md) 做了十二轮 GPT 只读审查，前十一轮都要求修复，其中多数是在同一个状态机里又找到一种新的事件顺序：提交、UPS 到达、Esc、新草稿、输入法组字、钩子超时、写库失败。第十二轮通过只说明那一轮没再找到问题，不说明各种顺序都已覆盖。要不要给轮数设上限？超过上限后改用什么手段？

## Resolution

2026-11-03 用户原话（`~/Documents/SKILLS` 目录下的 Claude Code 会话，讨论审查类 skill）：

- “我觉得通过多轮由代理进行的抽象代码审查，你可能会陷入过度拟合或“过度烹饪”一个 PR 的情况。”
- 对“顺序契约改成先写不变式、再在小范围内系统搜索”的收窄写法：“然后第三条按刚刚说的这个来.”
- “全局 CLAUDE.md 里加审查轮数上限那一条，你没点头，我没改；a2a 的 executor.md 也没动。 这两个都改一下”

决定（写入[执行主控角色卡](../roles/executor.md)）：

- 每个候选完整审查一次。要求修复的问题修好后，最多再做一次复审，复审只看修复范围，先重跑上一轮的反例。
- 复审又找出问题时，不开第三轮去找下一个反例：
  - 同一条不变式又被新的反例打破（或审查报告写了 `needs model`）：先在 ticket 里写出这些不变式，按 `evidence-first-testing` 的顺序契约在小范围内系统搜索，把每个反例留成回归测试并加进完成条件；
  - 其他问题：先复现出红态再修，用红绿证据关闭。
- 门禁不变：集成前仍需一次绑定最终候选提交的“可合并”审查（`workbench/src/gates/core.ts` 的 `review_required`）。上面两种情况修完后的这一次，只核对新增的测试能否拒绝错误实现（T-082 的变异检查），不再整体重审。
- 审查意见先复现成红态再修；复现不了就附证据回复审查员，不改代码；落在非目标或本票之外的，登记为后续工作，不在本票修。

同日 skill 一侧的对应改动：behavioral-acceptance-review 的 `FAIL` 必须附实际跑过的反例，并新增 `needs model`；evidence-first-testing 新增“审查意见先复现”和“顺序契约”两节；design-integrity-review 改为实现者自查。见 design-integrity-guardrails `e2b3402`、reality-evidence-engineering `55e591a`。

同日补充：[审查员角色卡](../roles/reviewer.md)加了两条：要求修复的结论必须附实际跑过的反例；复审先重跑上一轮反例，同一条不变式又被打破时报“未完成”并写 `needs model`，不再继续找下一个。
