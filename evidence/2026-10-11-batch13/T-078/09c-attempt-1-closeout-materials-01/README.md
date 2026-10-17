# 09C 第 1 场回收待批材料

状态：**材料静态核对 PASS；实际回收 INCOMPLETE，未执行**。[静态记录](../09c-attempt-1-diagnosis-01/materials-static-check.json) 仅核对语法、入口路径、原九 PID 绑定与未来依赖。只使用现有冻结 `t078_raw_retention.py`；本目录新增 verifier 只读 tar/外置 staging，不读现场 SQLite、不发信号。所有步骤由主控分开运行，不能整目录串行执行；批准与独立重数两处须人工签字。原场次始终 INCOMPLETE。

实际 owner 已在 `09c-materials-01/owner.json` / `owner-identity.json`，不重新生成或改写。root `/private/tmp/t078-2-09c-run-slm9wocj`、源码 `7a6edbff87df85077b3a05d38f3cfd5654cde9c1`。原九 PID：daemon **54275**；target shell/leader **54366/54368**；API ideation/executor **54272/54273**；ideation shell/CLI **57003/57004**；executor shell/CLI **58058/58059**。本表来自原收据，不代替执行时的完整 argv/lstart 双读与进程图；不符即 BLOCKED，不发信号、不删根。

1. 主控核对并签本目录 `cleanup-approval.json`，然后运行 `01-DRY-RUN-COMMAND.txt`。只读九身份，不归档、不停机、不删除。
2. `02-CAPTURE-COMMAND.txt`：活场景结构脱敏全部 HTTP/hook、既有证据树、目标 baseline/received、一致只读事务导出。外置 staging 为 `.../T-078/09c-attempt-1-capture-01/`，tar 为 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09c-attempt-1-raw-01/scene.tar.gz`，每原件保留 `pointers/<logical>.archive.json`。采集后核对源集合与字节稳定，tar 逐成员类型/字节读回；任何文件仍增长即停，不先关服务来获得稳定，也不自动重试覆盖输出。
3. `03-TAR-READBACK-COMMAND.txt`：只从 tar 重数实际 POST、UPS 根、PermissionRequest、unfinished，不用 requests.ndjson 行数代替 POST（失败保持的一次 POST 可能被日志写两次）。输出 `09c-attempt-1-raw-readback-01/readback.json`，签字为空。
4. `04-TAR-VERIFY-COMMAND.txt`：另从原 meta/hook/HTTP body 与停机前 live-rows 核对失败链：一个 Enter、原 queued request、stop `fe5603b6…`/created_at、delivered、无 ack/无目标 Esc，以及 C-I2 的错误和 C-E1 不完整原件。只保存归档检查结果，不把失败计数改成计划预算。主控扫描凭据、逐原件核对清单与失败原件后签 readback.json 的 approved_by/approval_ref。
5. `05-SAVE-MANIFEST-COMMAND.txt`：保存 bundle 清单与逐原件 archive 指针入口到仓内。原 HTTP/hook payload 留外置盘，不复制 HOME、凭据、SQLite/WAL。
6. `06-FINISH-COMMAND.txt`：先要求失败归档审阅 PASS（scene_status 仍 INCOMPLETE）、独立重数已签；标准 finish 再逐成员校验、核对源原件稳定与九身份/图，持久写独占 shutdown-intent，才认证 daemon_stop→panes.shutdown 正常关闭两角色/目标。两只原 API 各一次 SIGTERM，确认九进程退出，再只验原件文件/归档，全部通过才删根。**停机后不读 SQLite**，不直接给 Claude/目标发信号，不删 build slot。

`retain_failed_scene=true` 的含义是已明确批准保留并归档不完整 HTTP/hook 后回收，绝不把 unfinished 变成业务 PASS。若原生 CLI 仍在自动重试，采集/finish 的稳定性检查应 BLOCKED，不能省略；先保留现场报主控。C-E1 超过 150 秒后的不完整 SSE 与重试属于本失败场次原件，必须如实留存。没有任何步骤恢复第一份 execute-02/result.json；被覆盖原件已丢失，电子窗口/daemon/HTTP/hook 的可追溯重建单独保存，不冒称原字节恢复。

本轮所有命令只写未跑，cleanup 批准未签；本目录 verifier 尚未在未来 tar 上运行。标准 capture/finish 沿用已通过 A-16 的实现，不换一套清理路径。
