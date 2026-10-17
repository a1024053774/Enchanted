# 执行主控 #49 范围答复

来源：本 worker 当前会话的 ⟦主控 #49⟧。以下为收到的正文原文；不关闭 blocking issue，仅据答复恢复本卡工作。

执行主控（T-078）：scope-closeout-question.md 收到，你核对得对：我上一条写的"按 #44"是笔误（#44 是发给 T-077 的），没有给 T-078 收缩范围的决定。答复：不收缩范围，按原卡补齐这两项非 Claude 缺口后再冻结：
1. worker 库收件箱认证入口：workbench/bin/inbox 在 worker 会话身份下的 inbox_send/list/ack/ready 经 cli.ts 正确转交，按角色权限判定；补真实入口红/绿（worker 客户端，不用 operator 凭据代替），保留领域层反例。
2. Claude 主控窗格的启动参数与启动记录静态骨架（--session-id、--model、--effort、--settings），只构造与记录、用不启动 Claude 的检查证明，在 RESULTS 标"待真实 Claude 复核"。不运行 Claude 或其夹具。
完成后用你准备的 --final 路径冻结：workbench 提交（git add/commit 单独命令）→ 变基到最新 main（保留 T-076-1 身份与收尾修复）→ 一次完成条件、8/9/18、CAS、三项变异反例 → 一次只读独立审查。沙箱外步骤写脚本回复 READY 停下。你的 blocking issue 20261011T184051Z 我转构思主控备案（执行主控不能关闭 blocking）；这条答复即范围依据。
