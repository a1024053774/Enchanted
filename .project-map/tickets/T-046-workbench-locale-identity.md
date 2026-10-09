---
id: T-046
title: 工作台启动器的进程身份核对与 locale 无关
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
---

## What to build

T-045 调查中发现（`evidence/2026-10-09-batch5/T-045/RESULTS.md`"日志位置与独立发现"）：`a2a/scripts/workbench_runtime.py` 用 `ps -o lstart=,command=` 的文本记录并比对工作台进程身份，`lstart` 随调用者 locale 变化（中文与英文格式不同），换一个 locale 调用 `workbench status/stop` 会误报"PID 身份已改变"。改为与 locale 无关的身份核对，同时仍拒绝指向其他进程的记录；正在运行的工作台用旧格式写的记录必须仍能被识别（否则无法正常停止）。

这也是 T-040 第 3 项"第一次经 Synara 的日常分派"使用的真实任务：主控经门禁 create → run，由 Synara 原生 Codex 会话完成。

## Acceptance

- [ ] 独立 oracle `acceptance/workbench_identity_oracle.py` 在修复前失败（证据 `evidence/2026-10-09-batch6/T-046/oracle-red-base-3f274dd.json`），在候选上通过：三种 locale 写入的旧格式记录在三种 locale 下都识别为运行中；指向其他进程的记录被拒绝；进程已退出时报告未运行。
- [ ] 经门禁 run 自动完成：worker 显式 `a2a_submit`，独立 oracle 通过，CAS 集成，自动回收；任务窗口自动显示任务与 worker。
- [ ] 只改 `a2a/scripts/` 下的启动器文件。

## Resolution
