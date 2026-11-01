---
id: T-229
title: worker 窗格里的用户输入只记最终发出的那一条，不记按键
type: build
status: closed
blocked_by: []
claimed_by: executor (Claude Code, 2026-11-01)
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

- [x] 先写下这条记录可能出错的方式，测试对着它写。
- [x] 修前经真实入口留下红态：在 Claude、Codex worker 窗格里（本地脚本化接口）按方向键改字后发送，记录带 `keys`；用 ↑ 调出上一句发送，记录的文字与实际提交不一致或标了 `text_uncertain`。
- [x] 修后：同样操作只记一条，文字等于 CLI 实际提交的全文，没有 `keys`；任务书、门禁反馈、主控答复不进用户输入；同一段文字用户第二次提交仍记一条。
- [x] agy、opencode worker 的记录没有 `keys`，拼不准时标 `text_uncertain`。
- [x] 人工介入事件照旧产生。
- [x] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## 不做

改主控终端的记录方式；改门禁的人工介入规则。

## Resolution

PASS（2026-11-01）。代码提交 `1e22f08df`。十二轮 GPT 只读审查，第十二轮无阻塞意见。

- 用户输入记录只留最终发出的文字。Claude Code、Codex 取提交钩子报来的全文，后台派发按 T-216 的规则认领；agy、opencode 照旧按草稿记，拼不准只带 `text_uncertain`。人工介入照旧派生。
- T-206 fail-closed 保留：钩子请求没回 ok 就阻断，钩子最多等 8 秒，后台拒绝过期请求。
- 本票引出的阻断后窗格状态问题在本票修（用户 2026-11-01 选“在 T-229 里修”，T-234 并入）：窗口回车不开回合，UPS 确认后才开（方案 1，用户：“还是在 T-229 里直接做方案 1吧,相关回归也做”）；草稿按回车后有没有新输入释放；记录即提交点，之后的写入失败标窗格失败、不阻断；Codex 在 Esc 后的新回合是新提交。
- 回归里 T-157 stop-input、T-165 ordered、unrelated-stop 的界面状态检查时好时坏，基线上同样失败，登记 T-235，不在本票修。

证据见 [结果记录](../../evidence/2026-10-31-batch29/T-229/RESULTS.md)。
