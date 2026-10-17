# A-06 I1 ideation 回合待批材料

本回合只使用 ideation controller 的现有 A-06 B1 会话，经产品 `pane_dispatch` 登记并排队一条预先批准的正文；driver 只调用正常 gate 输入路径，不自行写 relay/request 业务文件，也不代写第二角色动作。dispatch 返回实际 `id` 与全局 `seq` 后，driver 先写入实际 dispatch 正文/seq 与 attempt/session/fence；Claude 请求到达后读回真实 request_id，Stop hook 到达后读回真实 stop_id，再补齐协议登记；随后只调用一次 `pane_release`，让原生 Claude 会话送出这一条输入。

完整待注入正文见 `i1-prompt.txt`。协议 fake API 只接受登记正文和登记身份，返回一次 SSE；正文、全局 seq、request/stop ID、attempt/session/fence、角色或预算任一不符都返回 409，driver 立即停止且不重送。

预期：1 个新 root、1 次 `/v1/messages`、I 角色 Messages 预算 6 中使用 1；模型 0。停止条件是收到登记 request_id/stop_id 对应的协议响应、Claude 回到 idle、事件中只有这一回合；不执行 I2、不启动 executor、不自动重试。

当前包为 `launch_status=NO_GO`，需主控签署 approval 后另行运行精确命令。执行前还必须确认 live API 的 `api-ready.json.protocol` 为 `a06-registered-anthropic-v1`；旧 A-06 API 进程没有这个标记时，driver 在 pane_dispatch 前拒绝，不向会话注入正文。
