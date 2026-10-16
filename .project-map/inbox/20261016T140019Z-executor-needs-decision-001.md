---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-078-controllers-in-workbench.md"]
created_at: "2026-10-16T14:00:19.066958Z"
schema: 1
title: "T-078 剩余三项验证需要用户决定：09C 签字授权、三窗格验收口径、系统输入法安排"
id: "20261016T140019Z-executor-needs-decision-001"
---

背景：T-078 的 A-15（09B）全部阶段 PASS，现场已回收；整票独立审查已开（冻结候选 92874fe7f）。RESULTS 对照 ticket 还有三项未满足。worker 已写最小计划（worktree evidence/2026-10-11-batch13/T-078/PLAN-REMAINING-T078-01.md），三项真实模型回合都为 0（假 API）。下面三件事需要用户决定，执行主控不能代定：

1. 09C 由谁签字。用户原话'授权你代签 T-078 09B 各阶段批准'只覆盖 09B，不覆盖 09C。09C 要在真实时间里证明：停止请求发出超过两分钟仍无 ack 时，ideation 只做中断。整个观察窗口限定在 stop 创建后 150 秒内，其中有一次许可要在 120～150 秒之间完成，人工来不及审签。
   选项 A（推荐）：授权执行主控代签 09C 各阶段，并允许'实际命令、stop、目标、原屏与预批准模板逐项一致时，自动按一次 Enter'；不一致就停，结果记 INCOMPLETE。
   选项 B：用户在场，亲自审签那一次许可。
   选项 C：本轮不做 09C，T-078 这一项保持 INCOMPLETE。
   预算：两个 Claude 会话，ideation 4 根 / 7 POST，executor 1 根 / 1 POST。

2. 三窗格的验收口径。ticket 要求'同任务两个主控＋一个 worker 的 Electron 截图/录屏'。
   选项 A：三个隔离的原生窗口同屏摆放，截图只截这三个窗口，算满足。
   选项 B：必须是产品本身单个窗口里的三个窗格；若产品现在不支持，就是新的产品工作，要另开票。
   截图会用到 Computer Use，限 worker 自己启动的隔离 Electron 窗口；如果系统还没给屏幕录制或辅助功能权限，需要用户自己在系统设置里给，主控不能代批。

3. 系统输入法。要证明真实中文输入法的候选和组合输入能正确送到后台与终端。需要用户指定一个已启用的中文输入法，并决定：
   选项 A：用户在场，亲手输入一次。
   选项 B：另批原生按键自动化探针。如果自动化只能直接插入文本或模拟 DOM 事件，这一项仍算 INCOMPLETE。
   选项 C：本轮不做，保持 INCOMPLETE。

在决定之前，执行主控只准备材料，不启动现场。独立审查照常进行，结论出来后另报。