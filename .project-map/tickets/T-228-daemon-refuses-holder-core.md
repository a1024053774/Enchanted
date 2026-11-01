---
id: T-228
title: core 崩溃约 3 秒后，编排后台起不来：holder 重拉的 core 被当成外来的拒掉
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

T-220 实测（[结果记录](../../evidence/2026-10-31-batch29/T-220/RESULTS.md) 第 1、4 节）：

- 私有 core 死后约 3.1 秒，holder（终端进程的父进程）自己重拉一个 `herdr-core serve`。它是 holder 的子进程，用原来的受控环境和私有状态目录，原来的终端都还在。
- 编排后台启动时，`workbench/src/hc.ts` 的 `HcRuntime.start()` 要求 core 的父进程是 1。holder 重拉的 core 父进程是 holder，于是报 `private hc core did not detach`，后台直接退出。所以只要 core 崩溃后超过约 3 秒才启动后台，后台就起不来，直到有人手动结束那个 core。
- 反过来，项目终端里的 hc 调用拉起的 core（父进程是 1，带着那个窗格的环境，状态写进用户默认 XDG 目录）却被接受，后台在它上面照常开终端。
- T-212 第三轮的崩溃绿态之所以通过，是因为测试里后台在 holder 重拉之前就重启了。

要做的：后台认 core 的依据，从“父进程是 1”改为“是本私有会话、受控环境下的 core”。

- 具体判据实测后定，例如核对私有状态目录里 core 登记的进程与当前 core 一致。写进代码注释。
- holder 重拉的 core：接受，窗格照常接回，屏幕记 inexact。
- 认不出的 core：不接受，后台不在上面开终端，并把原因记进事件、显示出来。崩溃后外来 core 的整体处理等 T-220 的决定，本票只保证不再静默接受它。

## Acceptance

- [ ] 先写下认 core 可能出错的方式，测试对着它写。
- [ ] 修前经真实入口留下红态，沿用 T-220 探针二的做法：
  - 停后台，杀 core，等 holder 重拉，再启动后台：后台退出，报 `private hc core did not detach`；
  - 终端里的 hc 调用抢先拉起 core 后重启后台：后台接受，并在上面开出终端。
- [ ] 修后同两种场景：
  - holder 重拉的 core 被接受，原终端接回，`shell_reattached` 记 `screen: inexact`，shell 进程号不变；
  - 外来 core 不被接受，后台不在上面开终端，事件里有原因。
- [ ] T-212 的 `test_t212_shell_hc_e2e.py --core-crash` 与 `--electron-screen --mismatched-screen` 回归通过；用户自己的 core 与状态目录前后不变。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。用户 2026-11-01 改分工：“antigravity 换用里面的 4 argon 模型可以做一些小任务, gpt 做审核,work 的工作由你在当前会话中做.”

## Resolution

（未开始）
