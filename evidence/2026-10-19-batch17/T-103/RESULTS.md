# T-103 / a1 项目与任务选择页

状态：**INCOMPLETE（待提交与独立验收）**。第八次真实旅程九项 PASS，七张截图已生成；09 的 `contracts-20261019T065323Z-summary.json` 也为 PASS，基线／候选两份 IPC 和两份真实窗口检查均退出 0。日志中的 AssertionError 是坏实现被预期拒绝的证据，详见主控 #17 小节。09 随后的提交因 evidence 位于稀疏 cone 外被拒，HEAD 仍为 cc18d93db；15 个 workbench 文件已暂存。现只按主控 #17 修提交脚本并沿用这两份 PASS 证据，产品和测试不改、不重跑。独立验收、稀疏地图及“经门禁移除”措辞仍待主控处理。

## 绑定与范围

- ticket：`.project-map/tickets/T-103-workbench-project-task-picker.md`，ready_rev 1。
- 起点：`cc18d93dbbcf2ee641dc92befe68e5b0609b4807`；分支：`exec/t103`。
- task / attempt：T-103 / a1；worker：s17-t103；Herdr pane：wF:p6Z。
- session：`4ff6af88-2671-4679-929b-3600d21a4f61`；原生会话：`01a1527f-d852-78b2-a13b-c5e266daeb0d`。
- launch：`launch-e2e8f3f912194346bc6568291e17e048`；启动记录配置为 `gpt-6.1-sol`、xhigh、default。记录配置不证明供应商实际 tier。
- 授权：派发逐字引用用户 2026-10-19 选“A 先补功能再打包”。执行主控随后明确：本票经 Herdr 文本交付，不走门禁 submit，没有任务卡或 oracle_paths；保护 `acceptance/` 和现有测试断言，提交后由主控独立审查、合入。
- 目标：列出已有项目和任务，切换任务的窗格视图；不指定 task 时进入选择页。
- 非目标：创建／删除／搜索、普通 zsh 窗格、后台自启、打包、模型调用、门禁变更和全局配置。

**Tracer bullet**：同一 tasks 表 → 后台两个只读命令 → preload IPC → 左侧项目／任务列表 → 现有窗格渲染。**Deep modules**：门禁拥有任务查询，main 拥有视图绑定与输入凭据生命周期，不增加另一套存储或窗格托管。**Ubiquitous language**：沿用项目、任务、窗格、编排后台和 launch。

## 实现

- `projects_list` 从当前 tasks 表的 project_id 去重；`tasks_list --project` 返回 task_id、project_id、标题和状态，按 ID 排序。未知项目为空列表，无效 ID 拒绝。两条命令不写请求事件或库，也不进入认领／验收／集成与操作锁路径。
- Electron 左侧显示项目和任务，支持刷新、鼠标与原生按钮键盘操作，标题与任务状态来自后台。空库给出中文提示。
- 切换前验证目标，等待旧视图已接收的输入操作，再撤销窗口输入凭据；切换后旧 pane key 失效。只断开视图，保留原任务的窗格布局与后台会话。不动 `workbench/src/panes.ts`。
- `--task` 可省略；指定 task 仍直接显示任务。`--launch` 仍要求 task。README 已同步启动和只读命令。

## 当前证据

| 验收条目 | 状态 | 证据或缺口 |
| --- | --- | --- |
| 红态：不带 task 退出 | PASS（已知坏版本） | `red-startup-01.json` 和 `run-20261019T063741Z-summary.json`；真实 start.mjs 与同一 Electron 的缺 task 路径按预期退出 1 |
| 红态界面无列表；绿态两项目、每项目两任务、切换窗格 | PASS（当前产品源码） | 同轮红态固定任务窗口可读且无列表；候选列表一致，完成五次跨项目选择，包含键盘选择；每次按独立 task、launch、终端字符串核对，旧 key 与不存在任务被拒 |
| 列表前后库字节不变、未知／无效项目反例 | PASS | 同轮 sqlite3、WAL 全字节相等；不用校验值，不把共享内存锁文件当业务库内容 |
| 移除后刷新 | INCOMPLETE（隔离库场景 PASS） | 同轮删除隔离夹具 task 行后，列表与所选窗格清空，历史归属不使任务复活；没有现成门禁删除命令，是否满足原条目仍待主控裁定 |
| 空库、显式 task 原行为 | PASS | `run-20261019T063741Z-summary.json`：显式入口 task、标题、launch 和独立终端输出一致；空库中文提示、无任务／窗格／alert |
| 真实入口截图与复现命令 | PASS（完整旅程） | 同轮七张：red-missing-list、green-picker、green-switched、green-narrow、green-removed、green-explicit-task、green-empty。复现见 02 脚本 |
| 不动门禁入口／操作锁 | 实现检查完成，待独立审查 | 只增加只读命令表项、查询与日志豁免；未改门禁状态迁移、锁、fence、CAS、attempt 绑定 |
| project_map status 0 问题 | INCOMPLETE（当前稀疏目录） | `map-sparse-01.json`：8 个缺失项、0 stale；完整主仓库只读检查为 0 问题、0 stale，见 `map-full-checkout-01.json`，不拿主仓库检查替候选目录通过 |

沙箱内完成 Node 语法检查（main、preload、start、daemon、core、driver），Python AST 解析、shell 语法检查及 `git diff --check`。这不是构建或端到端通过证据。一次 `py_compile` 因系统 Python 将缓存写到沙箱外而失败；未申请升级，随后只做不写缓存的 AST 解析，未把编译失败称为通过。

既有 `node --experimental-vm-modules workbench/tests/test_t091_start.mjs evidence/2026-10-19-batch17/T-103/start-forwarding-01.json` 退出 0，三条 launch 完整转发与 Electron 环境处理通过；同一测试拒绝其原有已知坏版本。该检查使用 VM 外部边界，不算真实 Electron 或后台绿态。

依赖由执行主控在沙箱外安装，rc 0；当时尚无 Electron 二进制，node_modules 占内置盘 **179,532 KiB**，workbench 安装前后增加 179,536 KiB，见 `install-01-summary.json`。第三轮显式安装成功后，worktree node_modules 为 **481,824 KiB**，本次补二进制新增 **302,292 KiB**；基线副本的 492,200 KiB 全在外置盘，见 `run-20261019T051645Z-summary.json` 的两份安装记录。锁文件及依赖版本未改。npm 输出既有依赖的 3 high severity vulnerabilities；未做归因或扩大到依赖升级。缓存、下载与构建槽继续在外置盘，无盘报错。

### 首轮环境失败与脚本修订（执行主控 #8）

主控运行 `RUN-OUTSIDE-02-E2E.sh`，rc 1。`run-20261019T050450Z-summary.json` 保留 INCOMPLETE：真实 start.mjs 的无 task 红态通过，随后基线 daemon_start 失败。外置盘 `run-20261019T050450Z/fixtures/red-state/daemon.stderr.log` 为 `EACCES: permission denied, access .../node-pty/prebuilds/darwin-arm64/spawn-helper`；这是安装环境失败，不算业务反例或产品红态。完整执行日志位于主控回传的 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t103-e2e-02.log`。旧摘要、归档和基线均保留。

执行主控明确指出基线 helper 为 644，并已把 worktree 中对应 helper 手工改为 755。本次只修测试脚本：基线 npm ci 后，仅对该副本的 `node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper` 执行 chmod 755，理由逐字记录为“按 README:319 处理测试副本”。修订后的脚本选择**新的时间戳目录，不复用旧副本**；目录已存在则退出。`baseline-install.json` 保存授权、目录、chmod argv 与前后 mode，下一轮 run 摘要会包含该记录。产品代码不自动 chmod，不补改已有失败归档。

### Electron 二进制缺失的原因与处理（执行主控 #9）

第二轮 `run-20261019T050726Z-summary.json` 仍为 INCOMPLETE、脚本 rc 1。helper 已由 644 改为 755，真实基线后台与任务夹具已建立；随后测试启动器直接读取 `node_modules/electron/path.txt`，得到 FileNotFoundError。基线与 worktree 的 Electron 目录都只有 npm 包内容，没有 path.txt／dist。原始日志 `t103-e2e-03.log` 和外置盘对应 run／fixtures 保留，不把此失败算为业务红态。

**REALITY GATE: PASS（处理方向）；实际环境恢复仍为 INCOMPLETE。** 目标是在当前锁定版本上显式准备二进制；不改依赖、全局 npm 配置、产品启动行为或主仓库 node_modules。以下是 2026-10-19 的已核对事实：

- observed：npm 为 12.0.1；worktree、基线与主仓库的 Electron npm 包都是 43.4.1。本地 `node_modules/electron/package.json` 没有 scripts 字段，锁文件对应条目也没有 hasInstallScript；包提供 `install-electron → install.js` 的 bin。主仓库同版本虽有 dist，也不能据此认定它由旧 npm 的 postinstall 下载。
- observed：Electron 从 42 起取消 postinstall 下载，改为首次使用时下载，并提供独立的 install-electron。[官方变更说明](https://www.electronjs.org/docs/latest/breaking-changes#behavior-changed-electron-no-longer-downloads-itself-via-postinstall-script)。43.4.1 的[官方包清单](https://github.com/electron/electron/blob/v43.4.1/npm/package.json)与本地结构一致。所以本次 npm 12 没有 Electron postinstall 可执行，不能归因为 allowScripts 把它拦了。
- observed：本地 npm 12.0.1 的 `@npmcli/arborist/lib/arborist/rebuild.js:198-225` 从 package.scripts 取 lifecycle，仅将存在的项目排队；bin 不受该脚本门控。日志只列 fsevents／msgpackr-extract 与上述事实相符。[npm lifecycle 文档](https://docs.npmjs.com/cli/v12/using-npm/scripts/)。
- observed：已安装 Electron 的 `install.js` 从同目录 package.json 取版本，把 `electron_config_cache` 作为 cacheRoot；下载完成后写 dist 和 path.txt。`index.js` 在 require('electron') 时可触发同一安装器；原测试直接读 path.txt，没有经过这个惰性入口。上一版测试准备漏了显式安装与完整性检查。[43.4.1 安装器源码](https://github.com/electron/electron/blob/v43.4.1/npm/install.js)。
- unknown：补下载能否完成、实际二进制能否执行、完整安装后内置盘增加多少。最小探针由执行主控运行下面的安装脚本；安装器或任何核对失败就停止并保留日志，不换版本、不回退缓存、不进入 UI 测试。

新增 `RUN-OUTSIDE-04-ELECTRON.sh`，接受两个绝对路径：已 npm ci 的 workbench，以及尚不存在的外置盘记录目录。它核对项目、锁文件和已安装包的 Electron 版本一致，再显式调用该包的 `node node_modules/electron/install.js`；不使用会解析其他版本的 npx，不修改全局 npm 配置。下载缓存固定 `/Volumes/WD-Elements/a2a-electron-cache`，下载临时文件也放外置盘；挂载失败立即停止。

安装后核对 path.txt、dist/version、二进制执行位，并以 `ELECTRON_RUN_AS_NODE=1 <该二进制> -p process.versions.electron` 读回实际版本；此探针不启动模型或 GUI。结果记录 argv、版本、权限、前后 node_modules KiB 及差额，且逐字节确认项目 package.json／锁文件未改。安装失败的 stdout／stderr 与 INCOMPLETE 记录留在新目录，不覆盖原失败。

`RUN-OUTSIDE-02-E2E.sh` 现会对 worktree 和新时间戳基线副本各执行一次此准备，run 摘要包含两份安装结果；补齐后再做真实 E2E。旧基线不复用。T-104 可在自己的 npm ci 后复用同一脚本，第二个参数应使用 T-104 自己的外置盘证据目录：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t103/evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-04-ELECTRON.sh /T-104-worktree绝对路径/workbench /Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/electron-新的名称
```

第三轮已核对该步骤在 worktree 与基线副本分别 PASS，具体体积和版本见下节；不能把安装步骤通过上调为整票通过。

### 第三轮：新驱动的 ready 等待环（执行主控 #10）

第三轮 `run-20261019T051645Z-summary.json`：worktree／基线的显式安装、dist/version、实际二进制版本 43.4.1 与执行位均 PASS。之后 red-fixed-task 的 Electron 握手 30 秒超时，cleanup 因启动未确认而保留进程和夹具。主控报告 Electron PID 85822、父启动器 85798、S 状态、无 renderer／GPU 子进程；worker 没有发信号、启动其他 Electron、移动 bundle 或修改 xattr。安装问题已解决，本次失败是测试驱动问题，不能算产品红态或再次归为安装环境。

只读证据如下：

- `red-fixed-task/driver.ndjson` 只有 start，说明外置盘 Electron 已进入驱动，版本 43.4.1／Node 24.18.1；stdout、stderr 都为空，没有 ready 握手。
- 夹具库 `orchestration_events` 的最后两条是该 task 的 pane_layout 请求及成功结果。基线产品已加载并调用后台；`run` 在创建窗口前会 await app.whenReady。结合主控观察的无 renderer，等待点指向 ready 之前。
- 新驱动旧版在模块求值期间 `await run(...)`；外层观察入口又 `await import(driver)`。Electron 等入口模块求值结束后才能继续 ready，而 run 等 ready 后才能返回窗口，形成互等。握手超时是其后果。修复只把窗口等待移到脱离模块求值的 Promise 回调，保留产品导入的 await 和真实窗口完成后的握手；不先发假 ready。
- 本仓库 `bisect_electron_ready.py` 及 2026-10-10 的 `evidence/2026-10-10-batch12/T-075/card-4/outside-checks-05/ready-bisect/results.json` 已在内置盘 Electron 二进制上用对照实测定位同一等待链。现有 electron_driver.mjs 因此使用 void run(...).then(...)。本票新驱动未沿用这一启动方式，重引入了已知问题。历史对照支持诊断，不替当前版本的真实重跑背书。[Electron ESM 文档](https://www.electronjs.org/docs/latest/tutorial/esm#you-must-use-await-generously-before-the-apps-ready-event)说明入口模块与 ready 的时序约束。

外置盘位置判断：外置盘上的二进制已经执行驱动、成功完成真实无 task 拒绝并请求后台；既有内置盘对照也能复现同类阻塞。因此，外置盘不是形成此等待环的必要条件。**本轮还没有外置盘成功渲染证据，不能宣称位置因素全部排除。** 修复后的重跑仍使用外置盘基线二进制和原有 30 秒握手期限；不换到内置盘绕过、不延长等待、不改产品。

第三轮已经完成与尚未完成的范围：

| 场景 | 结果 |
| --- | --- |
| 真实 start.mjs 不带 task | PASS：退出 1，符合已知坏版本的合同红态 |
| 真实 Electron 调用基线 run、不带 task | PASS：按预期拒绝，退出 1；未创建窗口 |
| 基线后台与两项目四任务夹具 | 已建立；包括一次 revoke 操作和历史输出输入。该操作返回 ready，并无 revoked 状态。属于测试准备，不能算选择页通过 |
| red-fixed-task 窗口、终端、无列表截图 | INCOMPLETE：等待环阻塞，未完成；截图数为 0 |
| 候选列表、切换、空库、移除、库字节检查 | 未进入，无绿态 |
| 85822／85798 与测试后台清理 | INCOMPLETE：旧现场保留；脚本交主控执行，不冒称已清理 |

修复后新增 `test_t103_driver_startup.mjs`：在 app.ready／窗口尚未可用时，直接求值真实驱动模块，要求入口先完成；第三轮保存的已知坏驱动不能完成，修订驱动能完成且尚未宣称窗口已就绪。初次 `driver-startup-10.json` 为 PASS；补充“不得在真实窗口前发送 ready”的检查后，`driver-startup-10b.json` 也为 PASS。它只证明等待链解除，不证明真实 Electron 渲染；同一检查已接到 RUN-OUTSIDE-02 的开头，防止再次把该等待环带入真实测试。新驱动同时记录 PID、时间、app-ready／window-created／window-loaded 阶段；Python 在等待握手前就保存启动 argv 和启动器 PID，避免再出现失败启动没有身份记录的缺口。现有测试断言未动。

主控按以下顺序执行：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-05-DISPOSE-85822.sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-02-E2E.sh
```

05 只针对主控点名的 PID 85822：核对用户、父进程 85798、Electron 与启动器的完整 argv、当前启动时间和无子进程，并在发信号前再次核对身份不变，才发送 SIGTERM。只等待 5 秒确认原进程退出，不发进程组信号，不自动 SIGKILL；身份变化或出现子进程就停止。新处置记录留外置盘并写小型摘要／清单，旧运行不覆盖。该脚本**不结束原测试后台**；只读查看的 red-state/daemon.pid 为 83691，后台和 `/private/tmp/a2at103-_o2_ksvs` 夹具仍保留供主控按原门禁收尾，不手工删除活跃库。

### 第四轮与缺 task 退出对照（执行主控 #11）

**关键问题的答案：是。** 基线构建 `t103-red-138f84f1a8/dist/main.mjs:244-245` 在 run 的第一条检查拒绝缺失 task，发生在第一次 await、后台请求及 app.whenReady 之前。裸 main 入口在 391～393 行 catch 后直接 console.error 并 app.exit(1)，不等待 ready。外层 start.mjs 自己也会更早拒绝缺 task，但这条 Node 启动器红态不能代替 Electron main 的退出验证。[官方 app.exit 文档](https://www.electronjs.org/docs/latest/api/app#appexitexitcode)说明其立即退出语义。

主控已运行 05，rc 0，85822 退出且未向其他进程发信号；结果为 `dispose-85822-20261019T052841Z-summary.json`，旧后台和夹具仍保留。第四轮 `run-20261019T052842Z` 再次安装检查通过、驱动等待链检查通过，但真实 red-no-task 在 30 秒握手期限后失败，留下 Electron 75497；主控观察它已由 launchd（PID 1）收养。worker 没有处置该进程。

只读重读日志时，文件已经比主控最初观察追加了内容：

- 05:30:50.445Z：PID 75497，start，task=null，app_ready=false。
- 05:30:53.362Z：product-imported；05:30:53.537Z：driver-registered，随后同一时间已记录 startup-failed，错误正是缺 task 的预期错误，app_ready=false。
- 05:31:36.039Z：app-ready。不能再把“始终没有 app-ready”当作当前完整日志事实。
- stderr 随后出现 stdout write EPIPE 的未处理 Promise 拒绝。驱动 failed() 在 await reply({startup_error}) 之后才 app.exit(1)；该 await 若拒绝，下一行退出不会执行。这是代码路径推断与实际 EPIPE 的对应，不是已经证明 Electron 的 app.exit 调用失效。

因此第四轮已经证明产品的缺 task 检查执行了，但没有完成退出和错误回执。上一轮“解除 ready 等待环”的本地检查不足以证明这个失败退出路径；第三轮的历史类比不能继续当作唯一根因。**REALITY GATE: INCOMPLETE（真实退出对照尚未完成）。** 本轮不再修改驱动、退出处理或产品，也不放宽期限，先保留变量做对照。

已只读核对主仓库内置盘和第四轮外置盘两份 Electron：package.json、dist/version 都为 43.4.1，path.txt 都指向 macOS 可执行文件。主仓库现存 dist 的安装来源仍不据此补推；新脚本还将分别运行真实二进制版本探针。

`RUN-OUTSIDE-06-COMPARE-STARTUP.sh` 固定第四轮同一基线构建、同一未修改驱动、同一环境策略与 stdout pipe／stderr 文件方式，每组只跑一次：

| 二进制 | 裸 main.mjs，不注入驱动 | 注入第四轮驱动 |
| --- | --- | --- |
| 主仓库内置盘，10 月 10 日安装的副本 | internal-bare | internal-driver |
| 第四轮基线外置盘副本 | external-bare | external-driver |

四组都不带 task，独立预期为因缺 task 退出 1；裸入口直接调用 Electron 加原 main.mjs，不经 start.mjs 的前置参数守卫，也不增加观察模块。驱动组必须同时收到正确错误回执并退出 1，单有 startup-failed 日志不能通过。版本、argv、PID／启动时间、起止时间、原始输出、驱动阶段与实际退出码均保存。

每组的观察上限仍为 30 秒；超时始终记为未满足合同，即使随后处置成功也不改为 PASS。只对探针自己新建且核对身份未变化的子进程发 SIGTERM 收尾，不自动 SIGKILL；若退出仍未确认，保留现场并停止后续组，避免继续留下孤儿。没有 npm install、构建、后台启动、模型调用、bundle 复制／移动或 xattr 修改。原有主仓库、第四轮基线和驱动字节保持不变，原日志不覆盖。

若两组裸入口都通过而驱动组失败，可把影响缩到驱动／握手；若内外盘的裸入口结果不同，说明“二进制副本／位置”这个维度存在差异，仍不能仅凭两份副本就分开文件内容与物理位置；若四组均通过，也只能说本次未复现，不能宣称旧故障消失。该脚本 rc 1 可以表示某组未满足退出合同，结果仍有诊断价值，应读各组状态和原始日志，而不是继续换安装环境。

先处置主控点名的 75497，再运行对照：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-07-DISPOSE-75497.sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-06-COMPARE-STARTUP.sh
```

07 按第四轮保存的 launch.json，核对 PID 75497、UID、父进程 1、完整 argv，并在发信号前复核启动时间与身份没变，才向这个 PID 发 SIGTERM；不发进程组信号，不动原后台或夹具，5 秒未确认则保留现场、不自动强杀。worker 只写脚本和只读诊断，没有执行 06 或 07。等四组结果回来后再决定最小修复与整套 E2E 重跑，不预先改驱动掩盖比较。

### 主控 #12：处置回传、Python 缺陷与退出路径判断

主控运行 07 后 rc 1，`dispose-75497-20261019T054148Z-summary.json` 记录了身份核对通过、SIGTERM 已发送，但 5 秒后仍未退出；该 INCOMPLETE 结果不覆盖、不改成 PASS。主控另行核对测试身份后发送 SIGKILL，回报 75497 已不存在。另有两个父进程均为 1 的孤儿 helper：81261 是 gpu-process，收到 SIGTERM 后退出；83529 是 utility，主控回报已清理，具体清理信号未提供，不补推。主控回报目前外置盘没有残留 Electron 进程。这些事实见 `controller-cleanup-12.json`，来源是主控人工处置回传，不冒称 worker 当时独立监控或发信号。

对照脚本首轮 `startup-compare-20261019T054155Z` rc 1，versions 和 cases 均为空。错误为 `AttributeError: module 'os' has no attribute 'listxattr'`；worker 本地确认 `/usr/bin/python3` 为 3.9.6 且确实无此函数。它是本票诊断脚本缺陷，不是 Electron 对照失败。已将这一调用完全替换为系统 `/usr/bin/xattr -l <Electron.app>`，记录 argv、退出码、stdout 和 stderr，不增加 Python API 兼容分支。

本地实际执行：

```sh
/usr/bin/python3 -B evidence/2026-10-19-batch17/T-103/compare_startup.py --preflight --output /private/tmp/t103-startup-preflight-12
```

退出 0，见 `t103-startup-preflight-12-summary.json`：同一个脚本读完两份真实安装的包版本、dist/version、path.txt、执行位与 xattr；两份均为 43.4.1，两次 xattr -l 均退出 0，仅列出 com.apple.provenance。预检不启动 Electron，runtime_probe 和 startup_cases 明确标为 NOT_RUN，不能当四组启动绿态。真实 06 也固定用 `/usr/bin/python3 -B`，与本地验证的解释器一致；截止期限仍为 30 秒。

对“app.exit(1) 之后被驱动拖住”或“Electron 43 在 ready 前改了行为”的判断：

1. 当前更直接的证据支持**驱动未完成退出前的回执**。startup-failed 不是 app.exit 调用记录；该函数随后 await reply，实际发生 EPIPE，会跳过后面的 app.exit(1)。因此目前没有“app.exit 已经调用，随后被驱动留住”的证据。
2. SIGTERM 不退出证明普通信号收尾未完成；它不是 app.exit 的调用证明。孤儿 helper 同样只说明父子进程收尾不完整，不能据此认定 JavaScript 退出调用已经执行，更不能把主控后来的清理补称为当时正常退出。
3. 原生实现确有可核对的版本差异：[43.0.0](https://github.com/electron/electron/blob/v43.0.0/shell/browser/browser.cc#L117) 的消息循环未就绪分支直接 exit(code)；[43.4.1](https://github.com/electron/electron/blob/v43.4.1/shell/browser/browser.cc#L123) 在 exit(code) 前增加 NodeBindings::TearDownOncePerProcess。早期退出路径仍存在，未见“必须等 ready 才允许 app.exit”的新增条件；清理步骤有差异也不等于已证明本机卡在该步骤。两份待测二进制都标为 43.4.1，真实裸入口对照尚未开始，仍不能宣布是 Electron 43 的行为变化导致本次失败。

接下来只重跑对照，当前没有要再次处置的旧 Electron PID：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-06-COMPARE-STARTUP.sh
```

脚本保留当前驱动和原产品构建；某组若再次超时且 SIGTERM 无效，会保存身份与现场并停止后续组，不自动 SIGKILL，也不把未跑组算通过。先取得裸入口和驱动的实际结果，再决定最小修复，不通过延长期限或换版本掩盖现象。

### 主控 #13：外置盘执行限制与共用内置盘运行时

06 的 `startup-compare-20261019T055050Z-summary.json` 保留 INCOMPLETE：主仓库内置盘 Electron 的 `-p process.versions.electron` 退出 0、输出 43.4.1；外置盘基线副本的相同命令在 30 秒超时，stdout／stderr 均未返回。两份 package.json 与 dist/version 都是 43.4.1，xattr 都只有 com.apple.provenance。这次还未加载产品或驱动就已挂起，故该现象不依赖产品或驱动。主控另外核对外置盘为 USB、APFS、Owners Disabled，裁定为本机环境的外置盘 Electron 执行限制；不据此外推 APFS、USB 或 Owners 设置哪一项单独致因。

按照主控裁定，06 到此停止，不再补跑四组，也不继续把 app.exit 或握手假设当作当前故障的根因。原有等待链单测只证明其局部逻辑，不能代替这一更直接的运行时事实，更不能给尚未验证的选择页背书。README 的安装说明已写明该环境限制。

本次 02 的唯一 Electron 运行时固定为：

```text
/Users/luckye/Documents/Code/a2a-wt-t103/workbench/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron
```

红态和绿态都用这个文件，且仍测试各自原有的产品构建。基线源码及 npm 依赖继续在新的外置盘目录；新基线不再下载或创建外置盘 Electron dist。只为其 Electron npm 包写入 macOS 平台的 path.txt 元数据，使用包已有的 `ELECTRON_OVERRIDE_DIST_PATH` 显式指定内置盘 dist，使真实 start.mjs 的 require('electron') 也返回同一路径，不改产品启动代码、不写全局配置或放链接到构建输出。

版本核对包含基线项目的精确依赖、锁文件、已安装 Electron npm 包，候选已安装包，以及选定 dist/version；均须等于 43.4.1。04 只对内置盘准备目录运行，并再次读回实际二进制版本。02 的 baseline-install.json 与 run 摘要记录共享执行路径、双方包版本、实际版本探针结果。每个 Electron 的 ready 或 startup_error 握手还须回报 `process.execPath` 与 `process.versions.electron`，Python 核对实际路径与版本后才接受场景，避免只记录请求配置而没有进程证据。

本地 `shared-electron-selection-13.json` 为 PASS：用真实 Electron npm 包的路径选择 API，分别从候选模块、旧基线模块，以及一个只有平台元数据而没有 dist 的新测试副本读取，三者都解析到上述内置盘同一文件；包版本／dist 也核对为 43.4.1。该检查不执行 Electron，不宣称真实界面通过。现有 worktree 的 node_modules 保留主控此前安装的位置和体积 481,824 KiB，本次不搬动；新基线的源码和 npm 依赖、构建缓存、下载缓存仍在外置盘，未把旧 worktree 目录误报为全部外移。

新重跑命令仍是：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-02-E2E.sh
```

该脚本使用新的时间戳保留旧失败。04 已拒绝对外置盘 Electron 包执行安装／版本探针；T-104 复用时也应选内置盘运行目录，外置盘 npm 依赖通过同版本 dist 显式绑定。握手和界面期限均未放宽。

**给 T-102 的打包交接提醒：**最终 `.app` 安装在内置盘 `/Applications` 后执行，不受此处外置盘执行问题影响。构建槽与缓存可留在外置盘；验证时从安装位置启动，不直接运行外置盘上的 `.app`。这条环境裁定不等于 T-102 已打包或验收通过；本 worker 通过本报告和给执行主控的交付回复传达，未操作另一个 worker 的会话或文件。

### 主控 #14：第二次选择的按键注入缺失

`run-20261019T060557Z-summary.json` 保持 INCOMPLETE。真实运行的前五项 PASS，红态和绿态实际握手均核对为同一个内置盘可执行文件、版本 43.4.1。完整日志为主控回传的 `t103-e2e-06.log`，原始记录与两张截图留在外置盘同名 run；没有重写旧摘要或旧驱动快照。worker 已目视检查红态无列表、候选两项目四任务的两张截图，尚未取得切换后的截图。

**等待的是第二次选择。** ticket 要求“切换任务后窗格内容跟着变”；预期任务与终端字符串来自运行前生成的夹具，不来自产品输出：

| 请求／观察 | 独立预期与实际结果 |
| --- | --- |
| id 3，06:07:56.187Z，点击 task-0-0-c0095b | id 7 已显示该 task、其 launch，且终端包含 `只读历史输出 task-0-0-c0095b / 11b1c76d`，第一次选择满足条件 |
| id 8，06:07:58.420Z，键盘选择 task-1-0-c0095b | 应有且仅有一个该 task 的窗格，终端包含 `只读历史输出 task-1-0-c0095b / 6b6dc879`；实际仍为 task-0-0 及旧输出，未满足条件 |

`input=false` 符合只读历史窗格夹具，不是这条等待谓词要求变为可输入。四条任务、busy=false、无 alert 也不能代替目标任务与对应输出。原超时没有输出期望值，现已把目标 task、终端字符串和窗格数加到报错中，原谓词保持不变；显式 task 启动也同时核对 task 与原独立输出。

保存的已知坏驱动只发 `keyDown Enter` 和 `keyUp Enter`，遗漏字符事件，且 `{sent:true}` 没有证明目标得到键盘输入。[Blink 原生按钮激活处理](https://chromium.googlesource.com/chromium/src/+/b937d39273b52034e8542dea4b040587be0a127f/third_party/blink/renderer/core/html/html_element.cc)在 keypress 的字符码为回车时触发点击；[Electron 43.4.1 的转换实现](https://github.com/electron/electron/blob/v43.4.1/shell/common/gin_converters/blink_converter.cc#L265)从 keyCode 构造字符文本。因此补发的 char 使用实际 `\r`（13），不能写成字符串 Enter。[Electron sendInputEvent 文档](https://www.electronjs.org/docs/latest/api/web-contents#contentssendinputeventinputevent)还要求所属窗口有焦点。由日志和源码判断，这次刺激不完整，尚不能据此认定产品切换失败。

修复只在新驱动中：先聚焦真实窗口和目标按钮，核对窗口、webContents、文档及 activeElement，再发 Enter down、CR char、Enter up；记录焦点与目标。没有改 React 按键处理，没有用 click 或 selectTask 兜底，没有放宽 20 秒界面期限或 30 秒握手期限。本次 app、src 与 README 均逐字节保持该轮快照不变，见 `readonly-diagnosis-14.json`。

新增 `test_t103_keyboard_entry.mjs`，先列明缺少字符／字符不对、焦点不对、目标不对的失败方式，再执行真实驱动的键盘分支。`keyboard-entry-14.json` 为 PASS：拒绝该轮冻结的坏驱动，候选发出完整三事件，错误焦点或目标在输入前拒绝。这是输入注入的局部检查，**不是实际浏览器切换通过**；RUN-OUTSIDE-02 会先运行它，再按原预期走完整真实旅程。

`followup-14-checks.json` 记录本地语法、驱动入口反事实、受保护文件未改和编码检查通过；`map-sparse-08.json` 仍为 8 个稀疏缺失项、0 stale，未把地图验收标为通过。

另保留一项清理缺口：主控回报没有残留 Electron，但旧摘要的 cleanup_error 显示基线后台 PID 77499 在 daemon.pid 删除后仍可见，旧脚本只立即查了一次进程。不能把“无 Electron”扩成“所有后台清理已证明”。现在在原有 10 秒停止期限内同时等 pid 文件消失、实际进程不存在；不补发信号，不改 daemon_stop 或门禁语义。旧运行仍保留退出未确认的错误，后续是否已退出不由这份记录推断。

worker 的只读 ps 查询被沙箱拒绝，见 `sandbox-process-probe-14.json`，没有申请升级或发信号。另备 `RUN-OUTSIDE-08-INSPECT-77499.sh` 供主控核对；它只记录该 PID 的当前状态，不执行处置。PID 仍存在时保留完整身份并报 INCOMPLETE，交主控核对，不把复用 PID 当成原后台。该脚本未在沙箱外运行。

重跑命令：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-02-E2E.sh
```

脚本仍用新时间戳，不覆盖 `run-20261019T060557Z`。本轮本地检查和真实重跑结果分开记录，整票不提前报 PASS。

### 主控 #15：显式启动的初始快照尚未返回

`run-20261019T062714Z-summary.json` 保持 INCOMPLETE，日志为主控回传的 `t103-e2e-07.log`。前七项真实检查均 PASS，新增证明跨项目往返、原生键盘选择、终端内容对应任务、旧 key／不存在任务拒绝，以及隔离库移除后的刷新。五张截图留在外置盘同名 run；worker 本轮目视检查 green-switched、green-narrow、green-removed，列表、标题、门禁状态及移除后无窗格与记录一致。900×650 窗口中左侧列表可纵向滚动，终端沿用原有横向滚动。

第八项是 ticket 第 3 条要求保留的显式 `--task` 启动。独立预期仍是 task-1-0-6498e9 的一个窗格、对应 launch，以及终端字符串 `只读历史输出 task-1-0-6498e9 / 90a82aa5`，并非任意一个 section 存在就通过。实际记录：

- 06:28:57.232Z，产品 run 完成，驱动报告窗口已加载；该信号没有宣称异步后台快照已经返回。
- 06:28:57.304Z，第一次 inspect：标题“正在读取项目”、busy=true、无 alert；窗格有 key、input=false、offset=0，终端尚空，没有 task 或 launch 字段。
- 06:28:57.349Z，测试已发 close。KeyError 在第一次谓词求值就抛出，未走完原有 20 秒观察期限；没有证据证明这个显式启动随后成功，也不能据此认定它无法加载。

原因在测试读取方式。`renderer.tsx:54` 的 SessionPane 初始 snapshot 为 null，127～139 行异步读取后才 setSnapshot；180 行的 data-task-id 来自 snapshot.task。已有窗格 section 可以先于任务快照挂载，驱动读取 undefined 后，JSON 不包含 task。测试把这个加载过程当成了字段始终存在的完成态，直接下标访问而崩溃。它不是另一个任务的已完成窗格，也不是空库提示。

最小修复只改新 E2E 脚本的两个同类等待位置：用 `.get('task')` 与独立目标 task 比较；字段未到时结果为 false，继续原有轮询。缺失身份、错误任务、错误输出或多个窗格都不会通过。显式启动取得最终值后还核对原夹具的标题与 launch。没有修改产品、驱动、现有测试断言或截止期限；`readonly-diagnosis-15.json` 逐字节确认该轮快照里只有 `workbench/tests/run_t103_picker.py` 改动。

局部反事实由真实保存的观察重放取得：

```sh
/usr/bin/python3 -B evidence/2026-10-19-batch17/T-103/replay-loading-15.py --output /private/tmp/t103-loading-15-replay.json
```

`predicate-loading-15.json` 为 PASS；补充可指定输出路径的参数后，`predicate-loading-15b.json` 也为 PASS：从冻结的坏脚本及当前脚本提取实际 lambda，在该条加载观察上，坏谓词复现 KeyError，修订谓词为 false；实际已完成且与夹具相符的观察为 true。错误 task、错误 trace、缺 task 但有预期 trace、无窗格和多个窗格都为 false。只证明轮询正确处理这批观察，不替实际显式启动或空库绿态背书。输出用独占创建保存，保留已有结果；重复重放需为 --output 另选新文件名。

主控 #15 回报 08 的 ps 已查不到旧 PID 77499，按主控回报记录退出已确认，不冒称 worker 独立观察。新一轮摘要没有 cleanup_error，已按原流程停止后台并把 252 个夹具文件、5,837,979 字节核对归档；旧轮的清理错误保留。

重跑仍执行：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-02-E2E.sh
```

使用新时间戳保留本轮失败，下一轮仍完整重跑红态、绿态及反例，不跳过已通过项。当前未提交，等真实显式启动、空库结果及必要裁定后再完成交付。

## 复现与交付

执行主控运行：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-02-E2E.sh
```

脚本从固定起点在外置盘恢复已知坏版本，按项目现有 npm ci 方式安装其依赖，分别构建基线和候选；每次新建构建槽，不放源码或依赖链接。真实后台以 detached 方式启动，Electron 测试进程脱离调用者进程组。候选经真实 start.mjs 启动 Electron，观察启动器只调用实际产品的 run，不替换 IPC、数据或输出。

按执行主控 #8 对新基线副本处理 helper 执行位后，再进入构建和真实验证；该测试环境处理的前后 mode 会进入结果，不作为产品修复。

夹具通过真实门禁 card_save/create 创建两项目四任务，含一次 revoke 操作（返回 ready）与长中文／标签字符标题。历史窗格记录及终端字节是明确的测试输入，不启动 CLI 或模型；随后逐项读回 SQLite、界面与 xterm 的可访问文本。往返切换、键盘切换、旧 key 输入／读取拒绝、不存在任务、显式 task、空库均在同一旅程检查。测试长度主要来自真实进程、独立输入、截图、失败保留与归档，不是以源码结果生成答案。

原始命令、构建产物位置、日志、截图、源码快照与夹具归档都在 `/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/`；仓库只接收 `run-*-summary.json` 与 `*.archive.json`。归档后按逐文件字节数和文件数核对，再清理原隔离夹具；异常不覆盖。运行中或提交前源码与快照不符则拒绝候选。

真实旅程已通过；新增合同由 09 脚本核对后，会按主控 #16 授权自动调用 03 提交（两个参数均须 PASS）。单独复现提交时，命令格式为：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-03-COMMIT.sh evidence/2026-10-19-batch17/T-103/run-20261019T063741Z-summary.json evidence/2026-10-19-batch17/T-103/contracts-实际时间-summary.json
```

该脚本要求原分支／起点和通过的源码快照，只接受本票范围内且与工作区字节一致的已有暂存内容，不清空暂存区；用 git add --sparse 暂存列明文件。尾注由原逐会话 hook 自动生成，不手写尾注，不 push。当前提交号未生成；不伪造 fence、spec_rev 或 submit 回执。

## 已报告的限制

1. 当前门禁没有删除任务命令，revoke 会保留任务。刷新移除反例仅在隔离夹具库删除一行，保存删除前记录、保留旧 membership，验证选择页以当前任务表为准；不能把它写成“经现有门禁删除命令验证”。是否满足 ticket 原条目由主控裁定。
2. 两处旧测试合同原与新窗口级 IPC 冲突，已按主控 #16 授权扩充并保留历史合同。09 已证明基线、候选、原反例、新变异和两份真实窗口合同 PASS；尚未完成提交与独立审查，不把合同通过当作整票已集成。
3. 这轮终端输入是只读历史输出，不能证明真实可写 agent 或普通 zsh 的输入生命周期；普通 zsh 归 T-104，模型调用不在授权范围。
4. 稀疏 checkout 的缺失文档未补造，也未改地图、术语表或他人 ticket。独立验收按主控安排另开只读会话，本实现 session 不自认独立审查。

本轮不做可靠性、性能或成本改善主张；`INCOMPLETE` 不得上调为 `PASS`。

## 旧 IPC 测试的原冲突与处理依据（主控 #16 已授权）

以下是改动前的定位，行号指 `cc18d93db` 的原测试。主控 #16 逐项接受此方案，授权扩充两处测试；后续执行结果见下一节：

- 第 25 行 `const expectedHandlers = withRecovery ? 7 : 6;`；第 279 行对候选调用 `exercise(candidate, true)`，所以预期为 7。第 134 行的两条断言分别是 `assert.equal(registrations.length, expectedHandlers)` 和 `assert.equal(new Set(registrations).size, expectedHandlers)`。候选保留原 7 个 pane handler，新增 `a2a:projects`、`a2a:tasks`、`a2a:selection`、`a2a:select-task` 四个窗口级 handler，共 11 个；数量断言会冲突，重复注册防护仍应保留。
- 第 136～140 行对所有 registration 执行 `assert.rejects(() => invoke(a, channel, bKey, 'must-not-arrive'))`，随后断言请求数不变。该要求适用于需要 pane key 的原 7 个接口；同一窗口的项目列表、选择状态等接口不以 pane key 为参数，不能要求它们因传入 bKey 就拒绝。第 138 行的 iframe sender 拒绝要求仍适用于全部 handler。

原处理建议：保留历史基线／变异原有的 6／7 接口合同，仅给候选增加显式的 11 个 handler 名称集合；同时核对集合完整和注册无重复。异窗 pane key 的拒绝与“未到达 transport”检查只遍历原 7 个 pane 接口；iframe／未知窗口拒绝仍覆盖全部 11 个接口。四个窗口级接口使用各自的正确参数与只读／切换预期另测，必要时只扩充 transport 夹具的列表响应。有效列表调用放在拒绝请求计数区间之外，不删弱原有拒绝检查。不能只把 7 改成 11 就视为处理完成。主控 #16 裁定这是新合同扩充，不算放宽验收。

## 主控 #16：完整旅程通过与两处合同扩充

第八次 02 的 `run-20261019T063741Z-summary.json` 为 PASS，九项检查全部完成。日志为主控回传的 `t103-e2e-08.log`；真实入口红态、两项目四任务、只读字节比较、往返／键盘切换、旧 key／不存在任务拒绝、移除刷新、显式启动和空库均有结果。七张原始截图留在外置盘同名 run。worker 补看了显式启动与空库截图，任务身份、输出、空状态与记录一致。夹具 296 个文件、7,843,144 字节已核对归档，摘要无 cleanup_error；主控另回报没有残留 Electron。此次不重新运行产品旅程，因为扩充只改测试，原旅程的全部 source_files 已逐字节核对不变。

测试授权变化仅限主控点名的 `test_t091_pane_ipc.mjs` 和 `test_electron_e2e.py`；没有改 acceptance/、panes.ts、门禁或其他既有测试断言。改动前先保存 `ipc-old-contract-red-16.json`：旧测试仍拒绝旧坏实现，但候选的 close 变异被 11≠7 的接口数断言提前截住，尚未到原来的关闭布局断言。这是旧合同与新合同冲突，不是关闭行为回归。

扩充后的合同由命令参数显式选择，不从实际注册列表推导答案：

- legacy 保留历史 6／7 个 pane handler、8 个 preload 键；picker 核对明确写出的 11 个 handler、12 个 preload 键及注册无重复。
- 异窗 key 仅遍历原 pane 接口，使用各接口有效的其他参数，并逐项断言没有到达 transport。iframe 和未知窗口使用有效调用参数覆盖完整接口集合，也核对 transport 没有收到拒绝请求。
- 四个窗口接口分别通过实际 preload 调用：projects 不带 key，tasks 传项目并检查空／无效项目，selection 无参数且不访问 transport，selectTask 接受 null 与任务 ID；拒绝无效目标并保留原选择，不发输入凭据。
- 原有缺 key、独立凭据／序列／输出、拒绝跨任务及历史第三窗格、关闭等待、布局恢复、最终空布局、空 preload 等检查保留。候选空布局重开只允许两轮确切的 task snapshot → pane_layout 只读序列，不允许 launch 选择或凭据请求；历史分支仍要求原 pane_layout-only 序列。
- 真实窗口的 window_contract 仅扩充显式名称集合与无重复检查，保留只读输入、无 user_inputs 写入和门禁状态不变等原断言。`--runtime-source` 只选择内置盘同版本 Electron 与观察驱动，实际被测构建仍由 `--source` 指定的基线／候选生成。

沙箱内 `ipc-legacy-16.json` 与 `ipc-picker-16b.json` 均 PASS，原四类反例仍命中原断言；候选的新变异把 projects handler 改为要求 pane key，被“Projects must work without a pane key”断言拒绝，实际错误 Unknown pane key。它是真实 main 源码的内存变异，不改产品文件。VM 替代了 Electron／transport 外部边界，不能当真实窗口证据。

沙箱外执行：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-09-CONTRACTS.sh
```

09 复用第八轮保存且核对过的外置盘基线，不 npm install、不增加内置盘依赖；基线和候选分别执行这两个测试，两个真实窗口共用内置盘 43.4.1。新日志、截图、夹具归档与测试源码快照放外置盘新时间戳目录，仓库保留摘要与 archive 清单。全部通过才追加结果到本报告、打印具体命令并按本次授权自动调用 03；失败保留现场，不提交。03 同时要求完整旅程与合同摘要 PASS、二者绑定一致、所有测试及脚本字节与通过快照一致，随后才暂存含这两个测试的文件并由原 hook 加尾注，不 push。

`followup-16-static.json` 仅记本地语法和原旅程源码不变。09、提交与独立验收在本节编写时仍未运行，不能上调为整票 PASS。行为验收独立审查依主控安排的新只读会话进行；本 worker 不以实现会话充当独立审查，也未调用模型。

### 09 合同验证回传：20261019T065323Z

状态：PASS（本次合同验证范围）。基线按 legacy 合同、候选按 picker 合同，两份 IPC 检查与两份真实 Electron 窗口检查均通过；旧有四类坏实现及新的窗口级 pane-key 变异被拒。两份窗口使用同一内置盘 Electron 43.4.1，均已确认窗口退出和后台停止。

摘要：`contracts-20261019T065323Z-summary.json`；原始日志、截图、夹具归档及测试源码快照：`/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/contracts-20261019T065323Z`。本次没有改动或重新借用其他产品候选；完整项目选择旅程仍绑定 `run-20261019T063741Z-summary.json`。提交与独立审查按主控后续结果确认，不把合同验证通过当作已集成。

### 主控 #17：预期的反例错误与只重试提交

日志 `t103-09.log` 的第 78～92 行 AssertionError 属于 baseline-ipc 结果里的 known_bad_result、single_pane_counterexample 和 close_mutant 等反例字段。测试有意执行坏版本，捕获其失败后，还要求它命中指定的原断言并写出 rejected=true；未失败或失败原因不符都会使总体失败。candidate-ipc 还要求新的 window_key_mutant 命中“Projects must work without a pane key”。它们不是候选产品未捕获的异常，也不是被忽略的失败：

| 坏实现／变异 | 必须被拒的行为 | 09 结果 |
| --- | --- | --- |
| 6974c2a 无 key 旧接口 | 接受未注册 pane key | rejected=true |
| 7e1c68a 单 pane tracer | 显式三会话只生成一个 pane key | rejected=true |
| close 变异 | 关闭时写成重新打开，未移除布局 | rejected=true |
| 11b3230 旧候选 | 最后窗格关闭后重开又选回 worker | rejected=true |
| 新窗口级 key 变异，仅 picker 合同 | projects() 被错误要求提供 pane key | rejected=true，底层 Unknown pane key |

四个正常目标的 baseline-ipc、baseline-window、candidate-ipc、candidate-window 均为 status=PASS、exit=0。仍以原始摘要与日志为证，不重写反例错误为“没有错误”。

随后 03 的 git add 未带 --sparse，Git 拒绝将 cone 外 evidence 加入索引。该命令已部分暂存 15 个 workbench 文件，并未创建提交；`commit-repair-17-before.json` 保存了 HEAD、暂存路径及原脚本与测试快照一致的核对。此失败属于提交脚本，不算测试失败。

按主控 #17 只修交付步骤：git add --sparse；保留已有暂存内容，只接受本票路径且逐字节等于工作区的项；提交正文引用完整旅程及本次 09 的摘要。03 自身不是产品或测试输入，本次授权修订不与旧提交脚本作自比较；原副本继续留在 09 的快照中，产品、测试及其余脚本仍必须逐字节相同。没有修改或重跑测试，没有清空暂存区。

只做提交的命令：

```sh
bash evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-03-COMMIT.sh evidence/2026-10-19-batch17/T-103/run-20261019T063741Z-summary.json evidence/2026-10-19-batch17/T-103/contracts-20261019T065323Z-summary.json
```

worker 仅做 shell／内嵌 Python 语法检查与只读提交前置核对，不在沙箱内执行 git add 或 git commit。提交是否成功及自动尾注以主控回传的实际结果为准；独立审查和集成仍由主控安排。
