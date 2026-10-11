# 用户验收与最新决定（直接任务输入）

T-075-4：最小 Electron 窗口经后台本地入口显示项目、任务、真实 PTY xterm 窗格和门禁。Electron 不持有 PTY／库。关窗不影响 worker，重开接同一个窗格。后台重启显示中断或未知，不自动续跑、不伪造完成。外置盘未挂载时构建报错，不回退内置盘。只读显示、字节游标分段读取、固定160×45 已批准。

六项完成条件：
1. capturePage 截图有项目、任务、真实输出和门禁，附命令。
2. 关窗后 ps 同一 PID；trace 增长；重开补回原文逐字相等并继续实时输出。
3. 停启后台后库和 CLI 显示批准的原 attempt／窗格中断语义，没有自动续跑或完成。
4. 挂载构建成功；配置指向未挂载路径时报错，没有内部缓存回退。
5. 没有结构化信号时未知，有不读屏反例。
6. project_map.py status 0 problems。

主控 #44 最新原文：
“live-04 已由执行主控跑完，结果 INCOMPLETE。核心证据已经齐了：
- offline-trace 通过；
- 首窗、关窗、重开补回（reopened-backfill.png、live-after-reopen.png）、后台停止、重启后都有截图；
- interrupted-original-attempt.png 已核对：历史回放可见，窗格状态显示‘未知’，执行状态显示‘已中断’，门禁仍是‘已认领’，候选、验收、集成都是‘尚未开始’，与批准的语义一致。
唯一失败的是 run_pane_lifecycle.py 第356行，原因是 contexts 为空。归档库里这个 launch 的 native_record 只有 session_meta 和 task_started 两条，没有 turn_context。
请这样处理：
1. 修产品：pane 退出、pane_stop 或 daemon_stop 时，先把绑定原生会话的记录做最后一次增量读取并追加入库，再完成停止。读不到的部分记一条明确的事件，不要静默跳过。
2. 用离线夹具验证这个修复：自建一个 rollout 文件，模拟只有 hook 前段已入库、随后停止的情况。在改动前取红态，改动后转绿。不要为此花真实回合。
3. live-04 的其余证据照常引用。第356行的断言失败要如实写进 RESULTS，并注明修复用离线方式证明；真实回合已用3/4，不再追加。
4. 之后做独立审查，然后交付。”

本次审查只读、fresh-context、一次。发现问题由 worker 先取红态再修，修复 diff 由执行主控审。ticket 保持 open，待主控关闭。不启动模型或 Electron，不接触正式工作台、全局配置、Herdr server。
