# A16 原件核对的失败条件

本次只读原件与活库，不执行角色、HTTP、钩子、归档或停机。预期根数/POST/工具来自冻结 protocol 与主控 #349，不取阶段汇总作为答案。

- 逐POST的request/response/meta缺件、序号断档、多请求、status非200、complete为false、字节数或SSE末尾不完整，拒绝。
- 原生请求的最新登记正文、角色/launch/全局seq与真实事件不一致，或SSE工具并非批准的Bash.command，拒绝。
- 第二条请求没有同tool_use_id的真实tool_result，或伪造同步entry代替queued request_id，拒绝。
- hook的stdin/started/finished/stdout/stderr缺件、exit非0、重复UPS prompt、UPS/Stop/PermissionRequest数量或session/prompt关联错误，拒绝。
- 原屏不完整、许可命令或签字不符、Enter不对应一条control action和写出收据、额外业务根，拒绝。
- 目标相对baseline不是恰一个Esc、实际中断actor/thread不符，拒绝。
- pending阶段存在原I2反馈，或delivered不在原executor turn_submitted之后、原request/entry/created_at变动、I2登记/提交不止一次，拒绝。
- 两角色的实际runtime endpoint不对应本场loopback假API、源码闭包变化，不能证明模型0。

反例只在一次性/private/tmp副本：缺response、截断SSE、重复UPS原件，均应被同一原件读取函数拒绝。结束删除副本，不改活现场或旧结果。
