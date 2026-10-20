---
id: T-108
title: 原生提问信号：用每会话 hook 采集“等待用户回答/等待主控回答”，在界面展示问题并把答复写回窗格
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：T-107 缺口 1（报告 `20261020T052452Z-executor-report-001`）。用户逐字（2026-10-20，执行主控会话，经执行主控转述 `20261020T053124Z-executor-needs-decision-001`）："a2a-构思主控 那边什么都没收到,关于 a.是否可以用 mcp 或者 hook,这种让模型想要发起问题时,让它调用相应的接口在我们的界面上展示出来 b.这种结构要清晰的展示出来[Image #3] 类似于这种,结构层次要清晰. c.这个要做的,不调用系统通知了,只在我们 app 内部通知"

用户逐字选项（2026-10-20，会话"a2a-构思主控"，AskUserQuestion）："A 先用 hook (Recommended)"，选项原文："用 Claude Code、Codex 自带的 hook 事件抓原生提问(如 Claude 的 AskUserQuestion、权限请求),在界面展示问题和选项;答复由界面写回该窗格。不需要模型“记得”调我们的接口,也同时解决“等待用户/等待主控”的状态信号。"

约束（AGENTS.md）：hook 只经每会话启动参数传入，不写 `~/.claude`、`~/.codex`；不用 Synara 的 MCP 网关；语义识别不靠正则或屏幕文字关键词。MCP 提问工具这次不做（用户未选 B）。

1. **采集**：Claude Code 用 hook 事件（`PreToolUse` 匹配 AskUserQuestion、权限请求、`Notification` 等，具体事件名先读 CLI 文档与已装版本核对）；Codex 用其文档化的 hook 或会话日志里的结构化事件（T-095 已有对 Codex 提问的读取，沿用）。先做**小探针**确认每家实际能拿到什么字段（问题文本、选项、是否阻塞），探针不通的那家上报缺口，不退回屏幕文字。
2. **状态**：采集到的事件驱动 T-107 的"等待用户回答"（会话的提问对象是用户）与"等待主控回答"（对象是主控，沿用 T-095）；提问被回答或取消后状态回落；识别不到仍显示"未知"，不上调。
3. **展示**：界面里有问题条目（面板或侧栏内的展开区），展示问题、选项、来源会话；用户点选或写几句作答，答复**写回该会话窗格**，并记为一条 `answer` 用户输入且指向该问题（T-071 的主控提问语义，不新造第二套）。
4. 提问来自受管 worker 时，答复路径不得绕过门禁语义（沿用 T-095 与 T-071 的处置规则）。
5. 事件进现有 SQLite 事件流，只追加。

## Acceptance

- [x] 探针：每家 CLI 的 hook 事件样本原文入证据，写明能取到的字段与不能取到的。
- [x] 红态：当前"等待用户回答"信号缺失。绿态：真实 Claude 会话触发一次 AskUserQuestion，界面出现该问题和选项，状态为"等待用户回答"；界面作答后答复进入窗格、状态回落、事件流里有对应 `answer`。Codex 同样走一次真实或已记录的真实原件回放。
- [x] 反例：hook 不触发或字段缺失时显示"未知"而不是运行中/空闲；对已回答的问题重复作答被拒；没有任何全局配置文件被写（前后对比 `~/.claude`、`~/.codex` 无变化，或由沙箱禁写）。
- [x] 真实模型回合数照实记录并控制在最少；`project_map.py status` 0 问题。

## 不做

不做 MCP 提问工具；不改门禁语义；不做自然语言解释答复。

## 裁定（2026-10-20，真实回合与 CLI 版本）

用户逐字（2026-10-20，执行主控会话，AskUserQuestion 的其他答复，经执行主控转述 `20261020T061506Z-executor-report-001`）："跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的"。

1. T-108 照跑 **1 个真实 Claude 根回合**（haiku 5.5 low，走 T-093 正常登录入口）。
2. Claude CLI 版本不再锁定：把 T-093 入口的精确版本锁定改为"读取实际版本并记录"；在当前版本（本机 2.1.304）上用探针重新确认版本敏感的假设（onboarding、内部状态），不成立就上报；其余隔离与凭据检查一律不放宽。

## Resolution

2026-10-20，执行主控。PASS。exec/t108 以 `--no-ff` 合入 main（af3a6d44e），没有 push。

- 实现（worker s18-t108，最终候选 ee17cddf8）：
  - Claude 与 Codex 的 hook 采集原生提问：侧栏显示“等待用户回答”，界面作答写回原 PTY；
  - 当前回合可信度统一判定：字段缺失、无法核实、非法响应、其他工具的权限请求，一律显示“未知”，撤销作答资格，PTY 零后续写入；
  - 同问题的权限请求必须带有和保存的问题一字不差的 questions 内容；
  - 原生确认早到时作答判为成功，写入链不被普通拒绝堵塞。
  - 中间合入了 main（d42e8b3fa，含 T-111）。
- 探针：Claude 2.1.304、Codex 0.163.0 的 hook 样本原文入证据。
- 真实回合：Claude 1 根、3 次模型调用，PASS（用户：“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”）。Codex 用已记录的真实 CLI 原件回放，新增真实回合 0。
- 无模型的原生完整入口（CLI 加 Electron）：8 项 PASS，含首答回执和作答后的后续输入。
- 默认合同：429 项 hook 失败矩阵，加 14 项作答生命周期。每轮修复前的候选都取得了业务红态。
- 独立审查六轮：
  - 01 NO_GO：缺 tool_name；
  - 02 NO_GO：未核实的 hook 后仍可作答；Stop 缺 stop_hook_active；
  - 03 NO_GO：缺 cwd、transcript_path、prompt_id；权限请求被旧问题遮蔽；
  - 04 NO_GO：只靠工具名就能伪造同问题权限；
  - 05 NO_GO：确认早到时被误拒，并堵死写入链；
  - 06 产品范围 PASS，唯一的 INCOMPLETE 是 worktree 稀疏检出造成的地图缺口。执行主控在沙箱外跑了 REVIEW-OUTSIDE-06：PASS（早到、晚到、原生入口、questions 均 PASS）；合入后 main 上 `project_map.py status` 0 问题。
- 执行主控裁定（来自 worker issue 20261020T081754Z-worker:s18-t108-issue-001）：同一个 AskUserQuestion 自身发出的 PermissionRequest，仍归属该提问；第四轮后进一步收紧为必须有完整的 questions 正向证明。
- 合入后 main 上 test_t091_pane_ipc.mjs、test_t108_questions.mjs PASS。
- 遗留：Codex 异步 hook 只返回 accepted，不能证明阻塞，保持“未知”；起点已有的 Codex xhigh 强制规则交给 T-112 处理。
