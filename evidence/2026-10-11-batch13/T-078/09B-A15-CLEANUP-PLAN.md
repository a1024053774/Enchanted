# A-15 owner-bound 回收材料（未运行）

2026-10-16，按主控 #332 只写材料。**INCOMPLETE／待主控审签与执行**。签字草稿 [cleanup-approval](09b-a15-cleanup-approval.json) 的 approved_by/approval_ref 均空，不能将各阶段的代签授权当作删除 root 的批准。

仅回收 root `/private/tmp/t078-2-09b-run-yp09xosq`。固定九进程：API ideation=59387、executor=59388；daemon=59398；target shell/leader=59550/59552；ideation shell/CLI=65816/65817；executor shell/CLI=93415/93416。来源为 [Stage A readiness](09b-a15-stage-a-01/readiness.json)、两份实际 B1 process-manifest、executor B1 保存的原始 identity binding，逐路径列于 [owner](09b-a15-cleanup-owner.json)。不凭手写的新身份接管进程。

先由主控运行 dry-run，只读核对 argv、lstart、原 ready、实际 launch/session、父子及前台进程关系，并再次读取全部身份确认未变。两个角色 shell 没有历史 lstart 原件：沿用现行规则，以原 manifest PID、两次当前 lstart/argv、原 CLI 寿命与 daemon/前台父子关系联合核对；不编造历史 shell 时间。九进程集合有额外子进程、任何身份不符或缺失均 BLOCKED，不发信号或删除。

正式步骤依次为：

1. **停机前脱敏归档。** redactor 只保留两角色 POST/响应/根/hook 计数、七条精确批准 tool_use/tool_result、三个业务错误码及 I1 原 pending 收据、目标 Esc 计数。原始请求的 headers/system/metadata、完整 messages、token/capability、HOME 配置、debug、SQLite/WAL 不复制进证据或 tar。完整 HTTP body 只在内存检查批准工具后丢弃；摘要的 API request_id 与异步 inbox request_id 分开核对。外置归档固定为 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a15-redacted-01/scene.tar.gz`，只含 projection 目录和 summary.json；逐成员类型、原文件字节及 tar 读回一致后 PASS。外置盘缺失、归档目录已存在、输入不符即停，不回退。
2. 主控审签 cleanup-approval 后正式 cleanup，再次核对九身份、原 ready 与 PID 文件；将归档摘要与停机前现场的白名单摘要逐字义比较，并保存 pre_stop_summary。若场景改变则 BLOCKED，尚不停止。
3. 以该 root 的 operator 凭据调用唯一门禁 daemon_stop；panes.shutdown 正常关闭两个 Claude 会话与 target。确认 daemon/角色/target 七 PID 退出、socket/PID 文件消失。**不直接给 Claude 或 target 发信号，不 reclaim、不 push。**
4. 两只原 API 每只紧邻双读身份后只发一次 SIGTERM，三秒内确认退出。仍存活则 BLOCKED、保留 root，不升级 SIGKILL，不重试信号。
5. 确认九 PID 全退出，停机后**只验 tar 的成员类型与摘要字节**，与已存 pre_stop_summary 相等。三个 A15 脚本均不导入/调用 SQLite；没有停机后 collect、数据库备份或依赖 WAL 的查询。最后仅删除解析无符号链接的固定 root，记录 archive_bytes、inventory、signals_sent、root_removed。任何一步失败保留原输出/root，不改判 PASS。

所有 build slot 本轮均不删除，slot 处置另列主控决定。所有输出目录为全新 -01，已存在即拒绝；若失败须用新编号并保留现场。外置 I/O 卡住仍不可把无结果写成 PASS。

材料的 [本地 file check](09b-a15-closeout-file-check-01/result.json) 为 PASS：用登记身份夹具验证 PID 复用和额外子进程拒绝、无守卫坏实现检出；凭据哨兵不会进入白名单、原样复制坏实现检出；额外 shell 命令拒绝；tar 逐成员字节与变更拒绝；模拟停机后数据库不可用仍只验 tar，旧后置读库坏实现失败。process_probes=0、scene_actions=0。这不是实际清理通过，也没有执行 redactor 的外置归档入口。

完整待执行命令见 [CLEANUP-COMMANDS](09B-A15-CLEANUP-COMMANDS.txt)，先 dry-run，再脱敏归档/人工检查，再另签正式清理。本轮全部只写未跑。
