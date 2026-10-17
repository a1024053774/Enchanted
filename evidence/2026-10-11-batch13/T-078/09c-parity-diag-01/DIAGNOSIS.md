# 主控 #368：九进程排练回收超时

结论 **INCOMPLETE**。业务链已通过；原整体结果保持 INCOMPLETE、回收保持 BLOCKED。第三场仍 NO_GO。本轮只读现场文件、准备诊断与恢复命令，没有发信号、按键、调门禁、打开停机后的 SQLite 或删除现场。

## 能确认的事实

- [原失败](../09c-caffeinate-parity-rehearsal-01/flow/cleanup-standard/result.json)在 `t078_raw_retention.py:554` 的 `wait_absent(managed,20)`，并非后面的 `wait_helpers_absent`。`managed` 是 daemon 26924、target shell/leader 27014/27016、ideation shell/peer 27047/27048、executor shell/peer 27061/27062，**不包括**两个 API，也不包括 caffeinate。
- 正常 daemon_stop 于 epoch `1792207149.280951` 返回；`1792207169.334649` 记录 BLOCKED。原 `signals_sent=[]`，两个 API 的 SIGTERM 分支尚未执行。正常返回本身不证明宿主进程已被父进程 reap。
- [停前辅助收据](../09c-caffeinate-parity-rehearsal-01/flow/cleanup-standard/auxiliary-before-stop.json)为 ideation caffeinate 27049、executor caffeinate 27063，直接父分别为 peer 27048/27062，argv 均 `caffeinate -i -t 300`、内核路径均 `/usr/bin/caffeinate`。它们不是本次抛错的七标签之一；日志不足以说明它们在之后的哪个时刻退出。
- 原 `flow/identity-seam.json` 的图记录 daemon 的父为 26889；[harness 记录](../09c-caffeinate-parity-rehearsal-01/flow/owner.json)也为 26889。`Scene.spawn` 保留原 `Popen`，`CScene.cleanup` 先调用标准 `finish`，只有它 PASS 后才对 `self.children` 调 `wait`。
- `wait_absent` 只反复读取 ps 是否为 None，没有保存每次结果、未退出标签或 stat；daemon stdout/stderr 均 0 字节。已有 SQLite 与 `live-rows.json` 是停前一致副本，最后事件止于停机前，不能补造停机后的 OS 观察。
- 主控 #368 当前观察为两个 PPID 1 的 Python 26921/26923，其他原受管进程已无。worker 只读 ps 被沙箱拒绝；原错误与该拒绝都已记入 [forensics.json](forensics.json)。没有将 ps 拒绝解释为“进程不存在”。

**不能确认当时具体哪个 PID 占满了 20 秒。** 原工具丢失了这项观察；事后当前快照不能还原历史。不能将本次错误归因为 caffeinate，也不能宣称 daemon 26924 已被实证为僵尸。

## 可证伪假设与最小修法

最有依据的假设是：daemon 宿主作为 harness 的直接子进程已退出，却因原 Popen 尚未 wait 而仍占 PID；标准 ps 缺席确认于是超时。依据是上面的原父链与明确的 wait 顺序。这也可能是宿主/其他七标签真实延迟退出，现有记录不能排除。

[01-CHILD-PROBE.txt](01-CHILD-PROBE.txt)供主控在沙箱外验证机制：只启动一个会自行 exit 0 的短命 Python，不启动场景/API/CLI/模型，不发信号。先保存该已退出直接子进程的原始 ps/stat，调用**原** `NativeRuntime.wait_absent` 应因未 reap 为红；再对原 Popen handle 执行 wait，仍用原函数确认真实 PID 缺席为绿。该信号只证明机制，不追认丢失的历史 PID。探针尚未运行。

若机制成立，修法限定在排练创建者：认证 daemon_stop 后，先等待并 reap **已持有原 Popen 的 daemon 子进程**，保存 exit code，再走不变的 OS 缺席确认。API 同理在自己的一次 SIGTERM 后由创建者 reap。只允许原 Popen handle，不能 wait 任意 PID、不能把 Z/改名进程当成已不存在、不能忽略受管缺失或延长 20 秒掩盖。标准回收的缺席等待应另外将每次原始 pid/ppid/pgid/stat/lstart/完整 command 和 remaining 标签落到回收输出目录，超时明确指出标签，避免再次丢证。

此处尚未更改共享回收或排练行为；待该 focused signal 与新带日志排练取得结果。若重排练仍超时，按新原件定位，不继续假定为 reap。

## 为什么真实探针 finish 曾 PASS

[探针回收](../09c-topology-probe-cleanup-01/result.json) PASS；其 [停前辅助清单](../09c-topology-probe-cleanup-01/auxiliary-before-stop.json)为 `[]`。所以那次没有测试“停机时还有 caffeinate”的分支。探针 daemon 是标准 detached 启动，排练 daemon 是仍由 harness 持有 Popen 的直接子进程，两者 wait 责任不同。这些事实足以说明两个结果不矛盾，不能证明真实 Claude 会主动收回所有 caffeinate。

当前严格规则不变：已见辅助进程仍须确认消失，否则 BLOCKED、不删 root。不得把被 launchd 收养或尚在 `-t 300` 内存活的辅助进程忽略成“退出”；本轮不增加辅助信号、不放宽亲缘或存活时间。确定性 peer 当前 HUP handler 只终止并 wait 自己创建的 helper；是否执行成功仍须新回收原件证明。

## 本次剩余回收

[recover.py](recover.py)只接受本次原 root、完整九 PID/argv/lstart、原 Stage A/B1/owner/ready、原停前归档与原 BLOCKED/daemon_stop 收据。每次动作前保存两轮原始 ps/stat；七个非 API、原两个 helper 与旧 harness 必须均缺席。两只 API 必须仍为原身份且 PPID 1；任何复用、缺失、改名或新父关系都 BLOCKED。

顺序见下面五份命令文件，各自整文件执行，输出均为新目录：

1. `01-CHILD-PROBE.txt`：独立假设探针；与残留清理无依赖。
2. `02-RECOVERY-INSPECT.txt`：只读核对、列动作；零信号、零归档、零删除。
3. 主控核对并签 [approval.json](approval.json)，再执行 `03-RECOVERY-ARCHIVE.txt`：把**原停前**脱敏 staging 与失败/当前身份收据归档到外置盘，逐成员类型与字节读回。不再读取已停 SQLite/WAL，不再导出/刷新业务行。
4. `04-RECOVERY-READBACK.txt`：从新 tar 独立重数。主控核对后签其 `readback.json`；应 POST 7/1、roots 4/1、PermissionRequest 3/0、未完成 HTTP/hook 均空。原业务结论不提升。
5. `05-RECOVERY-FINISH.txt`：重验原件/归档/签字/身份，先独占 durable recovery-intent，再仅对 26921、26923 各一次 SIGTERM，分别确认消失。所有原进程和 helper 缺席、字节复核通过后才删 exact root。**不再 daemon_stop，不向角色/target/helper 发信号，停后 SQLite 读 0。**不清理 slot。任何中途失败均保留新输出及 root，不自动重试。

已在 worker 实跑 recover 的 `--check-only`：原文件集合/字节、原 tar 逐成员读回、原收据/路径通过，ps/信号/SQLite 读均 0，见 [file-check.json](file-check.json)。真实身份与回收仍待主控执行，不能把静态检查称为回收 PASS。第3场冻结校验仍因整体 INCOMPLETE 拒绝，不准备启动。
