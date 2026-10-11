# T-075-4 运行记录

状态：**PASS（本卡交付；ticket 待主控关闭）**。一次独立审查原始 FAIL，唯一 P2 已先红后绿修复，[主控 #45 已审并批准修复 diff](controller-approval-45.md)，未追审。live-04 原收据仍为 INCOMPLETE；停止补采修复按主控 #44 用离线方式证明，其余生命周期证据正常引用。本结论采用该获批证据组合，不将历史失败改成 PASS。累计真实回合 **3/4**，没有追加。

- 任务：T-075，`ready_rev: 4`，worker `s12-t075-4`。
- 计划起点：`e55da7db17c25d9712909666119104fc96969a93`。
- 实施开始读回：`67306684dce5387adc6b44b074fb948913dbb841`；workbench、规范和地图相对计划起点无变更。
- 批准来源：[决定 01](controller-decision-01.md)。只读显示、字节游标分段读取、PLAN 第 6 节重启语义与固定 160×45 网格均获批准。spec 第 6 节交互输入链本卡未实现，归 S4。
- fork 片段从已推送的 `49cae984f22924de006e0f8358cb447eb881aaf6` 读取；实际迁入路径见下表。
- 本卡真实模型回合已用 **3/4**；live-01、live-03、live-04 各用 1 个，live-02 没有进入真实回合。Electron 与真实 Codex 运行均由执行主控执行。
- 原有两份 controller-poll.log 与主控追加的 dispatch.jsonl 修改保留，不属于本卡。

## 起点合同红态：PASS

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh red-02 red
```

包装器冻结起点的 workbench 到 `/tmp` 新目录，复用已装依赖，不 checkout、不 reset、不覆盖已有输出。新测试也复制进本次证据目录，记录完整 argv。测试通过真实 CLI 创建隔离 task/attempt，先对照 SQLite 确认夹具成立，然后分别调用界面构建入口、`workbench_snapshot` 和 `pane_output`。起点必须因三处功能缺失失败；夹具、权限、依赖或清理失败不能算合同红态。

执行主控 #36 已运行并报告 PASS，本 worker 读回 [包装器收据](outside-red-01/verdict.json) 和 [原始预检判据](outside-red-01/preflight/verdict.json)：三个缺失接口的合同断言均失败，夹具建立与后台退出均通过。完整准备命令、源码归档、冻结测试、stdout/stderr/退出码、逐项判据和夹具归档都在 `outside-red-01/`，未覆盖。原运行使用当时只支持 red 的包装器；上面为当前支持显式阶段参数后的等价重现命令。

脚本本身退出 0 只表示“三项预期红态已确认”；被测端到端预检退出 1。此阶段没有 Electron 截图、真实 PTY 生命周期、重启恢复或构建成功结论。取得有效红态后，才实施产品并扩展同一端到端入口。

## 静态检查

本轮仅做 Python AST、zsh 语法、文本编码和 diff 检查，均通过。源码路径计算已独立核对。静态检查时修正两处尚未运行的夹具问题：project_id 必须使用门禁允许的 ASCII 标识；基线归档含已核对的 `workbench/hooks/* → hook.py` 相对链接，提取器只放行这些链接，其他链接仍拒绝。它们不是产品失败或合同红态。

session 开始地图检查退出 0：0 problems、0 stale；沙箱外交接前再次检查并保存至 `preflight-static-checks.json`。ticket 保持 open，待主控关闭。

## 当前实现与 checks 检查

新增 `workbench/app/`：Electron main/preload、React/xterm 只读界面、构建与启动入口。main 只连 Unix socket；没有 PTY、库或任意命令入口。渲染层只有 snapshot/output 两个桥接能力，没有输入写回。后台新增 workbench_snapshot/pane_output，并让 pane_status/launch_show 能查询重启后的旧窗格；重启追加 pane_recovered，保留原门禁状态，不恢复 PTY 或队列。

输出按落盘 trace 的字节游标分段读取，xterm 完成解析后推进；错误停止读取，显式重连保持原 launch。构建在导入 Vite 前检查外置盘，新建唯一构建槽，拒绝覆盖旧槽；没有改变 node_modules 位置或在输出里建立链接。

实际搬运片段来源统一为 `49cae984f22924de006e0f8358cb447eb881aaf6`：

| 本卡文件 | 来源 | 改动 |
| --- | --- | --- |
| `workbench/app/TerminalScrollToBottom.tsx` | `apps/web/src/components/TerminalScrollToBottom.tsx` | 保留按滚动位置显示按钮的逻辑，改用普通 button 与本地 CSS，不引入其他组件库 |
| `workbench/app/style.css` | `apps/web/src/index.css` | 提取终端表面、导航细分界、系统字体栈与圆角比例 |
| `workbench/app/style.css`、`renderer.tsx` | `apps/web/src/theme/theme.seed.generated.ts` | 使用 Codex dark 的 #111111、#fcfcfc、#0169cc |

各片段保留 MIT 说明，构建产物也携带 LICENSE.synara。

checks-01 使用的命令（该标签已存在，不要重复使用）：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh checks-01 checks
```

该阶段先归档当前候选（包括未提交文件），从 `/tmp` 冻结副本运行，并复用已装依赖。检查包括：

- 相同三项预检转绿，Electron 加载实际产品并用 capturePage 截图，验证项目／任务／门禁与只读能力；此截图没有真实窗格，不能交付为最终 PTY 截图。
- 缺失挂载路径、内置盘普通目录两个构建反例，缓存目录前后清单。
- 既有 pane 状态、trace 失败、relay、后台门禁回归。
- 新增后台恢复测试：验收锁与中断、新 oracle／verification、CAS 前后恢复、外部 X 和删引用拒收。故障只终止测试创建的后台，保留完整日志和数据库读回；原 acceptance/ 断言未改。

待窗口阶段结果可核对后，再交接 1 个主 turn 的真实 PTY 关闭重开／输出比对／后台重启验证；全卡上限仍为 4。独立审查、产品已知坏实现反例、最终截图、ticket Resolution 与提交均未完成，不能宣布整卡 PASS。

静态发现的一项测试夹具适配：产品现在提前建立空 trace，原 trace 失败测试需要先将这份空文件保留为 `.before-fault`，再创建同名目录触发原来的 EISDIR。业务断言不变；checks-01/02 已通过该测试。

实现后的静态检查见 [implementation-static-checks-01.json](implementation-static-checks-01.json)：16 项检查通过，包含 Node 语法、Python AST、zsh、diff 和地图检查（0 problems、0 stale）。该检查时 JSX/Vite 构建、Electron 运行和新恢复测试尚未执行；后续运行结果见下节。

## checks-01 / checks-02：两轮均 INCOMPLETE

执行主控 #37 报告两轮结果，本 worker 已核对原始收据：

| 运行 | 结果与原始证据 |
| --- | --- |
| checks-01 | [总收据](outside-checks-01/verdict.json)；[窗口判据](outside-checks-01/window/verdict.json)；[Electron stderr](outside-checks-01/window/window-stderr.txt)；[启动 argv 与超时](outside-checks-01/window/window-driver.jsonl) |
| checks-02 | [总收据](outside-checks-02/verdict.json)；[窗口判据](outside-checks-02/window/verdict.json)；[Electron stderr](outside-checks-02/window/window-stderr.txt)；[启动 argv 与超时](outside-checks-02/window/window-driver.jsonl) |

两轮 window 中的三项预检都 PASS：实际外置盘构建成功，workbench_snapshot 返回真实任务，pane_output 明确拒绝未知 launch。随后 Electron 均报 `sandbox_extension_issue_file_to_process failed`、`Operation not permitted`，路径是 `/private/tmp/<源码副本>/workbench/node_modules/electron/dist/Electron.app`；驱动等待 ready 超时，没有取得窗口截图。旧收据的 `electron_started: false` 是构造器成功返回后才置位的标志；启动 argv 和 PID 已记录，不能把它解释成没有尝试启动进程。

其余八个检查组在两轮都符合预期：两个缺盘反例退出 1，缓存读回 PASS；pane 状态、trace 失败、relay core、relay CLI、后台门禁和后台恢复六组退出 0。其中后台门禁各 **15/15**、后台恢复各 **5/5**，均 0 failures、0 errors。它们证明对应候选的后台行为，不替窗口和真实 PTY 生命周期背书。

**运行条件说明（来源：主控 #37）：** checks-02 曾请求关闭执行主控自身的沙箱，但该请求没有被批准，因此 checks-02 与 checks-01 的运行条件相同；不能写成已在无沙箱环境重跑。执行主控在同一机器、同一 shell，从已安装 Electron 的真实路径启动最小程序，得到 ready 并退出，据此定位为源码副本 node_modules 符号链接导致的夹具启动问题。本 worker 没有重跑或扩大这项外部观察。主控已确认两轮没有残留进程。

## 夹具路径修复与 checks-03：INCOMPLETE

唯一的启动行为修复在 `workbench/tests/electron_client.py`：对最终 Electron 可执行路径使用 `Path.resolve(strict=True)`，传给 Popen 的是 `/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron`。依赖链接、产品代码与权限均未调整，不增加绕过沙箱参数或重试。

本地核对见 [fixture-realpath-check-01.json](fixture-realpath-check-01.json)：在 Popen 边界截获真实构造器产生的 argv，checks-02 的旧夹具仍给出链接路径，修复后的夹具给出主控指定的真实路径；两个构造器都没有启动 Electron。AST、zsh、diff 和地图检查通过，地图 0 problems、0 stale。这个核对只证明路径修复已进入实际调用参数，不能证明窗口已可用。

重现路径核对（输出路径必须尚不存在；保留的 checks-02 源码副本须仍在）：

```sh
python3 -B evidence/2026-10-10-batch12/T-075/card-4/check-electron-realpath.py --output /tmp/a2a-t0754-realpath-new.json
```

包装器新增 `window` 阶段，仅复跑受此次修复影响的界面构建、三项预检和实际窗口检查；已通过且产品代码未变的其他八项不重复运行。新命令：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh checks-03 window
```

checks-03 已执行，收据在 `outside-checks-03/`，原两轮源码归档、错误、退出码和夹具保留。仍为 0 个模型回合；成功后还需真实 PTY、输出逐字比对、窗口关闭重开、重启状态显示、反事实与独立审查。

## checks-03 原始结果与 checks-04 诊断交接

本 worker 已读回 [checks-03 收据](outside-checks-03/verdict.json)、[窗口判据](outside-checks-03/window/verdict.json) 和 [驱动日志](outside-checks-03/window/window-driver.jsonl)：三项构建／接口预检 PASS；启动 argv 的 Electron 路径已为真实安装路径；之后只有 `startup_error: TimeoutError('Electron response deadline')`，stderr 文件为空，未取得截图。旧 harness 没有保存原始 stdout，不能由“没解析到回应”推断 stdout 一定没有任何字节。

主控 #38 的补充观察：相同二进制能运行最小 ESM 入口并输出 ready；直接加载该源码副本的驱动且故意给未知参数，能到 parseArgs 并报错。因此入口文件可加载，尚不能在 stdout 通道与 ready 前的阻塞之间定因。主控确认 checks-03 没有残留进程。本 worker 未自行复跑 Electron，也未将这些诊断观察上调为产品通过。

本轮只改变测试夹具：

- `electron_driver.mjs` 向 `window/stages.jsonl` 追加带时间与 PID 的记录：模块加载、参数解析、构建清单读取、产品模块 import、product run、whenReady 调用与兑现、窗口创建、页面开始／完成／失败、首次快照请求及结果、ready 开始写出及写入回调。渲染进程退出、console 和致命错误也保留。顶层启动错误被记录后用 app.exit(1) 结束，避免未捕获参数错误留下错误对话框。
- `electron_client.py` 使用无文本缓冲的 stdout 管道、显式字节缓冲和有截止时间的读取，先处理已经收到的完整行，再等 fd；不再在 select 后调用可能自行预读或无限等待换行的 TextIOWrapper.readline。每个读到的原始字节写入 `window-stdout.txt`，stderr 直接落入 `window-stderr.txt`，两者互不混合。
- 输出目录由 harness 在启动前创建，将阶段文件的绝对路径经本次进程环境传给驱动，所以参数解析失败也能留记录。启动／关闭异常时，harness 核对 Popen 创建的独立进程组后发送 SIGKILL 并 wait，记录 PID、PGID 和退出码；没有重新启动或重投。只作用于自己的组。

**局部故障证据：** [client-io-01/results.json](client-io-01/results.json) 用真实本地管道证明：checks-03 的旧读取器在两个回应合并到同一次写入时，第一行成功、第二行超时；新读取器两行均返回，跨读取的中文 UTF-8 原样保存，不完整行在期限内报超时。另一个自建、忽略 SIGTERM 的 Python 子进程经新清理路径以 -9 退出。这些检查未启动 Electron 或后台，只证明 harness 的管道与自有进程清理边界。**它没有证明该缓冲缺陷就是 checks-03 初次 ready 超时的原因。**

重现上述局部检查（使用新输出目录；旧冻结源码须保留）：

```sh
python3 -B workbench/tests/test_electron_client_io.py --output evidence/2026-10-10-batch12/T-075/card-4/client-io-new --known-bad /private/tmp/a2a4src-kmstiux9/source/workbench/tests/electron_client.py
```

下一条沙箱外命令：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh checks-04 window
```

新证据目录为 `outside-checks-04/`。重点读 `window/window/stages.jsonl`、`window/window-stdout.txt`、`window/window-stderr.txt` 和 `window/window-driver.jsonl`，据最后一个实际完成阶段定位；不能把未出现的阶段补称为已完成。产品代码未因本轮诊断改变，原始失败没有覆盖，真实回合仍为 0/4。

## checks-04：INCOMPLETE；等待 ready 的对照准备

本 worker 已核对 [阶段记录](outside-checks-04/window/window/stages.jsonl) 与 [进程收据](outside-checks-04/window/window-driver.jsonl)：模块加载、参数解析、清单读取及产品 main 导入均完成；最后是 `when_ready_called`，app_ready 为 false。没有 app_ready_event、window_created 或 ready_send。stdout 和 stderr 都为空。harness 已对自有 PID/PGID 77017 发 SIGKILL，并 wait 得到 -9。此次阻塞发生在任何 ready 回应写出之前，不能归因于“回应已写出但 Python 没读到”。

主控 #39 在同一二进制、同一 shell 验证了无 setPath、逐项加入四个 setPath、Python PIPE 加 start_new_session 三种条件，均能在一秒内获得 ready。本 worker 只读了其 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/9a64ed90-d8e7-497a-803e-3ecdbc8fd69e/scratchpad/etest/` 中脚本：它们均用 `app.whenReady().then(...)`，没有在模块顶层 await 这条 ready 链。未修改或重跑主控的 scratchpad。

**二分前的因果假设（后由 checks-05 确认）：** 旧驱动在顶层 `await main()`，main 又 `await run()`，run 中等待 app.whenReady，导致入口求值等待 ready。产品正常主入口本来就是 `run(...).catch(...)`，不在顶层等窗口，所以先修夹具而不改产品。Electron 的 [ESM 文档](https://www.electronjs.org/docs/latest/tutorial/esm) 要求 ready 之前的初始化副作用按正确顺序完成，并指出异步 import 的时序；候选保留对 import 的等待，先同步调用 run 完成 setPath，再用 `.then(...)` 接续窗口与驱动协议，避免简单移除最外层 await 后让 setPath 晚于 ready。

新增 `workbench/tests/bisect_electron_ready.py`，三组共用 checks-04 的同一外置盘产品构建、同一真实 Electron、同一环境策略、PIPE 与独立进程组；只变驱动代码。顺序固定：

| 组 | 相对前组的唯一行为变化 | 待验证预期 |
| --- | --- | --- |
| A | 从 checks-04 原驱动去掉 app.whenReady 包装；仍等待 run | 八秒内仍没有真实 window_created |
| B | 保持无包装；将等待 run 改为注册 run 的完成回调，让模块求值先结束 | 出现真实 window_created，且 product_run_started 在 ready 前 |
| C | 在 B 上恢复原 whenReady 包装 | 仍能创建窗口，when_ready_resolved 被记录 |

C 的完整脚本已逐字核对等于当前候选驱动，不是另一份简化程序。每组先保存完整源码、argv 和 PID，原样落盘 stdout/stderr；最多观察八秒，然后只清理自己创建的进程组并确认退出。A 的预期超时是反例，不会上调为窗口可用；完整记录这三组后，任何一组偏离预期矩阵都不继续窗口验收，不自动换方法。

候选只改 `electron_driver.mjs` 的等待链；产品 `workbench/app/main.ts` 和构建产物未修改。真正的首次快照、截图与只读检查，只有上述三组对照成立后才通过既有 window 阶段继续验证。

下一条沙箱外命令：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh checks-05 bisect
```

证据先写 `outside-checks-05/ready-bisect/`，仅矩阵通过才写后续 `window/`。不运行其余已通过的后台套件，不创建被测 Codex，不消耗主回合。原 checks-01～04 失败和进程收据继续保留。

## checks-05：PASS（夹具根因与空窗格界面）

主控 #40 报告 PASS，本 worker 已核对 [总收据](outside-checks-05/verdict.json)、[三组原始对照](outside-checks-05/ready-bisect/results.json)、[窗口判据](outside-checks-05/window/verdict.json) 和 [capturePage 截图](outside-checks-05/window/window/claimed-no-pane.png)。

- A 去掉 whenReady 包装仍阻塞，8.009 秒后由自有进程组清理收尾。
- B 解除模块求值对窗口就绪的等待，约 0.464 秒创建窗口。
- C 恢复 whenReady 包装，约 0.169 秒创建窗口，明确记录 when_ready_resolved。
- B、C 的 product_run_started 均在 ready 前，路径设置时序没有被简单推迟到 ready 之后。随后实际窗口检查通过，正常关闭退出 0。

**根因属于工程／夹具：** 驱动模块求值在等窗口就绪，Electron 则等主模块求值结束后才发 ready，形成相互等待。修复仅解除驱动这条等待链；产品 main 和原构建保持不变。whenReady 包装、setPath、PIPE、新进程会话、外置盘导入及 A2A_ELECTRON_DIAGNOSTICS 环境未被当作根因替换掉。先前发现的文本缓冲问题有独立反例，但不是 checks-03/04 的 ready 阻塞原因。

此前四轮失败未覆盖或改为通过：checks-01/02 经链接路径启动 Electron 被拒；改成真实路径后 checks-03 仍超时；checks-04 首次定位到 when_ready_called。checks-02 的关闭沙箱申请未获批准，两轮运行条件相同。失败详情、源码副本和主控确认的进程收尾均保留在各节原始收据中。

截图能看到真实项目／任务、只读标签、尚未启动窗格、状态未知和门禁已认领；主控 #40 已确认内容与 fork 视觉家族一致，本 worker 也已查看 PNG。这张图证明实际界面查询，**没有真实 PTY 输出，不能用它满足最终截图条件**。

## live-01 原交接办法（决定 02 前）：已执行，INCOMPLETE

新入口 `workbench/tests/run_pane_lifecycle.py` 使用新的 `/tmp/a4live-*` 夹具及全新外置盘构建槽，从同一后台 CLI 建卡、注册、dispatch。被测任务只运行预先给定的 zsh 脚本；脚本每 0.25 秒打印一个带随机前缀的序号、中文和 `done accepted idle`，并追加自己的 heartbeat.progress。禁止产品修改、Git 提交、submit 或交付请求，所以不启动门禁回执回合。

验证顺序：

1. 核对真实 Codex 领导进程，截图初始未知状态；原门禁仍为 claimed。
2. 原子追加本卡预算预留，首次 release 只放出一个主回合；核对脚本进度和实际 PTY 中的新序号。若持续输出没有进入真实 PTY，保存失败并停止，不另造输出通道。
3. 关闭整个 Electron 进程，独立 ps 核对同一 shell／Codex PID，CLI 与直接 trace 读回证明关闭期间继续增长。
4. 用同一 task/launch 重开；保存窗口实际收到的字节与 trace 的固定区间并逐字比对。关闭期间的序号必须出现在 xterm 解析后的可见内容，随后还须出现新的输出。分别截图补回与实时状态。
5. 打印的 `done accepted idle` 不能把 busy 或 claimed 改成空闲／已完成；只读键盘、Enter、粘贴不能写到 PTY 或产生用户输入。补充 UTF-8 三字节拆读与非法游标／长度拒收。
6. 停止自有后台，确认原进程退出；截取后台离线状态，再以空 launch 配置重启。SQLite 和 CLI 必须读回同一 gate/attempt，pane 为 unknown/interrupted；启动、派发及主回合计数不增加，后台没有新 worker 子进程，trace 不增长。
7. 窗口显式重新连接，补回相同 trace，截图原 attempt 的中断状态。归档事件、Git、数据库及 trace，确认自有进程退出后删除整个隔离 CODEX_HOME；auth.json 不入证据。

本轮固定 `gpt-6.1-sol`、xhigh、Fast **请求**，Codex 0.162.1，approval never，B 通道。三个 hook 沿用决定 01／主控 #35 与 #40 的批准，完整展开 argv 会在 `lifecycle/launch-record.json`。每次启动的 turn_limit 为 1；`turn-budget.jsonl` 用文件锁记录预留与实际主回合，累计预留不得超过 4，不自动重试。原生实际模型与主回合另从已归档记录核对，不把请求配置当实际 tier。

沙箱外命令：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh live-01 live
```

该阶段冻结当前源码与任务／角色卡到独立副本，证据在 `outside-live-01/lifecycle/`。运行前的静态检查见 [live-static-01.json](live-static-01.json)：AST、zsh、diff 与地图通过（0 problems、0 stale）。构建缺盘两项与后台回归已有同产品版本 checks-01/02 的通过记录；后续仍须完成本候选的产品反事实和一次 fresh-context 独立审查，ticket 保持 open，待主控关闭。

## live-01 事实与计数修复

主控 #41／[决定 02](controller-decision-02.md) 确认：Codex 工具输出没有实时进入 PTY，但 TUI 持续重绘，trace 达 **378,480 字节**。原夹具在 `no_live_pty_marker: before-close` 停止，没有另造输出通道。脚本自身进度为 630，说明执行工具在运行；这不等于对应语义标记出现在 PTY。原 [失败收据](outside-live-01/lifecycle/verdict.json)、[生命周期记录](outside-live-01/lifecycle/lifecycle.jsonl)、源码归档及原始 trace 保留，不能补称关闭重开已通过。

隔离 home 已删除。计数另出现 `unable to open database file`，属于夹具／证据处理问题。冻结代码在 daemon_stop 响应后重开停机原库；本 worker 再次只读打开同一原库也失败，但归档后的独立 SQLite 副本可读。现在只在 `archive_and_cleanup` 完成且确认归档完整后，从该归档计数，不再读取这个停机边界上的原库，也不设失败后换库的重试分支。

[计数复验](turn-accounting-recheck-01.json) 显示：原读法仍失败，归档记录有且仅有 1 个主回合，原生会话 `01a129d5-ea99-7a03-a8f7-aff0b36b4181`，主 turn `01a129d5-eb7a-7733-b835-f1f26fd7d3cc`。未知 launch 返回未知计数，不写成 0。已在 turn-budget.jsonl 追加事后读回的 observed=1，标明依据；原预留条目、null 计数与错误收据未改写。

重新读取这个归档计数：

```sh
python3 -B workbench/tests/turn_accounting.py --database evidence/2026-10-10-batch12/T-075/card-4/outside-live-01/lifecycle/state.sqlite3 --launch 064a82d5-08f2-4b54-a21a-1bd3470550c2
```

主控明确指出 PID 4279、4332 属于用户正式 Synara，本卡没有操作它们。所有清理仍只依据自己启动的后台、窗格与独立 Electron 进程组，不按应用名称搜杀进程。

## 决定 02 后的 live-02 原交接（结果见下节）

完成条件不变，取证方法更新到全部相关断言：删除对工具输出标记、中文出现和特定序号的依赖，也不将 TUI 重绘称为工具 stdout。被测 worker 只执行一个普通的 90 秒 sleep 任务，单次 turn_limit=1；预算在全卡硬上限 4 之内进一步限制到本决定许可的累计 2，不自动追加第三个回合。

真实路径先在关窗前读取 CLI 的 total_bytes 和直接文件大小；确认 Electron 已退出后再读一次起点，然后在窗口关闭期间等待两个读回都增长，并独立 ps 确认同一 shell／Codex PID。重开前的字节上限作为固定比对终点，窗口从 0 补回的字节必须与 trace 原文完全相同，因此覆盖整个关闭期间新增段；重开后仍须继续增长。截图只要求真实 Codex TUI 内容。后台重启、原 attempt/gate 状态、无自动续跑等要求照原计划执行。

中文、跨块和不读屏由新 `test_offline_trace_e2e.py` 单独证明：复制 live-01 的稳定归档库，不改其中的 task/attempt；只在副本里直接写入带明确 `[offline trace fixture]` 标记的受控 trace。两个中文字分别从字节 65535、131071 开始，让它们跨越窗口实际使用的 64 KiB 分块；NUL 控制字节填充不产生可见文本。随后通过真实 pane_output 和实际 Electron 窗口，分别核对完整字节和完整中文。trace 中加入 `done accepted idle 等确认` 以及改标题 OSC，缺少结构化信号时窗口仍须显示未知，门禁仍为 claimed。此数据明确标为离线输入，不能冒充真实 PTY。

`live` 阶段先运行上述零模型离线检查，失败就不启动下一回合；离线通过后才执行真实生命周期。接收日志只读取已经写完整的 NDJSON 行，同时仍要求已收到的完整字节覆盖比对终点，避免并发追加后续回应时误读半行。

下一条沙箱外命令：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh live-02 live
```

原计划证据分别写 `outside-live-02/offline-trace/` 和 `outside-live-02/lifecycle/`。交接时的静态检查见 [decision02-static-01.json](decision02-static-01.json)。产品代码没有因取证方法改变而修改；原始失败不覆盖。该轮实际在离线阶段停止，结果如下。

## live-02：INCOMPLETE，负游标夹具已修

主控 #42 报告的原始失败保留在 [总收据](outside-live-02/verdict.json) 和 [离线收据](outside-live-02/offline-trace/verdict.json)。本 worker 核对：CLI 读回的 131,152 字节与 expected-trace.bin 完全一致；两处 UTF-8 起点为 65535、131071。窗口补回、中文显示和不读屏断言尚未执行，不能据此前半段通过宣称整项 PASS。

根因在夹具的负游标反例，已由 [commands.jsonl](outside-live-02/offline-trace/commands.jsonl) **第 13 行**直接确认：`--offset -1` 被 Node 参数解析器判为歧义，退出 2、stdout 为空，stderr 明确提示使用 `--offset=-XYZ`。夹具却先解析 JSON、后断言业务拒收退出码 1，因此报了 JSONDecodeError。该命令已有原始记录，日志末尾的 ps、daemon_stop、ps 属于后续清理；错误不在 Electron stdout 或 JSON 文件读取。ElectronClient 尚未构造，没有 window 目录。主控已确认没有残留进程。

修复仅涉及夹具：离线与真实生命周期均改成 `--offset=-1`，先核对退出码，再核对后台返回的 `invalid_output_offset`。没有改变产品接口或放宽反例。加入共用的命令记录器，供离线、真实生命周期、窗口预检及外层准备命令使用：每条命令启动前打开独立的 stdout、stderr 二进制文件；commands.jsonl 记录编号、argv、文件路径与开始／结束，超时、启动失败、解码失败也保留原文和堆栈。CLI／构建 JSON 解析错误带原始输出路径；失败收据另保存清理前的最后一条命令及调用堆栈。Electron 原始 stdout、stderr 和阶段日志继续按原办法保存。

诊断和独立检查的失败方式见 [live-02-diagnosis.md](live-02-diagnosis.md)。[本地检查](command-evidence-01/results.json) **PASS**：同一个 Node 参数解析器拒绝旧写法、接受新写法并保留负值；非零退出、非法 UTF-8、超时部分输出、缺少可执行文件和正常中文 JSON 都有逐命令原始文件。该检查没有启动后台、Electron 或模型，不能代替完整复验。

重新生成本地检查（用新输出目录名，不能覆盖原证据）：

```sh
python3 -B workbench/tests/test_command_evidence.py --output evidence/2026-10-10-batch12/T-075/card-4/command-evidence-02
```

本轮语法、diff、UTF-8 和地图检查见 [live03-static-01.json](live03-static-01.json)。产品代码保持不变，累计真实回合仍为 **1/4**。下一条沙箱外命令：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh live-03 live
```

先跑零模型的离线 trace；通过才启动最多一个真实回合，失败即停止，不重试。证据写入 `outside-live-03/`。本轮若进入真实回合，累计最多 2/4；后续仍须完成产品反事实、fresh-context 独立审查及最终交付。ticket 保持 open，待主控关闭。

## live-03：INCOMPLETE，已修屏幕观测时序

主控 #43 报告的结果与 [总收据](outside-live-03/verdict.json) 一致，原始失败保留。已完成的证据：

- [offline-trace](outside-live-03/offline-trace/verdict.json) PASS：中文跨两处分块、CLI／窗口原文字节相等、不读屏、非法游标拒收、只读输入均通过。
- [live-before-close.png](outside-live-03/lifecycle/window-first/live-before-close.png) 由 capturePage 生成，主控已核对真实 Codex TUI、任务卡、派发提示、模型设置、忙／运行中及门禁已认领。生成入口为 `outside-sandbox.sh live-03 live`，具体捕获请求在 window-first-driver.jsonl。
- [关窗前进程](outside-live-03/lifecycle/before-close-processes.json) 与 [关窗期间进程](outside-live-03/lifecycle/while-closed-processes.json) 的独立 ps 均读到 shell 95310、Codex 领导进程 95311。[trace 读回](outside-live-03/lifecycle/closed-output-readback.json) 显示窗口退出后的 13,158 字节增长到重开前 17,358 字节。
- 重开窗口收到的 `[0,17358)` 与 trace 原文逐字相等，覆盖关闭期间新增段；原文与实际收到的数据分别保存在 `lifecycle/reopened-backfill-trace.bin` 和 `lifecycle/reopened-backfill-window.bin`。

失败发生在随后“补回后的终端文字非空”断言。[窗口协议](outside-live-03/lifecycle/window-reopened-driver.jsonl) 第二次 inspect 已是 offset=18661，超过比对终点 17358；terminal 是 44 个换行，strip 后为空。最后那条 CLI `pane_output --offset 13158` 是独立差量读回，并非窗口游标。因此收据没有证明补回仍未追平。

[诊断](live-03-diagnosis.md) 记录了 xterm 6 的具体调用链：无障碍文字取自 `buffers.active`，但 DOM 刷新有 1000 ms 节流，可能晚于写入完成和游标更新。本轮 Codex argv 也含 `--no-alt-screen`。现有证据更符合文本层刷新滞后，最终以修复后的真实入口复验为准，不把推断写成产品绿态。

夹具现在在后台返回 next_offset=total_bytes 时保存高水位 H，暂缓**下一次**输出请求。它不更改已经返回的字节、游标或总长度，不停止 PTY。客户端从这一时点等待窗口游标严格等于 H 且当前激活屏幕文字可见，再将窗口实际收到的全部 `[0,H)` 与 trace 原文比对，完成或失败都释放取数屏障。H 必须覆盖原定的关窗区间；不靠固定等待时间宣称完成，也不追逐不断增长的末尾。

继续读取 xterm 为当前激活缓冲区生成的可访问行，没有改为普通缓冲区专用读取。下一轮离线入口新增普通屏幕→备用屏幕→普通屏幕的确定性切换：两块屏幕有不同专用文本，读回必须只包含当前屏幕文本；同时在屏障期间追加 trace，证明固定 H 不变、释放后继续取到新字节。此检查只用授权的离线 trace，不能冒充真实 PTY。

[本地协议检查](checkpoint-client-01/results.json) PASS：保存下来的失败 inspect 会被旧版游标判据放过；新版等待文字出现，拒绝空屏和超出固定 H，并在正常完成、超时、比对异常时释放屏障。这是明确标注的本地协议模拟，不证明 Electron 渲染。复现命令：

```sh
python3 -B workbench/tests/test_electron_checkpoint.py --recorded evidence/2026-10-10-batch12/T-075/card-4/outside-live-03/lifecycle/window-reopened-driver.jsonl --known-bad /private/tmp/a2a4src-y43b2oof/source/workbench/tests/electron_client.py --output evidence/2026-10-10-batch12/T-075/card-4/checkpoint-client-02
```

live-03 的 [归档计数](outside-live-03/lifecycle/archived-turn-accounting.json) 为 1 个主回合，原生会话 `01a129f4-f978-7ae1-874a-ee9fcf121601`；隔离 home 已删除。本轮未调用模型。预算保护按主控 #43 收紧为累计 3，不自动使用第 4 个。产品 app/src 与 live-03 冻结副本逐文件相同；本轮改动限测试和证据。语法、编码、产品文件对照、diff 与地图检查见 [live04-static-01/results.json](live04-static-01/results.json)。

下一条沙箱外命令：

```sh
zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh live-04 live
```

先跑零模型离线入口，包括新高水位和屏幕切换检查；通过才进入一个真实回合。失败即停，不自动重试，证据写入 `outside-live-04/`。真实重开显示、后续新输出和后台重启仍待验证，产品反事实、独立审查及最终交付仍未完成。ticket 保持 open，待主控关闭。

## live-04：生命周期证据已取得，原运行仍为 INCOMPLETE

主控 #44 核对了 [重启截图](outside-live-04/lifecycle/window-restart/interrupted-original-attempt.png)：历史回放可见，状态未知、执行已中断，门禁仍为已认领；没有候选提交、验收或集成。该结果符合批准的恢复语义。完整 [原收据](outside-live-04/lifecycle/verdict.json) 未改写；唯一失败是冻结版 run_pane_lifecycle.py 第 356 行的 `contexts` 非空断言。

实际归档库中，本 launch 的 native_record 只有 session_meta 和 task_started，没有 turn_context；因此该轮实际模型、审批／网络策略的 turn_context 读回仍是缺失，不能拿启动请求代替。累计新增 1 个真实主回合，达到 3/4；[计数](outside-live-04/lifecycle/archived-turn-accounting.json) 与预算日志一致，隔离 home 已删除。主控 #44 明确要求不再追加真实回合，接受下面的离线修复证据并继续引用其余 live-04 证据。

六项完成条件的证据索引：

| 条件 | 结果与证据 |
| --- | --- |
| 项目、任务、真实 PTY 和门禁截图 | 首窗 [live-before-close.png](outside-live-04/lifecycle/window-first/live-before-close.png)、重开 [reopened-backfill.png](outside-live-04/lifecycle/window-reopened/reopened-backfill.png)、[live-after-reopen.png](outside-live-04/lifecycle/window-reopened/live-after-reopen.png)。均由 electron_driver.mjs 的 capturePage 生成；请求与 PID 在对应 driver.jsonl |
| 关窗后进程不变、输出增长、重开补回与继续输出 | [closed-output-readback.json](outside-live-04/lifecycle/closed-output-readback.json)、before-close-processes.json、while-closed-processes.json；[字节与游标记录](outside-live-04/lifecycle/lifecycle.jsonl)。reopened-backfill、reopened-live 的 `*-window.bin` 与 `*-trace.bin` 分别逐字相等，固定高水位与窗口文字在 `*-checkpoint.json` |
| 后台重启不续跑、不完成 | [restart-readback.json](outside-live-04/lifecycle/restart-readback.json)、[原进程已退出](outside-live-04/lifecycle/stopped-original-processes.json)、[归档 SQLite](outside-live-04/lifecycle/state.sqlite3)、[原始事件](outside-live-04/lifecycle/orchestration-events.json)、[中断截图](outside-live-04/lifecycle/window-restart/interrupted-original-attempt.png)。CLI、库与截图的 gate/attempt 一致；启动与 submit_intent 均只有一次，重启后台无子进程，trace 没再增长 |
| 已挂载构建成功，缺盘报错且无回退 | live-04 两次构建成功，manifest 在 offline-trace/build.json 和 lifecycle/build.json；缺盘／普通目录反例及缓存前后清单见 [checks-01](outside-checks-01/checks.json)、[cache-readback.json](outside-checks-01/cache-readback.json)，checks-02 结果相同。最终原生采集修复未改构建代码 |
| 缺结构化信号显示未知，不读屏 | [offline-trace 收据](outside-live-04/offline-trace/verdict.json)：终端文字和 OSC 标题含 done、accepted、idle、等确认，状态仍为未知且门禁已认领；普通／备用屏幕切换通过。trace、CLI、窗口三个原文字节文件均保存；数据明确为离线夹具 |
| 地图健康 | [完整仓库收尾检查](delivery-precommit-01/receipt.json)：0 problems、0 stale；提交后的再次读回见 delivery-code-01/receipt.json |

这批截图与生命周期产物的原生成命令是 `zsh evidence/2026-10-10-batch12/T-075/card-4/outside-sandbox.sh live-04 live`；原 argv、冻结源码与逐命令原始输出都在 outside-live-04。该命令包含真实模型调用；主控 #44 已禁止本卡继续执行它。离线产物可用 `outside-sandbox.sh 新标签 offline` 单独生成，不需要模型回合。

## 停止时最后一次采集：离线红态、修复与绿态

代码核对比“只在 hook 读取”更具体：查询和 terminate 也会 scan，但 terminate 的 scan 在 SIGHUP **之前**，退出回调只记 pane_exit。故退出期间才写入的记录会遗漏。红态夹具先经 UserPromptSubmit 读入 session_meta/task_started，再在模拟的退出回调前追加带随机模型标记的 turn_context，故意不发 Stop。文件、SQLite 和原生记录归档都是真实本地 I/O；PTY 回调模拟，不声称重新证明真实 Codex 的落盘时序。

改动前 [native-final-red-01](native-final-red-01/cases/results.json) **9/9 业务断言失败**：自然退出、terminate、shutdown、回收遗漏最后完整记录；缺失／截断／损坏／半行／未绑定会话缺少明确采集结果。失败原文与 stderr 保留。

产品修复在退出回调内、pane_exit 之前，对**已经绑定**的原生会话从原字节游标最后读取一次。成功追加 native_final_read；读不到或残留半行追加 native_final_read_failed，携带绑定与已读位置，保留完整前缀。该步骤不发现或接管另一原生会话，不补完成事件；停止后的状态查询不再追加采集。主动停止、门禁回收和后台 shutdown 都经过同一退出回调。事件写入本身失败时沿用已有 observer 失败通道，不能假装记录成功。

改动后 [native-final-green-01](native-final-green-01/test_native_final_read/results.json) **9/9 PASS**；同批 pane_dispatch_state 和 trace_failure 回归 PASS。逐项检查完整记录仅一次入库、原文一致、采集结果先于 pane_exit、失败有事件、状态未知／中断、重复停止与后续查询不重采。没有真实模型、Electron 或真实 PTY 调用。

重新生成绿态（新目录）：

```sh
node workbench/tests/test_native_final_read.ts /tmp/t0754-native-final-green-new
node workbench/tests/test_pane_dispatch_state.ts /tmp/t0754-pane-state-new
node workbench/tests/test_pane_trace_failure.ts /tmp/t0754-trace-failure-new
```

红态所用旧产品是 live-04 冻结源码：`outside-live-04/candidate-source.tar.gz`。将其提取到新目录，依照先前冻结夹具仅在源码目录链接已装依赖，再令 `A2A_PANE_MODULE` 指向旧副本 `workbench/src/panes.ts`，运行当前同一个 test_native_final_read.ts，可再次取得相同业务红态；不启动真实 Codex。

边界：live-04 原 contexts 断言没有因离线 PASS 被改写为通过；停止采集修复按主控 #44 指定的离线方式证明。PLAN 列出的五类产品变异体尚未全部执行；现有反事实为起点三项缺接口红态、原生采集旧版本红态及夹具已知坏版本。独立审查须据此评估，不能将计划写成已运行。

## 一次独立审查与缓存修复

审查者为 fresh-context `gpt-6-astra` / xhigh，只读；通过 collaboration 创建独立 agent，未继承实现会话。目标为 [冻结候选](review-candidate-01/target.json)，原始输出完整保存在 [independent-review-01.md](independent-review-01.md)。本卡只做这一轮独立审查，没有追审，也没有将 worker 自查称为独立审查。

原始结论 **FAIL**，唯一 P2：README 中首次安装的 `npm ci` 命令只指定 npm cache。Electron 43.4.1 的实际安装器读取 `electron_config_cache`，缺省时 @electron/get 5.1.0 选内置盘 `~/Library/Caches/electron`；原 check-cache 只核对 npm cache，无法拒绝这个配置。

复现顺序与结果：

1. `review-cache-red-01` 是**探针错误**：尝试 resolve `@electron/get/package.json` 被 package exports 拒绝，没有形成完整缓存反例。原 stderr 保留，不能算业务红态。
2. 修正探针读取已安装 package 的路径后，[review-cache-red-02](review-cache-red-02/probe/results.json) 取得有效红态：缺少 Electron cache、指定内置路径都被旧 guard 放过；实际安装器从原 README 命令拿不到 cacheRoot，解析到内置盘。正确外置参数的正例原本就通过。
3. 产品修复仅给 check-cache 增加 Electron cache 精确路径校验，并在 README 命令中显式设置 `electron_config_cache=/Volumes/WD-Elements/a2a-electron-cache`。未改依赖、lockfile、全局配置或 .npmrc；沿用原挂载和 npm cache 检查。
4. [review-cache-green-01](review-cache-green-01/probe/results.json) **4/4 PASS**：缺失／内置路径均退出 1，外置路径退出 0，实际 Electron 安装器收到且解析为已批准外置路径。下载函数被观测器替换，解压禁止执行；网络、安装和缓存写入均为 0。它证明安装器参数选择，不补称真实下载已复验。

当前 npm 的 `ci.js:135–149` 在 arb.reify 前执行根 preinstall，install.js:160–176 同样前置；因此这次修复沿用现有 guard，不另加安装包装器。只读审查探针的完整命令见独立报告。复验修复：

```sh
node workbench/tests/test_install_cache.mjs /tmp/t0754-install-cache-new
```

审查还独立核对了 live-04 的原始 SQLite、PTY、截图和离线采集原库，没有提出其他可确认的 P1/P2 产品缺陷。限制仍保留：实际 turn_context 缺失、五类产品变异体未全部执行；冻结包不是完整仓库，审查者对包内地图检查得到 49 problems，不能当成实际仓库损坏。当前完整仓库的最终地图收据另行保存，不能删除或上调原审查结论。

具体修复 diff、修复后文件与当时完整仓库检查收据在 [review-fix-01](review-fix-01/receipt.json)。其当时的 INCOMPLETE 收据保留；主控 #45 随后明确批准该 diff 并要求收尾。没有追审，未再次请求或运行真实模型。

另上报非阻塞登记问题 `20261011T080957Z-worker:s12-t075-4-issue-001`：MAP 中 workbench/README 的 Covers 尚未包含 app 和 package.json。正文见 [living-doc-coverage-issue.md](living-doc-coverage-issue.md)，worker 没有越界修改地图，留执行主控处理。

## 最终交付

交付绑定：T-075-4 / attempt a1 / session `5202c316-d88e-47cd-98cc-35900f8e7aca` / launch `launch-edbfaf3f24c5425681d802b1e259cd84`；原生 worker 会话 `01a12991-a865-7b82-8af7-5d1ce8ccf8bf`。本 worker 启动记录为 Codex 0.162.1、gpt-6-astra、xhigh、Fast 请求；不把请求当成供应商实际服务层证明。

提交前核对产品／测试等于冻结候选加主控批准的三文件修复；完整仓库 status 为 0 problems、0 stale。检查命令和原始 stdout/stderr 保存在 delivery-precommit-01。git add 与 git commit 单独执行，无环境变量前缀；只提交 workbench、本卡证据及 T-075 Resolution，不带入两份 controller-poll.log、dispatch.jsonl 或其他任务文件。

实现提交与九项尾注、提交后地图读回保存在 [delivery-code-01/receipt.json](delivery-code-01/receipt.json)。收据提交只补交付记录，产品／测试不变；最终交付完整提交号以终端 DONE 行为准。T-075 的九项 Acceptance 逐项证据表在 ticket Resolution，保持 open，待主控关闭。

保留的限制：三张旧卡的证明各自绑定其版本；最终候选未重新跑全套旧 8/9/18，也未跑完 PLAN 五类产品变异体。live-04 的实际 turn_context 读回缺失未补称通过；最后采集由获批离线夹具证明，安装缓存修复未做真实下载。所有历史失败与独立审查原始 FAIL 都保留，没有上调或覆盖。
