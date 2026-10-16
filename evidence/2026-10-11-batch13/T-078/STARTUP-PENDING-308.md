# 主控 #308：待投递队列与首启逐屏按键

修复的离线领域检查 **PASS**；真实 daemon/CLI 的扩展排练 **INCOMPLETE，待主控沙箱外运行**；本差异的新独立审查 **INCOMPLETE**。A-14 现场续行 **NO_GO**。本轮未向任何现有窗格发键、注入、release、Stop 或回收。

根因在 `workbench/src/panes.ts` 的 screenKey/assertStartup：unknown、无 active、无故障、未停、未归档、未写入、无用户草稿、无未完成输入之外，还要求 queue 为空。pending 上线只登记入队恰好使该条件永远为假。产品修复仅删除 `!pane.queue.length`，同一 assertStartup 的其余条件以及三次检查位置均未改；键授权、快照字节、前台身份、首启次序、单次信任确认也未放宽。screenKey 本身不调用 drain，drain 仍只在 idle 时写出；因此批准的首启键不会把排队业务发进主题/安全提示/信任屏。

**Tracer bullet** 是 unknown＋一条 inbox 队列→批准的六个首启键→初始 release→同一条 queued 派发的唯一提交。**Deep modules** 保留 screenKey 的批准边界和 drain 的忙闲边界；没有新入口、重试或 reload。**Ubiquitous language** 中首启控制键不等于业务提交，pending/queued 不等于 delivered。

## 红态、绿态与范围

`09b-a14-startup-readback-01/readback.json` 从现有 A-14 SQLite 只读取得 executor 的 dispatch_queued（事件 109，全局 dispatch.seq=3，id `56827fd6-a03f-4c77-9dd6-ab39513e7b15`）。无 paste/turn_submit、无 screen-key intent/written，executor 实际 POST=0。主控已保存的 s1 ArrowUp 原件保持不变，真实 CLI 返回 screen_requires_startup，零发键。

`09b-startup-pending-red-01/results.json` 在修改产品前实跑：unknown＋一条 inbox 的首键与完整首启正例均精确失败于 screen_requires_startup，零写入。原队列前置否决也遮挡了后面的屏幕/前台检查，原始四项失败如实保留。`09b-startup-pending-green-02/results.json` 在一行修复后 15/15 **PASS**：首键、完整六键且零业务提交、release 后唯一 paste/CR；busy、idle、active、failed、stopped、archived、writing、draft、pending input 仍拒绝；异步身份检查期间出现草稿仍拒绝；非 executor、屏幕变化、无前台身份仍拒绝。green-01 保留，green-02 另记录 base revision 和产品差异，没有覆盖前证据。测试使用真实 Panes/store 与不可变 A-14 截屏/批准，PTY 和进程身份为 spy，不冒称实际窗口或真实 daemon 检查。

扩展既有 A13 排练，使 pending 条目经真实 Stop/relay 保存、真实 controller_start 入 unknown 队列后，用真实 gate CLI/daemon 连续执行六个已批准的首启键；每键都要求 state unknown、active null、同一队列、零业务 paste/submit，只有 release 后才要求 delivered、原 I2、ack/反例链。provider/PTY 仍为该离线排练已声明的 spy，反馈与门禁不模拟。阶段脚本先在一次性副本恢复旧队列否决取红，再在精确候选副本取绿；不改实际源码或 A-14 现场、不调用供应商 CLI/API/model。只复制 workbench/src、该排练文件与读取既有依赖的链接，退出后删除副本；各命令 5 秒、扩展场景 120 秒硬期限、外层每次 145 秒。SQLite/WAL/SHM 延续已有收尾留证，阶段核对 integrity。命令见 `STARTUP-PENDING-ENTRY-COMMAND.txt`。本轮只实跑其 --check-only 和 Node 语法检查，未启动该排练服务。

## 当前现场与 s1 命令

**不能在现有 A-14 上应用修复后重跑 s1**。A-14 daemon `48461` 按启动时 ESM import 缓存原 Panes；`pane_screen_key` 只把请求送回该进程，没有 reload 入口。新写文件不会替换它的方法。P1 在每个 key 阶段还会逐字核对 sources.tar.gz；已只读核对旧批准包确有 queue 否决、当前源码已不同。因此直接重跑会先被 Approved source changed 拒绝，即使绕开检查，旧 daemon 仍会 screen_requires_startup。不能修改旧批准包、跳过源码核对或给现有进程热补丁。daemon 的历史恢复不接管旧 PTY/会话能力，重启同一 root 也不能解决此场景。

`09b-a14-s1-retry-NO-GO.json` 列出按实际 launch label、批准和屏幕绑定的完整 s1 重跑 argv，输出 label 为全新 `a14-executor-s1-ArrowUp-02`；它是 **NO_GO 的诊断提案，不是执行授权**，没有发送。原签字件不改。当前没有可安全执行的 A-14 s1 重跑命令。最小后续是主控先完成这一个差异的独立审查，再裁定 owner-bound 回收 A-14、建立加载修复的新实例；新 B1 生成器会按实际 readiness/成功 launch/s1 快照生成精确命令，不能把旧 A-14 的绑定直接带入。

独立 ps 只读探测被沙箱拒绝，已如实记入 `09b-startup-scene-reuse-analysis-01.json`，未请求升级；PID 来源为主控阶段 A readiness，没有冒称本轮重新验证所有进程存活。不能续行的结论来自加载/恢复路径与旧批准源码的逐字差异，不依赖该 ps 探测。
