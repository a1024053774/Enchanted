# 主控 #369：创建者回收原子进程，仍要求 PID 实际缺席

候选仅改两个测试工具与一个新增测试，产品/app/acceptance 不改。新完整排练尚未运行，第三场仍 NO_GO；不得用本地夹具绿态替代新排练。

主控运行的 [物理子进程探针](../09c-parity-child-exit-probe-01/result.json) PASS：原子进程32408退出后，父32407尚未reap时ps为Z，旧wait_absent拒绝；原Popen wait后，同一旧wait通过。这证明回收顺序缺陷机制；旧排练20秒中具体哪个PID未消失仍因缺失原ps而不可恢复，不追认26924为当时的已证实僵尸。

## 改动与边界

- `test_t078_09c_real_chain.py` 的 DirectChildRuntime 只由排练创建者使用。构造时核对原Popen的pid/args与spawn登记、三只直接子进程原owner图的PPID等于本进程。认证daemon_stop返回后，先对原daemon Popen wait；原coordinator/conditional-driver等直接Popen也逐个wait。两只API仍分别只接受原来一次SIGTERM，然后wait其原Popen。subprocess.run已自行wait的短命命令不另接管。退出超时即保留现场，不补信号。
- 所有wait之后，仍走标准NativeRuntime的真实ps缺席确认、原helper缺席确认、归档/文件字节复核；没有把Z当退出、没有忽略任何受管PID、没有REHEARSAL豁免、没有增加角色/目标/helper信号。原Popen等待与OS缺席是两个独立事实。
- `t078_raw_retention.py` 的wait_absent保存每轮完整ps输出，列出label、pid、ppid、pgid、stat、lstart/command；Z观察另列。超时错误如 `daemon(pid=32408,ppid=32407,stat=Z)`。PID复用立即拒绝，ps失败/超时仍拒绝并留诊断。日志写在finish独占输出目录，不写回已归档的root证据树，停后SQLite读仍0。
- 标准真实场景继续使用NativeRuntime，没有原子进程Popen登记，不会调用DirectChildRuntime或waitpid。launchd短暂持有Z时仍等待真实ps缺席；Z持续存在则BLOCKED。没有把临时Z改成立即失败，从而保留原来“在期限内实际消失即可”的语义。独立直接调用wait_absent须指定exit_output，标准finish已统一绑定。

## 证据

| 检查 | 结果与范围 |
| --- | --- |
| [red-01](red-01/result.json) | 改动前经原CScene.cleanup与原wait入口：未reap先查缺席失败；真实Z样本缺PID/父进程诊断。运输层明确为夹具。 |
| [known-bad](known-bad/source.json) / [red-02](red-02/result.json) | 从实际Git HEAD `61dddb30c0374b5c84e58898596271ce7e2f2fb4` 导出的两文件复现相同两条红态，旧源码保留。 |
| [green-02](green-02/result.json) | 10项PASS。真实Z原输出逐字节（UTF-8文本）保留、明确PID32408/父32407；实际CScene.cleanup按stop→wait daemon/其他原Popen→OS缺席→各API信号→wait→OS缺席。 |
| 同一绿态的边界反例 | launchd的Z→缺席仍PASS且禁止调用waitpid/kill；活进程、复用PID、错误创建者、原handle PID/argv不符、重复handle、原子进程wait超时均拒绝。超时不发API信号。 |
| [Z视为缺席变异](mutant-verdict.json) | 同一真实Z断言捕获，失败 `Z must never count as absent`；坏源码与INCOMPLETE输出保留，不能算候选通过。 |
| [拓扑22项](topology-01/result.json) | PASS；原caffeinate窄规则、未知后代、父链/路径/参数/数量/竞态拒绝不变。 |
| [归档8项](retention-regression-01/result.json) | PASS；先归档读回才停机、缺签/损坏字节/错PID拒绝、晚到文件阻止删除、停后只查文件。显式生命周期夹具，无真实API/daemon。 |
| [排练check-only](scene-preflight-01/preflight.json) | PASS；命令依赖路径与原request结构存在、源码AST、产品/app/acceptance相对7a6edbff8无变化；零场景启动。 |

本地新测试没有启动场景进程、daemon、API、角色CLI、Electron或模型；没有现场信号。运输层不能证明OS回收，所以完整九进程排练仍待主控沙箱外执行。

## 沙箱外复跑

整文件执行 [REHEARSAL-COMMAND.txt](REHEARSAL-COMMAND.txt)。新输出 `09c-caffeinate-parity-rehearsal-02`，不覆盖失败的-01。仍为真实daemon/inbox/Stop/relay/HTTP/Electron、确定性PTY替身，两角色CLI与供应商模型均0；实钟>120秒且<150秒，硬超时420秒。

要求整体PASS、POST7/1、roots4/1、三许可、目标单Esc/无ack、协调器执行1、重复拒绝PASS、原九身份/完整拓扑照常执行、标准cleanup PASS/root删除/停后SQLite读0。另查看 `flow/cleanup-standard/child-waits/` 三个直接受管子进程与其他Popen的REAPED收据，以及 `exit-observations/` 的实际缺席原件；helper仍单列确认。任一步失败保留新root/原件，不重试或放宽。

本次修复没有重新冻结第三场。现c3校验仍绑定失败的-01，并且会拒绝新增工具差异；待-02整体PASS后再按主控裁定更新收据/源码闭包绑定，不能将旧排练静默记PASS。

## 旧残留收尾

主控#369 [恢复finish](../09c-parity-recovery-finish-01/result.json) PASS：26921/26923各一次SIGTERM、无daemon命令、root已删、停后SQLite读0。外置 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09c-parity-recovery-01/scene.tar.gz` 为167497字节，归档/独立签字重数与严格凭据扫描0由主控读回；逐POST7/1、roots4/1、PermissionRequest3。本轮连同原inspect/归档/读回/签字件入库；旧失败结果和历史证据缺口不改。
