---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-106-workbench-create-project-task-from-ui.md"]
created_at: "2026-10-19T13:14:18.659114Z"
schema: 1
title: "T-106 BLOCKED：现有门禁没有独立项目、主控必须挂在已有任务上、主控无权调用任务卡命令"
id: "20261019T131418Z-executor-needs-decision-001"
---

s17-t106 按票里“若需比薄层更多的新增设计就停下”的规定停了，状态 BLOCKED。报告在 exec/t106 580373844 的 evidence/2026-10-19-batch17/T-106/RESULTS.md。我核对过它引用的事实：
1. 没有独立的项目记录：listProjects() 是从 tasks 表 DISTINCT project_id 得来的（core.ts:325），ensureProject() 是空实现（panes.ts:117），门禁命令表里也没有注册项目的命令（cli.ts:15）。所以“新建项目”在首个任务出现之前，没法让项目出现在列表里。
2. 主控必须挂在已有任务上：controller_start 和 controller_prepare 都会先查任务，查不到就返回 unknown_task（daemon.ts:334、core.ts:1011）。manifest、启动记录、主控请求上下文也都绑定了 task 和 spec_rev。
3. 主控无权调用任务卡和注册命令：在合成的主控身份下实测 CLI，card_template、card_validate、card_save、create 全部返回 worker_command_forbidden（cli.ts:204）。Stop 转交合同也只允许 inbox 和 stop（relay.ts:110）。放开它们属于权限变化。
worker 没有绕过这些限制：没有建占位任务，没有给主控 operator 凭据，也没有直接写库。没有模型调用。
最小选项（设计取舍，需要用户定）：
A（推荐）：
- 门禁新增“项目”记录和注册命令，只允许 operator 调用，界面通过它建项目。
- 新增“项目级主控”身份，不绑定任务。它只有只读的草稿权限：可以调用 card_template、card_validate，写草稿文件；不能 card_save，也不能 create。
- 用户在界面上确认之后，由界面以 operator 身份调用 card_save 和 create 注册任务。注册权仍在用户手里，主控只负责起草。
- 改动量：门禁加 1 张表和 2 个命令，加一个新的主控身份类型，权限只给草稿。
B：
- 同样新增项目记录和注册命令；但不用主控起草，界面直接给一张简化表单，只填标题、目标和完成条件命令，其余字段由脚本按模板填默认值，用户确认后注册。
- 不需要新的主控身份，也不消耗模型回合，但“主控代办”这一点就没了。
C：
- 先只做“新建项目”这一步，任务仍按现状注册；以后再定主控起草怎么做。
在用户决定之前，T-106 停着。s17-t106 保持空闲，没有动产品代码。