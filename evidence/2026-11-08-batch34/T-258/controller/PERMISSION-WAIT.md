# 本轮 macOS 权限等待的识别与处理

用户要求停滞时主动检查权限，不等截图提醒。本轮两次“文稿”弹窗均由用户点击。第二次尝试通过 Computer Use 操作 `com.apple.UserNotificationCenter`，工具明确以安全限制拒绝；未换通道绕过，未写 TCC 数据库或全局权限配置。

已取得独立系统证据：20:00:42（纽约时间）Enchanted 的 `kTCCServiceSystemPolicyDocumentsFolder` 请求为 Unknown；20:03:55 有 `CFUserNotification response`，随后为 Allowed (User Consent)。正式 worker 的交付于 01:04:58Z 被门禁受理。见 `permissions-observation-02.json`，包含可重放的只读 `/usr/bin/log show` 命令。

同一日志还记录旧构建路径的访问请求。旧原生主控保留的 CLI/MCP 进程可能让不同构建身份轮流请求授权；这是推断，不声称已证明所有重复提示都由它造成。用户已指定桌面对话为唯一执行方，旧主控确认暂停后，经界面 `/exit` 正常退出，保留 resume 会话；PID 47149、47334 已结束。

后续每次新构建启动，以及启动超过 20 秒没有原生身份、文件命令长时间没有输出时，先核对当前 Enchanted 窗口和对应 bundle 的 TCC 请求/回执，再核对进程与任务进展。只看 Unknown 或停滞不能确认为权限弹窗；日志缺失时保持未知。已授权且工具可操作的提示直接处理；工具明确拒绝时及时说明具体限制，由用户点击后立即核对继续执行。不能把权限等待当作业务红态，也不能据此扩大文件权限或改启动期限。
