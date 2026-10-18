# T-096-1 当前交付记录

**INCOMPLETE**：`-01` 残留已由主控收尾、归档，收尾操作 PASS；`red-b-02` 与 `tracer-b-02` 均在第一轮后台故障注入阶段失败，尚未到达重启读回。修复后的 `-03` 及 `-02` 只读归档命令待主控运行。原失败摘要保持不变。

当前范围以主控 #89 转达和 main `8cf91b26e` 的 T-096“裁定”节为准：只恢复两个主控；worker 保留为“未恢复”，不启动 CLI、不重绑定、不改 attempt。不修改 `workbench/src/gates/`。主控 #88 允许先完成不依赖门禁裁定的路径。

主控没有跨重启的固定 PID 绑定：`Panes.controllerLaunch()` 返回的身份不含 PID；`caller()` 在单次请求内固定当次 leader（`panes.ts` 的 controller 分支），daemon 的 `assertCurrent()` 核对当次前台进程；`core.ts:340` 的 `registerController()` 只核对 task/project/spec_rev。worker 的旧 PID 绑定留在 `core.ts:2485`，没有改动。

2026-10-18 主控 #91 的实跑、原件核对与退出探针修复：

- `cleanup-failed-01.run.json` **PASS**：两场 `-01` 的六个 PID 已由主控确认退出，两个夹具已复制并比较。`red-b-01-cleanup-failed-01.archive.json` 为 78 文件／3,129,075 字节，`tracer-b-01-cleanup-failed-01.archive.json` 为 75 文件／3,080,910 字节，comparison 均为 true；这些现有记录一起提交，不改旧失败摘要。
- 原件核对见 `phase-readback-02.json`：两场均只有 epoch 1 的 daemon 启动收据、一次 controller_start、`window-1` 与 `before-view.json`；没有 `daemon-start-2.json`、`window-2`、`after-view.json` 或 `gate-after.json`。异常调用点为 `for owner in owned: kill(owner)`，位于第二轮后台启动之前。因此两场都**没有到达重启读回**，不能记作红态／绿态通过；仅初始真实 Claude argv 核对 PASS，fake POST 均为 0。
- `red-b-02.run.json` 的主异常 PID 为 15840，`tracer-b-02.run.json` 为 16098。调用链显示 alive 先执行一次 ps，再由 process_identity 立即执行第二次 ps；第二次遇进程消失时抛 rc 1。主控事后核对 14 个 PID 都已退出；原目录仍有死端点，故 finally 报 endpoint remains、cleanup false。本 worker 只读核对这些原件，未运行实际 ps 或归档。
- 修复为当前 runner 和 `-02` 归档命令共用的 `probe_process`：每次只用一个 ps 结果，rc 1 且 stdout／stderr 都为空才判退出；其余错误照旧。alive 不再做重复查询，发信号前刚好退出的 ProcessLookupError 明确记入退出回执；权限错误和身份变化不吞掉。
- `process-probe-contract-01.json` **PASS**：替代 ps／信号边界，覆盖空 rc 1、带输出 rc 1、其他返回码、坏格式、单次读回、信号前退出、权限错误和 PID 变化；上一候选 `958ede25f` 被退出竞态反例拒绝。
- `archive_failed_02.py` 只读核对固定两个 `-02` 夹具、14 个 PID 和端点状态；不启动或停止 agent、不改源目录。明确排除死 IPC socket 与 operator 私密凭据，保留其原件，复制其余部分并比较数量／字节／路径。清单列明排除项及比较范围，不把过滤后的副本称为完整原树。
- `archive-02-contract-01.json` **PASS**：真实临时文件、复制和 symlink，替代 PID／socket 探针；存活 PID、活动／未知端点及后续 epoch 均拒绝，源文件／旧摘要原样保留，私密和 IPC 不进入副本；独立已知文件数／字节数核对通过，绕过排除项的变异被拒绝。未操作真实两场 `-02` 目录。
- 既有收尾、固定 `-01` 收尾入口和 argv 解析局部回归分别为 `restart-cleanup-contract-07.json`、`fixed-cleanup-contract-04.json`、`runner-materials-probe-01.json`，均 PASS，仍限替代进程边界。下一次使用 `red-b-03`／`tracer-b-03`，命令见 `RUN-RESTART.md`。

2026-10-18 主控 #90 的实跑与脚本修复：

- 两场原始摘要为 `red-b-01.run.json`、`tracer-b-01.run.json`，完整日志在各自外置盘目录。真实初始 Claude argv 核对通过，fake POST 均为 0；两场都未走到重启后的验收断言，不能当作合同红态或绿态。
- 已确认脚本缺陷：`process.stdout.read()` 在非阻塞模式可能为 None；计划内杀掉 Electron 后旧 Observer.close 拒绝非零退出；旧 finally 在布局查询／Observer 收尾出错后跳过 daemon_stop。原摘要中的 cleanup_error 分别是 caller_identity_required、observer_exit_nonzero。另：red-b-01 的实际 argv 未含 `--expect-red`，重跑命令明确带上该参数。
- 修复集中在本票脚本和测试，没有改产品 src/app/gates。`restart_cleanup.py` 由 runner 和固定收尾脚本共用，负责非阻塞输出、退出证明、私有 operator 请求及顺序收尾；失败诊断被保留，不作无声 fallback 或重放停止请求。
- `cleanup_failed_01.py` 只处理主控列出的两个夹具／六个 PID。先核对全部身份，再各用原 operator 凭据执行 daemon_stop；不强杀、不新开 attempt，确认退出才归档，原件和旧失败摘要保留。旧运行缺历史精确 lstart 的限制已写进脚本、preflight 和运行说明。
- `restart-cleanup-contract-06.json` **PASS**：以 `10c0168db` 为反事实，两个真实报告的缺陷均在替代进程边界重现；当前 runner 的实际 AST 及共用收尾函数通过 None／部分输出、计划内非零退出、布局诊断、身份变化、停止回执丢失、活写入者、归档失败和私有凭据等检查。没有执行真实残留收尾。
- `fixed-cleanup-contract-03.json` **PASS**：固定收尾脚本真实入口在替代进程／socket／归档边界下，只有两场／六 PID、第二场不符时零 stop、停止前 PID 变更拒绝、退出先于归档、凭据不进归档、原失败摘要不变。删掉最后身份复核的变异被业务断言拒绝。
- `restart-cleanup-contract-01.json` 的局部夹具缺 cleanup_complete 字段属于测试适配失败，原件保留；后续报告不覆盖它。

本次局部证据：

- `decision-b-contract-02.json` **PASS**：真实 SQLite／原生文件，替代进程边界；两个有效主控恢复、三个失败各自保留、worker 无新 PTY、attempt 原字节不变、argv 全字段、原启动记录不变、关闭集与位置、0 次输入写入。上一 WIP `a8fbc72bd` 被“worker 必须未恢复”断言拒绝。
- `layout-ipc-contract-02.json` **PASS**：真实 main/preload 模块，替代 Electron/transport；退出应用保留打开集、显式关闭只删一个、重开沿用位置、失败 worker 无输入凭据。关闭却不移除保存集的变异被业务断言拒绝。
- `daemon-restart-contract-b-02.json` **PASS**：真实 transport 模块，替代 IO 边界；死进程加拒绝连接的旧端点允许重启，活进程、未知 owner、活 socket、非 socket、异步期间更换 PID 均不删除端点、不发凭据。起点 `3c9016d02` 的死端点重启被业务断言拒绝。`-01` 的 VM 缺 URL 属测试边界适配失败，原件保留。
- `runner-materials-01.json` **PASS**：脚本语法、原生 argv 缓冲解析；空参数、空格、引号、Unicode 与换行保留，环境不进入 argv。未调用 macOS sysctl，不作实际进程证据。

`run_restart.py` 已按裁定 B 重写：真实配置 Claude 2.1.302、真实 daemon／Electron；只有三格夹具中的 worker 使用受控 C receiver。原生续接的 argv 从 macOS sysctl 独立读取；实际终端还须显示历史 nonce。历史由脚本在停止的隔离目录中预置，明确为合成夹具，不冒称模型生成或 CLI 自行保存。遇初始化／信任／权限屏不自动确认，读回不成立就 INCOMPLETE。详见 `RUN-RESTART.md`。

`static-checks-b-01.json` 的语法、编码、修改范围和项目地图检查 **PASS**（0 problems、0 stale living docs）。Claude 启动版本与 driver 选择局部回归分别见 `t091-version-regression-b-01.json`、`driver-selection-b-01.json`，均 PASS，适用范围仍为替代边界。

尚未完成：两个 `-02` 夹具的真实只读归档、`-03` 的真实单格与三格重启、三个独立故障和失败隔离、真实 CLI 历史读回、完整 GUI 回归、独立审查、门禁 submit。原门禁重绑定阻塞已由裁定 B 移出本票；不再等待它实施。

下列为第一轮 WIP 的原始局部证据，保留其适用范围：

身份：s16-t096；T-096 / a1；执行器 gpt-6.1-sol / xhigh；派发来源 launch-14dcc6be543a483ab0b03021f573d028；起点 main 3c9016d02；合同 ready_rev 1。CLI 实际供应 tier 未核对。

Ubiquitous language 沿用 CONTEXT.md 的启动记录、原生会话、attempt 与窗格。Deep modules：恢复的 argv 与原生会话核对由 `paneRecovery.ts` 承担，启动配置仍只读原启动记录；窗格集是同库现有事件流的投影，没有第二套 profile。

已有证据（均为局部合同，不是后台或 GUI 验收）：

- `contract-red-01.json`：修复前 recover 重启数为 0，命中应为 1 的业务断言。真实 SQLite，替代进程边界；模型回合 0。
- `contract-tracer-green-02.json`：同一合同转绿，核对前台身份确认、原启动记录不变，以及非 session 选择器的 argv 字段保留。
- `t091-ipc-regression-01.json`：新 layout 命令未被旧 VM 边界识别，属于测试适配失败，保留。
- `t091-ipc-regression-02.json`：只增加 operator layout 命令边界后，原 pane-key、窗口隔离、序列号、输出路由、历史 attempt、错误绑定等断言通过；两个已知坏版本仍被原业务断言拒绝。
- `t091-version-regression-01.json`：原 Claude 启动版本合同及版本校验变异检查通过。

第一轮的阻塞正文保留在 `ISSUE-worker-runtime-rebinding.md`，作为日期记录；当前裁定不恢复 worker，因此不再把它作为本候选的推进阻塞。首轮脚本未运行；当前运行步骤以 `RUN-RESTART.md` 为准。
