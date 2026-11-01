---
id: T-220
title: 私有 core 崩溃后，由谁拉起新 core、新 core 继承谁的环境
type: research
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## Question

T-212 让编排后台用受控环境启动私有 hc core，所以终端里拿不到 `A2A_*`、agent 会话标记、hc 私有目录等变量。但 core 被杀或崩溃之后，第一个发起调用的 hc 客户端会自己拉起新 core，新 core 用的是这个客户端的环境。这个客户端可能是编排后台，也可能是终端里的 agent（例如执行 `hc` 命令的 Claude Code）。如果是后者，之后新开的终端会继承那个 agent 的环境。

T-211 只根据源码作了推断。T-212 在 `round2-crash-01/02` 里实测：后台记录了 `hc_connection_lost`；终端内脚本调用 `hc server start` 没有在期限内返回，所以没测到新 core 的环境。证据在 `a2a-worktrees/T-212-evidence/round2-crash-observation.json`，归档后在 `evidence/2026-10-31-batch29/T-212/`。

T-212 第三轮 `round3-crash-green-01` 又测到一部分：当终端里没有 hc 客户端时，core 被杀后由重启的编排后台拉起新 core，新 core 下的终端读到的是后台的环境（标记 `T212_CORE_STARTER_MARKER=restarted-daemon`，私有 `XDG_STATE_HOME`）。终端内 agent 抢先拉起的情形仍未测到。

T-212 已经做到：core 断开后，侧栏把该终端标为未知；接回时，记录里留下 `shell_screen_inexact` 和 `screen: inexact`。界面上还没有任何“历史不完整”的提示，后台对 inexact 屏幕仍照常复位并接回；这两点在这里决定。

要查明以下几点：
1. core 崩溃后，哪些调用会自动拉起新 core。
2. 终端内的客户端能否抢先拉起它。
3. 由它拉起时，新终端实际拿到的环境是什么。
4. core 崩溃后，编排后台应如何检测、由谁按受控环境重新启动 core。

在受管窗格切片之前回答这些问题。崩溃后屏幕标为 inexact、历史丢失（T-211 第 3 项）的处理也在这里一并核对。

## Resolution

（未开始）
