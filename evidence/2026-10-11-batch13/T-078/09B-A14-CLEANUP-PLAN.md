# A-14 owner-bound 回收待审材料

2026-10-16，主控 #315／#321。**脚本与本地纯检查准备 PASS；现场 dry-run、脱敏归档、停止与删除均 INCOMPLETE／未运行。** worker 未查询当前进程或现场文件。执行命令见 09B-A14-CLEANUP-COMMANDS.txt，主控逐条审阅执行。

固定 root 为 `/private/tmp/t078-2-09b-run-gbxz0tyb`。owner 文件列出实际旧 Stage A、两个实际成功 B1 manifest 和 I1 结果，不使用新实例的 current_attempt 或 PID。

| 进程 | 固定 PID | 身份来源 |
| --- | ---: | --- |
| ideation API | 48453 | A-14 原 readiness 与成功 B1 binding 的完整 argv/lstart |
| executor API | 48454 | 同上 |
| daemon | 48461 | 同上，另核对 root 的 daemon.pid |
| target shell / leader | 48560 / 48562 | 同上及父子关系 |
| ideation shell / Claude | 48938 / 48939 | 原 process-manifest；CLI lstart 为 Fri Oct 16 00:01:04 2026 |
| executor shell / Claude | 52257 / 52258 | 原 process-manifest；CLI lstart 为 Fri Oct 16 00:05:01 2026 |

两个 Claude shell 没有历史 lstart，不能补造。脚本用原 shell PID、与原 CLI session/debug 路径及历史 CLI lstart 的绑定、daemon→shell→CLI 父子关系、前台进程组，以及全部九个 PID 两次当前完整 argv/lstart 读回核对。daemon 后代必须正好是原 target 和两个角色的六个进程；多出进程、缺失、重用、身份或前台关系不符，全部在动作前 BLOCKED，不发信号。

dry-run 只读全部身份并列计划，不停止、归档、删除。正式动作还要求 `09b-a14-cleanup-approval.json` 的主控签字；草稿 approved_by/approval_ref 均空，本轮不代签。

先运行独立脱敏脚本：只读真实 API 请求与数据库，在内存中取白名单。保留 ideation 2 请求/2 响应、executor 0/0；批准的 I_SEND_STOP Bash command 与 queued tool_result（request_id `60a4b816…`）、错误码、原 stop `7d260ac3…` 的不可变 pending 回执、投递状态序列、feedback=0、目标新增字节=0。命令 argv 必须与冻结 protocol 按实际 ID 替换后逐项相同；工具结果必须是同 request 的 queued=true/delivered=false。未知形状拒绝，不把原文照抄进归档。

不复制 raw messages、system/tools 描述、headers、metadata、debug、HOME、operator/角色凭据或原 SQLite。外置归档固定为 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a14-redacted-01/scene.tar.gz`，只有 projection 目录和 summary.json。复用已验证的逐成员归档器，核对名称、类型及每个普通文件字节；正式 cleanup 再独立读取 tar 成员和本地摘要逐字比较，并与现场重新投影比较。此处明确只留脱敏摘要，不声称归档了完整 root。

确认摘要与九进程身份未变后，走真实门禁客户端的认证 daemon_stop，由旧 daemon 的 panes.shutdown 正常关闭两个 Claude 与 target，不直接给它们发信号。确认这七个进程退出、socket/pid 文件消失，再对两个原 API 各核对两次身份、各一次 SIGTERM，三秒内确认退出；不自动 KILL、不重试。最后重新核对九进程全部缺失，归档成员与停机前已核对的摘要字节不变，才删固定 raw root。停机后不再 collect 或访问 SQLite/WAL。任一失败保留 root 与输出，状态 BLOCKED。

slot 仅从现存证据中的路径字符串列清单，见 09b-a14-slot-inventory.json；没有查询外置盘当前状态，也没有 slot 删除代码。实际处置由主控另定。

`09b-a15-file-check-02` 的本地检查：原登记身份夹具正例；CLI PID 重用、API 外来 root、错误 native session、错误父进程、未知 daemon 后代五个反例均拒绝；无检查的已知坏 validator 被测试拒绝。脱敏凭据哨兵不进入输出，额外 shell 命令拒绝，归档字节变化拒绝。使用抄录自已保存 B1 的字段，不是本轮真实 ps；全部 live_A14_access=false/process_probes=0。实际 dry-run 仍须主控执行。

主控 #322 已执行 dry-run PASS、脱敏外置归档 PASS，扫描凭据字样为 0，并签字正式执行。认证 daemon_stop 与 API 各一次 SIGTERM 已完成，九进程均退出；旧脚本却在停机后再次 collect 的 SQLite 查询报 unable to open database file，状态 BLOCKED，root 未删。原结果和签字件不改写。上述流程已按本次修复更新；不要重跑原四步，余步只运行 09B-A14-CLEANUP-FINISH-COMMAND.txt。具体证据、事后精确改动与本地数据库不可用反例见 09b-a14-cleanup-fix-01/README.md。
