# a2a 门禁与编排后台（T-075-3）

用 Node 26.5 及其原生 TypeScript 类型剥离直接运行，无 Bun、打包或编译步骤：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/隔离状态目录 status --task 任务编号
```

先对同一隔离目录调用 `daemon_start`，结束时调用 `daemon_stop`。客户端只通过
`control.sock` 访问常驻后台，不再直接打开门禁库。后台未启动时命令明确失败，不自动拉起或重试。
`daemon_start` 使用 detached 子进程和独立日志。
后台常驻与一次真实窗格派发已验证；工具沙箱的 socket 连接曾被 EPERM 拒绝。
T-075 rev 4 的 A2 探针在工具层被拒，未验证成；按用户决定改用 B 文件转交。
B 已通过隔离真实 Codex 的显式交付、机械检查与 CAS 集成；本卡一次独立审查 PASS。
该结论限本地夹具，不包含 Electron、后台重启恢复或完整工作台切换。

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
npm ci --cache /Volumes/WD-Elements/a2a-t075-npm-cache
npm ls --depth=0
```

缓存由本目录 `.npmrc` 指向外置盘；安装前检查挂载与缓存位置，失败就退出。
`node_modules` 是本目录中的普通目录。依赖锁定 `effect@4.0.0-beta.25`；来源预览包
改为 npm 官方包是执行主控的决定，记录见本批证据 `controller-decision-01.md`。

另锁定官方 `node-pty@1.1.0`。本次 darwin-arm64 预编译包使用 `--ignore-scripts` 安装时，
`prebuilds/darwin-arm64/spawn-helper` 曾缺执行位，已由执行主控手工改为 755。
后台启动核对 node-pty 实际选择的 helper 是否可执行；失败直接报错，不自动 chmod 或重装。

## 运行时边界

`GateRuntime` 由 `panes.ts` 实现一个 Codex worker 窗格；本卡没有 Claude、普通 attach
会话、Electron 或后台重启恢复。生产 CLI 没有直接开库的运行时替代入口。
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

默认产品路径为 `~/Library/Application Support/a2a-orchestrator`；本卡测试只用显式
`--state /tmp/...`，不创建默认路径，不接触正式 `a2a-workbench` 目录。
新增 launch_records、dispatch_records、orchestration_events、relay_requests、relay_results
都在 state.sqlite3，触发器禁止
UPDATE/DELETE。按 T-075 rev 3，原门禁状态表保留为由事件推出的当前视图，历史以事件为准；
membership.sqlite3 和锁库保留。事件重建与视图一致性验证留给后续切片，本卡不迁移存储。

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
Git 尾注钩子当前只读会话环境；最近回合模型与强度取不到时写 unknown，不把启动请求当实际值。
本卡真实候选的这两项均为 unknown；原生记录另有实际回合模型与强度。后续需把已核对的
回合事实传给钩子；只预填启动记录的请求参数时，仍须标明其来源，不能冒充最近回合观测。

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
