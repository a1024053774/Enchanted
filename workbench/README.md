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
B 在 T-075 的旧候选上通过隔离真实 Codex 的显式交付、机械检查与 CAS 集成。
该结论不覆盖整个 T-076-2。质量串受控 Tracer bullet、加宽检查与 8/9/18 回归
已在各自冻结候选上通过；真实P-review02已证明只读沙箱拒绝写入及完整B结论通道，
真实worker首拒后自动修复、新只读审查、主控后填分及唯一集成已在隔离real-delivery-02完成；
本卡独立交付审查为PASS / LIMITED_GO，仅覆盖隔离受管交付；
完整工作台尚未切换，T-076保持open，待主控关闭。

受管派发提示要求 `git add <路径>` 与 `git commit …` 各自独立执行，
检查命令另行运行，以便两个已授权的 Git 前缀规则分别匹配。
若独立命令仍被拒，worker 上报并结束，不自行重试或调整沙箱。

`acceptance/entry/a2a_gates.py` 将参数原样交给这里的 CLI。门禁核心仍由后台中的
`A2AGates.call` 独占写入；保留操作锁、fence、CAS、attempt 绑定和中断恢复。
受管任务通过 JSON 任务卡注册；交付按卡检查路径、完成条件与提交尾注，
机械通过后新开只读 reviewer，有效“可合并”结论到达后由执行主控带评分集成。
普通会话的 `attach --instructions` 仍是提示文本，
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

非空 `red_commands` 每项必须显式给出 `test_paths`，例如
`{"argv":["python3","tests/check.py"],"test_paths":["tests/check.py"]}`。
只接受相对起点新增或修改的普通文件；拒绝路径越界、Git元数据、目录、重复项与symlink。
门禁为每项建独立B/C目录，只把声明的候选测试文件放到B上，同命令要求B正常退出且非零、C退出0。
无法启动、超时或未知退出不算红态；非零是否来自有效业务断言，由独立审查判断，不解析stderr关键词。
M验收目录独立，顺序为路径、完成条件、红态、项目规则、尾注、独立审查。

项目规则从注册时工作分支提交中的 `.a2a/quality.json` 冻结：

```json
{"schema":1,"rule_checks":[{"id":"lint","argv":["npm","run","lint"]}]}
```

缺文件明确记录未配置；损坏配置拒绝注册。规则在M执行，候选改写或删除配置不会改变本任务的冻结规则。

版本与快照存入同一 SQLite 库，旧记录不修改；`card_show --card-version N` 读指定版本。
注册冻结选定版本，认领时再追加包含当时工作分支起点和唯一写入者的绑定快照。
源文件或后续卡版本不会改变已注册合同。显式采用新卡用
`revise --spec-rev N --card-version V`，会使旧 attempt 与候选失效。

路径用仓库相对文件名、末尾 `/` 的目录或 `.`，禁止项优先，不解释 glob。
认领会比较同一 Git 仓库中活跃 attempt 的允许路径集合，并扣除双方禁止路径；
未创建的文件也参与判断。交集默认返回 `path_overlap`。执行主控确需并行时，
在 `claim`、`dispatch` 或 `run` 上显式加 `--overlap-reason '具体理由'`，
理由、冲突身份和路径一起保存到 `claim_path_check` 事件；worker 的转交通道不增加认领权限。
门禁检查候选相对起点的净改动，以及 M 相对 G 的净改动。
尾注归属按 Task、Attempt、Session、Role 四项核对；外来任务或坏尾注被拒。
完全无 A2A 尾注的提交产生来源为“推断：缺尾注”的 action 用户输入和派生人工介入，
不阻止集成，同 attempt 同 commit 重验不重复记录。

工作分支必须是已存在的 `refs/heads/*`。门禁不再读写 `refs/a2a/integration`，历史引用保留。
Git 事务先锁住 G，在实际检出目录用双树快进保护本地修改，再 CAS 到 M；覆盖型修改被拒，
无冲突修改保留。未知副作用保留原 integration intent 待核对。没有 push、stash 或用户目录 reset。
`verify` 机械完成返回的 task 状态为 `reviewing`；只有独立审查结论通过才为 `verified`。
`integrate` 只接受与该 attempt、卡快照和候选绑定的审查通过记录及执行主控评分。

## 质量串候选（T-076-2，尚未验收）

首轮交付被路径、完成条件、尾注或独立审查打回后，门禁保存失败，再登记
`⟦门禁 #序号⟧` 修复消息；空闲时由原队列注入。只有明确打回授权后，原 attempt 的
同一原生会话才能从新回合重交新 C；没有打回时仍不能换候选。同 attempt 第三次打回
保存 issue 并暂停，不再注入修复消息。消息与 ACK 都不计为人工介入。

机械通过后，后台为 C 创建 detached 审查目录和独立 thread/session/launch，
不续接旧原生会话。`daemon_start --launch-config` 的 `reviewers` 数组按启动次序提供
每个已批准 reviewer 的 `codex_home`、`role_card`、`role_card_revision`、`hook_authorization`。
每项 home 必须独立、没有已有原生会话记录；没有该实例配置就明确拒绝，不沿用 worker home。
reviewer 用 `--sandbox read-only -a never`，不安装 Git 尾注 hook、不增加可写目录，
会话 hook 仍只经启动 argv 传入。P-review02已用真实read-only reviewer的单次sentinel写入拒绝
证明该实例的权限效果；完整结论经Stop/B入库，证据见本卡outside-p-review-02。

按用户2026-10-13的决定，Codex会话使用gpt-6.1-sol、xhigh及普通速度，
worker/reviewer的argv显式传`-c service_tier="default"`，派发事件与启动记录写requested tier为`default`。
显式覆盖也用于隔离CODEX_HOME，用户全局priority设置保持不变。
记录仅表示请求设置，不代表供应商实际执行tier；其他沙箱、hook及身份检查不变。

reviewer 的最终消息必须是完整 `review_submit` JSON；身份和候选模板由门禁派发。
匹配 Stop 的后台 hook 处理器把显式 JSON 落入该 launch 专用请求文件，再经原 B relay
转交。程序不剥 Markdown fence、不抽取一段 JSON、不从自然语言猜结论。
非法结论保存原文、上报并暂停；有效结论只接受“可合并”加空清单，或“需修复”加位置、
失败场景、建议。结论绑定 C、合同和独立启动/原生身份。有效结果存库、reviewer idle 后回收，
不另开纯 ACK 回合。审查目录按下述 S3 规则命名和清理。

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state integrate --task T-080-1 --attempt ATTEMPT --score-file /绝对路径/score.json
```

当前集成评分 JSON 为：

```json
{"result":"通过","boundary_discipline":3,"boundary_reason":"理由","engineering_taste":2,"engineering_reason":"理由","notes":""}
```

数值须为 0–3 整数，理由非空，notes 必须存在（可空）；缺项拒绝，不编造默认分数。
评分意图绑定 integration intent，Git 成功后最终 `score_recorded` 与集成状态同事务落库；
相同命令重放不再打分或改 Git，不同分数不能覆盖。schema=1 字段对齐 Herdr 打分格式，
事实由任务卡、交付回合和事件提取，不写真实 `records/scores.jsonl`。
交付缺当前回合的实际模型/强度时拒绝，不能沿用请求值或上一回合的值。

`abandon --task T --attempt A --score-file FILE` 终结原attempt，不执行Git集成。
放弃只传 `{"result":"放弃","reason":"理由"}`，不带分数/备注/评分facts；升级传与通过相同的两项评分及理由、notes，
把result改为“升级”。命令不自动启动更强执行器。无交付时从该worker启动记录和已观察回合取元数据，未观察到模型则如实记unknown；
没有可核对启动来源则拒收。终结与评分一起落库，重放不重计；pending integration intent须先核对，不能用放弃掩盖未知CAS。
终结不等于窗格已回收：只在idle后用原attempt的reclaim回收；未完成的reviewer会保留上报。

`scores_validate --file /绝对路径/scores.jsonl` 是只读格式校验，不导入、不双写Herdr文件。
接受schema=1的执行主控行和指向原分的独立用户行；缺必填项、非法评分/事实字段、重复attempt、错误来源绑定和不完整尾行拒收。

`run --wait-seconds N` 现在等待修复、审查和执行主控的显式集成命令，仍只绑定原 attempt。
它不会在机械通过后自动填分/集成，也不因第一次质量打回就回收 worker。修复或审查等待
到期时保留现场；收到最终集成后，确认原 worker idle 才回收并结束。

本候选只用于ticket隔离验证。红态/规则、终结评分、双向格式校验与CAS评分恢复已有受控正反例；
reviewer创建失败、后台重启时的未完成审查、退出未确认已有红态及暂停/上报后的绿态。
原始错误和review身份保留，不自动重试或续接；故障属于历史审查时不覆盖新attempt或终结结果。
经批准的夹具迁移后，8/9/18及T-075/T-076-1受控回归通过，证据见
[legacy-green-06](../evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/run.json)。
手工claim即使有合法review与评分，缺少受管启动来源仍拒绝集成。受控结果不代替真实模型验收；
先前不传tier的最小复验及P-review02只证明当时冻结版本；显式default最小复验与priority/只读变异体已通过。
真实正例槽2–6及独立交付审查槽7已完成，累计真实7/8；正例见本卡outside-real-delivery-02，
审查原文见[REPORT](../evidence/2026-10-11-batch13/T-076/card-2/outside-delivery-review-01/REPORT.md)。
原日志归档要求及完成收据均保留。tasks/attempts/verifications一致，
memberships/session_presets无法重建；attachment中断窗口未由本条真实正例覆盖，全库一致性仍INCOMPLETE。
这不代表完整工作台或整张ticket已经验收。

worker 目录为 `<state>/worktrees/<project_id>/<task>-a<N>`，分支为
`a2a/<task>-a<N>`；N 沿用该 task 的递增 fence。验收目录加 `-verify-<K>`，
保持 detached。已完成验收的结果先持久化，M 保存在
`refs/a2a/verifications/<task>/a<N>/v<K>`，然后清理临时目录。
中断、结果未知或清理失败时保留现场并记录问题。

审查目录为同一项目命名空间下的 `<task>-a<N>-review-<K>`，保持 detached；
K 按该 attempt 已记录的审查意图递增，同 C 的有效审查复用不新建目录或递增序号。
审查结论入库后，确认原 reviewer 已停止且归档，再核对目录身份、候选 HEAD 与干净状态并删除目录及 Git worktree 登记。
清理事件单独追加，不改写 `review_result` 的审查对象，因此目录删除不改变 R8 沿用结论的身份绑定。
脏目录、未知 HEAD、退出未确认或清理结果未知时保留可核对的现场，沿用审查生命周期的暂停和问题上报语义。

已集成 attempt 在确认窗格回收后清理；无绑定线程的手工 claim 在集成后清理。
干净的撤销 attempt 在没有活跃线程时清理，否则等显式 reclaim。
清理前先保存并读回 `refs/a2a/attempts/<task>/a<N>`；已集成的还删除 worker 分支名，
撤销、终结失败的保留分支。脏工作区、未交付的 HEAD 或身份不符时不删，
通过现有 `issues` 和执行主控的 `inbox_list` 查询 system issue。
覆盖型未提交改动导致集成被拒时，同样保存绑定原 attempt 的问题条目。

工作分支已变时，integrate 在原任务操作锁内重新运行 verify 的同一检查链。
同一候选、卡快照和 attempt 的连续失配计数保存在 attempt 中；前三次自动重验，
第 4 次返回 `integration_revalidation_limit`，任务暂停并保存 system issue。
重复 integrate 不重置额度。只有已确认在 Git prepare 阶段终止、且未写工作区的
新 intent 可以进入这条重验路径；中断恢复的 pending intent 或未知副作用仍要求核对。
`integration_compare_failed` 事件携带候选审查的身份绑定；每次重验走同一质量串，
候选和完整身份绑定不变时沿用有效审查，候选改变时新开审查。该事件本身不是审查通过记录。

验收发生内容冲突时，只有 Git 合并退出 1 且索引含未合并条目才进入冲突整理。
原始命令结果、冲突文件、索引阶段与差异先保存；原 C 和 G 分别保存在
`refs/a2a/verifications/<task>/a<N>/v<K>-candidate` 与 `v<K>-base`，它们不表示验收通过。
原 worker 身份可确认时，冲突说明经原窗格队列以 `⟦门禁 #序号⟧` 回写，忙时等待。
任务进入 `rework`；重复 verify 不重发、不另建验收或 attempt。
只有投递已确认的修复请求允许下一回合显式重交新 C，重交后新 C 再次冻结。
原 claim 基线和卡快照不变；路径、尾注检查排除门禁从工作分支读到的已集成基线，
仍检查新 C 的实际增量和新 G→M 的净改动。重交进入同一 verify 检查链，记录需要重新审查。

会话已确认停止时，门禁归档旧 worker，从当前 G 经同一认领入口创建新 attempt，
新提示包含旧 C 和冲突背景，程序不替 worker 解决冲突。
仅有回合 Stop、领导进程替换或不明进程状态都不构成会话结束；
已知领导进程退出且只剩原 shell、上一回合已空闲时，才额外记录原生会话结束。
消息投递、会话观察或新 attempt 创建结果未知时，保留记录、工作区并上报，不自动重试。
已完成记录且投递确定的临时冲突目录在核对现场未变后清理；未知状态保留。

上述 S3 代码正在本卡验收中；受控窗格检查不能替代真实 worker 的冲突整理验证。

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

`GateRuntime` 由 `panes.ts` 实现每个后台实例一个 Codex worker 及每次交付新开的 reviewer 窗格；
没有 Claude 或普通 attach 会话。生产 CLI 没有直接开库的运行时替代入口。
worker名额释放及新attempt的原生记录归属由T-077联验；此卡保留S1的single_worker_slice约束。
旧 `native-runtime.ts` 是隔离测试边界；它的旧证据不能证明新后台或真实窗格可用。

真实启动需在 `daemon_start --launch-config /绝对路径/launch.json` 中给出固定 Codex
路径、隔离 `codex_home`、角色卡及版本、代码版本、hook 授权引用和回合上限。
`dispatch --runtime-mode workspace-write` 始终启动交互 zsh 中的 Codex：`-a never`、
workspace-write、任务卡指定模型（当前统一 gpt-6.1-sol）、xhigh、显式 `-c service_tier="default"`（普通速度，覆盖全局 priority）、关闭更新检查。
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

请求在所属 launch 内用 `request_id` 去重：相同内容返回原结果，不重复执行；同一 launch 内同一编号换内容明确拒绝。新 attempt 的新 launch 可以使用相同编号。
已有请求按持久化的 launch 与编号查回，沿用原结果；只有 intent、没有结果的请求仍报结果未知，不重新执行。
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
