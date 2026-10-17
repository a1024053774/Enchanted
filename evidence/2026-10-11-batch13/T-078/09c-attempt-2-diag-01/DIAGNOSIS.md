# 09C 第 2 场：拓扑拒绝的只读诊断

状态：**场次 INCOMPLETE；额外进程身份 UNKNOWN；第 3 场 NO_GO**。主控 #363/#364 要求先证明额外子进程的来源，再决定允许项。本轮没有改任何 `workbench/`、产品允许项、原 owner、冻结包或旧结果，没有按键、业务发送、启动场景或停机。

## 已发生的链路

原现场 `/private/tmp/t078-2-09c-run-iznfrv18`；原 owner 在 `../09c-attempt-2-materials-02/owner.json`。完整冻结版本 `1dfa09207b34c7ccadfe81cb92a46338fa619526`，运行工具基线 `dc15dc3f0169f8689c5cded440676031cfa48bf5`。原九进程为 daemon **93964**、target shell/leader **94061/94063**、API ideation/executor **93961/93962**、ideation shell/CLI **94466/94467**、executor shell/CLI **95221/95222**。这些是启动收据，不能代替当前存活核对。

`../09c-c2-preparation-01/timed-01/result.json` 保存了完整调用栈：C-I1 check/Enter 成功；C-I2 observe、完整 screen、prepare 已执行；签名之前 `NativePermission.actual()` → `check_identities()` → `NativeRuntime.topology()` 拒绝 `unexpected_daemon_descendants`。C-I2 permission 草稿仍未签，未进入 Enter。原 C-I1 的 `execute-02/settlement.json` 记录原 queued request **95058fd0-1e9d-4028-b1c1-f45845dd3584**，stop **bfa23030-9da9-413f-87fc-e7cb81317987**，`created_at=2026-10-17T01:06:15.258Z`。原 clock-origin 字节已另存 `forensic-originals/clock-origin.json`，不重建起点。

失败结果的文件写入时间为 UTC **01:06:18.365195**（C-I2 execute-02）、**01:06:18.565589**（外层 timed-01）。它们只是异常后的写入时间，不冒称发生 `ps` 的确切时刻。

本轮只读 HTTP meta 逐件清点见 `forensic-originals/evidence-index.json`：ideation **3 POST**（C-I1 两条、C-I2 首条），均 200/complete；executor 第 1 POST 的保持 SSE 在约 150 秒后以 `C_executor_hold_deadline` 未完成，随后自动重试第 2～11 POST，均 409/`dispatch_replayed`。因此本场 executor 已 **11 POST**，超过计划 1；不是只修检查后就能继续的现场。原失败和自动重试必须归档，不得重试本场 C-I2 或继续计时段。

## 额外进程：目前不能确认

`workbench/tests/t078_raw_retention.py:389` 先核对原九节点的 PPID/PGID/TPGID；到第 397 行才比较 daemon 的全部后代与登记的七个受管进程（两 API 独立于 daemon）。本次在后一条拒绝，说明此前原节点图核对已通过；**原异常未保存完整图、额外/缺失 PID 或完整 argv**。所以无法从这个字符串还原是哪一个额外进程。

保留的原日志选行：

| 原件 | 行/UTC 时间 | 直接事实 |
| --- | --- | --- |
| ideation claude-debug.log | 362 / 01:05:30.900Z | `Started caffeinate to prevent sleep` |
| 同上 | 405 / 01:06:14.786Z | Bash `tool_dispatch_start`，toolUseId `3f1f4517-5c86-49f8-a226-bb426f9d082e` |
| 同上 | 411 / 01:06:14.851Z | 再次出现 `Started caffeinate` |
| 同上 | 424 / 01:06:14.887Z | `Spawning shell without login` |
| 同上 | 432 / 01:06:15.001Z | 同一 Bash `tool_dispatch_end outcome=ok` |
| executor claude-debug.log | 360 / 01:06:15.609Z | `Started caffeinate to prevent sleep` |

原字节选行在 `forensic-originals/*-debug-selected.bin`，原文件路径/行号/mtime 在 evidence-index。**这些行都没有 caffeinate 的 PID、完整命令、父链或 fork 记录；caffeinate 只是候选线索。**Bash 已报结束也不能证明没有遗留子进程。另一个待排除的假设是 daemon 自己执行 `processInfo` 时短暂派生的 `/bin/ps`（产品 `panes.ts:355` 确实调用 exec）；没有实际 PID 证据，不能将它判为本次原因或允许项。没有证据表明是 Electron，也不能由其名称猜测归属。

本 worker 只读 `/bin/ps` 被沙箱拒绝：`PermissionError [Errno 1] Operation not permitted`，未提权。已交 `PROBE-OUTSIDE-COMMAND.txt` 给主控；`probe-topology.py` 会保存两次原始数值图及仅该 daemon 后代/原九进程的完整 argv、comm、lstart、PPID 链、UTC 观察时间。它不读环境、凭据、SQLite，不发键或信号。**当前快照只证明当前 PPID，不等于历史创建者证明，也不能恢复已退出的失败时进程**。若进程已消失、快照竞态或无法关联 CLI 工具，仍须保持 UNKNOWN，报主控决定进一步取证方式。

## 修复门与拒绝条件

目前不把检查判为“过严”，也不把额外进程判为异常业务。先由原 `ps`、lstart 与 CLI/daemon 日志确认每个额外 PID 的完整命令、父链、创建时段和职责。**只有证明属于批准的角色 CLI 工具子进程，才考虑加入最小允许描述**；若是 CLI 防休眠辅助、daemon 内部探测进程等其他类别，先交主控确认是否满足 #364 的要求，不能自行类推授权。

之后才实现、冻结并审查：失败前保存数值图/两次身份/差异上下文；保留原九 PID、argv、lstart 与原节点关系的严格核对。允许描述须约束已证明的可执行路径、完整参数、原父 CLI 的 PID/lstart、所属角色/场景和相关工具/请求；不按进程名、root 子串或“所有后代”放行。未知子进程、错误父链/监视 PID、拼接参数、PID 复用、原节点缺失/改变、两次快照不一致仍拒绝，零签名/零按键。此为方案，**尚未应用、尚无绿态**。

排练跳过检查的完整清单、现状红态和逐项补齐办法见 [SKIPPED-CHECKS.md](SKIPPED-CHECKS.md)。现有两次排练仍可支持其真实 daemon/relay/HTTP/Electron/时钟业务断言，**不能证明操作现场九进程、owner 来源和拓扑等价**。新完整排练、反例、独立审查通过之前，不冻结或启动第 3 场。

## 回收与第 3 场

[回收材料](../09c-attempt-2-closeout-materials-01/README.md) 复用未改的标准 retention：原九身份/拓扑、活库停前导出、全部脱敏 POST/hook、归档逐成员字节读回、独立签字，然后认证 daemon_stop/panes.shutdown、两 API 各一次 SIGTERM、确认退出、停后只验文件并删根。拓扑仍未知时，capture/finish **会继续 BLOCKED，不能为了清理省略它**。需要主控先运行只读取证并裁定；本轮没有运行任何回收步骤。

[第 3 场最小计划](ATTEMPT-3-PLAN.md) 是未绑定、不可启动的后续清单。当前卡点是缺少 #364 要求的进程证据，以及据此才能完成的所有者/拓扑等价排练；不是可以把旧场次判为 PASS 的材料问题。
