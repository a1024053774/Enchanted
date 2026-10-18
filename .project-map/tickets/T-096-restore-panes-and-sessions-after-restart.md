---
id: T-096
title: 工作台重启后恢复之前打开的窗格与对应会话（按记录的启动参数续接，不用裸 resume）
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："重启后继续之前对话打开的面板与相应的会话这个是应该的，不然我每次都要重新打开，手动输 resume 很麻烦"。

机器或工作台重启后，用户之前打开的窗格与其 agent 会话应自动回来：窗格按"项目 → 任务 → agent 会话"的归属重新排好，每个会话按**启动记录里保存的完整 argv** 续接原会话。

背景（事实）：2026-10-17 机器重启后，Herdr 自动用不带参数的 `codex resume` 恢复了 worker（PID 7209），模型、思考强度、沙箱都没有记录；执行主控关掉它，改用 `launch-worker --resume` 重接（launch-97cdf0bc…）。本票要让工作台的恢复路径不重蹈这个问题。

1. 工作台保存"当前打开的窗格集"：每个窗格的 task、role、launch id、session id、窗格位置；写入时机明确（窗格创建/关闭时落盘，不靠退出时钩子）。
2. 重启后恢复：对每个窗格按启动记录的 argv（含模型、思考强度、沙箱、service tier）续接原 session；CLI 实际版本与记录不符、启动记录缺 argv、session 已不存在的，**明确报错并保留该窗格为"未恢复"**，不静默换配置或开新会话。
3. 恢复本身不产生模型回合；用户输入前不调用模型。
4. 沿用 T-091 的多窗格与 T-093 的 profile 记录，不另造一套状态。

## Acceptance

- [ ] 红态：当前 `main` 上重启后窗格集为空、不会自动续接（读回现状）。
- [ ] 绿态：用假 API 起三个窗格，杀掉整个后台与 Electron，重启后三个窗格回来，各自进程身份、task、role、launch 与 argv 与重启前记录一致；模型回合 0。
- [ ] 反例（每个在真实入口失败并保留现场）：启动记录缺 argv；CLI 版本与记录不符；session 已不存在；某窗格恢复失败不影响其余窗格，且不被记成"已恢复"。
- [ ] 不得用裸 `resume` 或默认配置补位；恢复后的 argv 与记录逐字段相等。
- [ ] 不改 Herdr，不写 `~/.claude`、`~/.codex`。
- [ ] `project_map.py status` 0 problems。

## 说明

- 构思主控据用户上述原话建票并标就绪（用户说"这个是应该的"，未单独说"开工"；若不对请撤回）。无真实模型回合，不触及 T-004 停止条件。
- 写入范围预期：`workbench/src/`、`workbench/app/`、`workbench/tests/`、本票证据。
