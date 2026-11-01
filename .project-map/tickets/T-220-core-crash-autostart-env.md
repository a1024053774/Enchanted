---
id: T-220
title: 私有 core 崩溃后，由谁拉起新 core、新 core 继承谁的环境
type: research
status: closed
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

2026-11-01 事实查明（PASS），[结果记录](../../evidence/2026-10-31-batch29/T-220/RESULTS.md)。

1. holder 发现 core 不在后，约 3.1 秒自己重拉，新 core 用原受控环境与私有状态目录；运行中的编排后台不重拉、不重连。没有 holder 时，测过的九条 hc 命令都会拉起 core。
2. 终端里的 hc 调用能抢先：它是即时的，holder 要等约 3 秒。
3. 由终端拉起时，新 core 和它开的终端带着那个窗格的环境，包括它的 `A2A_TERMINAL_TOKEN`；状态写进用户默认的 XDG 目录；原来的终端全部丢失，后台重启后记为 `shell_exit_unconfirmed`，关不掉。
4. 后台 `HcRuntime.start()` 要求 core 父进程是 1：holder 重拉的 core 被拒，后台起不来；终端拉起的外来 core 反而被接受。

用户决定（2026-11-01，执行主控会话）。执行主控提出：Enchanted 终端里只用 a2a 命令，a2a 命令建在 hc 上，身份取终端令牌；终端去掉私有 core 的 `HC_*` 地址变量；理由是 agent 若用裸 hc 往别的终端发字，后台没有记录，那段文字会被记成用户输入。用户回答：“确认”。

- 项目终端启动时去掉 `HC_SOCKET`、`HC_SESSION`、`HC_TERMINAL_ID`、`HC_TERMINAL_SOCKET`。终端里敲 `hc` 用的是用户自己的 hc 设置，碰不到私有 core；终端之间发字、查看都经 a2a 命令。建造票 [T-230](T-230-enchanted-terminals-a2a-only.md)。
- 后台按身份认 core、断开后自己接回、认不出的不接受：[T-228](T-228-daemon-refuses-holder-core.md)，先做。
- 界面：标 inexact 的窗格显示“历史不完整”；后台对 inexact 屏幕照常复位并接回，不改。并入 T-230。
- T-226 Q3 随之定为 A（后台独占重启，画面不完整时明确提示，身份核对通过才继续）。
