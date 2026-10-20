---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md"]
created_at: "2026-10-20T05:31:24.362855Z"
schema: 1
title: "用户对 T-107 三个缺口的新方向：a 用 MCP 或 hook 让模型主动上报提问；b 层级树结构要清晰；c 只做 app 内通知，不用系统通知"
id: "20261020T053124Z-executor-needs-decision-001"
---

用户逐字（2026-10-20，执行主控会话）："a2a-构思主控 那边什么都没收到,关于 a.是否可以用 mcp 或者 hook,这种让模型想要发起问题时,让它调用相应的接口在我们的界面上展示出来 b.这种结构要清晰的展示出来[Image #3] 类似于这种,结构层次要清晰. c.这个要做的,不调用系统通知了,只在我们 app 内部通知"
对应 T-107 的三个缺口（详见收件箱 20261020T052452Z-executor-report-001）：
a. “等待用户回答”和“等待主控回答”的信号：用户提议，模型想提问时通过 MCP 工具或 hook 调用我们的接口，在工作台界面上展示问题。要注意的取舍：项目规则是“权限只在工作台内、经每会话启动参数传入、不写 ~/.claude 和 ~/.codex”；T-069 说过不用 Synara 的 MCP 网关。所以需要定的是：用 hook 还是 MCP；Claude Code 和 Codex 分别用哪种；问题和回答怎么回流到 CLI。
b. 层级结构要清晰。用户附了一张参考截图，但执行主控这边只收到一个 PNG 占位图标，看不到内容，已请用户重发或描述。这一项对应“派发记录父 launch，worker 挂到主控下”，加上视觉层次。
c. 只做 app 内通知，不调用系统通知。这会改 T-107 原来“一次系统通知”的要求。
另外：我上一条 report 只写进了收件箱，会话重启后没有发跨会话消息，所以你那边没有被唤醒。这次会同时发消息。
请和用户澄清后开票并标就绪。