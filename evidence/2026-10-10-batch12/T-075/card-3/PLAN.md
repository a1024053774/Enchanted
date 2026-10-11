# T-075-3 实施计划（待执行主控确认）

日期：2026-10-11。任务：T-075，`ready_rev: 2`；派发：`⟦主控 #23⟧`；唯一写入者：`s12-t075-3`。

计划交付状态：**PASS**；实施状态：**INCOMPLETE**。本轮只读取材料、写计划与上报冲突；未启动后台、PTY 或真实 Codex，未运行验收，未提交代码。本文是本卡日期记录，不是新的规范源。

起点完整提交：`8071a4638f94c9465c939445624d61c9c4809561`。开工时 `git status --short` 已有 `evidence/2026-10-09-batch11/controller-poll.log` 修改，阅读期间另出现 `evidence/2026-10-10-batch12/controller-poll.log` 修改；两者均保留、不纳入本卡提交。实现获准后再次记录实际起点，不覆盖本次读到的起点。

## 1. 目标、边界与实施前的决定

目标：通过唯一后台 CLI，在 node-pty 托管的 zsh 里启动真实交互式 Codex；认领并派发夹具任务，由 worker 自己提交和调用后台 `submit`，再由执行侧调用 `verify`、`integrate`，使夹具工作分支从独立读回的 G 前进到 M。九项尾注、启动记录、派发登记、原始信号、门禁逐项结果和 Git 引用必须相互对应。

非目标：Electron、后台重启恢复、Claude、独立 reviewer 产品流程、红态/规则式检查产品流程、自动打回与评分、S3 worktree 命名清理与冲突回写、S4 主控/收件箱/唤醒。一次 fresh-context 代码审查是本卡交付检查，不等于实现 reviewer 产品流程。

修改只涉及 `workbench/`、本证据目录及 T-075 的 Resolution；不改 `acceptance/`、`scripts/`、spec、地图、术语表、fork 或全局配置。计划阶段也不改 ticket。所有产品验证显式指定 `/tmp` 下的新数据目录；不创建产品默认目录，不接触正式工作台数据。

**REALITY GATE: INCOMPLETE。** 方向已由任务卡确定；以下契约差异交执行主控处理，worker 不据此擅自改变验收。

1. **缺尾注的预期冲突。** [本卡](../../card-T-075-3.md)第 51、60 行把缺尾注列为应拒绝的反例；[spec 第 8 节](../../../../.project-map/specs/native-cli-orchestration-2026-10-10.md#8-追溯打分复盘与指标)、T-075-2 Resolution、`workbench/src/gates/core.ts:1268–1295` 与 `test_missing_trailer_records_one_inferred_action_and_integrates` 则规定：完全缺尾注记录 action 和人工介入，标“推断：缺尾注”，不阻止集成。建议保留已确认契约，把本卡这一项改为“正确记账且不得漏记”；若主控要求改为拒收，须先取得契约变更决定。待答复前不写这项的新预期，也不宣称所有反例可同时符合两个口径。
2. **当前存储不是单库、全追加。** `core.ts:126` 打开 `state.sqlite3`，`membership.ts:25` 另开 `membership.sqlite3`；`core.ts:976–994` 与 `membership.ts:38` 等更新当前状态。spec 第 9 节要求一个库、状态变化也是新记录。本计划建议在本卡接线时统一数据库所有权，并把涉及的状态变更存为追加版本；不做历史数据迁移。请主控确认这项修正归本卡，或给出明确的切片边界；不能把现有双库/覆盖更新写成已符合 spec。

确认计划不替代上述冲突的答复，也不替代后续沙箱外脚本交接。计划写完按本卡要求停止。

两项差异已按角色卡上报 blocking issue：`20261011T040449Z-worker:s12-t075-3-issue-001`。blocking 只指后续实现需要决定，本轮计划编写已完成。

## 2. 已核对的事实与材料

| 状态 | 事实 / 证据 | 对计划的影响 |
| --- | --- | --- |
| observed | Node `v26.5.0`；`workbench/package.json` 锁定 `effect@4.0.0-beta.25`、`node-pty@1.1.0` | 沿用类型剥离，不增加依赖或编译链 |
| observed | `A2AGates.call` 是现有门禁写入所有者；`GateRuntime` 已定义创建、启动、读取、停止、归档边界 | 窗格实现接入该边界，CLI 不再直接开库执行门禁 |
| observed | `acceptance/entry/a2a_gates.py` 只转发到 `workbench/src/gates/cli.ts` | 保留该 CLI 路径作为唯一客户端，不必修改这个转发器 |
| observed | `acceptance/entry/native-entry.ts` 是旧隔离运行时测试入口，直接构造核心或传入测试 runtime | 旧套件证据须与新后台入口证据分开；不将旧模拟运行时结果写成真实窗格通过 |
| observed | `core.ts:2260` 附近的交付提示仍要求 `a2a_submit MCP`，dispatch 记录还硬编码 `gpt-6.1-sol` | 接线时删除这些过时事实，交付提示写实际后台 CLI，模型取任务卡及启动记录 |
| observed | `node-pty/lib/unixTerminal.js` 从所选 native 目录找 `spawn-helper` | 启动前核对真实 helper 的执行位；失败直接报错，不 chmod、不自动安装 |
| measured（既有证据） | T-074 rev 4 的后台在 CR 写出时记忙，Stop 后放行；Esc 无 Stop，不自动放行 | 产品沿用该规则，旧实验不替代本卡新入口的验证 |
| observed | 会话开始、结束 hooks 的既有 argv 见 `T-074/rev4-codex/launch.json` | 沿用已经测过的会话级机制，具体 argv 在实施时冻结并由主控批准 |
| unknown | Codex 的 workspace-write 子命令能否访问新 Unix socket；Git hook 的调用环境能否同样访问 | 最高优先级真实探针；失败停止，不换 TCP、文件邮箱或放宽沙箱 |
| unknown | 新产品首次启动的可用信号、当前回合信息及 hook 环境是否满足初始化和尾注需要 | 不凭时间、屏幕或请求模型配置猜测；按第 7 节探针处理 |

已读：`AGENTS.md`、`CONTEXT.md`、`intent.md`、`MAP.md`、T-075 rev 2、T-074 rev 4；native-cli spec 第 1–6、8–9、12–13 节及 Test seam；现有门禁 CLI/core/membership、任务卡测试、`scripts/git-hooks/hook.py` 和 node-pty 本地源码/类型。session 开始地图检查为 **0 problems、0 stale，退出 0**。

## 3. 模块划分与门禁接线

遵循 **Tracer bullet**：先把“CLI → 后台 → 同一个库 → GateRuntime → PTY → hook/submit → 门禁 → Git”串成保留在生产路径的一条薄切片，再补反例。遵循 **Deep modules**：保留门禁核心和窗格宿主两个实质边界，不新造 provider、通用调度框架或一层一层的转发包装。遵循 **Ubiquitous language**：使用项目、任务、attempt、agent 会话、原生会话、启动记录和派发记录，不把窗格 idle 称为验收成功。

| 模块（拟定文件） | 责任 |
| --- | --- |
| `workbench/src/gates/cli.ts` | 唯一公开 CLI：解析原门禁命令及后台/窗格命令，连接后台，输出 JSON 与明确退出码；删除其独立开库执行的生产路径 |
| `workbench/src/daemon.ts` | 本地 Unix socket 服务、生命周期、请求分流、建立库与门禁实例、管理窗格宿主；不是另一个给 worker 使用的门禁入口 |
| `workbench/src/store.ts` | 单个 SQLite 连接的所有权、编排事件/启动记录/派发登记的追加写入与读取；门禁事件仍由门禁自己的语义入口产生 |
| `workbench/src/panes.ts` | node-pty、zsh/Codex 启动、进程身份、输入串行化、排队、结构化信号与状态；实现 `GateRuntime` |
| `workbench/src/gates/core.ts`、`membership.ts` | 接入宿主与单库，更新实际交付命令和模型记录；保持操作锁、fence、CAS、规格及 attempt 绑定；存储变更以第 1 节答复为准 |
| `workbench/hooks/` | 每会话 signal 发送器、Git 钩子；只经同一 CLI 访问后台，不直接写 SQLite，不使用 `records/launches.jsonl` |
| `workbench/tests/`、`workbench/README.md` | 新后台入口端到端场景、探针与运行说明；说明 helper 执行位、隔离目录、状态未知、入口和证据界限 |

拟保留 `--state ABS_DIR` 参数，作为后台数据目录。新增命令使用现有下划线命名，例如 `daemon_start`、`daemon_status`、`daemon_stop`、`pane_status`、`pane_dispatch`、`pane_input`、`pane_release`、`signal`、`launch_show`；任务命令保留 `card_* / create / dispatch / claim / submit / verify / integrate / events / reclaim`。受管真实路径用 `dispatch` 完成认领和创建 worker 窗格；纯脚本反例用 `claim`。所有写窗格行为均在后台，客户端不能拿 PTY 句柄。

旧隔离测试入口不扩成第二个产品入口；测试 runtime 仅作为测试依赖。实施时若旧测试必须改 `acceptance/` 才能连接新边界，保存具体失败并交主控决定，不修改断言、不保留 CLI 的本地开库后门来让旧测试通过。

## 4. 进程模型、IPC 与目录

`daemon_start` 用 Node `spawn` 启动后台，设置 `detached: true`，stdio 指向独立日志文件，后台不继承调用者的管道，启动侧在取得有期限的 ready 握手后 `unref` 并退出。记录调用者与后台的 PID/PPID/PGID/SID、启动 argv 和时间。另起一个检查进程，在启动命令已经结束后通过 `ps` 和 `daemon_status` 读回身份与存活状态，不能只相信 detached 配置。macOS `ps` 的会话字段按本机实际支持项记录；字段名如为 `sess`，明确它与 SID 的对应，不能冒充已读到不存在的字段。

后台缺失时普通客户端明确失败；不在每次命令中隐式拉起后台，不重放结果未知的请求。已存在且身份不明的 socket/PID 文件不删除、不接管。后台重启后的恢复留给 T-075-4；本卡不会从旧状态恢复一个新 worker。

IPC：`node:net` Unix domain socket，JSON 请求/响应，带请求号和绑定的 task/attempt/session/fence/spec 版本。目录权限 0700、socket 限当前用户。受管 worker 的请求还绑定其启动记录与窗格身份；不能仅因请求自称 executor 就获得集成权限。不记录凭据或会话访问密钥。先验证 socket 路径长度、创建/连接权限及子进程环境，不提供备用传输。

请求处理不能把整个后台锁到一个长回合结束：门禁操作保留现有操作锁；hook 事件、只读查询和正在执行的 worker 的 submit 必须能被处理。SQLite 事务只覆盖同步落库，不跨 PTY、完成条件命令或网络等待。自动 `run` 若接入，必须显式给 `--wait-seconds`，后续验收/集成/回收固定原 attempt；本卡主正例优先分步命令，便于保留每一步证据。

产品默认目录为 `~/Library/Application Support/a2a-orchestrator`。验证目录示意：

```text
/tmp/a2a-t0753-<独立标签>/
  fixture/                     # 新建夹具 Git 仓库
  state/
    state.sqlite3              # 唯一业务库；WAL/SHM 是它的伴随文件
    control.sock
    daemon.pid                 # 临时进程定位；身份还须独立核对
    daemon.stdout.log
    daemon.stderr.log
    worktrees/<attempt>/       # 沿用现有门禁目录，不实现 S3 清理
    verification/<id>/
    traces/<launch>/           # 本卡所需原始 PTY/原生记录；不含凭据
  codex-home/                  # 隔离 home，验收后整个删除，不打包
```

`state/` 不是第二个仓库。夹具及 worktree 原样留在 `/tmp`，归档时保留 Git 元数据到 tar，仓库里只提交证据文件和归档，不登记内嵌 gitlink。产品默认目录和正式 `a2a-workbench` 目录均不探测、不创建。

## 5. 库表与追加记录

不另建 JSONL 业务事实源，也不把运行事件放到 Herdr 期的 `records/`。计划新增的表均用触发器拒绝 UPDATE/DELETE；事件中的状态改变以新行表达。

| 表 | 最小字段及约束 |
| --- | --- |
| `launch_records` | `launch_id` 主键；时间、project/task/attempt/session/fence/spec_rev、CLI 路径与版本、请求模型/强度/tier、完整 argv、`-c` 配置内容、角色卡路径与代码版本、项目起点、worktree、shell argv、获准的环境字段。记录先落库再 spawn；实际 PID、原生会话和启动失败另追加事件 |
| `dispatch_records` | 单调序号、请求号、标记、来源 executor、project/task/attempt/session/launch、完整角色卡和任务卡文本、原文编码、登记时间；文本在任何 PTY 字节前提交到库 |
| `orchestration_events` | 单调序号、事件类型、接收时间、原生时间（若有）、project/task/attempt/session/launch/dispatch 关联、原始 payload、观察来源。全局后台事件允许无 task，不伪造任务身份 |
| 现有 `events`、任务卡版本/快照、`user_inputs` | 保留已验收字段与语义，读回时连到新启动/派发记录；机械检查不能只保留最终 pass/fail |
| 状态版本表（待第 1 节确认） | task/attempt/verification/run/membership/preset 等按对象 ID 与版本追加；读取最新版本，CAS 与唯一写入所有权仍由原核心负责；不以覆盖当前行代替状态历史 |

每次拒收追加原始请求的可公开字段、明确错误和当时绑定；错误不能只出现在 stderr。必须覆盖：后台与窗格启动/失败/退出，worktree 创建与残留，派发登记/排队/写入/结果未知，CR 提交、开始/结束/权限等待信号，手工输入/action 与人工介入，身份和规格检查、路径检查、每条完成条件、尾注检查、提交文件数与增删行数、验收与 CAS 结果。

本卡未实现的审查/评分/面板/复盘不造空白通过记录；报告标“本卡非目标”。PTY 原始字节可作为轨迹文件，库里保存其索引和来源；不能以磁盘日志代替应入库的启动、派发或信号事件。不计算无实际用途的 hash/fingerprint。

## 6. 窗格、参数、环境和尾注

后台使用 node-pty 启动 `/bin/zsh` 交互终端，在该 shell 内启动 Codex；Codex 退出后保留 zsh。使用 argv 和严谨的 shell 参数引用，任务正文不拼成 shell 命令。记录 shell PID、Codex 领导进程与原生会话；同组工具子进程不能被认成领导者替换。

Codex 固定本机待核对的 CLI 版本（T-074 实测为 0.162.1），冻结可执行路径及 `--version` 输出。若版本不符先报告，不能自动更新或用 Enter 回答更新提示。所需参数：

```text
codex -a never --sandbox workspace-write
  -m gpt-6-astra
  -c model_reasoning_effort="xhigh"
  -c service_tier="fast"
  -c check_for_update_on_startup=false
  -c <本会话 UserPromptSubmit / Stop 信号配置>
```

结束信号计划选择 T-074 已测的 Stop hook；开始 hook 只采集，不作解锁依据。PermissionRequest 若装，只作原始事件采集；`-a never` 下出现意外权限交互即停止。具体 hook argv/配置在沙箱外脚本前给主控审阅，逐次批准后才安装；不同时用两个结束源竞争解锁。若改选 `notify`，必须先证明主 turn 与辅助完成通知能正确区分，不凭通知数量当回合数。

显式传给受管进程的环境至少包括：`A2A_PROJECT`、`A2A_TASK`、`A2A_ATTEMPT`、`A2A_SESSION`、`A2A_ROLE=worker`、`A2A_LAUNCH`，以及后台目录/入口、fence/spec 绑定；隔离 `CODEX_HOME`、必要 PATH/终端信息。Git 配置只通过该会话的 `GIT_CONFIG_COUNT=1`、`GIT_CONFIG_KEY_0=core.hooksPath`、`GIT_CONFIG_VALUE_0=<workbench 钩子目录>` 注入。清除继承的上层 `A2A_*`、`GIT_CONFIG_*` 和原生会话身份后建立本 attempt 的环境，不把主控的身份写进 worker 提交。

钩子向后台取得当前启动/回合事实，用 `git interpret-trailers` 追加且只保留一组：

`A2A-Task`、`A2A-Attempt`、`A2A-Session`、`A2A-Role`、`A2A-Tool`、`A2A-Model`、`A2A-Effort`、`A2A-Native-Session`、`A2A-Launch`。

原生会话优先核对工具进程提供的 `CODEX_THREAD_ID` 与已绑定的主会话；最近回合模型/强度从该主会话的结构化记录采集。取不到模型时按 spec 写 `unknown`，不把启动时请求值当实际值；Fast 只报告请求配置，不能宣称供应商实际 tier。钩子不直写库，不修改 Git config；若仓库已有钩子，保留它的调用与失败语义，避免因指定 hooksPath 悄悄绕过。先做小夹具验证，不在用户仓库实验。

README 写明：本次 node-pty 使用官方 1.1.0 darwin-arm64 预编译；`--ignore-scripts` 安装后 helper 曾缺执行位，执行主控已手动补为 755。后台启动检查选中的 helper 存在且可执行，不可执行立即失败并指明路径，不自行修复。需要新依赖时先停下；任何安装/构建必须核对 `/Volumes/WD-Elements` 真正挂载，不能回退内置盘缓存。

## 7. 派发、状态与最小探针

派发登记分配序号，组装 `⟦主控 #序号⟧`、角色卡、绑定后的任务卡、完整身份和准确的后台 `submit` 命令。登记成功才进入队列。窗格空闲时只允许一个 writer：先写 `ESC[200~ + 正文 + ESC[201~`，再单独写 CR；沿用 T-074 的分离时序并实测。CR 写出前在同一串行写入段锁成忙，持久化写入意图，写后追加结果；中途失败保留“未知”，不自动补 CR、不重投。

来源由实际入口决定：自动派发不记为用户输入；用户亲手输入和用户放行分别记 message/action，落入受管 attempt 则记录人工介入。测试模拟输入标 `simulated`，不伪称用户本人。只有新的、属于当前 launch/主原生会话、对应未结束提交的 Stop 才能将忙变为空闲；辅助会话、重复或过时事件只记录，不能放队列。开始 hook 可能延迟、重复，只作记录。Esc、断连和缺失 Stop 不推断空闲。状态只呈现有证据的空闲/忙/未知，CLI 退出与“交付已集成”分开。

首次启动状态是未知，不因 spawn 成功、定时等待或终端出现提示符就标空闲。探针核对本版本是否有足够的结构化初始化事实；若没有，按已定“用户放行”语义由执行主控协调明确操作并记录，不能脚本伪造 Stop 或静默初始化为空闲。无法在授权方式下完成首次派发则停下交 needs-decision。

所有探针均在计划获准后执行，负责人为本 worker，沙箱外运行者为执行主控，证据使用本目录的新标签：

| 探针 | 输入与方法 | 通过 / 失败、停止条件 | 证据标签 |
| --- | --- | --- | --- |
| P0：IPC 与启动前置 | 新 `/tmp` 目录，检查 Node/CLI/helper；后台创建 socket；调用者退出后独立读回 ps 与 ping | backend 存活且 PGID/SID 脱离；缺执行位、绑定失败、身份不明直接失败，不修权限/不接管 | `probe-host-01/` |
| P1：真实沙箱可达性 | 在规定 argv 的真实 PTY Codex 主 turn 中，要求用普通沙箱工具执行后台只读 probe/status 命令，并执行一次带随机 challenge 的事件回送；同时核对 Git hook 所需环境 | native 工具记录显示命令未升级权限，返回 challenge 与后台入库对应；连接 EPERM、缺能力或须扩大权限即停止，不改传输/沙箱 | `probe-sandbox-01/` |
| P2：初始化与信号 | 同一真实会话核对首次派发前的状态依据；记录开始、Stop、主原生会话、最近回合模型；从库读回 | 正常结束回到空闲，主/辅助区分成立；初始化无依据、信号歧义、不问模式出现批准即停止 | 与 P1 共用真实回合，分文件保存 |
| P3：Git hook | 可达性确认后，真实交付回合实际 `git add`、`git commit`；库与 Git 直接读回九项尾注 | hook 能通过入口读取本 attempt 事实，原生身份一致；失败保留现场，不能手填尾注冒充自动生成 | `real-delivery-01/` |

P1 的 challenge 是传输配对值，不是测试从实现结果生成答案。P1 未通过前，只允许准备最小生产连接与宿主薄片，不铺开完整编排功能。真正的 sandbox 拒绝不是探针程序错误；只允许修复脚本自己的缺陷，说明原因、保留旧标签、换新标签重跑。

## 8. 红态、端到端正例与反例

所有预期先由任务卡/spec 和本节冻结；正反例都从 `node workbench/src/gates/cli.ts --state <独立目录> ...` 发起。读 SQLite/Git/ps 作为独立 oracle，不绕门禁写任务状态。计划中的测试文件尚未创建。

红态拟命令：

```sh
python3 workbench/tests/test_orchestrator_e2e.py --case real-delivery --source-rev 8071a4638f94c9465c939445624d61c9c4809561 --label red-parent-01
```

实现时先写 driver，再将同一 driver 指向保留的起点源码运行。必须因 `daemon_start`/窗格命令不存在而失败；不能把“测试文件不存在”“依赖没装”当业务红态。父版本红态不启动真实模型。绿态使用同一场景与断言，指向冻结候选；保存 exact argv、cwd、环境白名单、stdout/stderr、退出码和归档路径。

真实正例采用中等复杂度夹具：worker 在允许的两个源码文件中实现有正常/边界输入的确定性转换；独立完成条件及固定预期在派发前写好，worker 不能改。认领后的基线记 B；执行侧用脚本在工作分支做一个不冲突提交形成 G，再让 worker 交付 C，迫使门禁验证非平凡的合并 M。`git rev-parse refs/heads/main` 在 verify 前读 G，integrate 后读 M，并用 Git 检查父提交、文件内容与九项尾注；这些独立值与库内 verification/integrated 事件比对，不从事件反推预期。

完整顺序：`daemon_start → card_save → create → dispatch（含 claim/启动/登记/注入）→ worker 修改/commit/submit → verify → integrate → events/launch_show/pane_status → 独立 Git/SQLite/ps 读回`。只有确认 worker 已空闲且交付已提交后，才允许经门禁回收自己创建的窗格；不实现 S3 worktree 清理。若 submit 已落地但 worker 仍忙，继续等结构化结束信号，不提前关 pane。

| 场景 | 独立预期与保留证据 |
| --- | --- |
| 越界文件，含禁止目录、重命名两端、删除、空格文件名 | verify 拒收并记录 path_check；工作分支不动 |
| 两条完成条件中第二条失败 | 明确记录每条结果，第二条失败导致拒收；不得借用第一条结果；目标分支不动 |
| 候选中间提交带外来 Task 尾注 | 即使末端提交正确仍拒收，指出真实坏提交和 trailer_check |
| 部分缺项、重复尾注、旧 attempt/session 尾注 | 坏尾注或身份不匹配拒收，不与“完全无尾注”混淆 |
| 完全缺尾注 | **等待第 1 节决定**。现行契约的预期是唯一 action＋人工介入，重验不重复，允许集成；若改成拒收，先更新授权与验收依据 |
| 过期 fence、撤销后旧 attempt、过期 spec | 分别拒收并留事件，不改变新 attempt，也不把旧事件绑定到 current_attempt |
| 目标工作区有会被覆盖的 staged/unstaged/untracked 内容 | 拒收，逐字保留内容和 Git 状态，不 stash/reset |
| 验收后另一个写入者把 G 改为 X | CAS 拒收、不覆盖 X；保存 X 的独立 rev-parse 与拒收事件；本卡不自动重试 |
| 任务卡缺字段/非命令完成条件/版本过期 | 在后台入口拒收，注册快照不随源文件修改改变 |
| 同时请求写窗格、CR 后立即第二次派发 | 第二条排队；登记在前、字节在后；不依赖开始 hook 的到达 |
| 旧 Stop、辅助会话通知、无 Stop 的中断 | 不自动放行；需人工操作时留 action 及介入来源 |
| helper 不可执行、库追加写失败 | 启动或派发失败，未落登记不得写 PTY；仅在自建夹具模拟，不改已装依赖 |
| 追加式表 UPDATE/DELETE 尝试 | 隔离库中失败，原始行完整；不在产品库做破坏性探针 |

重跑 T-075-2 的任务卡正反例行为（现有 14 项）、CAS 竞争和双完成条件检查，入口必须为后台客户端。旧交付/恢复/编排 8/9/18 套件可作为相关核心回归，但不把其中的模拟运行时当新后台验收；后台重启恢复不在本卡声明通过。按实际接线影响确定运行清单，不以改断言消除失败。

新验收要至少在起点失败，并用已知坏变异体验证关键断言：移除登记先于注入、放过旧 fence 或移除 CAS 期望旧值，应各导致业务断言失败。变异只在隔离候选副本里做，不覆盖共享工作树或红态记录。

## 9. 真实模型预算与沙箱外清单

本轮计划已用真实 Codex 主 turn：**0**。本卡被测 Codex 全部会话累计硬上限 **10**，重跑不重置计数。目标用 2–4 个：

| 用途 | 预算 |
| --- | --- |
| 沙箱可达性、初始化、结构化开始/结束 | 1–2 个 |
| 实际夹具实现、自动尾注与 worker 自己 submit | 1–2 个 |
| 探针脚本修正后的必要复验、可说明原因的补充 | 最多 6 个余额；不是自动重试配额 |

每次注入前查持久化预算账；按原生主会话输入/turn 核对，辅助标题/子会话通知另列。没有原生记录的已提交请求保守占一个名额。第 10 个主 turn 后停止新增输入并报告；运行失败不自动追加 turn。固定 `gpt-6-astra`、xhigh、Fast 请求。fresh-context 只读审查也有额度成本，单独记账；若需额外真实 CLI 会话启动，由主控按同一沙箱外交接批准，不以“审查”名义暗中扩大本卡被测预算。

待计划与冲突答复后，再写 `card-3/outside-sandbox.sh`，按阶段参数运行，每次输出新标签目录：

1. 前置检查、全新 `/tmp` 夹具/数据目录、冻结 Node/Codex/helper 版本与权限、后台 socket/脱离进程组测试。
2. 隔离 Codex home：只复制 `auth.json`，写仅信任实际夹具根目录的配置，只加入 `git add`、`git commit` 两条 allow prefix_rule；每会话 hook 配置先经主控批准。不要输出 auth 内容、复制整个用户配置或增加可写目录来替代 Git 规则。
3. node-pty/zsh/真实 Codex 启动、P1/P2 沙箱探针；未通过即结束该阶段，不继续真实交付。
4. 后台 CLI 的脚本反例、真实交付、独立读回；受沙箱限制的 Git worktree/引用事务和已有隔离套件一并列出精确命令。
5. 核对并只停止本次启动的后台/窗格；不自动杀同名进程；归档不含凭据的证据，删除本次创建的整个 Codex home，保留失败夹具和运行记录。

此 worker 不自行申请扩大沙箱执行这些项。脚本准备后只回 `T-075 OUTSIDE-SANDBOX READY` 并停止，由主控执行。主控执行脚本时发生的批准、放行和人工干预须保留来源，不计成自主能力。

## 10. 检查、审查与后续交付

实现前先读 `evidence-first-testing`；冻结候选后只做一次 fresh-context、只读独立审查，按 `behavioral-acceptance-review` 检查独立 oracle、已知坏实现与产品行为。结构风险如属于同一次检查，合并进该审查，不另外开第二个 reviewer。审查发现问题先复现红态再修复，修复 diff 交执行主控，不自行追加追审。

中文 `RESULTS.md` 将逐项记录 PASS/INCOMPLETE/BLOCKED/NO_GO、task/attempt/session/fence/spec/完整代码版本、argv 与原生证据、正反例、真实 turn 数、沙箱外执行者、未知和跳过项；每项产物附可重现命令。最后只提交本人文件及 T-075 Resolution，保留 open，写“T-075-3 完成，待后续卡，待主控关闭”；提交带当前 worker 的九项尾注，不借用夹具 worker 身份。

若修改门禁触发 living doc stale，更新范围内的 `workbench/README.md`；地图 Verified 或术语表需主控处理，不越界修改，未解决不得报告整卡 PASS。交付前重跑并保存：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

本轮交接：PLAN.md 已形成，尚无实施授权确认、探针结果或产品验收结论；按 `⟦主控 #23⟧` 的“先交计划，停下等我”停止。
