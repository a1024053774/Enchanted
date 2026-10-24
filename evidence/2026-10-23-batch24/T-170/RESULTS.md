# T-170 启动失败的 attempt 无法回收：结果

- 写入者：执行主控（Claude Code）。T-164 第三轮发现，按 T-004 自建；构思主控 answer 20261024T135340Z-ideation-answer-001 要求核对 B a2 现场并裁定。
- 基线：main `6412c5e08`（产品代码与 e3b14d27b 相同）。真实后台、门禁、PTY；Codex 换成编译的替身，重放 B a2 原始终端输出（`b-a2-pty.raw`），`--version` 答 `codex-cli 0.164.0`；不发模型请求。
- 结果见 `CHECKS.json`；运行目录按 T-088 归档（`*.archive.json`）。

## 根因

B a2 的 Codex CLI 在启动时因账号路由超时退出 1，没有原生会话；后台如实记 `launch_failed`，窗格 `failed`、`stopped`。reclaim 先要求 `runtime_identity.native_session !== null`（报 identity_conflict），即使放过这一条，失败窗格 `blocked=true` 又会被 `checkErrorReclaim` 与 `run_blocked` 拒绝。没有任何门禁路径能回收这种 attempt。

## 修改

`workbench/src/gates/core.ts` reclaim：attempt 与实时读数的原生会话都为空、窗格已停止、未在运行、没有回合、错误读数为 provider 已不在且无活动回合时，视为“从未启动”，跳过原生会话与 blocked 检查，照常走停止、归档、清理。其余情况不变。

## 证据

| 项 | 结果 |
| --- | --- |
| 红态（`--revision 6412c5e08`，red-1/2） | 2/2 `red_reproduced`：leader 已观察到、原生会话为空，reclaim 报 identity_conflict，再派发报 already_claimed，与 B a2 一致 |
| 绿态（green-1/2） | 2/2 PASS：reclaim 受理，工作区移除，任务可再派发 |
| 反例（`--scenario hang`，hang-1） | PASS：替身不退出、原生会话为空时 reclaim 仍拒绝，工作区保留 |
| 回归 | T-158 revise-retry、T-146 session-state、T-146 native exit probe 均 PASS |
| 早期无效夹具 | `runs-python-standin`：Python 替身的进程命令是解释器路径，产品认不出 leader（leader_pid 为空），与真实现场不符，作废保留；改为编译替身后重跑 |

## 未覆盖

- 未构造“清空条件之一”的坏实现逐项变异；反例只证明活进程不被回收。
- 未在真实 Codex 账号路由失败下复验（外部故障不可控）。
