# 主控 #365：拓扑取证与排练检查接线候选

状态：**本地入口/反例 PASS；真实三时点探针与新的完整排练 INCOMPLETE，未运行**。不改 `workbench/src`、app、acceptance 或冻结 protocol；不碰第2场现场，不加任何子进程允许项，第3场仍NO_GO。

主控新增的 `../09c-attempt-2-diag-01/current-topology-01/` 原件随本次提交保留：两次 daemon 后代均为原七节点，extra/missing均空。它证明这些观察时刻没有额外后代，不能恢复失败时已退出或重挂父的进程，也不能单凭 `Started caffeinate` 日志认定旧故障的进程名。

## 已实现与已跑的证据

1. `NativeRuntime.topology` 仍严格核对原九节点关系及整个后代集合。拒绝前在**自己的root/topology-diagnostics/<uuid>** 保存此次原数值ps stdout/stderr、UTC时间、差异，以及该树/原身份的逐PID完整command、comm、lstart、当前父链和原始ps字节。先保存原图，再做详情探测；进程已消失/ps失败如实记INCOMPLETE，不补猜。没有取全系统其他会话argv/环境。新目录随标准raw_sources进入脱敏归档。
2. 删除 `scene != REHEARSAL` 两处豁免及 REHEARSAL owner 的接受路径。所有场景都核对原收据、九进程、两次身份与全拓扑；全量标签换顺序也不能跳过。停机后单API子集核对保留原生命周期语义。
3. 确定性真实链改为两组**真实zsh→Python peer**；真实PID/PPID/PGID、原Stage A五身份、两B1 manifest、真实API ready及源版本经同一owner producer/validator。peer实际接收session/debug参数，manifest明确写Python而非伪装Claude。新增同一B1收据/屏幕计划检查与真实P1 `--stop-before-cli` 前置入口；供应商仅在node-pty执行边界替换。
4. 协调器继承的cleanup改走同一 capture→tar逐成员字节读回→独立重数→finish/拓扑→认证daemon_stop→API各一次SIGTERM→验退出/文件→删根；SQLite停前一致backup包含WAL，停后读0。未绑定owner或任何原件/拓扑不符时保留现场，不能用强制清理来取得PASS。

实际本地记录：`guard-red-01`为旧scene豁免红态；`diagnostic-red-01`与`known-bad-diagnostics-01`为旧拒绝不留快照红态；`guard-green-03`为同一入口绿态（含真实收据文件的21项绑定/标签反例）；`guard-mutants-02`四个去检查变异（receipt、九进程、topology、diagnostic）均在新增断言失败。它们的ps/进程transport明确是夹具，**不冒称真实子进程取证**。

`tools-regression-01`原43项归档/条件Enter/适配检查PASS；`handler-regression-01`因单元API-ready重复创建失败，原件保留；修正夹具为核对既有producer原件，`handler-regression-02`纯Handler离线回归PASS。原受控服务ready不重写；仅offline producer补齐自己声称的unit字段。`probe-entry-01`覆盖缺批准/未签/错上限在建root前拒绝、重复turn输出零读取/零键/旧result字节不变，以及出现/消失时点记账。最新终查会补本次语法/路径/当前入口输出；旧结果不覆盖。

第一轮guard-mutants-01准备时文本替换匹配了两处，尚未生成/运行变异；空目录不作通过证据，错误另存 `guard-mutants-01-preparation-error.json`，正式用-02。没有在工作树回退/应用坏源码。

## 无豁免清单与证据边界

[PARITY.md](PARITY.md) 逐项对照 #364 上轮清单。所有直接场景豁免已删除；完整真实九进程/归档生命周期、供应商首启与实际version/help的外部证据仍待主控分别运行排练/真实探针。测试运输层与确定性输入用明确标签记录，不能把unit spy计为真实链PASS。新排练尚未跑，不继承旧七进程排练的拓扑结论。

这条线采用 Tracer bullet：同一启动入口、真实ps、阶段屏障、收据与回收串起来再取证。Deep modules 用于共享进程快照与原owner验证，避免为探针另写API协议。Ubiquitous language 保持“原身份”“后代”“出现观察/消失观察”“允许项”分开；观察到进程不等于已批准允许。

## 下一步，分开运行

`PROBE-COMMANDS.txt` 和未签 `setup-approval.json` 在源码提交后由 `write-materials.py` 从实际git提交号生成。先新隔离root/假API/真实daemon与确定性目标，再由主控审签B1、逐屏六键；只启动**一个**真实Claude2.1.296角色，不启动Codex或executor Claude。idle采样10秒、HTTP屏障期间15秒、真实PermissionRequest待批时15秒，采样间隔至少100ms；角色模型0、1根/1POST，**工具许可Enter上限0**。首启六键仍各自独立批准。

`REHEARSAL-COMMAND.txt` 为新的完整协调器真实链命令，九个持久进程均是真进程，供应商为确定性PTY peer，模型0；真实时钟>120000/<150000ms、POST7/1、roots4/1、目标单Esc/无ack，420秒硬超时。先读探针证据，仍不允许任何未知子进程；排练如遇拓扑异常应保存原始图并INCOMPLETE，不加长时间或绕过。对本候选的新独立审查尚未进行。
