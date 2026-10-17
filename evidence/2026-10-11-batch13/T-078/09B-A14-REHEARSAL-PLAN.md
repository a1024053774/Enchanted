# A-14 无模型真实边界排练（主控 #304）

状态：材料准备；完整排练 INCOMPLETE，待主控沙箱外运行 `09B-A14-REHEARSAL-COMMAND.txt`，本轮未启动服务或窗口。A-14 提交和 Stage A 均 NO_GO。静态证据不能替代本次真实边界运行。

**Tracer bullet**：真实门禁 claim 原生确定性 target，controller_start 创建角色会话并挂到真实 node-pty；UPS → HTTP phase_plan → PermissionRequest → Electron 一次 Enter → Bash inbox send 的真实排队回执 → HTTP tool_result → Stop/relay → pending → executor 上线/unknown 零业务字节 → 初始 release/turn_submitted → delivered → 原 I2 → E1 PermissionRequest 后停。**Deep modules**：HTTP/阶段绑定仍调用候选 API 和 shared protocol core；Stop/relay/投递由产品拥有，不写业务表、不合成条目或回执。**Ubiquitous language** 保持 queued 与 pending/delivered 的区别。

唯一 provider 边界替换：测试 host 调用未经修改的 daemon.serve，只在 controller 的 node-pty spawn 边界把 Claude 换成确定性 Python 进程；PTY 本身真实。产品的固定 Claude 路径检查不能把 Python 当成 Claude，故 host 对此边界核对实际替身 PID、完整 argv 与双读 lstart，将同一进程用于 caller liveness；不冒称验证了原生 Claude 进程识别或 onboarding。worker target 使用既有 C receiver，由真实 dispatch/claim 返回 attempt/session/fence/thread/workspace，不填伪造或 null attempt。API、relay、认证、UPS/PermissionRequest/Stop CLI、数据库及窗口输入路径不替换。替身从实际 launch.settings 取得原 hook command，不由 operator 代发 send/stop/ack。

请求结构来自 A12 dispatch-01/result.json 的真实 Claude Code 2.1.296 body_raw，tool_result 形状来自 A12 脱敏 summary。只保留消息顺序、文本块类型、cache 形状、Bash input_schema 和中性结构；不复制 system/reminder 文本、描述、metadata、headers 或认证字段。实际正文、tool_use ID、Bash command、queued request_id/path 来自本次 scratch。替身只允许执行冻结 protocol 的 I_SEND_STOP；完整字符串必须等于安全 shlex.join，body 和 refs 绑定本 scratch 的真实 target。executor 不执行任何工具。

两场景串行运行，各用新 scratch、两个真实 HTTP API、daemon 和 target：

1. flow：I1 经 pane_dispatch/release 进入 PTY。先不给 API 批准文件，观察 HTTP 等待、零 SSE、零工具事件；随后 driver arm 原批准，原请求得到 200/tool_use。observe 只读等实际 PermissionRequest，不再派发或 arm。主控 #304 的 scratch 批准限定 I1 一次性 Yes；现有 permission helper 起自己的隔离 Electron，经 awaited window.a2a.input 写一个 CR。角色上下文执行 tool_use command，I1 2 POST/1 root，Stop 后原条目 pending、发送方可见、零反馈。随后串行 controller_start executor：unknown 阶段已排队，但 received.bin 零字节；先 arm I2，再 E1 初始 release。真实写出使投递 delivered，原 request/entry 的 I2 恰一次，1 POST/1 root。E1 得到 1 POST/tool_use 与 PermissionRequest 后停，零 Enter/Bash/tool_result/Stop。这里是 E1 完整两请求阶段的前半，不冒称 E1 完成。累计 ideation 2 roots/3 POST，executor 1 root/1 POST；按实际 request.bin 数与 phase 日志交叉核对。
2. timeout：独立 scratch 的 I1 初始 UPS/HTTP，批准始终缺失。服务原有 180 秒等待不改、不快进。返回 409 phase_approval_deadline 后，替身保存场景 INCOMPLETE 并自行退出，不重试、不发 Stop、不生成条目或 relay 记录。只允许 1 POST/1 root，实测 HTTP elapsed 必须至少 180 秒。汇总只有在该 INCOMPLETE 确为预期拒绝、且两场清理均 PASS 时才 PASS。

每条本地命令有期限，整场 500 秒硬超时；正常预计约 4～6 分钟，超时反例必需至少 180 秒。daemon/API 脱离调用者进程组，角色启动串行。SIGALRM/SIGTERM/SIGINT 进入 finally 清理。正常关闭用认证 daemon_stop→panes.shutdown 结束 PTY 角色与 target；两个未回收的 Popen API 子进程各一次 SIGTERM，2 秒确认退出；角色、target、Electron PID 逐个确认不存在。清理异常记 BLOCKED、保留 root，不强杀未知进程或删现场。

daemon 退出后执行 SQLite checkpoint(TRUNCATE)，backup 生成一致副本，并复制当时存在的 -wal/-shm；immutable 只读 integrity_check=ok 后才删 scratch。只复制本次脱敏 HTTP/peer/动作，operator.json 不复制。产品创建的 /private/tmp/a2a-requests-* 也仅按真实 launch 记录、在本轮 PID 退出后回收。标准构建使用唯一 slot；只列 slot，不删除。候选源文件保存副本并在结束时逐字节确认未改变。

峰值进程预计为两 API、一个 daemon、target shell/leader、两个串行启动的替身，以及 I1 临时 Electron/renderer；无 Codex/Claude/子 agent。内存估计 350～650 MiB，尚未测量。

本排练即使通过，也不证明真实 Claude 权限 UI、首启主题/信任、E1 工具执行或完整 E2–E6/I3–I4。它补 daemon/relay/HTTP/PTY/Electron 接线证据；主控读回 PASS 后才能继续提交和另签 Stage A。
