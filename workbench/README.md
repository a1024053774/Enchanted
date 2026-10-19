# a2a 门禁、编排后台与工作台

T-096 恢复已合入 main；57c3bfb63 的七场原生恢复回归曾通过。第三轮审查随后发现正常登录记录缺认证字段会绕过拒绝，现已改为假 API 合同白名单；新候选七场原生回归仍须重跑。Electron 创建或显式关闭窗格时，把 launch 与位置追加到
现有 SQLite 事件流；退出应用只断开视图，保留打开集。未传 `--launch` 时读取该任务
保存的窗格集，并沿用位置。只有从未保存过布局才选择当前窗格；明确关闭最后一格后，
保存集为空，重开仍显示空视图。后台只自动恢复假 API 的主控窗格：按原启动记录构造完整续接 argv，
Claude 仅把 `--session-id` 换为 `--resume`；其余参数与隔离假 API 环境取原记录。
恢复在原版本／session 核对之后、PTY 启动之前建立规范 executable_path；旧历史记录不变，只给运行时副本补齐。已有规范身份与当前目标不同则拒绝，不改变 argv 或硬设 leader。
已知限制：正常登录的主控记录不自动续接。recover 在任何 CLI 命令前检查现存正常登录标记，不只依赖 authentication；任一正常登录标记存在即保留为“未恢复”，返回 `normal_login_restore_requires_protected_start`。请经正常登录入口重新启动；不执行版本命令、不启动 PTY、不读 auth。
仅当 P1 角色版本、公开假 token、规范 loopback base URL、隔离目录及既有假 API shell 启动形式与完整原 argv 的逐字对应同时匹配，且没有正常登录标记时才进入原恢复核对。正常登录以 exec 开头的启动形式也属于拒绝标记；shell 字段缺失或不属于既有假 API 形式的记录归为无法识别。合法旧记录可省略 authentication；无法正面识别的记录返回 `restore_record_unrecognized`，不猜测配置或执行 CLI。状态接口保留明确错误及正常登录的中文重启提示，现有界面显示“未恢复”与错误码。完整重建 R/F/D/C 生命周期另票处理，见 [请求 20](../evidence/2026-10-16-batch16/T-093/REVIEW-REQUEST-T093-20.md)。
缺 argv、版本不符、原生会话文件不存在时保留该窗格并显示“未恢复”，其余窗格继续恢复。
恢复不发送提示词或放行旧队列。按 T-096 的 2026-10-18 裁定 B，worker 窗格保留并显示
“未恢复”，不启动 CLI、不重绑定、不改变 attempt；后续由执行主控按中断恢复流程处理。
真实 Electron／daemon／CLI 验证入口与已知限制见
[运行说明](../evidence/2026-10-16-batch16/T-096/RUN-RESTART.md)。

T-078-2 P1 已接入 `controller_start --task ID --manifest /绝对路径/manifest.json`。
T-078 的假 API profile 使用隔离 HOME／CLAUDE_CONFIG_DIR、公开假 Bearer token 和 loopback Messages API。
T-093 另加正常登录 profile，配置与事实核对见下节；真实模型回合仍须用户在合入后另说开工。
根提交预算须在 manifest 预声明为 1～6 根，尚不宣称可用于日常主控。假 API 启动需逐次批准；单角色
收件箱候选及当前绿态审批流程见 [SLICE-1-GREEN-3](../evidence/2026-10-11-batch13/T-078/SLICE-1-GREEN-3.md)。
隔离 settings.json 仅设置 `theme: dark`，移除 IS_DEMO，并设置文档化的
`CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`，禁用标题侧模型请求和终端状态报告。
假服务用文档化的 `ANTHROPIC_AUTH_TOKEN`，
移除 `ANTHROPIC_API_KEY`，只由假 API 验证 Bearer 头，不设置 apiKeyHelper 或内部批准状态。
启动、每屏明确按键、continue、cleanup 分别审批。按键经后台 operator 凭据认证，
保存目录与屏幕原字节，执行主控操作不记为用户亲手输入；不自动补 Enter。
主题数字键无已核对依据，不配置。`selected_label` 是按键的目标项：
ArrowUp 到 Auto、ArrowDown 到 Dark mode，再单独批准 Enter 确认 Dark；
启动时直接 Enter 默认项被拒，同一屏 ID／原字节不能再次操作。
workspace-trust 用单独批准的 ArrowDown 到 `Yes, I trust this folder`，读回后另批 Enter；
前一条必须是同一窗格的该次导航，确认快照须延续导航原文。默认 Enter 和 Digit1 均拒绝，
整个 launch 只允许一次信任确认；不保留数字键路径。
用途只适用隔离假服务实例：onboarding-theme／onboarding-notice／workspace-trust。
onboarding-notice 只允许 Enter：从已登记的主题确认快照之后取输出，剥离终端控制序列，
与 08c 的固定 Security notes 文字逐字比较；原字节也必须等于本屏批准快照。
文字不同、额外提示或重复确认均拒绝。其他权限、认证、遥测或共享选择仍停下。
原生 debug 与 hooks 的原始 stdin、stdout、stderr、退出码和耗时落进该实例目录。
HookTrace 核对启动的 preset/launch，只接受 `<root>/roles/<preset>/hooks`；
不接受旧的 `<root>/hooks` 布局。
单回合及 09A-3R2 两回合 Esc／空框放行、拼接阻断已有绑定版本的实际证据；
当前 controller 转交候选仍须新实例验证，不能复用这些旧结论作验收。
遇到 API key 批准或目录信任提示，保存终端原文并停下，不输入或选默认。
cleanup 绑定 CLI 的 PID、启动时间和命令，确认退出前不报告 PASS 或删除隔离根。
角色卡经固定 CLI 帮助列出的 `--append-system-prompt` 传完整文本；启动记录仍保留来源路径。
controller 的 role card 只从绑定 preset 的 `roles/<preset>/role.md` 读取；root/role.md 会被拒绝，
不保留旧路径兼容分支。两个 preset 共用 broker/state/repo，HOME、config、tmp、shell、requests、
hooks、user-data 和 debug 按 preset 隔离。Claude 信号回合预算支持 manifest 声明的 1～6 根，
超出 6 根在 launch 构造处拒绝，Stop/prompt 绑定仍按实际 prompt_id 核对。
P1 API 在启动时绑定 loopback 的端口 0，由操作系统分配端口并先记录实际 manifest；
主控运行入口拒绝未分配的端口 0。旧实例材料已过期。
launch 仅记录进程启动，首屏另经 screen 阶段读回，不把即时输出当作稳定首屏。
Bearer 已取得标题侧请求；08b 的 Enter 因目标项字段误判被拒，已用实际批准文件复现并修复；
08d 已在真实 CLI 确认主题与固定 Security notes，停在默认 No 的信任屏后清理；
08e 已确认信任，并取得一回合主请求、实际 UPS/Stop exit 0 和 busy→idle（变基前可行性）。
09A 用两条 nonce：实际 hook 的 prompt_id 绑定回合，Esc 写出后释放 active、保留队列，
用户在窗口放行后才提交第二条；旧 Stop 不结束新回合。nullable 主控窗口按任务版本与
实际 CLI 身份核对，worker 仍核对 attempt。09A-3R2 两场景的实际假服务／CLI／UI
结果及归档见 [RESULTS](../evidence/2026-10-11-batch13/T-078/RESULTS.md)，不外推到新候选。
09B/09C 的实际双主控收件箱与 stop/ack、120 秒无 ack 只中断仍未启用／未完成，范围保留。
旧 T-078-1 的通过结果不替它背书。

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

## 普通终端

后台支持属于项目的普通 zsh 窗格，不绑定任务或 attempt，不走受管任务认领与交付。
在已有后台上用同一管理凭据创建、查询和关闭：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state shell_start --project 项目号 --cwd /绝对路径/项目目录
node workbench/src/gates/cli.ts --state /绝对路径/state pane_layout --project 项目号
node workbench/src/gates/cli.ts --state /绝对路径/state shell_close --launch 启动记录号
```

项目号沿用后台标识格式（英文字母、数字、`_`、`.`、`-`），cwd 必须是已有绝对目录，
可以选择任务 worktree。后台启动 `/bin/zsh -l -i`，读取该 HOME 的登录与交互配置；
只注入 `A2A_PROJECT`，不传模型参数或 agent 身份，不修改全局 shell 配置。
启动记录的 `role` 为 `shell`，task、attempt、session、fence、spec_rev 均为空。

窗口接线复用现有 transport：`window_open` 和 `workbench_snapshot` 带 `project`、`launch`；
输入沿用窗口凭据、sequence、request_id 和 `window_input`，不调用 agent 输入记录器，
不产生人工介入。窗口请求日志只保存命令及回执标识，不保存输入载荷，拒绝路径也一样。
`shell_created` 与 `shell_closed` 追加到现有事件流，事件数据注明 `role: shell`。
终端输出仍保存在既有 PTY trace，可能包含 shell 回显。

显式 `shell_close` 或 shell 的 `pane_layout_close` 会结束该终端，核对关闭前观察到的
shell 和子进程退出后才确认关闭。`window_close` 只撤销视图凭据，不结束终端。
关闭 Electron 的既有行为仍为断开视图。后台重启保留普通终端的打开集，但不自动拉起
zsh；历史快照返回 `lifecycle: ended`。退出无法核对时保留 unknown／明确错误，不伪称结束。
在界面左侧选择任务后，窗格栏的“新建终端”会在该任务所属项目的目录打开 zsh。
普通终端标为“普通终端 · zsh”，与 agent 会话并存，不显示 worker 的人工介入提示或队列放行按钮。
同项目的任务共用项目终端打开集；切到其他项目时只断开视图，不结束原终端。
重新打开界面会显示项目保存的终端；后台重启后的旧终端显示“已结束”，输入禁用。
新建、关闭或切换失败时保留错误，不自动重放创建请求。真实 Electron 验证见 T-104 本批证据。

启动前显式设置 `A2A_OPERATOR_CREDENTIAL`，指向本次启动专用、尚不存在的绝对文件路径。
启动者创建 0600 凭据文件，后续管理 CLI 与 Electron 从同一环境变量读取；后台按凭据
认定执行主控身份，不按 `--from` 或 `--role` 自报。每次后台启动使用新凭据，旧文件不覆盖。
不要把凭据内容放进 argv、证据或 Git；后台停止后由创建者清理。只读查询仍可匿名调用。
这条凭据路径与交互输入的首个候选已通过四项真实入口合同；库客户端通过八项检查。
8/9/18 复验曾在 coop 的 submit 出现身份回归；分开管理凭据与原生身份后，
outside-inbox-02 的 8/9/18 全部通过。后续窗格运行时变更尚待真实入口复验。
这些局部结果不代表 T-078 整票完成。

后台把认证后的角色作为 GateActor 传给门禁；只有真实原生会话才提供 SubmitCaller
的 thread/turn。管理凭据不虚构线程，不能替代受管 worker 的原生身份。
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
受管任务通过 JSON 任务卡注册；交付按卡检查路径、验收文件、完成条件与提交尾注，
机械通过后新开独立 reviewer，有效“可合并”结论到达后由执行主控带评分集成。
普通会话的 `attach --instructions` 仍是提示文本，
不参与受管任务注册。
旧 HTTP 转接经本次对话确认后删除；本入口只接受本地门禁命令。

## 任务卡与交付

使用同一个 CLI 生成模板，填写目标、非目标、路径、验收文件、argv 完成条件等字段后校验并保存：

```sh
export A2A_OPERATOR_CREDENTIAL=/绝对路径/隔离目录/operator-本次启动.json
node workbench/src/gates/cli.ts --state /绝对路径/state daemon_start
node workbench/src/gates/cli.ts --state /绝对路径/state card_template --task T-080-1 --repo /绝对路径/repo --ticket /绝对路径/T-080.md
node workbench/src/gates/cli.ts --state /绝对路径/state card_validate --task T-080-1 --card /绝对路径/card.json
node workbench/src/gates/cli.ts --state /绝对路径/state card_save --task T-080-1 --card /绝对路径/card.json --expected-version 0
node workbench/src/gates/cli.ts --state /绝对路径/state create --task T-080-1 --repo /绝对路径/repo --branch refs/heads/main --card-version 1
```

模板含 14 个字段。CLI 值精确为 `Claude Code` 或 `Codex`；任务类型为规格中的八个值。
完成条件格式为 `{"argv":["python3","acceptance/check.py","{worktree}"]}`，
`{worktree}` 只能占据完整的一个参数，在独立 M worktree 中运行。完成条件非零退出仍
返回 `oracle_failed`，这个名字只为保持已有公开错误预期，不存在旧 oracle 注册入口。
create 不再接受 `--base`、`--oracle` 或 `--instructions`。

`oracle_paths`（验收文件）必填且至少一项，列出完成条件依赖的仓库内测试、脚本、夹具和配置。
只接受确切文件路径或以 `/` 结尾的目录前缀；拒绝 `.`、绝对路径、通配符、`..`、`.git`，
且不得与 `red_commands[].test_paths` 有交集。认领时按当前工作分支起点的 Git tree 核对：
确切文件须已受控，目录前缀下须至少有一个受控文件；缺项返回 `oracle_not_found`，不创建 attempt 或 worktree。
候选相对冻结认领起点改动验收文件，或在受保护目录下新增文件，均以 `oracle_modified` 拒收；
同时核对 G→M 的净改动，事件与摘要列出具体路径。打回写回原 worker，并计入同一 attempt 的三次上限。
worker 认为验收文件有误时走问题上报，由主控或用户改卡。

非空 `red_commands` 每项必须显式给出 `test_paths`，例如
`{"argv":["python3","tests/check.py"],"test_paths":["tests/check.py"]}`。
只接受相对起点新增或修改的普通文件；拒绝路径越界、Git元数据、目录、重复项与symlink。
门禁为每项建独立B/C目录，只把声明的候选测试文件放到B上，同命令要求B正常退出且非零、C退出0。
无法启动、超时或未知退出不算红态；非零是否来自有效业务断言，由独立审查判断，不解析stderr关键词。
M验收目录独立，顺序为路径边界、验收文件、完成条件、红态、项目规则、尾注、独立审查。
验收文件检查不通过时不执行完成条件。

项目规则从注册时工作分支提交中的 `.a2a/quality.json` 冻结：

```json
{"schema":1,"rule_checks":[{"id":"lint","argv":["npm","run","lint"]}]}
```

缺文件明确记录未配置；损坏配置拒绝注册。规则在M执行，候选改写或删除配置不会改变本任务的冻结规则。

版本与快照存入同一 SQLite 库，旧记录不修改；`card_show --card-version N` 读指定版本。
注册冻结选定版本，认领时再追加包含当时工作分支起点和唯一写入者的绑定快照。
源文件或后续卡版本不会改变已注册合同。显式采用新卡用
`revise --spec-rev N --card-version V`，会使旧 attempt 与候选失效。

修改边界 `paths.allow` / `paths.deny` 用仓库相对文件名、末尾 `/` 的目录或 `.`，禁止项优先，不解释 glob。
认领会比较同一 Git 仓库中活跃 attempt 的允许路径集合，并扣除双方禁止路径；
未创建的文件也参与判断。交集默认返回 `path_overlap`。执行主控确需并行时，
在 `claim`、`dispatch` 或 `run` 上显式加 `--overlap-reason '具体理由'`，
理由、冲突身份和路径一起保存到 `claim_path_check` 事件；worker 的转交通道不增加认领权限。
门禁检查候选相对起点的净改动，以及 M 相对 G 的净改动。
尾注归属核对 Task、Attempt、Session、Role。受管提交另把 Launch 与该 attempt 的启动记录号核对，并把 Tool、Model、Effort 与同一条记录核对；Model 为 unknown 时仍接受。不一致时拒收，码为 trailer_identity_mismatch。带有 A2A 尾注、但该 attempt 没有这份启动记录时，尾注检查直接拒收，码为 trailer_launch_record_missing，trailer_check 事件写明缺启动记录。外来任务或坏尾注被拒。
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
reviewer 的 Git 审查 worktree 和候选提交保持不可写；门禁另建一次性 `candidate_workspace` 副本，
reviewer 用 `--sandbox workspace-write -a never` 进入该副本，副本不含 `.git`，只允许在其中构造
2～5 个变异。启动 argv 显式关闭网络代理并排除 `/tmp` 与 `$TMPDIR`，不安装 Git 尾注 hook，
会话 hook 仍只经启动 argv 传入。审查结束前门禁核对候选提交、审查 worktree、worker worktree
和共享仓库引用未变（worker worktree 与审查开始时 `review_requested` 记下的 HEAD、分支和干净状态比较，不要求等于候选；T-090），随后删除候选副本；边界不符则作废结论并上报。
报告入库不等于获得集成资格：`integrate` 在任务操作锁内核对本次 review 的
`review_reclaimed` 完成记录。结束核对与副本、审查 worktree 清理全部完成后才写该记录；
完成前集成明确拒收，不前移项目工作分支。

按用户2026-10-13的决定，Codex会话使用gpt-6.1-sol、xhigh及普通速度，
worker/reviewer的argv显式传`-c service_tier="default"`，派发事件与启动记录写requested tier为`default`。
显式覆盖也用于隔离CODEX_HOME，用户全局priority设置保持不变。
记录仅表示请求设置，不代表供应商实际执行tier；其他沙箱、hook及身份检查不变。

reviewer 的最终消息必须是完整 `review_submit` JSON；身份和候选模板由门禁派发。
模板中的 `review_requirements` 原样返回；`report` 是非空 JSON 对象，须含“完成条件与变异检查”键，用于保存完成条件审查、
变异命令与结果。解析器严格核对顶层字段，relay 和门禁结果保留完整报告。
门禁在保存报告前核对其中的 `mutation_checks.workspace` 等于本次候选副本路径。
门禁只核对报告容器、必需节键与请求格式，不判断报告结论或变异结果是否正确。
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
相同命令重放不再打分或改 Git，不同分数不能覆盖。后台与 `scripts/score` 新写入的打分行一律为 schema=2，
事实由任务卡、交付回合和事件提取，不写真实 `records/scores.jsonl`。
通过或升级的 `facts.rejections` 必须完整包含 `identity_version`、`path_boundary`、`oracle`、`completion`、
`red_state`、`rule_checks`、`independent_review`、`commit_trailers`；验收文件打回计入 `oracle`，不计入 `path_boundary`。
缺项拒收，不把缺失次数补为零。用户分和放弃结果沿用各自不带评分事实的合同，新行仍写 schema=2。
交付缺当前回合的实际模型/强度时拒绝，不能沿用请求值或上一回合的值。

`abandon --task T --attempt A --score-file FILE` 终结原attempt，不执行Git集成。
放弃只传 `{"result":"放弃","reason":"理由"}`，不带分数/备注/评分facts；升级传与通过相同的两项评分及理由、notes，
把result改为“升级”。命令不自动启动更强执行器。无交付时从该worker启动记录和已观察回合取元数据，未观察到模型则如实记unknown；
没有可核对启动来源则拒收。终结与评分一起落库，重放不重计；pending integration intent须先核对，不能用放弃掩盖未知CAS。
终结不等于窗格已回收：只在idle后用原attempt的reclaim回收；未完成的reviewer会保留上报。

`scores_validate --file /绝对路径/scores.jsonl` 是只读格式校验，不导入、不双写Herdr文件。
按每行 schema 校验，可读取混合版本：历史 schema=1 按原七项检查集（无 `oracle`）只读校验，
schema=2 的评分事实按上述八项检查集校验；历史行不改写、不迁移。未知 schema 拒收，写入端没有选择 schema=1 的参数或路径。
`scripts/score --source user --score-of ...` 可关联 v1 或 v2 的执行主控原记录，新用户分均为 v2。
缺必填项、非法评分/事实字段、重复 attempt、错误来源绑定和不完整尾行均拒收。

`run --wait-seconds N` 现在等待修复、审查和执行主控的显式集成命令，仍只绑定原 attempt。
它不会在机械通过后自动填分/集成，也不因第一次质量打回就回收 worker。修复或审查等待
到期时保留现场；收到最终集成后，确认原 worker idle 才回收并结束。

本候选只用于ticket隔离验证。红态/规则、终结评分、双向格式校验与CAS评分恢复已有受控正反例；
reviewer创建失败、后台重启时的未完成审查、退出未确认已有红态及暂停/上报后的绿态。
原始错误和review身份保留，不自动重试或续接；故障属于历史审查时不覆盖新attempt或终结结果。
经批准的夹具迁移后，8/9/18及T-075/T-076-1受控回归通过，证据见
[legacy-green-06](../evidence/2026-10-11-batch13/T-076/card-2/outside-legacy-green-06/run.json)。
手工claim即使有合法review与评分，缺少受管启动来源仍拒绝集成。受控结果不代替真实模型验收；
先前不传tier的最小复验及 P-review02 只证明当时冻结版本；显式 default 最小复验与 reviewer 边界变异体需按当前候选重新取得。
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
每次审查另有 `<state>/review-copies/<review_id>` 一次性候选副本；它不登记为 Git worktree，且不含 `.git`。
审查结论入库后，确认原 reviewer 已停止且归档，再核对候选提交、审查目录、worker 目录（相对审查开始时的快照）与共享引用未变，
删除候选副本，最后删除审查目录及 Git worktree 登记。
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

Electron 43.4.1 的 npm 包已没有 postinstall 下载；npm ci 成功不代表其二进制已安装。
启动测试前显式运行已安装包的 `install.js`，把 `electron_config_cache` 指向外置盘，
并核对 `path.txt`、`dist/version` 与可执行文件。T-103 的
[独立安装脚本](../evidence/2026-10-19-batch17/T-103/RUN-OUTSIDE-04-ELECTRON.sh)
接受 workbench 绝对路径与新的外置盘记录目录，保存版本、命令、权限检查与磁盘占用；
只对内置盘的 Electron 安装目录使用，不改变 package.json、锁文件或全局 npm 配置。

本机已知限制（2026-10-19）：Electron 43.4.1 放在 USB 外置盘（APFS、Owners Disabled）
执行时，连不加载产品的版本探针也可能挂起。相同版本在内置盘能立即返回；这是当前
环境的执行限制，不外推为所有 APFS 或 USB 磁盘的问题。Electron 二进制一律从内置盘
执行，外置盘仍用于基线源码与依赖、构建槽、npm 缓存和 Electron 下载缓存。
测试基线可用 Electron 包已有的 `ELECTRON_OVERRIDE_DIST_PATH` 显式指定同版本内置盘
dist；平台路径元数据须完整，不能依赖外置盘上的 Electron.app。T-103 的红态、绿态
共用一个内置盘二进制，并核对实际进程回报的路径与版本。

T-102 打包时把最终 `.app` 安装到内置盘 `/Applications` 后运行；这个安装位置不受
上述外置盘执行限制影响。外置盘可保留打包产物与缓存，验证时不直接运行盘上的 `.app`。

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
Esc 后先由用户自行处理 CLI 草稿，看到输入框为空后点击“输入框已空，放行”。
该 action 记为“用户声明输入框已空”，引用实际中断写入收据；后台不删除草稿，
也不把声明记成机器读到的输入框状态。后台核对当前窗口、launch、中断和窗格输入代次，
声明后又有键入、粘贴、二进制输入或组合输入则拒绝陈旧放行。受管 worker 同时记人工介入。
UserPromptSubmit 只阻断当前登记注入的正文错配，输出 hook JSON block 并保留原始诊断；
不按文本标记拦截手打提交，不裁剪、不重送，Stop 的提交匹配语义不变。
09A-3R2 的实际隔离场景证据已有独立版本绑定；新候选的入口检查使用真实
daemon/window socket 与 hook CLI、模拟 PTY 和 vendor 身份，不等于实际 Claude 复验。

`daemon.ts` 导出 `serve(root, config, createGates?)`。第三个参数只供测试在代码里注入门禁对象（受控线程运行时或变异体），默认是 `new A2AGates(root, panes)`。产品的 `daemon_start` 不传这个参数，CLI 和环境变量也都没有对应的开关。交付 8、恢复 9、编排 18 这三套旧场景，经 `workbench/tests/run_daemon_acceptance.py` 在本后台入口上运行（T-075-5）。这个运行器为每个测试在短路径上显式启动并停止一个隔离后台，不改 `acceptance/` 中的任何断言。

## 主控启动记录（静态准备）

主控启动的静态准备入口为 `controller_prepare --task ID --preset ideation|executor`，
使用后台的管理凭据。启动配置的 `controllers` 按这两个 preset 分别提供
`executable`（绝对路径）、`model`、`effort`、`settings`、`role_card`、
`role_card_revision`，并提供公共 `code_revision`。settings 当前只收 hooks 与
permissions；认证环境另待用户决定，不能把凭据放入 settings。

此命令只构造 argv 和追加启动记录：包含 `--session-id`、`--model`、`--effort`、
`--settings` 及角色卡正文，attempt 为 null，execution_state 为 prepared。
它不创建进程、不读取 CLI 版本、不签发会话凭据；CLI 版本记 unknown，生命周期为
“未启动”，明确标记“待真实 Claude 复核”。静态构造／存储的通过不替代真实启动验证。

受控假 API 主控的实际入口为 `controller_start --task ID --manifest /绝对路径/manifest.json`。
现有 manifest 的 `executable` 为明确的 CLI 绝对路径，`version` 为预期版本（例如 `2.1.302`）。
后台在该角色的隔离环境中执行一次 `--version`，要求完整输出为 `<version> (Claude Code)`，
通过后才登记启动记录并启动 PTY。记录保留实际版本和探测的 argv／stdout／stderr。
路径不存在返回 `controller_executable_missing`，探测失败返回 `controller_version_probe_failed`，
版本不符返回 `controller_version_mismatch`；不自动查找或改用其他版本，不修改全局设置，
不关闭自动更新。静态配置构造仍不启动 CLI；T-091 的 2.1.302 启动与版本反例已由
green-02 取得真实 PASS，证据仅绑定其冻结候选，见下方结果记录。

## 正常登录 profile（T-093）

当前整票 INCOMPLETE：第三轮独审对 788d75f4a 报 NO_GO，P1 为缺 authentication 的正常登录记录被恢复。恢复白名单局部红绿通过；r20 仅两场原生 PASS，no-argv 初始化中断，根因 unknown。本轮补 helper 失败诊断及红绿，不放宽身份条件；新候选 t093-r21-* 七场何时运行由用户决定，尚未重跑。网络两层、运行时身份、libproc 等其余审查结论仍按报告的范围保留，不替新恢复入口背书。
主控 #125 进一步限定：正常登录记录一律保留为“未恢复”，需经正常登录入口重新启动；假 API 恢复合同不变。该拒绝已用独立旧探针及实际 recover 局部合同取得红绿，不代表原生 OS／恢复验收已完成。
夹具按派发合同独立构造完整标记文本，对整个请求 JSON 精确比较，不使用包含或内容归一化。
最新修正与七场重跑命令见 [请求 20](../evidence/2026-10-16-batch16/T-093/REVIEW-REQUEST-T093-20.md)；请求 19／18 保留旧审查与运行来源，重复运行必须另选全新输出名。
共享调用点与 T-091／T-078／T-096 回归命令仍见 [请求 13](../evidence/2026-10-16-batch16/T-093/REVIEW-REQUEST-T093-13.md)。

仍经同一个 `controller_start --task ID --manifest /绝对路径/manifest.json`，保留原生
UserPromptSubmit、PermissionRequest、Stop、身份核对与队列转交，不增加门禁或策略引擎。
manifest 在既有字段外设置 `authentication: "normal-login"`、`version: "2.1.302"`、
明确的 `credential_source: "macos-keychain"` 或 `"file"`，以及唯一的 `upstream_url`。
生产正常登录入口的上游端口固定为 443，使用配置的 HTTPS 地址，没有端口覆盖选项或 fallback。
无模型测试链使用可配置的非特权端口，默认 `http://127.0.0.1:18443`，不占用用户的 443。生产入口显式向 `prepare` 传 443；测试入口传测试端口，两者均由同一个 `claudeLoginSession.policies(session)` 读取 upstream_port 生成 F profile，只改变端口参数。
测试脚本的 `T093_TEST_UPSTREAM_PORT` 同时传给链路、编译检查与独立核对器；端口冲突时保留失败，不切换端口、不复用或关闭别人的监听。

正常登录使用独立的受保护 daemon。先准备已有合同要求的角色目录、task 和 manifest，再由操作者启动：

```sh
python3 -I -S -B workbench/src/claudeLoginSession.py --manifest /绝对路径/manifest.json \
  --repo /真实HOME以外的工作区 --forward-port 本地固定端口 \
  --upstream-address 配置上游的固定IPv4 --lifetime-seconds 600
```

本票不运行上述真实登录命令或真实模型回合。root、root/state、repo 和全部运行数据必须在
OS 账号真实 HOME 以外；严格禁写 HOME 因而也禁止写其中的项目工作区。角色目录仍是
root/roles/ideation 或 executor，包含 home、claude、tmp、shell、requests、hooks、user-data 与 role.md。
CLI executable 使用规范实际路径，避免版本符号链接与进程身份不一致；Git 元数据也须在真实 HOME 外。
启动器直接 exec 进入 C 中的现有 daemon 入口，并在 C 中创建本次 root/operator.json；
后续操作继续走原入口。后台与 PTY 生命周期不依赖前端窗口。
正式 Python 入口必须使用 `-I -S -B`，关闭环境／site 启动和字节码缓存；入口会核对三项标志，
并在其他导入前关闭字节码写入。普通 Python 启动不在支持范围内，其解释器启动早于脚本检查。
准备函数失败时先让 R 保存主错误，再删除私有准备根；清理错误不替换原异常。真实入口在 state 下
独占保存 login-preparation-failure-UUID.json 和单独的 .cleanup.json，只记录类型／errno，不公开错误原文。

`upstream-address` 是 URL 的显式 IPv4 网络地址，由操作者配置。**OS 层不再按主机限制**，F 的 OS 出站规则为 TCP `*:443`；其他出站端口不允许。
应用层捕获配置主机，在 transport 前及 lookup 边界核对；不匹配即拒绝并记 upstream_host_mismatch。入站 Host 不决定目标，F 不跟随重定向。
正常请求固定连接配置的 IPv4，不查询 DNS、不轮换地址，TLS 使用 URL 的原始主机名验证证书。HTTP 假上游必须匹配 127.0.0.1；
不支持 IPv6。绿态只配置本地假上游，真实域名的 DNS／TLS 与真实模型仍未实测。

| 进程／阶段 | profile 与权限 |
| --- | --- |
| R 凭据准备 | 在业务沙箱之外精确读一次。文件来源只读 ~/.claude/.credentials.json；钥匙串只查 Claude Code-credentials 和指定 login.keychain-db，不枚举、不换来源。仅复制 claudeAiOauth 到私有 /private/tmp/a2a-claude-login-*，文件 0600 |
| C 根 daemon、PTY、zsh、CLI、原生 hook／tool、进程查询 helper、事实子进程 | 最外层只施加一次 C，后代继承；禁写整个真实 HOME，保留 HOME 读取屏障，只例外读取 CLI／Node、workbench 源码及依赖；TCP 只到 F 的固定本地端口，Unix socket 仅本次 control.sock；禁止 Security，保留 fork／exec |
| F 独立进程 | 在 C 启动前独立施加 F，脱离调用者进程组并 reparent；只写自己的 forwarder 记录目录、只监听固定 P；OS 允许任意主机的 TCP 443，配置主机／IPv4 由应用层锁定；禁止其他出站端口、Security 与 fork |
| D 基线及清单／隔离根清理 helper | 原始 auth 读取前由一次短 D 进程采基线；长期 D 独立施加相同 profile。无出站、无 Security、无 fork，只写私有根及自己的收据目录。HOME 只读目录/stat，不读正文（源码除外）；快照仅留私有根，C 输出差异后由 D 删除整个根 |

R 只有固定参数／FD／临时目录准备及一次原始 auth 读取；没有不受保护的长期监督进程。
为供 Node 解析真实路径，C、F 与外部 V 仅允许查询既有源码／依赖／可执行文件祖先目录的
`file-read-metadata`，以精确 literal 列出，包含真实 HOME；不允许枚举这些目录或读取其他文件正文，
也没有增加写入权限。完整链在 C、F 下用源码根的公开 AGENTS.md 验证正文读取仍被拒。
短脱离 helper 各自以对应 profile 的 true 结束，实际 PID 与退出码单列。各后台进程有覆盖
前置检查、服务与收尾的硬期限。D 在失败／根进程退出时清理本次登记的组与私有根；
清理不确定会记录失败，不能补作 PASS。已有可写 HOME FD 在应用 profile 前关闭；日志不得重定向进真实 HOME。

前台身份核对统一调用 `/usr/bin/python3 -I -S -B workbench/src/processSnapshot.py PTY_PID`，5 秒期限。
它在同一 C 内调用系统 libproc，只枚举该 PTY 的后代，读取 PID／PPID／PGID、TTY 前台组和可执行文件路径，不读 argv、环境或认证。
查询前后复核进程出生时间及身份；权限拒绝、短数据、截断、身份变化或不连通的树均拒绝，不改用 ps 或无保护查询。
查询异常保留原错误码／details，daemon 回复和 request_rejected 事件另带 diagnostics.process_query：helper 的 stdout、stderr、exit_code／signal、killed、error_code、root_pid／helper_pid、单调 elapsed_ms。spawn 未成功或状态未知时用 null；捕获范围仍受原 maxBuffer 限制。身份核对失败仍立即停止，不重试、不回落、不放行终端写入。
已观察到的退出／僵尸不作为活 leader；多次内核读取不宣称原子快照，原有 hook／Stop 的身份重查保留。
前台组条件不变；真实启动边界另外记录规范 executable_path 与内核路径比较，实际 argv 原样保留。alias 启动后改指另一目标不能接管原身份，helper 的实际 PID 也登记在 C 的进程记录里。

版本检查、auth status、交互 CLI 均直接继承 C，不再调用内层 sandbox-exec。
未通过启动器的正常登录请求返回 normal_login_outer_profile_required；不会退回未受保护模式。
默认假 API profile 的合同保持原样。

隔离配置只新建 `hasCompletedOnboarding: true` 和当前规范工作区的
`projects[路径].hasTrustDialogAccepted: true`。它们是 **2.1.302 内部状态**，换版本须重新核对。
onboarding 预检会直连 api.anthropic.com/api/hello 与 platform.claude.com/v1/oauth/hello，
不经过 BASE_URL；正常模式必须用上述状态避免触发。事实记录生成状态是否完整，并用终端和
私有 debug 日志分类 `onboarding.preflight_observed`；沉默的被拒连接尝试未测量，不冒称已统计。
C 的 OS 规则阻止直连上游；转发原件证明的是 F 实际接收的全部 HTTP 请求，包含失败与重试。

F 复用原转发器，先逐条写盘并 fsync 再连接上游。请求体与认证头不落盘，方法、路径等元数据
也参与凭据脱敏；保留序号、方法、无 query 路径、长度、bearer 匹配布尔值及每次响应／错误。
原件在 `state/login-audits/<launch>/forwarder/journal/requests.jsonl`，F 自身不重试或跟随重定向。
CLI 的 400 后重试算新请求；记录失败时停止转发新请求。终端仍只持久化去凭据字节，
原值及 JSON／URL／base64 变体都扫描；跨片段前缀暂不公开，OSC/DCS 负载不进入 trace。
配置、debug、原生历史与凭据副本随整个隔离根删除。C 的管理临时目录另在 audit/C-tmp，
避免结束后的事实子进程重建已删除的隔离根。

操作者在发送模型提示前，使用独立 V profile 的只读事实入口：

```sh
python3 -I -S -B workbench/src/claudeLoginSession.py --stage facts --preflight --audit /绝对路径/state/login-audits/LAUNCH
```

preflight 标明 before_cli_input、当时的入口计数与扫描结果，结束后 HOME 对比仍是 pending；
preflight 与结束事实的 network_boundary 明确报告 os_host_filter=false、实际 os_remote_ports 和 application_host_lock=true。生产为 [443]，无模型测试为所配置的测试端口；这不是逐连接网络审计。
测试 U 在零监听、部分监听或正常退出时均写关闭收据，记录成功创建／关闭的监听器数和独立关闭错误。C 必须核对收据的 PID／进程组、全部端点关闭和 ESRCH 才确认收尾；启动失败本身不代替退出证明。
后续重新读取会重数当前原件，保存的入口计数／扫描时间仍是历史事实。它不批准模型输入。
正常结束后用同一入口去掉 `--preflight`。C 内部子进程使用 `node workbench/src/claudeLoginCheck.ts [--preflight] AUDIT`，
继承 C，不再嵌套 V。外部入口关闭额外 FD、禁写真实 HOME、禁网络和 Security，并保留 HOME 读取屏障。

当前事实 schema 为 2，只读该版本的 ledger；旧 schema-1 证据须用其绑定的旧代码重放。
命令重新数请求并与结束计数对账，报告真实 HOME 路径引用、结束时的 state 凭据扫描、
原件计数、前后清单差异、进程/profile 来源和隔离根删除收据。不会重新读取原始 auth，
退出码只表示读写／解析是否成功，不自动批准或拒绝模型调用。

元数据只列 .claude、.claude.json、.claude.json.backup、Library/Keychains，
不读正文、不跟随链接、不比较 atime，不用校验值；其他 HOME 范围排除。
目录在 stat 后消失会显式标 missing；权限错误仍作为采集失败报告。
差异全部报告、不推断因果。按用户裁定 A（main c06a73179），清单有无差异均不决定通过，
以 pass_condition=false 标明。凭据、计数、身份与清理断言不因此放宽。

无模型验证只用合成登录、编译假 CLI、真实 PTY／daemon／hook／Stop 和受保护的本地假上游。
主控在沙箱外执行，每次使用新输出路径，不请求提权：

```sh
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh \
  /绝对路径/a2a-wt-t093 完整冻结SHA /private/tmp/新的摘要.json none
```

旧残留已由主控清理。旧演练与 chain-07/08 仅属于各自候选；请求 16 的生产 443 profile 编译通过，primary／green 因假 U 不能监听 443 而失败。请求 18 随后在 57c3bfb63 以同一生成器的 18443 测试端口通过编译、完整链与六场核对；最新原件／限制见请求 19。
演练使用同一 R/G/C 入口和实际 OS profile，只配置合成 auth／假上游；primary 主动失败用于验证清理不能覆盖原异常。
正式六场的预期业务断言与命令在交接请求 10。worker 的 Codex 沙箱不能嵌套相同 profile，因而不在本会话尝试。

测试长期 D 仅比产品 D 多本次合成 source-home 的 file-write-unlink，仍禁读其普通文件正文；原始基线 D 规则另列为 D_baseline。
C/F 对认证源的拒读拒写不变。D 先读回 C 已 fsync 的 cleanup_pending 检查点，才删合成源；正式产品不删除用户认证源。
结果 JSON 在测试收尾前先发布，清理错误单列；`.events.jsonl` 保存各阶段主失败／清理状态，V 将退出记录绑定原登记身份，并用信号 0 独立核对每个 PID／组与最终报告进程退出。
测试链必须读到上游端点关闭收据，并在原期限内以 ESRCH 确认进程组消失；EPERM 仅表示未确认。`node workbench/tests/test_t093_upstream_shutdown.ts 新输出.json` 检查收据先于退出的窗口，拒绝把 EPERM 当退出、持续权限拒绝、存活或缺收据。
最终 all_exited 必须与每条最终 group／child 退出记录一致；`node workbench/tests/test_t093_writer_exit.mjs 新输出.json` 检查先前 ESRCH 后最终 EPERM 的时序，任一未确认行禁止删除。
所有实际 PID、进程组和对应 profile 会写入结果；原始合成凭据、二进制、sqlite 与临时源码不进证据或 Git。
结果只保留文本事实、原件小记录、反例和清理状态，历史报告与失败不覆盖。
processInfo 影响所有 pane：窗口输入、放行／中断、反馈和 hook／Stop 身份重查。T-091 IPC／版本、T-078 runtime／relay 和 observer／alias 已补本轮局部回归；T-096 原生七场由主控逐屏批准后直接调用原 runner，均 PASS，模型与 fake POST 为 0。详细业务复核与原件位置见请求 19；局部替身不等于额外的原生 T-078 材料回放或全 pane 生产验证。

## Electron 窗口

T-091 单格 Tracer bullet 已取得真实输入输出读回；当前候选沿同一条通路支持一个任务内的
多个会话窗格。重复 `--launch` 传入两个主控与当前 worker，窗口会按真实 role／preset
排列为上方构思主控、执行主控，下方全宽 worker；窗宽小于 1000px 时排成三行。
各格保持 160×45 与独立滚动，不因尺寸改变重建终端或更换身份。
三格真实绿态及反例、四类 GUI 回归已在 f20a74ada 上通过；core 回归与最终独立审查
仍为 INCOMPLETE，结果见
[T-091 结果记录](../evidence/2026-10-16-batch16/T-091/RESULTS.md)，重跑清单见
[T-091 三格检查](../evidence/2026-10-16-batch16/T-091/THREE-PANES-RUN.md)。
本地 VM 检查不替代真实 Electron、PTY 或门禁运行证据。

core 回归入口会先运行 `workbench/tests/test_t091_business_mutant.py`，检查 CAS 分类器的
三项业务证据、拒绝控制及原合同文本，防止旧断言名称导致已触发的变异被漏判。
core -03 的四组原套件已通过；分类器修正后的完整 -04 及 lock 反例仍待实跑。

运行中的主控窗格没有 worker attempt，仍可输入；worker 窗格须匹配当前 attempt。
每次写入继续由后台核对窗口凭据、任务版本与原生身份。窗口展示的 launch、thread、
active dispatch 与输入可用状态供驱动核对；驱动发键只代表尝试，送达须有同一窗口请求的
用户动作、PTY 写入意图与写入收据，不能用 `sent:true` 代替。

窗口经同一个 Unix socket 查询后台，不加载 node-pty 或 SQLite。显示一个项目、任务、
多个会话窗格和共享的当前任务门禁状态；终端网格固定为 160×45。当前输入候选在固定的活动 launch 上启用
键盘、IME 和粘贴入口，历史窗格保持只读；全部输入由后台写入 node-pty，renderer
没有后台凭据、PTY 或数据库权限。每个窗格的窗口输入凭据绑定一个 launch，关闭时撤销，不随
current_attempt 更换目标。后台在等待前占用窗口序号和 request_id，重用请求号会被拒绝；
输入调用失败时停止后续发送，不自动重投。

六条 IPC handler 每进程只注册一次，以 sender 窗口及该窗口登记的 pane key 路由，
拒绝未知 key、其他窗口的 key 和非 mainFrame 调用。preload 的只读 `paneKeys` 来自
BrowserWindow 的非机密启动参数；snapshot、output、input、beginComposition、
releaseQueue、observeFocus 均显式带 key，不保留无 key 的输入通路。凭据只留 main。
每格独立持有输入序号、发送队列和放行请求；并发 snapshot 共用一次窗口凭据请求。
关闭会等待已接收的输入与凭据请求，随后撤销凭据，不移除其他窗口仍使用的 handler。
同一 Electron 进程共用应用级 user-data，不把每会话 HOME 与应用级目录混为一谈。

窗格显示完整 task、launch、worker attempt；主控角色依据快照中启动记录的 preset。
多 launch 在建窗及签发凭据前逐项检查同任务、运行状态和当前 worker attempt；错误 task、
旧 attempt、未运行或重复 launch 均拒绝，不静默替换成当前 worker。单格历史查看仍保持只读。
输入能力与焦点分开：实际 textarea 聚焦且允许输入时才显示“正在输入”和蓝色边线；
不自动聚焦。输出读取错误时暂停该格输入。系统 IME 仍不在本票验收范围。

输入在写入 PTY 前进入 user_inputs；受管 worker 的人工介入在同一事务里派生，带
input_id。粘贴去掉协议包裹后保存文本；终端控制键记 action。长度为零的 onData
只记带窗口、序号和时间的 terminal_input_empty，不写 PTY、不生成用户输入或介入。
组合输入开始时先登记草稿占用；结束或取消组合输入不代表 CLI 输入行为空，
占用由用户提交或 Esc 后明确放行清除。二进制终端输入按原始单字节写入，保存
带 base64 原始字节的 action，不把其中的控制字节当成用户提交。上述三项修复
已通过 outside-input-green-01；主控多窗格和主控凭据运行路径仍待真实 Claude 复核。

后台登记注入正文时仅移除末尾 CR/LF，与已观察到的 Claude 提交形式一致；保留中间文字与空白。
UserPromptSubmit 对活动注入与实际 prompt 逐字核对，拼接或中间差异仍阻断，不自动重发。

设备查询应答由后台处理，前端用公开 parser 接管查询，避免自动应答混入用户输入。
按 T-078 执行主控决定 03，前端拦截 DECSET/DECRST 1004；混合序列中的其他模式
保持顺序交给 xterm。每次拦截记原始序列。CLI 因此收不到工作台窗口的焦点变化。
P1 与首个候选的四项输入合同已经通过；其余失败方式和当前扩展后的候选仍待复验。

构建必须在外置盘真实挂载后进行，每次使用一个尚未存在的构建槽：

```sh
npm --prefix workbench run build -- --slot local-01
# 不指定任务时，先选择已有项目下的任务
node workbench/app/start.mjs --build /Volumes/WD-Elements/a2a-workbench/local-01/dist --state /绝对路径/state --user-data /绝对路径/ui
node workbench/app/start.mjs --build /Volumes/WD-Elements/a2a-workbench/local-01/dist --state /绝对路径/state --task 任务编号 --user-data /绝对路径/ui
# 同一任务三格（身份取自已有启动记录）
node workbench/app/start.mjs --build /Volumes/WD-Elements/a2a-workbench/local-01/dist --state /绝对路径/state --task 任务编号 --launch 构思主控launch --launch 执行主控launch --launch 当前workerlaunch --user-data /绝对路径/ui
```

左侧按项目列出当前门禁库中的任务，显示任务编号、标题与门禁状态。点击任务切换
会话视图；切换只断开旧视图的输入凭据，不关闭后台会话或改动保存的窗格布局。
“刷新列表”重新读取库，已移除的任务不再显示；所选任务被移除时返回选择页。
空库显示创建任务的提示，界面不提供创建或删除操作。项目来自现有任务的
`project_id`，不另存项目目录。命令行也可只读查询，不要求 `--task`：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state projects_list
node workbench/src/gates/cli.ts --state /绝对路径/state tasks_list --project 项目编号
```

两条列表命令不写库或请求事件；未知项目返回空列表。`--launch` 仍要求同时指定
`--task`，其任务内多窗格选择方式不变。preload 的 `paneKeys` 保留启动时的窗格集；
当前视图由 `selection` 和 `selectTask` 的返回值提供，切换后旧 key 不再可用。

Electron 的启动环境须带该后台对应的 `A2A_OPERATOR_CREDENTIAL`；它只在 main
进程中读取，并用于领取窄的窗口输入凭据，不传给 preload 或 renderer。

缓存、构建临时目录和 dist 都在外置盘；没有内置盘回退。`A2A_BUILD_VOLUME` 可指定
验收用的检查路径，普通目录和符号链接不能通过挂载检查。已有构建槽不会覆盖；不要在
输出目录中放源码或依赖链接。启动只读取已有构建产物，不自动构建、装包或启动后台。

默认后台目录为 `~/Library/Application Support/a2a-orchestrator`，默认 Electron 数据位于其
`ui/` 子目录。验证时同时显式指定后台与 UI 的 `/tmp` 隔离目录。

## 库版收件箱客户端（当前只在夹具项目验证）

`workbench/bin/inbox` 复用同一门禁 CLI 与后台，不打开数据库、不读写文件版收件箱。
必须显式传 state（或本会话 A2A_STATE）。管理端提供对应的管理凭据；worker 和 controller 的
send/list/ack/ready 沿既有 B 请求文件通路，由本会话 Stop 携带实际 launch 凭据
转交，结果以门禁回执写回。queued 只表示本地请求已排队，不是后台执行成功。
worker 转交时及门禁内同时核对原生进程和当前 attempt，撤销后不能继续写入。
controller 使用 schema2 请求，带实际 launch、preset、project、task、spec_rev、受管身份、
native_session 和当前 prompt_id，不补 worker attempt/fence。匹配 UPS 后后台发布当前
context；实际库客户端写请求文件，匹配 Stop 才执行。caller 同时核对持久启动记录、
当前任务项目／版本、active／prompt、shell／leader 和原生会话，并在异步观察后重新核对。
`--from`、`--role` 只是沿用命令格式，不能改变实际身份；worker 只能发 issue、
读取本人的条目、ack 本人的条目；ready 按权限拒绝 worker。
worker 入口已通过 outside-worker-inbox-green-01 的 14 项检查；四项单规则变异体
分别产生了可读回的越权结果，且只触发对应断言失败。最终变基候选仍须重新验证。

```sh
workbench/bin/inbox --state /绝对路径/state ready --project 项目编号
workbench/bin/inbox --state /绝对路径/state list
workbench/bin/inbox --state /绝对路径/state send --to ideation --kind report --body-file /绝对路径/report.txt
workbench/bin/inbox --state /绝对路径/state ack --id 收件箱条目号
```

ready 只读取该后台已绑定项目的 ticket，返回可执行且依赖已关闭的就绪项；字段
不合规时返回诊断和失败状态。它不标记就绪、不写项目地图，也不接受任意仓库路径。

收件箱、ack 和投递收据都只追加。`queued` 是已排队，`delivered` 才是运行时确认写入；
重复 ack 复用原条目及投递结果，不重发。读取 queued 收据时可追加运行时后来确认的状态。
没有实际接收者时，条目和未送达原因保留，命令不能报告投递成功。

角色地址 ideation/executor 暂无会话时，条目保留为 `pending, reason:role_session_missing`，
执行结果 `ok:true` 表示已留存，不表示已送达。发送方同 request_id 的 relay_processed 事件
可见该状态，此时不注入反馈回合。controller_start 注册实际角色后，只恢复明确待上线的条目，
沿原有 wake/dispatch 队列投递；首启 unknown 时不写业务输入。已有排队条目不阻止经批准的
主题、安全提示和信任屏单键操作，逐屏按键本身不放行队列。初始放行后，只有真实
turn_submitted 收据才使投递变为 delivered，再向原发送方登记原有的一条执行反馈，
关联原 request_id/entry_id，不重做 send；09B 的 I2 在此时只确认，预算不增加。
原条目 created_at 保持不变，120 秒无 ack 的起点不因上线而重置。
缺少确定结果的旧 pending、unknown 写入与多会话歧义不能自动重送；反馈派发意图已保存但
结果不明时同样不重发。完整双 Claude 场景仍须新实例与独立审查，不以 PTY spy 代替实测。

worker Stop 收件箱转交已在隔离入口通过验证；controller 已接入同一原生请求文件／
Stop 通路，实际 Claude 单角色工具绿态仍待批准运行。真实双主控转交、stop→执行→ack、
120 秒无 ack 只中断仍未完成，不能作日常派发入口。本仓库的 `scripts/inbox` 保持原样，
切换前不双写。局部领域与 native/PTY spy 不代替实际 Claude 窗格或独立验收。

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state workbench_snapshot --task 任务编号
node workbench/src/gates/cli.ts --state /绝对路径/state pane_output --launch 启动记录号 --offset 0 --max-bytes 65536
```

`workbench_snapshot` 可加 `--launch` 查看本任务的历史窗格。窗口第一次选定 launch 后固定
该身份，不随 current_attempt 改变而切换。`pane_output` 返回 base64 原始字节和
start_offset、next_offset、total_bytes；每块最多 65536 字节，从同一追加 trace 读取。
新窗口从 0 补回，已有窗口收到 xterm 的解析完成回调才推进游标；缺失、缩短或错序
明确报错，不跳过字节。关掉 Electron 只断开视图，后台和窗格由独立进程托管。

后台重启会追加 `pane_recovered`。假 API 主控窗格按启动记录的原 argv 重建 PTY 并续接原会话（T-096，用户裁定 B）；正常登录主控明确保留为“未恢复”，需从正常登录入口重新启动，不在 recover 重建受保护生命周期。
worker 窗格只作历史查询并显示“未恢复”，不重建 PTY、令牌、队列，也不改它的 attempt。已有 pane_exit 可证明停止时执行显示“已中断”；没有结束证据显示“未知”。
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
崩溃残留的 socket/PID 文件：能证明所有者已退出、端点已死的，允许重启（T-096）；所有者存活或未知、端点仍活着的，
仍然阻止启动，产品不会按 PID 猜测所有者并自动接管。

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
Stop 响应关闭后后台才排空反馈队列；响应成功或 paste_written 不表示回车已写出。
观察者应等待该反馈 dispatch 的 turn_submitted，并核对活动提交及写入收据。
Claude 的 PermissionRequest 必须匹配当前 prompt／active；同窗口一次许可 Enter
只记 control action/write，不增加根提交 intent 或替换原 active，普通 Enter 仍按用户提交记录。
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
