# 主控 #367：有证据的 caffeinate 窄允许项

状态：**本地回放/反例PASS；真实内核路径、完整九进程排练、两处回收尚未运行；第3场NO_GO**。不改产品、协议、预算；不发键、不重跑TURN、不对现场发信号。

主控审阅了原始采样并裁定合法：idle-02无额外后代；in-flight **94**次与permission-wait **95**次均完整，全程 PID **12761**，`caffeinate -i -t 300`，当前父链 **12761→8705 Claude→8703 zsh→8505 daemon**，UTC首次观察02:20:07.779449、末次02:20:38.180788。原ps、lstart/comm/full command及各summary随本次提交保留。主控的“与第2场相符”是归因支持，不是恢复第2场丢失的故障时PID图；该历史限制保留。

## 唯一新增的允许规则

保留原受管PID/完整argv/lstart、PPID/PGID/TPGID和整个后代集合检查。额外进程只有同时满足以下条件才可作为**辅助进程**返回，绝不加入角色身份或抵消缺失受管进程：直接父PID是原登记ideation_cli或executor_cli领导PID；父身份再次精确核对；**内核实际可执行路径**解析为`/usr/bin/caffeinate`；argv恰为`caffeinate -i -t N`，N为ASCII正整数、1～300；同一角色最多一个。辅助进程身份/路径双读且进程图复读稳定；其他一律拒绝。所有拒绝仍先保存原ps快照。

不使用PATH查找或comm名字猜二进制。macOS SDK `libproc.h:102` 的proc_pidpath和`sys/proc_info.h:749`的最大路径缓冲定义是实现依据，使用stdlib ctypes调用。旧ps原件仅有bare argv0，没有内核路径；因此[真实ps回放](caffeinate-green-03/result.json)中的路径值明确是按主控#367分类提供的transport输入，**不冒称原PID的内核路径原件**。[KERNEL-COMMAND](KERNEL-COMMAND.txt)将在新短命自有进程上实际核对系统caffeinate，以及argv0和参数同形、实际为自编其他程序的反例；本轮未运行。

22项本地回放涵盖原始ps正例、时长1/299、错误zsh/daemon/target父、错误路径/同名别的程序、-w/-s/-d/额外参数、N>300/零/负/小数、同角色两个、任意其他新程序、缺角色/目标、PID/父链竞态；均按要求接受/拒绝。改前 [red-01](red-01/result.json) 命中原 `unexpected_daemon_descendants`。辅助进程只单列收据；正常停机后另外确认它们消失，不直接发信号。未确认则BLOCKED，不删root，也不继续API信号；[profile-green-02](profile-green-02/result.json)含此顺序反例。

真实链peer现在真实派生系统caffeinate，原九个持久身份仍不变，额外两个只是辅助进程；ready在helper创建后完整原子发布。peer收到正常HUP时仅收回自己持有的Popen子进程。启动与归档分别保存拓扑收据；自然到期可以消失，不要求一直存在300秒。归档包含启动时真实两个helper的收据，实际路径由同一NativeRuntime检查，不模拟成功结果。

## TURN末尾失败的根因

`panes.ts` 的active是**提交收据**：`id=41705a5b-6a05-43da-982e-bb39b88d3cd3`；其`dispatch=1c526942-0c94-454a-82dd-a083ae1de1ed`才是派发ID。实际turn_submitted seq56和PermissionRequest seq64见 [submission-events](submission-events.json)。旧代码把active.id与dispatch.id相等比较，所以即使同一派发仍在许可等待也必然失败。历史pane_status未落盘，本轮没有伪造该原件；局部重放的status从真实submission字段构造并明确标注。

修复为：同launch下恰一条实际turn_submitted、active.dispatch匹配派发ID、active.id匹配该提交ID、仍busy且无失败。先落完整pane_status，再判定。[旧断言红态](submission-red-01/result.json)与[7项绿态/反例](submission-green-01/result.json)保存。旧turn-01/result.json仍INCOMPLETE，**不要重跑TURN**：一根/一POST已发生且turn-intent存在；修复只用于后续入口。

## 回收与排练顺序

1. 主控先运行KERNEL-COMMAND，核对实际系统路径与同名假程序反例。
2. 两场分别按 [CLOSEOUT.md](CLOSEOUT.md) 分步审签：原件脱敏→逐成员字节读回→独立从tar重数/审阅并签字→保存指针→owner-bound正常停机；停后SQLite读取0。probe是实际七进程的独立单角色profile，原Stage A/五身份、B1两身份、ready/源/claim/target全核对；09C业务入口显式只接受九进程09C profile，不能拿七进程profile替代。第2场仍按原九PID和原图，没有采纳新的helper为身份。
3. 回收后运行 [REHEARSAL-COMMAND](REHEARSAL-COMMAND.txt)，新目录09c-caffeinate-parity-rehearsal-01。没有REHEARSAL豁免；真实九进程/真实OS helper、真实daemon/relay/inbox/Stop/HTTP/Electron、标准归档/停止，真实时钟>120秒且<150秒、POST7/1、roots4/1、单Esc/无ack、模型0、420秒硬超时。失败保留，不另放宽进程集合。
4. [第3场材料](../09c-attempt-3-materials-01/PLAN.md)先准备、不启动。新freeze-c3机械要求上述两份新PASS、九身份/实际两个helper/归档/单Esc/无ack/重复拒绝等原件；缺收据时在prepare或建root前拒绝。[freeze-gate](freeze-gate.json)本地已证实未创建packet。通过后才生成标准materials-05与真实未签Stage A批准；本轮没有伪造PASS来冻结它。

其他本地回归及未通过的夹具准备保留原件：topology-regression-01是旧spy错误期望非法REHEARSAL能继续到拓扑；改为在receipt门拒绝，-02通过，真实09C排练仍走全部门。profile-green-01是relative archive路径的unit夹具错误，-02修正绝对路径后通过；该纯unit遗留scratch已逐成员字节归档后删除，原INCOMPLETE结果不改。recorded-entries首次漏--expect，argparse拒绝、未运行测试，-02通过。closeout材料首次shell heredoc分隔符冲突、无写入/场景动作，诊断保留。以上不算业务红态。
