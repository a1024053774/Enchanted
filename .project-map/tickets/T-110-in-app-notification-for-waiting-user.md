---
id: T-110
title: 应用内通知：会话进入“等待用户回答”时在 app 内提醒（不调用系统通知）
type: build
status: closed
blocked_by: [T-108]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：T-107 缺口 3，**修改 T-107 第 5 条**。用户逐字（2026-10-20，执行主控会话，经执行主控转述 `20261020T053124Z-executor-needs-decision-001`）："a2a-构思主控 那边什么都没收到,关于 a.是否可以用 mcp 或者 hook,这种让模型想要发起问题时,让它调用相应的接口在我们的界面上展示出来 b.这种结构要清晰的展示出来[Image #3] 类似于这种,结构层次要清晰. c.这个要做的,不调用系统通知了,只在我们 app 内部通知"

用户决定：只做 app 内通知，**不调用系统通知**。取代 T-107 第 5 条里"一次系统通知"。

1. 会话进入"等待用户回答"（T-108 的信号）时：侧栏该会话项与所属项目行高亮；应用内出现一条通知（右上角提示条或侧栏角标），点击聚焦对应窗格或问题条目；只通知"等待用户回答"，不通知普通运行/空闲变化。
2. 通知在问题被回答、取消或会话结束后自动消失；同一问题只提醒一次，不重复刷。
3. 设置里可关闭应用内通知。不请求 macOS 通知权限，不调用系统通知 API。
4. 应用在后台时：Dock 图标角标显示等待用户回答的数量（这是应用自己的图标，不算系统通知；若用户不要，可关）。

## Acceptance

- [x] 红态：当前无应用内通知。绿态：真实 Electron，真实或回放的"等待用户回答"信号出现 → 侧栏高亮和应用内通知同时出现，点击聚焦；回答后消失。
- [x] 反例：同一问题不重复提醒；运行/空闲变化不提醒；代码里没有调用系统通知 API（检索证据）。
- [x] 依赖 T-108 的信号；`project_map.py status` 0 问题。

## Resolution

2026-10-20，执行主控。PASS。exec/t110 以 `--no-ff` 合入 main（360f29898），没有 push。

- 实现（worker s18-t110，最终候选 aea89b9d5）：
  - 只用 T-108 的“等待用户回答”信号（同一个可信度判定）；“未知”、权限等待、运行和空闲都不提醒。
  - 侧栏高亮与应用内通知同时出现，点击后聚焦对应窗格；回答、取消或结束后消失；同一问题只提醒一次。
  - 设置里有独立开关，可以分别关闭应用内通知和 Dock 角标。
  - Dock 角标用 app.dock.setBadge。当前固定的 Electron 43.4.1 不会主动请求通知权限，但如果用户拒绝了通知权限，不保证角标可见。
  - 修复链：
    - 4455b51c8：侧栏读取失败时，让通知和计数失效；
    - 4a6d6bb9e：断连期间重载时，保留已绑定的视图；
    - 92bc88208：只在连接成功、发送前分配 window 序号。断连期间失败的命令曾经消耗序号，导致重连后 window_answer 一律被拒；
    - aea89b9d5：测试清理时，等待身份一致、正在退出的 CLI 进程。
- 真实入口（真实 Claude CLI 加本地假 API 加 Electron，不调用模型），执行主控在沙箱外运行 /private/tmp/t110-outside-08.json：PASS。
  - 四个红态都被拒：hidden-notices、disconnected-badge、reconnect-view、reconnect-answer；
  - green、disabled 都 PASS；
  - RECEIPT-COMPARE PASS。
- 检索：候选的 workbench/app、src、hooks 里没有 Notification 或系统通知 API，也没有通知权限请求，grep 退出码 1；唯一的角标调用在 main.ts:46。
- 独立审查：
  - 01 NO_GO（F1：断连后 Dock 角标残留）；
  - 02 产品范围 PASS（含 92bc88208 序号改动与清理放宽的范围审查）。唯一的 INCOMPLETE 是稀疏 worktree 的地图缺口；合入后 main 上 `project_map.py status` 0 问题。
  - 审查附的 REVIEW-OUTSIDE-02.sh 额外 Electron 变异没有跑完：脚本依赖 rg，沙箱外的 PATH 里没有，在系统通知检索一步就中止了。同一次运行的边界合同变异都按预期被拒（unknown-notifies、answer-keeps-notice、switch-ignored）。系统通知检索由执行主控用 grep 补做。
- 合入后 main 上 test_t091_pane_ipc、test_t108_questions、test_t110_window_sequence、test_t110_reconnect_view 都 PASS。
- 过程记录：执行主控为了腾出内置盘空间（当时只剩 411MB），清理了 /private/tmp 下已关闭票的临时目录，其中误删了 T-112 正在使用的 t108-* 夹具（见 issue 20261020T130602Z）。
