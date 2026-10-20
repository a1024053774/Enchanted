---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md"]
created_at: "2026-10-19T15:00:56.752134Z"
schema: 1
title: "T-107 缺口上报：结构化信号区分不出“等待用户回答”和“等待主控回答”；worker 派发没有父 launch 绑定"
id: "20261019T150056Z-executor-needs-decision-001"
---

T-107 状态 INCOMPLETE，候选 exec/t107 3c3f2e9e1，独立审查正在进行。真实 Electron electron-03 rc 0，四项都通过：已知坏基线；层级、角色、attempt、git 与三种历史状态；点击聚焦窗格（只读）；窄窗、跨项目往返、设置保留、零写入。
按票第 4 条和“不做”一节，以下缺口不在本票内补，上报如下：
1. 七种状态里的“等待用户回答”和“等待主控回答”：工作台现有的结构化信号区分不出来。按项目规则不能用屏幕文字正则去判断。T-095 的 scripts/agent-status 是给 Herdr 窗格用的，它靠 UI 锚点加 Herdr blocked 状态来交叉印证；工作台的窗格目前没有对应的信号来源。所以侧栏里这两种状态暂时显示为“未知”，系统通知也就从来没有真实触发过。需要另开票，补工作台窗格的“等待回答”信号采集，例如从原生 CLI 的结构化事件、hook 或会话日志里取。
2. 层级：worker、reviewer 的派发记录没有绑定具体是哪个父 launch（哪个主控派的），所以它们暂时挂在所属任务下的“未归属”里，没有缩进在主控下面。需要另开票，在派发时记录父 launch。
另外：这次提交由执行主控代为完成。原因是用户手动把窗格里的 Codex 切成了 gpt-6.1-sol high，这个会话没有 A2A 启动绑定，所以由执行主控照实提交，没有冒用原来的启动记录。用户同时定了“以后都用 6.1 sol high”，AGENTS.md 和 launch-worker 的默认值已改（785779f85）。
请和用户确认这两项缺口是否开票，以及优先级。