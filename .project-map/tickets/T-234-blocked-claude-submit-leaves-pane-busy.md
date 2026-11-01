---
id: T-234
title: Claude Code、Codex worker 窗格里被阻断的用户提交，窗格停在“忙”，直到下一次成功提交
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

T-229 第七轮验证发现，范围外（T-229 结果记录）：用户在受管 worker 窗格里提交，UserPromptSubmit 钩子把这次提交阻断后（用户输入记不下来，或后台没在期限内处理），窗格停在 `busy`，要等用户下一次成功提交才回到正常。这期间派发会一直等。

- Claude Code：`workbench/src/panes.ts` 的窗口输入把回车当作输入证据，先标 `busy`，之后靠 UPS 开回合、靠 Stop 回到空闲。提交被阻断时这两样都不会来。`active`、`cli_turn` 都是空的（T-229 `r7-request-hangs-claude`）。
- Codex：回车时就建了 `active`，Codex 自己的 rollout 照样写 `task_started`，`active.nativeTurn` 被绑上，但被阻断的回合不发 Stop（T-229 `r7d-request-hangs-codex-2`：`state: busy`，`active.nativeTurn` 有值）。

T-229 之前，记不下的输入在 attach 那一侧就失败了，回车根本没写进去，所以碰不到这条路径。T-229 把 Claude、Codex 的记录挪到钩子之后，回车已经送进 CLI 才被阻断。

要做的：钩子阻断了一次用户提交时，窗格要回到阻断前的状态（空闲，或原来的回合），不留没有回合的 `busy`。阻断是后台给出的，就由后台在同一处改窗格状态；钩子命令自己给的阻断（后台没回、超时）后台不知道，要想清楚怎么让窗格得知，不要靠猜。

## Acceptance

- [x] 先写下这条路径可能出错的方式，测试对着它写。
- [x] 修前留红态：用 T-229 的 `--case record-fails`、`request-hangs`，两种 CLI 被阻断后窗格 `state` 都为 `busy`。
- [x] 修后两种 CLI、两种情况窗格都回到空闲，之后主控派发能照常送进去。
- [x] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

并入 T-229 关闭（2026-11-01）。用户选在 T-229 里修（选项“在 T-229 里修”）。最终做法与本票最初设想不同：不在阻断后恢复窗格，而是窗口回车根本不改窗格状态，回合在后台确认 UPS 后才开始（方案 1），所以被阻断的提交什么都不改。修前红态见 T-229 `r7-request-hangs-claude`、`r7d-request-hangs-codex-2`；修后两种 CLI 的 `record-fails`、`request-hangs` 等阻断场景都检查窗格空闲、之后的派发照常送进去，变异 `enter-starts-turn` 失败在这两项。审查与证据见 [T-229 结果记录](../../evidence/2026-10-31-batch29/T-229/RESULTS.md)。
