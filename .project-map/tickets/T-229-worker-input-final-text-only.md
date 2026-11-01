---
id: T-229
title: worker 窗格里的用户输入只记最终发出的那一条，不记按键
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

用户 2026-11-01：“在终端输入的算是用户输入的,然后只记录我发送之后的完整的这一条,不要把输入过程中的操作以及其他琐碎的东西记录进去,只记录最终的我发的话”。

主控终端里已经是这样（T-133 选项 A，T-216 沿用）：Claude Code、Codex 的提交钩子报来全文，一次提交记一条。受管 worker 窗格（T-206）还不是：

- `workbench/src/inputDraft.ts` 把 attach 看到的按键拼成一句，按回车时记一条；按过方向键、Home 等时，记录里还带 `content: { action: "terminal-submit", keys: [...] }`，就是输入过程的按键；
- 用 ↑ 调出历史、补全时，attach 拼出的那句和 CLI 实际提交的不同，只能标 `text_uncertain`。

要做的：

- 用户输入记录只留最终发出的文字，不再记 `keys`。
- Claude Code、Codex 的 worker 窗格，文字取 CLI 提交钩子报来的全文；后台自己派发进去的（任务书、门禁反馈、主控答复）不记，判断依据与 T-216 相同：对上我们自己送进去、还没被认领的派发原文。
- agy、opencode 没有提交钩子，仍按 attach 拼出的那句记；拼不准时照旧标 `text_uncertain`，不改成猜测。
- 在受管 worker 窗格里直接输入仍记为人工介入（AGENTS.md），这一点不变。

worker 窗格切到 hc 之前或之后做都可以；如果先切 hc，派发的认领沿用 T-216 的 `hc_send_intent`。

## Acceptance

- [ ] 先写下这条记录可能出错的方式，测试对着它写。
- [ ] 修前经真实入口留下红态：在 Claude、Codex worker 窗格里（本地脚本化接口）按方向键改字后发送，记录带 `keys`；用 ↑ 调出上一句发送，记录的文字与实际提交不一致或标了 `text_uncertain`。
- [ ] 修后：同样操作只记一条，文字等于 CLI 实际提交的全文，没有 `keys`；任务书、门禁反馈、主控答复不进用户输入；同一段文字用户第二次提交仍记一条。
- [ ] agy、opencode worker 的记录没有 `keys`，拼不准时标 `text_uncertain`。
- [ ] 人工介入事件照旧产生。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## 不做

改主控终端的记录方式；改门禁的人工介入规则。

## Resolution

（未开始）
