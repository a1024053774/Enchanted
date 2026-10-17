# 主控 #175：现场主 Messages 已到 3 次

worker 只读 api.jsonl，发现三个 `/v1/messages`，第二、第三次都携带同一 Bash tool_result；该包预算为 2，额外请求必须留证，不把许可阶段的失败算完整通过。没有写旧 root、发送输入或尝试续跑。

客户端实际 `worker_request_directory_required` 已有缺陷特定红态；ACK／正常 Stop／idle 仍 INCOMPLETE。worker 正准备本实例归属核对／单独清理脚本，旧实例不能补 ACK 或改现场后重新宣称原跑通过。此消息只报警，不另启动模型、服务或发进程信号。
