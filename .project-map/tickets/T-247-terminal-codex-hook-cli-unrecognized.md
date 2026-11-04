---
id: T-247
title: 普通终端里交互式 Codex 的钩子认不出是哪个 CLI，会话号和回合状态都报不上来
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by: executor
ready_rev: 1
---

## What to build

2026-11-04 补做 T-246 的 Codex 嵌套端到端（用户：“这条要做”）时发现：普通终端里交互式运行的 Codex（v0.164.0）报不出自己的会话。“复制深度链接”一直显示“Codex 还没报来这次会话的会话号”，`native_session` 一直为空。内层的 `codex exec` 却能报上来。

钩子探针（`--probe`，结果见 `evidence/2026-11-03-batch31/T-246/codex-nested/probe-1.json`）显示原因：

- `a2a hook`（`workbench/src/terminalCli.ts`）先按环境变量判断是哪个 CLI：Codex 要求有 `CODEX_THREAD_ID`（`terminalClis.ts` 的 `inCommand`）。
- 交互式 Codex 不给它的钩子进程设 `CODEX_THREAD_ID`。钩子因此认不出 CLI，不带 `cli`、`cli_pid` 上报，后台就丢掉了这条会话报告和回合状态（T-195、T-242 的普通终端功能）。
- 内层 `codex exec` 能报上来，只是因为它继承了外层 shell 工具环境里外层的 `CODEX_THREAD_ID`。

影响：普通终端里交互式 Codex 的深度链接（T-195）和回合状态（T-242）从来没有生效过。此前的端到端测试只在普通终端里跑过 Claude Code。有角色的终端主控（T-133）不受影响，因为那条路径按 `session_id` 与已批准角色的会话核对，不看 `cli`。

要做的：钩子由运行它的 CLI 启动，最多经过一层 shell 中转，所以改为跳过 shell 后取第一个祖先作为报告者，它不是认识的 CLI 就不报，不看环境变量。`a2a request` 等命令仍按原来的 `commandCli`。

## Acceptance

- [x] 修前红态：真实入口下外层交互式 Codex 报不出会话。
- [x] 修后绿态：Codex 嵌套端到端八项通过，变异体失败于预期处；t246（Claude）、t242、t195、t184、t133 回归通过。
- [x] 独立审查无未处理的阻塞意见。

## Resolution

2026-11-04 关闭（PASS）。`workbench/src/terminalCli.ts` 的 `hook` 跳过 shell 中转后取第一个祖先，它不是 Claude Code 或 Codex 就不上报 CLI。修前红态：真实 Codex 嵌套中外层报不来会话；假进程树（真实 `a2a hook` 入口）失败于 A、B、C、D、G。修后：真实 Codex 嵌套八项 PASS（两次），假进程树七种情形 PASS。第一版修法“最近的 CLI 祖先”保留为变异体，失败于 C、G（审查阻塞 1、2）。t246、t242、t195、t184、两项 t133 回归 PASS。复审的阻塞查明是复审员沙箱不允许执行 `/bin/ps`，已附复现证据答复。已知局限：运行者装在带空格的路径下时不上报；以 Codex 沙箱模式运行时钩子能否读进程表未核对。

证据：[T-247 RESULTS.md](../../evidence/2026-11-03-batch31/T-247/RESULTS.md)。

2026-11-04 补记，局限修复（用户：“这两个局限要解决”），**PASS**：
- 带空格路径：包装脚本声明 `A2A_HOOK_CLI`、`A2A_HOOK_PID`，钩子按进程树（pid、ppid、可执行文件名）核对，不再拆 argv。
- npm Codex：只有声明的进程是 Node 等运行时，才认它的同名原生子进程。
- 沙箱：真实交互式 Codex 在沙箱外运行钩子，两种沙箱模式实测 PASS；`ps` 不能执行时只报事件、不带 cli。
- 审查与复审各一条阻塞，都已修；复审之后按 T-240 改为不变式穷举（1,554 条链全过）。

见 RESULTS“局限修复（第二版）”一节。
