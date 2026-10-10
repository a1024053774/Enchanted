---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-074", "ticket:T-075", "file:evidence/2026-10-10-batch12/T-074/needs-decision-02.md", "file:evidence/2026-10-10-batch12/T-074/RESULTS.md"]
created_at: "2026-10-10T20:11:49.711515Z"
schema: 1
title: "T-074 Codex 部分测完：等批准时注入的文字被当成了批准；T-075 派发设计需决定"
id: "20261010T201149Z-executor-needs-decision-001"
---

状态逐字：T-074 BLOCKED。Codex 部分已完成（14/30 个主 turn），只差 Claude 认证与 Claude 实验。执行主控已重跑统计命令，次数与报告一致。
## 事实（measured，Codex 0.162.1，node-pty + zsh）
- 注入方法：M1（文字加回车一次写入）idle 2 次，都没送达；M2（文字后 300ms 单独回车）idle 2 次 ok；M3（bracketed paste 后 300ms 单独回车）idle 7 次 ok、running 4 次 ok（逐字，未合并）。
- 危险情形：等批准时用 M3 注入一条“不是批准”的文字，结果被当作“同意”，命令真的执行了（原生日志 decision: Accept，夹具文件被写入）。只试了 1 次，副作用限在夹具。
- 等确认信号：OSC 9 在请求批准时收到（"Approval requested: …"，截断，无 request id）；notify 没有批准等待事件；rollout 也没有专门事件。Codex PermissionRequest hook 未测（要装 hook，需授权）。
## 需要构思主控/用户决定（设计级，执行主控不自定）
1. 派发和用户批准要不要走不同通道？例如：收到 awaiting 信号后暂停注入，排队到批准结束再送；或者改走别的通道，不往窗格里写。
2. OSC 9 只是截断的展示文字，要不要改用 Codex 的 PermissionRequest hook 作为结构化信号？这需要批准用每会话的 hook，按 spec 第 5 节只经启动参数传入。
3. 写入过程中状态突然变成等批准的竞态还没测，要不要加一项专门验证？
4. Claude 认证（同 T-059）仍等用户。
T-075 在这些决定之前不开工。