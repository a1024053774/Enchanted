# 单角色真实 inbox／工具切片：失败方式与 oracle

当前产品入口未修改，真实红态未启动。独立契约来自 T-078 的真实角色收件箱验收及主控 #163／#172 的顺序；新 API 夹具绿态不替代真实入口。

| 失败方式 | 最小观察／停止条件 |
| --- | --- |
| 将手写 JSON 或 operator 调用当角色转交 | 只接受实际 Claude API1 的 Bash tool_use → 同 ID API2 tool_result → 实际 UPS／Stop；驱动不写 requests，不调用 inbox 业务入口，不改库行 |
| worker 专用 writer 在 controller 上拒绝 | 记录真实 Bash tool_result 的 is_error、daemon_call_failed 与 worker_request_directory_required；角色 env 保持 controller／ideation，不补假 attempt/fence |
| 后续 Stop／caller 的缺口被首个红态掩盖 | 首个红态只界定客户端拒绝；没有 request 文件意味着本次不声称触发 controller_relay_not_enabled。取红后才按真实层次实现并扩绿／边界反例 |
| 假服务编造错误证明 | 假服务回复只含精确 Bash 命令和普通 ACK＋nonce，不返回预期错误文字；错误必须在实际 CLI 提交回来的 tool_result 中 |
| tool_result 混入新根提交或错 ID／命令 | API2 末条 user 必须携带唯一同 ID tool_result，历史唯一 tool_use 及 command 精确匹配；root submit intent／UPS 各 1，主 Messages 恰为 2 |
| API 忽略 nonce／预算 | 新 nonce 改变输入与 ACK；第 3 个主 Messages 拒绝，count_tokens 单列；预算坏变异必须被检查捕获 |
| 把 manual／Bash 可用当工具许可 | 固定 manual、Bash/Read，无 bypass／全工具 allow；本次精确工具先批准。若出现原生 PermissionRequest，另读实际屏并只批一次 Yes，不默认按 Enter |
| 在错误对话框按 Enter | matching PermissionRequest 的 session／tool_name／tool_input.command，busy active dispatch，同 root；原 PTY 字节与批过屏相同，窗口真实可见光标在 `❯ 1. Yes`；不符即停，不换键、不猜选择 |
| 键 attempted 误称送达 | 一次同窗 Enter 的 action、准入、write intent、written 相同 request/window；记录 0x0d 为 control action，不记 message；截图和 PTY 原件保留 |
| 审批 Enter 被当新的根提交并替换 active | 当前 panes.userInput 对所有 CR 都登记 user intent；探针以实际 UPS1/API2 核对原生预算，同时保存审批键对应多余 intent 和原登记提交结算缺口；不能称为合法新回合或原注册正确结算 |
| 跨 approval／过期 window／版本 | 新 launch/session/thread/HOME/nonce；每步绑定、实际 PID/lstart、冻结源码字节；撤销／变化／未知不重送，保留本次结果 |
| hook 读回过早／错 prompt | 等实际 Stop.finished.json；UPS 与 Stop prompt_id 相同、session/launch 正确、exit0、唯一 idle。原 hook stdin/stdout/stderr 在 root/hooks 保留 |
| 把局部逻辑与夹具 SSE 当真实 Claude 通过 | 本地 protocol12 只证明脚本序列和反例；真实工具／窗口／hook 未运行时一律 INCOMPLETE；新独立 reviewer 未做 |
| 清理顺手删除旧 slot 或广域杀进程 | 本包不执行 cleanup；运行后按本次 owner/ready/PID/lstart/argv 单独交主控清理脚本。旧／新 slot 均不删，原件不覆盖 |

工具屏的精确绘制仍是 unknown：公开文档提供一次 Yes 的含义，不代替 2.1.296 本实例的原屏。当前驱动只接受上述明确选项；若实际版本显示不同，先保存屏与原因，再交主控裁定，不能放宽后宣称原条件通过。
