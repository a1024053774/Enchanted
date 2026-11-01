---
id: T-231
title: test_native_final_read.ts 在 HEAD 上失败：离线夹具靠 hook 触发扫描，被 noncurrentHook 拒掉
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

T-227 第二轮发现，范围外（[结果记录](../../evidence/2026-10-31-batch29/T-227/RESULTS.md)）：`workbench/tests/test_native_final_read.ts` 在 HEAD（`bbf8d5f80`）的 `panes.ts` 上也失败，九个场景里有八个报 `hook_native_session_mismatch`，只有 `unbound` 通过。

- 测试用 `UserPromptSubmit` hook 让扫描绑定 native 会话；`noncurrentHook`（`workbench/src/questions.ts`）会拒掉 `session_id` 与 `pane.native` 不同的 hook，夹具里 `pane.native` 还是空，所以扫描根本没跑。
- 不是 T-227 引入的；哪一次提交开始失败还没查。
- 这份测试本该保护的是退出、终止、关闭、回收时的最后一次原生日志读取（T-075-4），现在它不再提供证据。

要做的：先查清是测试过时，还是产品里 Codex worker 的 native 会话绑定真的坏了；按查到的根因修测试或产品。

## Acceptance

- [ ] 写明从哪次提交开始失败，以及原因：测试过时，还是产品行为变了。
- [ ] 若是产品缺陷：先经真实入口留红态，再修。
- [ ] `test_native_final_read.ts` 九个场景按原意图通过；用一个已知的坏实现（例如去掉退出前的最后一次读取）证明它仍能识别。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

（未开始）
