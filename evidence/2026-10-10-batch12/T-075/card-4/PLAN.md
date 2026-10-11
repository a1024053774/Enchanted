# T-075-4 实施计划（待执行主控批准）

日期：2026-10-11。任务：T-075，`ready_rev: 4`；派发：`⟦主控 #34⟧`；唯一写入者：`s12-t075-4`。

计划编写状态：**PASS**。实施及验收状态：**INCOMPLETE**。本轮只读取项目材料和本地依赖、编写本计划；未改产品、未启动 Electron、后台或被测 Codex，未运行产品验收，未提交。本文件是本卡日期记录，不替代 ticket 或 spec。

起点：`e55da7db17c25d9712909666119104fc96969a93`。实现获准后再次读回 HEAD，将两次版本写进 RESULTS，不覆盖本次起点。开始时已有 `evidence/2026-10-09-batch11/controller-poll.log` 修改，阅读期间另有 `evidence/2026-10-10-batch12/controller-poll.log` 修改；两者保留，不纳入本卡提交。

## 1. 目标、边界与需批准的选择

目标：最小 Electron 窗口连接常驻后台，显示一个项目、一个任务、一个真实 PTY 窗格和门禁状态；关窗不影响窗格，重开补回输出；后台重启留下可查询的中断事实，并沿用原门禁恢复契约；构建缺外置盘即失败。

非目标沿用任务卡：不做 S2–S5 的审查产品流程、打回、评分、清理、主控、收件箱、面板、通知或设置；不做 Claude、provider 或 MCP 网关。每次交付的一次独立代码审查仍须完成，不等于实现 S2。

**建议主控批准本卡只读显示。** xterm 可以选择、复制和滚动；本卡不将键盘、粘贴或鼠标终端输入写入 PTY，不提供“放行”按钮。理由：本卡六项完成条件聚焦显示、生命周期和恢复；现有后台没有用户输入写入接口，而 xterm 6 的公开 `onData` 同时承载手工输入和自动终端应答，不能直接把它全部记录成用户输入。完整输入还需处理 IME、粘贴、控制键、CR 即忙、Esc 后放行及持久化失败，属于另一条需要独立证据的行为链。只读使本卡可以先证明窗口与后台的边界，输入功能留到主控安排的后续卡。**这只是提案；未获批准不按只读方案实施。** 若主控要求本卡交互输入，先修订输入与验收部分，再实施，不能悄悄缩减要求。

另外两项请随本计划一并核定：

- 输出采用**按字节游标分段读取**，持续读取代替长连接推送；不增加第二套订阅协议。
- 重启后将 attempt 的**执行状态**投影为“已中断／未知”，门禁的 `claimed/submitted/verifying/integrating/accepted` 等既有状态保留原值；门禁恢复只能由显式 `verify`／`integrate` 驱动。界面同时显示这两种事实，不把启动新后台当成任务完成。

本轮批准门槛来自任务卡“先交计划，停下等我”。批准计划不代替随后 `outside-sandbox.sh` 的执行交接，也不代替真实被测会话 hooks 的逐次批准。

## 2. 已核对的事实与最小探针

**REALITY GATE: INCOMPLETE。** 进程方向已有依据；只读范围待批准，运行事实须在批准后取得。

| 类别 | 已知事实或未知 | 依据与影响 |
| --- | --- | --- |
| observed | 当前后台经 Unix socket 提供单请求 JSON 响应；CLI 是客户端，后台拥有门禁和 PTY | `workbench/src/transport.ts`、`daemon.ts`；保持同一 socket 和门禁入口 |
| observed | PTY 输出先追加到 `traces/<launch>/pty.raw`，目前没有输出读取接口 | `panes.ts` 的 `onData`；新读取接口以已落盘 trace 为事实来源 |
| observed | 窗格只在 `Panes.panes` 内存 Map 中，重启后 `pane_status` 无法查旧窗格 | `panes.ts`、`store.ts`；需从启动记录和追加事件建立历史查询投影，不重建 PTY |
| observed | `daemon_stop` 通过 SIGHUP 结束自有 PTY；启动不替换已有 socket/PID 文件 | `daemon.ts`、`transport.ts`；正常停止与崩溃残留分别验收 |
| observed | `verify`、`integrate` 已有操作锁、中断记录、G/M 核对和 `needs_reconciliation` | `gates/core.ts`；恢复所有权继续在门禁核心 |
| observed | 运行时只有受管 Codex 启动；argv 明确在 Codex 退出后 `exec /bin/zsh -f -i` | `panes.ts:createThread`；没有普通 shell 启动入口，不为测试增加假 Codex 或第二种派发路径 |
| observed | xterm 公开 `onData` 无来源字段；内部 `triggerDataEvent` 同时服务用户输入和设备应答 | 本地 `@xterm/xterm/typings/xterm.d.ts`、`src/common/services/CoreService.ts`；只读方案不订阅写回，终端协议应答仍由后台负责 |
| observed | 所需依赖已在 package/lock 中；没有 app 目录实现及 build script | `workbench/package.json`；不增加包，使用已装 Electron/React/Vite/xterm |
| observed | fork 当前提交是 `ddb765956cae4a4d0b87b875970601068567ed93` | 只读组件来源；迁入片段逐项保留来源与 MIT 声明 |
| observed | spec 第 5 节尚保留旧 socket 放行表述，T-075 rev 4 与卡 3 已选择 B | 沿用 ticket 明确的修订，不恢复 A2，不改 spec，不把旧文字当新授权 |
| unknown | Electron 43 与本机 Node 26 构建组合是否可运行，实际图形会话能否截图 | 探针 P1；不能用构建成功代替 Electron 运行 |
| unknown | 分段读取在中文跨块、持续输出与关窗重开时是否完整 | 探针 P2；不能用肉眼截图代替原文比对 |
| unknown | 当前后台迁移后的恢复场景是否完整符合原契约 | 探针 P3；卡 1、2 的通过不替本候选背书 |

已读 `AGENTS.md`、`CONTEXT.md`、`intent.md`、`MAP.md`、T-075 rev 4、T-074 结论、native-cli spec 第 1、3、5、6、8、9、12、13 节及 Test seam、recovery spec 全文、后台直接调用链、相关测试及卡 3 报告。session 起始地图检查退出 0：0 problems、0 stale。

| 探针 | 输入与方法 | 通过／失败／停止条件 | 负责人和证据 |
| --- | --- | --- | --- |
| P1：最薄窗口 | 隔离目录，现有后台 CLI，新窗口连接并显示真实 task snapshot 和一个真实输出块；Electron `capturePage` | 成功加载、连接及 PNG 可读才通过；缺依赖、权限或运行时不兼容保存失败；需要新包或扩大权限即停 | worker 写脚本，执行主控沙箱外运行；`card-4/<run>/p1/` |
| P2：输出完整性 | 超过两块的已知中文/ASCII/ANSI 输出，跨块边界，输出期间关闭并重开窗口 | 窗口收到的字节按 offset 拼接，与独立读取的 trace 对应区间完全相等；丢失、重复、乱序或截断均失败 | 同上；`card-4/<run>/lifecycle/` |
| P3：恢复 | 正常停启后台；另在隔离验收中用 barrier 终止执行 verify/integrate 的后台 | CLI、SQLite、Git refs/reflog 与第 6 节一致才通过；恢复误写 accepted、无核对重跑副作用、丢失证据即失败；必须改验收契约时停 | 同上；`card-4/<run>/recovery/` |

## 3. 界面结构与组件来源

遵循 **Tracer bullet**：第一步就打通“现有 task/launch → 后台查询和 trace → socket → Electron → xterm → capturePage”，保留在产品路径，再扩展关闭重开和恢复。遵循 **Deep modules**：后台隐藏 trace、持久化和身份查询；Electron 主进程只桥接明确的只读能力，渲染层没有 SQLite、文件系统、shell 或 PTY 权限。遵循 **Ubiquitous language**：项目、任务、agent 会话、窗格、attempt、启动记录与门禁状态沿用 CONTEXT，不把 idle、Stop 或进程退出叫作交付完成。

窗口初始约 1440×900：左侧约 224px 的项目／任务导航，右侧为任务标题、agent 会话信息、终端和门禁状态条。显示真实项目名、任务标题、选中的 attempt/启动记录短号；门禁区显示当前门禁状态、候选/验收/集成结果及明确错误。普通使用文案保持中文；不把数据库字段名堆成产品说明。

主行动是查看正在执行的窗格；视觉重点是占主要面积的真实终端。界面不放示例指标、无来源数据或空白功能入口。后台不可达时在原位置显示“后台未连接”，历史内容标明为上次读到的记录；允许明确点击“重新连接”，不隐式启动后台或重试写操作。

复用 fork 的 `apps/web/src/index.css` 导航分界和终端表面样式、`theme/theme.seed.generated.ts` 中的 Codex 暗色种子，以及 `components/TerminalScrollToBottom.tsx` 的滚动定位组件。后者改用本卡已有 React 和普通 button，不搬 `IconButton`、图标库、provider、nativeApi 或 terminalRuntimeRegistry。仅迁入实际用到的片段；文件头和来源说明保留两位 MIT 版权方，继续附 `workbench/LICENSE.synara`。

同一界面采用以下六项基准；字体用已存在的系统栈，不下载字体：

| 项目 | 值与来源 |
| --- | --- |
| 底 | `#111111`，fork Codex dark surface；同色终端表面 |
| 字 | `#fcfcfc`，fork Codex dark ink；次级文字用同色降低不透明度 |
| 强调 | `#0169cc`，fork Codex dark accent；错误、成功为语义色，未知用中性色并带文字 |
| 边线 | `rgba(252,252,252,0.12)`，本卡对 fork 细分界结构的固定映射；1px，无叠加阴影 |
| 字体栈 | UI：`-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`；终端：`"SF Mono", "SFMono-Regular", Menlo, monospace` |
| 圆角 | 小控件 6px，容器基准 10px，按 fork 的 0.625rem 及 0.6 比例；终端主体与导航分界保持直边 |

固定本卡终端网格为当前后台的 160×45，避免只读窗口尺寸变化改变正在运行的 worker。xterm 使用同一网格；较小窗口允许外层滚动，不在本卡新增 PTY resize 接口。状态与错误始终有文字，复制和滚动保留可见键盘焦点。截图用于布局与事实核对；最终外观由主控／用户判断，不能把 skill 自评称为审美通过。

## 4. Electron 与后台接口

拟新增 `workbench/app/`：Electron main、隔离 preload、React 渲染层、样式、Vite 配置、构建和启动入口。main 通过 `transport.request` 使用现有 Unix socket；不 import `daemon.ts`、`panes.ts`、门禁核心或 node-pty，也不打开任何库。preload 只暴露指定查询与输出读取，不暴露通用 IPC、任意路径读取或任意门禁命令。窗口使用 `contextIsolation: true`、关闭 Node integration，限制导航和新窗口；加载本地构建产物。

| 接口 | 行为与边界 |
| --- | --- |
| 新增 `workbench_snapshot --task ID [--launch ID]` | 返回真实项目／任务、门禁当前视图、所选 attempt、启动记录的展示字段、窗格生命周期、结构化活动状态及来源。首次未指定 launch 时只选择一次该 task 当前窗格；之后绑定原 launch，不跟随新的 current_attempt 切换 |
| 新增 `pane_output --launch ID --offset N --max-bytes N` | 后台从绑定的 trace 分段读已落盘字节，返回 `launch/start_offset/next_offset/total_bytes/data_base64`；默认上限 64 KiB。拒绝负数、越界、过大请求和未知 launch；客户端不能提供文件路径 |
| 扩展 `pane_status --thread ID`、`launch_show --launch ID` | 支持读取历史启动记录和重启后的中断投影；历史对象没有可调用 PTY，不恢复 token、队列或 worker 身份 |
| 现有 `status/events/orchestration_events/daemon_status` | 原样用于独立 CLI 读回；门禁状态和事件仍来自原所有者 |

新查询加进既有 CLI 的参数校验和后台分流；没有第二个服务端口。快照组合调用门禁的只读接口与编排存储；不在渲染层根据终端文字推断状态。不新增通用项目管理 API；一个任务所需的项目数据由已保存的 task/launch 提供。

正常关闭最后一个窗口时 Electron 退出，只停止本窗口的读取；没有 `daemon_stop`、`reclaim`、SIGHUP 或 PTY dispose 调用。重新运行相同启动命令，绑定同一个 task/launch。默认产品数据仍为 `~/Library/Application Support/a2a-orchestrator`；Electron 的 userData/sessionData 放其 UI 子目录。本卡测试全部显式指定 `/tmp` 下的后台和 Electron 数据目录，在 Electron ready 之前设置，避免默认写入 `a2a-workbench`。

## 5. 输出补回、持续读取与输入记录

输出是同一条分段读取路径：新窗口从 offset 0 开始；每次读取取得明确的字节区间，渲染层将 base64 解为 Uint8Array 交给 `Terminal.write`，等待 write callback 后才推进游标。中文不会在块边界先被转成不完整字符串。已有积压立即读下一块，追平后约每 100ms 查询一次；每个窗口同时至多一个输出请求，窗口关闭后取消后续调度。任务／门禁快照单独低频读取，约 1s 一次。

不先读整份文件再另接实时广播，因此没有切换窗口；相同 cursor 和 trace 同时用于补回与新输出。不按“最后若干行”截断，不用 xterm scrollback 代替持久轨迹。trace 缩短、缺失或 offset 不一致时明确报“输出不完整”，停止推进；不跳回 0 假装重连成功。网络断开显示未连接，用户重新连接时仍绑定同一 launch；新窗口重新从 0 回放。没有后台替换导致的自动换窗格。

读取类高频请求不重复保存 PTY 文本到编排事件表；原始输出仍只有 trace，启动、终止、中断和拒收事实仍追加记录。trace 写入失败沿用当前失败处理；查询不能把内存中尚未落盘的输出称为已记录。原始 ANSI、CR、中文和空字节均按字节保留。验收将同时保存渲染前的实际收到字节和 xterm 解析后的文本，前者用于逐字比对，后者与 PNG 证明真正显示。

**输入记录（取决于只读提案获批）：** xterm 设置只读并且不接任何 PTY 写回 IPC；禁用粘贴、按键和终端协议自动响应向后台转发。现有 `Panes.terminalProtocol` 仍独占设备查询应答。选择、复制、滚动不产生 worker 输入。测试以键盘／粘贴事件和设备查询为反例，确认 trace 没有新增输入回显，库里没有伪造的 `user_inputs/human_intervention`。主控通过原 `pane_dispatch` 注入的文字仍先登记为派发，不能记为用户输入。此卡不宣称完成 spec 第 6 节的交互输入链。

如果主控决定交互输入归本卡，必须先补定来源分离、逐次绑定 launch/attempt/session/fence、先持久化用户输入及人工介入再写 PTY、CR 即忙、Esc 不放队列、记录失败拒绝写入、未知结果不重投等接口与端到端反例；不能把只读实现改一个 `onData` 回调就交付。

## 6. 后台重启：逐项对照 recovery spec

重启时依据原 launch、`pane_started/pane_exit/pane_stop_intent/daemon_*` 等持久事件追加中断观察，带原 task/attempt/session/fence/launch 和新后台实例标识。旧 launch 可查询和回放，但不放回 live PTY Map，不重新派发、自动换 attempt、自动放队列或重新授予旧 token。没有可靠结束事件时，进程结局显示“未知”；已记录停止事实则显示“已中断”。仅 PID 存在不足以重新认领进程。

不为“中断”新造门禁成功状态。`workbench_snapshot` 和 `pane_status` 返回执行中断投影；原门禁 `status` 返回未被改写的 gate state 和同一 attempt。验收保存这两份 CLI 输出与直接 SQLite 读回，解释例如“门禁：已认领；执行：已中断”。已 accepted 的历史交付也不能因窗格结束被改成未通过。

| recovery 可观察契约 | 本卡处理与独立验收 |
| --- | --- |
| 1. 排除同一任务重叠 verify/integrate；锁释放不等于通过 | 保持任务操作锁。真实 oracle barrier 期间第二次命令得到 `operation_busy`；普通查询仍可用。杀死执行者后由 OS 释放锁，窗口仅报告结果尚未知，不自行发验收 |
| 2. verify 中断 | 重启不自动执行 verify，也不把旧 verification 改成 passed。下一次显式 verify、持有原操作锁后，由既有 `interruptVerification` 保存旧 ID 为 interrupted、追加事件、保留 candidate/oracle/worktree/command_intent；同一有效候选产生新 ID 和新 worktree，完整 oracle 退出 0 才 verified。无旧退出码即 unknown，不收编孤儿 oracle 结果 |
| 2. 当前 attempt/spec 已变化 | 新窗口保持所选旧 launch 的历史身份；不得将旧 Stop、submit 或 verification 接到新 attempt。用 revoke/revise 后的真实入口拒收反例证明不复活旧候选 |
| 3. pending integrate，引用仍为 G | 保留原 intent；下一次显式 integrate 核验 attempt/session/fence/spec、candidate、verification、intent 后继续同一 CAS(M,G)，不新建意图 |
| 3. Git 已为 M，账未记完 | 核对同一 intent 和内容后补记 accepted；对比 reflog，不能再次更新 Git |
| 3. 第三个引用 X 或引用缺失 | 显式 integrate 返回 `needs_reconciliation`，保留意图和现场，不更新 Git，不标 accepted；revoke/revise 不得绕过合法 pending intent |
| 4. 成功后重放幂等 | 原命令重放不增加集成副作用；历史事件、旧工作区与候选保留；旧身份 submit 仍被拒 |

正常停启路径先用现有 `daemon_stop`，确认旧 PID 及自有子进程退出、socket 清理，再 `daemon_start`。硬崩溃的锁和 intent 测试只杀测试创建的后台／CLI 进程；绝不杀用户服务。崩溃会留下 socket/PID 文件，沿用“未知所有者拒绝启动”：先保留拒绝输出，测试 harness 核对自己记录的进程已退出后，记录并清理自己创建的这两个残留文件，再显式启动。本卡不增加自动偷锁、替换 socket 或 PID 存活即接管的恢复分支。

## 7. 构建与外置盘检查

不增加依赖。`workbench/app/build.mjs` 是产品构建入口，package 中加对应命令。Vite 构建渲染层及 Electron 的 main/preload；Node builtin 和 Electron external，输出中不打包 node-pty。main/preload 使用 Electron 能直接加载的 JS/CJS，不依赖它能否原生执行 TypeScript。

入口在导入 Vite、创建目录和启动子进程之前校验外置盘：默认检查 `/Volumes/WD-Elements`；测试用显式 `A2A_BUILD_VOLUME` 指定别的检查路径。必须存在、是目录、不是链接冒充，规范路径与设备号证明它是独立挂载点（与父目录设备号不同）。缺失路径、内置盘普通目录和符号链接均拒绝。缓存和输出只能由这个已核对的根派生，不能用另外的路径变量绕过检查。

计划目录为外置盘下 `a2a-workbench/<构建槽>/vite-cache`、`tmp` 和 `dist`；构建槽使用明确标签，不计算无用途的 hash。Vite cacheDir、构建临时目录和 outDir 均显式指定；Electron 下载继续使用现有 `/Volumes/WD-Elements/a2a-electron-cache`，npm 缓存仍为 `a2a-t075-npm-cache`。源码、已装 node_modules 和产品数据位置沿用现状；不在仓库创建 dist 链接，不搬动共享输出，不向输出目录链接源码或依赖。

仅清理本构建入口创建并核对归属的输出槽，不能让 Vite 对任意路径 `emptyOutDir`。终端运行只读取已生成产物，不隐式构建或安装。未挂载反例先把路径指向 `/tmp` 下不存在的目录，再以存在但未挂载的普通目录补反例；检查退出码、错误及约定的缓存候选目录前后清单，确认没有 `.vite`、`.vite-temp`、内置盘 dist 或 npm/Electron 缓存回退。不得真的卸载磁盘。

## 8. 端到端正例、反例与红态

预期来自本卡六项完成条件、T-075 Acceptance 和 recovery spec；不从产品返回值生成答案。先写可独立运行的端到端测试，再拿起点合同红态；这是“新界面尚不存在”的红态，不冒称旧产品缺陷。

拟统一入口（下列为待实现命令，**尚未运行**）：

```sh
python3 workbench/tests/test_electron_e2e.py --source /绝对路径/a2a --output /绝对路径/card-4/一次全新运行目录
```

红态把同一个新测试指向起点 `e55da7db17c25d9712909666119104fc96969a93` 的隔离源码副本，使用现有依赖；缺少 app 构建入口或 `workbench_snapshot/pane_output` 必须明确失败。依赖缺失、权限失败或测试自身异常不计合同红态；保留后修正测试，再用新目录重跑。不上来修改当前产品后才补一个形式红态。

| 场景 | 正例或反例的独立判据／产物 |
| --- | --- |
| 窗口与真实 PTY | Electron 加载真实后台数据，xterm 显示指定夹具输出；capturePage PNG、DOM/终端文本、启动 argv、后台 CLI 与数据库读回相互对应 |
| 关闭窗口 | 保存旧 shell/工具子进程 PID，关闭整个 Electron 进程后另一个检查进程用 ps 核对存活；从后台输出入口和直接 trace 读回都证明字节数增加。不能只看进程配置或 daemon PID |
| 重开同一窗格 | launch/thread/attempt/shell PID 均与关窗前相同；回放包含关闭期间的输出，随后收到新序号。用直接读 trace 的固定高水位区间与窗口收到的 bytes 完全比较，保存 expected/actual，不算 hash |
| 中文与块边界 | 控制夹具包含中文、emoji、CR/LF、ANSI 和超过 128 KiB 输出，明确切在多字节字符中间；raw 比较和 xterm 最终可见文本都正确 |
| 只读输入及设备应答 | 对实际窗口输入文本、Enter、粘贴，输出中含设备查询；不写入 PTY，不产生用户输入／人工介入。现有派发记录不被补记成用户输入 |
| 未知与不读屏 | 初始缺结构化信号显示“未知”；真实 PTY 打印 `idle / done / accepted / 等确认` 等诱导文字及改标题 OSC，状态只跟结构化来源。已有 busy 不变成 idle/accepted；重启后相同历史文字仍不能解除未知或中断 |
| 重启 | 同第 6 节；无自动新 launch、无新 worker PID、无旧队列重放，task/attempt/intent 保留；恢复结果由 CLI、SQLite、Git 独立核对 |
| 构建正反例 | 实际挂载时产物可启动；缺失路径及内置盘普通目录均失败，内置缓存候选清单无新增 |
| 身份／游标反例 | 旧 launch 的读请求不能换成新 current_attempt；非法 cursor、trace 缺失或缩短明确失败，窗口不显示“已追平”或悄悄接新窗格 |
| 当前候选回归 | 运行受影响的 pane 状态／trace、后台门禁、relay 测试；门禁恢复用真实后台入口复验。T-075 的旧 8/9/18 场景保持断言原样，必要的生命周期适配只放 workbench/tests，不修改 acceptance/ |

新增行为用起点或有针对性的已知坏副本证明测试有效，至少覆盖：省略关闭期间字节、窗口关闭误停后台、缺信号标 idle、重启自动续跑或标成功、缺盘仍继续构建。每项在隔离源码副本中分别运行；必须是行为断言拒绝，不把变异脚本崩溃计为检出。只为新增行为做必要反事实，不为凑数量扩测试。

旧 8/9/18 通过记录分别绑定卡 1、2 的版本；卡 3 报告已说明不背书旧全套后台适配。本卡 RESULTS 将逐条列原始证据和本候选重跑范围。如果旧场景无法在不改断言／不改产品范围的情况下接入后台，保存具体失败并上报，整票相应项保持 INCOMPLETE，不能用历史 PASS 抹平。

## 9. 脚本化 zsh 与真实回合预算

优先用确定性的 zsh 输出源证明窗口行为。当前生产启动链只支持受管 Codex；虽然 Codex 退出后会回到 zsh，但只读方案没有向这个 shell 注入脚本的入口。因此不采用“先退出 Codex 再往 shell 写命令”的测试，不新增普通 shell 产品功能，也不以假 `codex --version` 欺骗启动检查。

本计划的主方案预算为 **1 个真实主 turn**：给真实 worker 的任务只是在自己的夹具中运行预先编写的 zsh 输出脚本，持续产生可预测的序号、中文和诱导状态文字；不改产品、不 Git 提交、不 submit，所以不会触发回执回合。测试在该工具仍输出时关窗、重开，再停止自建后台，证明进行中的 attempt 被中断。脚本和外部 oracle 均由测试预先定义，预期不取自模型回答。工具输出是否实时进入真实 PTY 也必须实测；若 CLI 聚合输出导致这一场景无法观察，保存失败并交主控决定，不增加伪造输出通道。门禁恢复反例使用现有 claim 路径的确定性夹具，不消耗模型回合。

真实被测会话固定 Codex CLI 0.162.1、`gpt-6.1-sol`、xhigh、`service_tier="fast"` 请求、关闭启动更新、审批 never；配置沿用卡 3 的 B 通道，不改权限。**全卡硬上限 4 个主 turn**，预期只用 1 个，其余不是自动重试额度；需要追加时先说明原因和累计数给主控。每个实际开始的主 turn 都计入，辅助标题通知单列；启动／初始化失败也保留，不能重复运行直到通过而不计数。

CODEX_HOME 在 `/tmp`，只复制 auth.json，信任已核对的夹具根，只加 git add/git commit 两条前缀规则；hooks 只在主控逐次批准后安装。副本不进证据或 Git。结束先核对自建所有进程退出，再删除整个 home；其他失败夹具、trace、数据库和 Git 现场保留。若无法在预算和现有入口内得到稳定输出，报告 INCOMPLETE，不改为无头调用、假运行时或新依赖。

## 10. 截图与沙箱外交接

截图由测试专用 Electron 驱动加载产品窗口，等待快照和 xterm write callback 后调用 `webContents.capturePage()`，将 `NativeImage.toPNG()` 写到证据目录。驱动使用 Electron 的已有 API 操作自身窗口，不用 Computer Use，不添 Playwright。断言尽量经实际窗口、preload 和后台入口；测试驱动只观察、操作和保存证据，不给产品插入“测试成功”分支。

至少保存：首次窗口、重开后含离线期间输出、后台停止时、重启后的中断／未知状态。每张 PNG 附实际命令、窗口尺寸、时间、task/attempt/launch、源码版本和证据高水位；另保存本轮完整 CLI 调用、stdout/stderr/exit、进程读回和库快照。构建配置不能仅为截图伪造任务或状态。

批准后写 `card-4/outside-sandbox.sh`，分阶段且每次用新目录保存，默认不覆盖旧结果。以下都交执行主控沙箱外运行，worker 不申请联网提权：

- 外置盘构建、临时目录／缓存写入及缺盘反例。
- 启动隔离后台、Unix socket、node-pty 和 ps 身份读回。
- Electron 启动、关窗重开、输入反例和 capturePage。
- 经批准的隔离真实 Codex 启动及最多 4 主 turn；hooks 参数在脚本中明确列出。
- 自建进程故障注入、恢复契约测试、夹具 Git 操作、归档与隔离 home 收尾。

脚本准备好后回复 `T-075 OUTSIDE-SANDBOX READY` 并停止，由主控执行。不能在等待期间先自行跑其中部分。纯文件阅读、计划／测试／产品代码编辑、静态 diff 与地图检查在当前沙箱内进行。

## 11. 实施顺序、审查与交付

1. 等本计划批准，特别是只读提案；核对 ready_rev 与起点是否变化。
2. 编写独立端到端脚本和沙箱外交接脚本；先取得起点合同红态与必要最小探针。环境或探针失败另记，不计为红态。
3. 通过实际入口完成 Tracer bullet，再补分段回放、历史窗格投影与上述恢复场景；同步更新 workbench/README.md。
4. 冻结候选，运行正例、反例及相关回归，检查截图实际内容；保存原始失败及每轮源码版本，不覆盖异常结果。
5. 按任务卡做一次 fresh-context 只读独立审查，使用 behavioral-acceptance-review 检查外部 oracle 和已知坏实现；若出现异常处理或恢复分支，同时按 design-integrity-review 路由纳入同一完成检查点。审查问题先复现红态再修，修复 diff 交执行主控审，不自行扩大为多轮追审。
6. RESULTS 逐项对应任务卡六项完成条件与 T-075 全部 Acceptance，区分前三卡证据、本候选新证据、未跑和非目标。记录实际数据目录、CLI/模型、请求 tier、输入、事件、主 turn、失败、审查与重现命令。T-075 只写 Resolution，保持 open、“待主控关闭”，不替主控勾选或关闭。
7. 运行地图检查并保存输出。若 README 覆盖关系或 Verified 需要改地图，由执行主控处理；worker 不改 MAP/CONTEXT/AGENTS。状态未达到 0 problems、0 stale 时明确报 INCOMPLETE。
8. 只提交本卡授权文件与 ticket Resolution；git add、git commit 各自独立，核对本 worker 的尾注。不 push。最终按卡输出 `T-075 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。

本计划交付前再次执行的地图命令：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

本轮交接前实跑结果：退出 0，`Problems (0)`、`Stale living docs (0)`。PLAN 已回读并检查 UTF-8、无 BOM、LF 换行和无替换字符；这只证明文件交付与地图检查完成，不是产品验收。

本轮在计划交接点停止，不开始第 2 步。
