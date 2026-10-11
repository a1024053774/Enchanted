# a2a 门禁、编排后台与只读工作台

用 Node 26.5 及其原生 TypeScript 类型剥离直接运行，无 Bun、打包或编译步骤：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/隔离状态目录 status --task 任务编号
```

先对同一隔离目录调用 `daemon_start`，结束时调用 `daemon_stop`。客户端只通过
`control.sock` 访问常驻后台，不再直接打开门禁库。后台未启动时命令明确失败，不自动拉起或重试。
`daemon_start` 使用 detached 子进程和独立日志。
普通请求的传输期限为 120 秒；`run` 的有效显式等待参数另加 120 秒收尾余量，
避免长任务被短客户端期限截断。传输超时仍报告结果未知，不重放请求。
`daemon_stop` 显式进入关闭流程，返回 `stopping: true` 是受理确认；以 PID/端点消失确认退出。
关闭时拒收新请求，自动 run 在等待及门禁边界停止推进；已开始的门禁操作与回执写入先收尾，
随后停止自建窗格、保存退出事件、关闭数据库。停止不替代 reclaim，也不把失败或未知结果改成通过。
后台常驻与一次真实窗格派发已验证；工具沙箱的 socket 连接曾被 EPERM 拒绝。
T-075 rev 4 的 A2 探针在工具层被拒，未验证成；按用户决定改用 B 文件转交。
B 已通过隔离真实 Codex 的显式交付、机械检查与 CAS 集成；本卡一次独立审查 PASS。
该结论限卡 3 的本地夹具；Electron 与重启恢复的实现和验证进度另见文末卡 4 记录，完整工作台尚未切换。

受管派发提示要求 `git add <路径>` 与 `git commit …` 各自独立执行，
检查命令另行运行，以便两个已授权的 Git 前缀规则分别匹配。
若独立命令仍被拒，worker 上报并结束，不自行重试或调整沙箱。

`acceptance/entry/a2a_gates.py` 将参数原样交给这里的 CLI。门禁核心仍由后台中的
`A2AGates.call` 独占写入；保留操作锁、fence、CAS、attempt 绑定和中断恢复。
受管任务通过 JSON 任务卡注册；交付按卡检查路径、完成条件与提交尾注，
通过后以 CAS 推进项目工作分支。普通会话的 `attach --instructions` 仍是提示文本，
不参与受管任务注册。
旧 HTTP 转接经本次对话确认后删除；本入口只接受本地门禁命令。

## 任务卡与交付

使用同一个 CLI 生成模板，填写目标、非目标、路径、argv 完成条件等字段后校验并保存：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state daemon_start
node workbench/src/gates/cli.ts --state /绝对路径/state card_template --task T-080-1 --repo /绝对路径/repo --ticket /绝对路径/T-080.md
node workbench/src/gates/cli.ts --state /绝对路径/state card_validate --task T-080-1 --card /绝对路径/card.json
node workbench/src/gates/cli.ts --state /绝对路径/state card_save --task T-080-1 --card /绝对路径/card.json --expected-version 0
node workbench/src/gates/cli.ts --state /绝对路径/state create --task T-080-1 --repo /绝对路径/repo --branch refs/heads/main --card-version 1
```

模板含 13 个字段。CLI 值精确为 `Claude Code` 或 `Codex`；任务类型为规格中的八个值。
完成条件格式为 `{"argv":["python3","acceptance/check.py","{worktree}"]}`，
`{worktree}` 只能占据完整的一个参数，在独立 M worktree 中运行。完成条件非零退出仍
返回 `oracle_failed`，这个名字只为保持已有公开错误预期，不存在旧 oracle 注册入口。
create 不再接受 `--base`、`--oracle` 或 `--instructions`。

版本与快照存入同一 SQLite 库，旧记录不修改；`card_show --card-version N` 读指定版本。
注册冻结选定版本，认领时再追加包含当时工作分支起点和唯一写入者的绑定快照。
源文件或后续卡版本不会改变已注册合同。显式采用新卡用
`revise --spec-rev N --card-version V`，会使旧 attempt 与候选失效。

路径用仓库相对文件名、末尾 `/` 的目录或 `.`，禁止项优先，不解释 glob。
门禁检查候选相对起点的净改动，以及 M 相对 G 的净改动。
尾注归属按 Task、Attempt、Session、Role 四项核对；外来任务或坏尾注被拒。
完全无 A2A 尾注的提交产生来源为“推断：缺尾注”的 action 用户输入和派生人工介入，
不阻止集成，同 attempt 同 commit 重验不重复记录。

工作分支必须是已存在的 `refs/heads/*`。门禁不再读写 `refs/a2a/integration`，历史引用保留。
Git 事务先锁住 G，在实际检出目录用双树快进保护本地修改，再 CAS 到 M；覆盖型修改被拒，
无冲突修改保留。未知副作用保留原 integration intent 待核对。没有 push、stash 或用户目录 reset。
验收仍由 verify 完成，integrate 只接受与该 attempt、卡快照和候选绑定的通过记录。

## 安装

```sh
cd workbench
python3 -c 'import os; assert os.path.ismount("/Volumes/WD-Elements"), "外置盘未挂载"'
electron_config_cache=/Volumes/WD-Elements/a2a-electron-cache npm ci --cache /Volumes/WD-Elements/a2a-t075-npm-cache
npm ls --depth=0
```

缓存由本目录 `.npmrc` 指向外置盘；安装前检查挂载与缓存位置，失败就退出。
`node_modules` 是本目录中的普通目录。依赖锁定 `effect@4.0.0-beta.25`；来源预览包
改为 npm 官方包是执行主控的决定，记录见本批证据 `controller-decision-01.md`。

另锁定官方 `node-pty@1.1.0`。本次 darwin-arm64 预编译包使用 `--ignore-scripts` 安装时，
`prebuilds/darwin-arm64/spawn-helper` 曾缺执行位，已由执行主控手工改为 755。
后台启动核对 node-pty 实际选择的 helper 是否可执行；失败直接报错，不自动 chmod 或重装。

## 运行时边界

`GateRuntime` 由 `panes.ts` 实现一个 Codex worker 窗格；没有 Claude 或普通 attach
会话。生产 CLI 没有直接开库的运行时替代入口。
旧 `native-runtime.ts` 是隔离测试边界；它的旧证据不能证明新后台或真实窗格可用。

真实启动需在 `daemon_start --launch-config /绝对路径/launch.json` 中给出固定 Codex
路径、隔离 `codex_home`、角色卡及版本、代码版本、hook 授权引用和回合上限。
`dispatch --runtime-mode workspace-write` 始终启动交互 zsh 中的 Codex：`-a never`、
workspace-write、任务卡指定的 gpt-6-astra 或 gpt-6.1-sol、xhigh、Fast 请求、关闭更新检查。
网络及托管网络代理关闭，不设置 socket 放行名单。三个 hook 向同一 CLI 的 `signal`
送原始 stdin；Stop 另外读取显式请求文件。启动参数、环境白名单、请求模型与实际回合模型分开记录。

初态为“未知”。`pane_process_info --thread ID` 从 ps 核对前台领导进程；按本卡决定，
执行主控再用 `pane_release --thread ID --reason 原因` 首次放行，记 executor action，
不当作用户输入或人工介入。派发先登记、空闲时 bracketed paste 后单独 CR；CR 写出即忙，
只有匹配主回合的 Stop 才返回空闲。不读屏，Esc 或缺 Stop 不自动放行。
本卡暂只提供首次 release，后续人工输入与中断放行尚未完成，见证据目录 RESULTS。

`daemon.ts` 导出 `serve(root, config, createGates?)`。第三个参数只供测试在代码里注入门禁对象（受控线程运行时或变异体），默认是 `new A2AGates(root, panes)`。产品的 `daemon_start` 不传这个参数，CLI 和环境变量也都没有对应的开关。交付 8、恢复 9、编排 18 这三套旧场景，经 `workbench/tests/run_daemon_acceptance.py` 在本后台入口上运行（T-075-5）。这个运行器为每个测试在短路径上显式启动并停止一个隔离后台，不改 `acceptance/` 中的任何断言。

## 只读 Electron 窗口

窗口经同一个 Unix socket 查询后台，不加载 node-pty 或 SQLite。显示一个项目、任务、
窗格和门禁状态；终端网格固定为 160×45，只允许选择、复制和滚动。没有终端输入接口，
用户输入记录与 Esc 后人工放行属于 S4，设备查询应答仍由后台处理。

构建必须在外置盘真实挂载后进行，每次使用一个尚未存在的构建槽：

```sh
npm --prefix workbench run build -- --slot local-01
node workbench/app/start.mjs --build /Volumes/WD-Elements/a2a-workbench/local-01/dist --state /绝对路径/state --task 任务编号 --user-data /绝对路径/ui
```

缓存、构建临时目录和 dist 都在外置盘；没有内置盘回退。`A2A_BUILD_VOLUME` 可指定
验收用的检查路径，普通目录和符号链接不能通过挂载检查。已有构建槽不会覆盖；不要在
输出目录中放源码或依赖链接。启动只读取已有构建产物，不自动构建、装包或启动后台。

默认后台目录为 `~/Library/Application Support/a2a-orchestrator`，默认 Electron 数据位于其
`ui/` 子目录。验证时同时显式指定后台与 UI 的 `/tmp` 隔离目录。

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state workbench_snapshot --task 任务编号
node workbench/src/gates/cli.ts --state /绝对路径/state pane_output --launch 启动记录号 --offset 0 --max-bytes 65536
```

`workbench_snapshot` 可加 `--launch` 查看本任务的历史窗格。窗口第一次选定 launch 后固定
该身份，不随 current_attempt 改变而切换。`pane_output` 返回 base64 原始字节和
start_offset、next_offset、total_bytes；每块最多 65536 字节，从同一追加 trace 读取。
新窗口从 0 补回，已有窗口收到 xterm 的解析完成回调才推进游标；缺失、缩短或错序
明确报错，不跳过字节。关掉 Electron 只断开视图，后台和窗格由独立进程托管。

后台重启会追加 `pane_recovered`，原窗格只作历史查询，不重建 PTY、令牌、队列或
worker。已有 pane_exit 可证明停止时执行显示“已中断”；没有结束证据显示“未知”。
窗格退出回调会最后增量读取已绑定的原生会话文件，再记录 pane_exit；主动停止和后台
停止也经过这条路径，不依赖 Stop hook。完整记录追加进库和 native.jsonl；文件缺失、
截断、解析失败或未完成的一行记为 native_final_read_failed，保留读到的位置，窗格
仍显示未知／中断，不补造完成事件。停止后的查询不继续采集新的原生字节。
测试的最终 SQLite 读回统一使用 `fixture_artifacts.archive_stopped_database`：确认 writer 退出，
复制主库与残留 WAL，只在归档副本上改为独立 DELETE 文件，再以只读方式检查。
`test_probe_cleanup.py` 检查关闭后的 WAL、未遗漏的已提交行、原文件保留和未确认退出时保留现场；
`test_stopped_readback.py` 重放三个停止后直读原库失败的夹具。
门禁状态原值保留，因此“门禁已认领”和“执行已中断”可以同时出现。原 verify/integrate
命令显式重放才执行恢复，启动或读取窗口不能把未知结果改成通过。
崩溃残留的 socket/PID 文件阻止启动；产品不会按 PID 猜测所有者并自动接管。

默认产品路径为 `~/Library/Application Support/a2a-orchestrator`；本卡测试只用显式
`--state /tmp/...`，不创建默认路径，不接触正式 `a2a-workbench` 目录。
新增 launch_records、dispatch_records、orchestration_events、relay_requests、relay_results
都在 state.sqlite3，触发器禁止
UPDATE/DELETE。按 T-075 rev 3，原门禁状态表保留为由事件推出的当前视图，历史以事件为准；
membership.sqlite3 和锁库保留。`stateConsistency.ts` 提供只读事件重建与逐表比较；
不补事件、改表或修存储。对静止的夹具库运行，报告一致、不一致或无法从现有事件重建：

```sh
node workbench/src/stateConsistency.ts --state /绝对路径/state --output /绝对路径/新报告.json
```

报告包含 tasks、历史 attempts/verifications、runs、attachments 与另库的 memberships/
session_presets，列出差异、缺历史来源和未覆盖表。attachment creating 缺事件、active 行与
attached 事件不同事务，以及成员/预设另库覆盖写都不能用最终行相等掩盖；诊断不一致或
不可重建返回 INCOMPLETE。两库分别有读事务，不宣称跨库同事务。

受管 worker 仍使用同一 CLI 显式 `submit`；`status`、`issue` 也走同一条转交路径。
CLI 将带 task、attempt、session、fence、spec_rev 的请求写入 `A2A_REQUEST_DIR`，返回
`queued=true, delivered=false`；这仅表示文件已落盘。每个 attempt 使用独立的
`/tmp/a2a-requests-*` 目录，位于 Git 工作树外，不污染候选提交。Stop hook 读取文件后，
经同一 CLI 向后台转交；没有文件就没有交付。后台仍检查当前 attempt、回合身份及原门禁条件。

请求用 `request_id` 去重：相同内容返回原结果，不重复执行；同一编号换内容明确拒绝。
身份不符、字段不完整及重复转交都有追加事件。旧 Stop 不消费尚未处理的请求，
处理结果未知时保留意图，不自动重试。一次 Stop 的新结果合成一条 `⟦门禁 #序号⟧`
回执，先登记，再在空闲窗格里 bracketed paste 并单独回车。回执会启动新的原生回合，
计入启动记录里的回合上限；本卡已获准一个交付回合和一个只确认回执的回合。
Git 尾注钩子从隔离 CODEX_HOME 中读取 CODEX_THREAD_ID 绑定的唯一根 CLI JSONL，
以最新 task_started 对应的 turn_context 取实际模型与强度；辅助会话不提供取值。
当前回合缺上下文时写 unknown，不沿用上一回合或请求值。启动请求另存
A2A_MODEL_REQUESTED/A2A_EFFORT_REQUESTED；实际沙箱读取与提交时序还须通过真实回合验收。

运行时 agent 身份与交付回合分开：attempt 绑定 launch/thread、shell、原生会话和 Codex 领导者；
首次输入前原生日志可以尚未出现，执行者核对有效前台领导者后通过 pane_release 放行首次派发；
门禁只补首次可观测的原生会话，不用请求值补身份。
run/reclaim 核对该身份，回执回合改变不会覆盖已提交的 turn_id。submit 仍要求当前活动
caller/turn 和受管 session/fence/spec/attempt 一致。换领导者、换原生会话或缺已绑定事实
拒收；停止后只沿用已核对的身份及确认的生命周期，不按新 PID 接管。

`run_daemon_acceptance.py --suite <coop|recovery|run> --output-root /绝对路径/证据根 --label 新标签`
可把本轮三套验收写到独立证据目录；默认输出根沿用原 T-075/card-5。旧 validation 模式
包含冻结的基线运行器，保留原输出根；新切片使用 suite/probe，不混写旧证据。

## 来源与改动

来源固定为 Synara 提交 `49cae984f22924de006e0f8358cb447eb881aaf6`。
迁入 `core`、`cli`、`membership`、`rolePermissions`；MIT 版权与完整许可保留在源码及
[LICENSE.synara](LICENSE.synara)。只提取门禁及其请求校验实际需要的 schema、类型与依赖，
其中模型选择的已有解码规则保持原样，不代表本工作台支持这些模型运行时。

进程执行直接使用 Node 的 `child_process.execFile`；本卡面向 macOS，不带原平台适配层。
本地 import 补 `.ts` 后缀，构造器参数属性展开为等价字段与赋值。
验收入口只调用本仓库门禁；旧 fork 的实现不再由这些入口加载。

重现命令与完整证据见
[T-075-1 迁移记录](../evidence/2026-10-10-batch12/T-075/RESULTS.md) 和
[T-075-2 当前结果](../evidence/2026-10-10-batch12/T-075/card-2/RESULTS.md)；
后台与 B 的进度见 [T-075-3 运行记录](../evidence/2026-10-10-batch12/T-075/card-3/RESULTS.md)。

只读窗口与重启查询见 [T-075-4 运行记录](../evidence/2026-10-10-batch12/T-075/card-4/RESULTS.md)。
界面迁入片段来自已推送的 `49cae984f22924de006e0f8358cb447eb881aaf6`：
`apps/web/src/components/TerminalScrollToBottom.tsx`、`apps/web/src/index.css` 与
`apps/web/src/theme/theme.seed.generated.ts`。保留 MIT 声明，未迁入 provider 或 MCP 网关。
