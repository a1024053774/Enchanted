# T-216 worker 交接报告

**结论：NO_GO。当前候选不能验收、不能据此关闭 T-216。** 单项目 Claude 路径已有真实入口红绿证据，T-124、T-132、T-171 回归通过；只读行为审查发现两项 P1 投递缺口和一项 P2 处理人显示错误，均未解决。任务要求的 agy 独立审查也尚未执行。按任务书在“需要主控决定”处交接，保留全部现场，不继续扩大实现或缩窄验收范围。

日期：2026-10-31（America/New_York）。工作目录 `/Users/luckye/Documents/Code/a2a-worktrees/T-216`，分支 `t216-issues-controller-first`，基线 `cac1880f0de5bf029abd5838f46f65f2dbe24d67`。没有 commit、push；没有修改主 checkout、T-212 worktree、用户全局 CLI 配置或用户 Herdr/hc。运行环境见 [environment.json](environment.json)。候选完整差异（含新增测试）见 [candidate.patch](candidate.patch)。票据保持 open。

## 已改文件与原因

| 文件 | 改动与目的 |
| --- | --- |
| `workbench/src/gates/core.ts` | `raiseIssue` 保存后调用现有收件箱投递；blocking 不再立即进入“等你决定”；主控可关闭普通 blocking，转交必须带理由；处置保存主控 launch/角色申请引用；保留 T-171 只有用户确认修订失效的规则。 |
| `workbench/src/panes.ts`、`workbench/src/daemon.ts` | 把获批的 Claude 项目终端主控接进既有队列；钩子区分收件箱与用户输入；用原生 transcript 关联 Claude 在 Stop 期间收到的排队消息，防止复用旧 prompt id 导致队列停住；投递附编号、原文、上报者、阻塞标记和命令。此实现的 CLI、跨项目适用范围仍有下述 P1 缺陷。 |
| `workbench/src/contracts/a2aGates.ts`、`workbench/app/IssuesPage.tsx` | 增加“主控已答”，显示处理人、转交理由及重开操作。先答后关闭的显示仍有下述 P2 缺陷。 |
| `workbench/src/terminalCli.ts`、`workbench/src/terminalMcp.ts` | 补主控处置说明和 MCP `disposition` 工具；五类只交用户的问题只写入提示说明，不在门禁按关键词分类。 |
| `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`、`workbench/roles/worker.md`、`.project-map/roles/executor.md` | 写清先交主控、主控回答的来源、关闭/转交命令，以及权限、范围、验收条件、安全、不可逆操作只交用户。 |
| `AGENTS.md`、`CONTEXT.md`、`workbench/README.md` | 同步 T-210 已决定的语义、术语和入口说明；处理 project-map 的 stale README 提示。文档中的目标行为不构成当前候选已经全面通过的证明。 |
| `workbench/tests/test_t216_issue_push_e2e.py` | 文件头先列失败方式，再经真实后台、socket、获批主控终端、真实 Claude 交互模式和 Electron 检查路由/记录/界面；模型是本地脚本化接口。唯一源码夹具补丁向既有 gate 时钟依赖注入偏移，用于 15 分钟检查。支持 `--revision` 跑旧版同一场景。 |
| `workbench/tests/test_t124_controller_e2e.py` | 夹具按真正的“主控答复：/用户答复：”字段识别阶段，避免把 worker 角色说明里的“主控答复”误当答案。答复归因等验收断言未放宽；自带 `answer-as-user` 变异仍被拒绝。 |
| `workbench/tests/test_t132_issues_panel_e2e.py`、`workbench/tests/test_t171_superseded_issue_e2e.py` | 用主控明确转交建立“等你决定”，替换已被 T-210 改写的 blocking 立即等待假设；仍核对真实界面答复、关闭、修订失效与用户输入。 |
| `workbench/tests/test_t078_a13_rehearsal.ts` | 同步恢复收件箱方法的角色/项目参数；该旧隔离场景未通过，见下表。 |

不做的部分保持不变：默认问题视图、跨项目“等你”分组、hc 父子通知；没有加关键词分类器、供应商调用、平行门禁或新的重试路径。Ubiquitous language 沿用 CONTEXT；Tracer bullet 为上报到主控、处置再送回 worker。新增终端入口复用收件箱与队列，不另建一套门禁。

## 命令与结果

完整实际命令及输出路径见 [COMMANDS.md](COMMANDS.md)。重跑须使用新的输出名称，测试拒绝覆盖证据。后台由既有 `transport.ts` 以 `detached: true` 启动；测试 Electron 使用 `start_new_session=True`。模型全部连接夹具的本地脚本化接口，没有调用真实供应商。

| 运行 | 退出码与结果 | 证据 |
| --- | --- | --- |
| 修前原代码的 T-216 场景 | 1，预期红态：主控收不到、blocking 立即等用户 | [red-04.json](red-04.json)、[输出](red-04.log) |
| 最终测试 `--revision cac1880f0…` | 1，同一业务断言拒绝完整基线；红态有效 | [red-05-final-test.json](red-05-final-test.json)、[输出](red-05-final-test.log) |
| 最终候选 T-216 `--gui` | 0，15 项 PASS；范围为同项目 Claude 路径 | [green-05-final.json](green-05-final.json)、[输出](green-05-final.log)、[处理人截图](t216-final-processors.png) |
| T-124 端到端回归 | 0，26 项 PASS | [regression-t124-04.json](regression-t124-04.json)、[输出](regression-t124-04.log) |
| T-124 `--mutant answer-as-user` | 1，预期拒绝：`controller_answer_recorded_as_controller` 看到错误的 `from: user` | [变异摘要](regression-t124-answer-mutant-01.json)、[输出](regression-t124-answer-mutant-01.log) |
| T-132 问题界面回归 | 0，6 项 PASS | [regression-t132-01.json](regression-t132-01.json)、[输出](regression-t132-01.log)、[用户答复截图](t132-user-answer.png) |
| T-171 修订失效回归 | 0，11 项 PASS | [regression-t171-01.json](regression-t171-01.json)、[输出](regression-t171-01.log) |
| T-133/T-107 终端记录回归 | 1，整体 INCOMPLETE；17 项通过，`home_terminal_header_known` 失败 | [当前摘要](regression-t133-01.json)、[输出](regression-t133-01.log) |
| 同一 T-133/T-107 在完整基线 | 1，同样只有上述家目录终端标题项失败；未修范围外问题 | [基线摘要](regression-t133-baseline-01.json)、[输出](regression-t133-baseline-01.log) |
| T-078 inbox domain 隔离测试 | 1，紧急中断两项失败；完整基线同样失败，未改 | [当前结果](regression-inbox-domain-01/results.json)、[基线结果](regression-domain-baseline-02/results.json)、[基线命令输出](regression-domain-baseline-02.log) |
| T-078 pane runtime 隔离测试 | 1，`interrupt_only_esc_not_reclaim` 失败；完整基线同样失败，未改 | [当前输出](regression-pane-01.log)、[基线输出](regression-pane-baseline-01.log) |
| T-078 A13 离线收件箱排演 | 1，INCOMPLETE，首个 UPS 被 `question_origin_unverified` 拒绝；未到恢复收件箱调用，未在旧版复跑，不作归因结论 | [结果](regression-inbox-rehearsal-01/result.json)、[命令回执](regression-inbox-rehearsal-01/command-1.json) |
| `git diff --check` | 0，PASS | 当前工作区检查，无空白错误 |
| `project_map.py status --root .` | 0，PASS，0 problems、0 stale living docs；T-216 仍 open | [status 输出](project-map-status.txt) |

已读回两张真实 Electron 截图：主控答、主控关、转交理由和“你答”均可见。没有据此宣称所有操作序列都正确，先答再关闭的反例仍有问题。

## 每条验收状态

| T-216 验收条目 | 状态 | 依据与边界 |
| --- | --- | --- |
| 修前真实入口红态：收不到投递、blocking 立即等用户 | PASS | `red-04`；最终测试在完整基线的 `red-05-final-test` 再次拒绝。 |
| 非 blocking 与 blocking 各投递一条、带编号原文、不进用户输入 | **NO_GO** | 同项目 Claude 正例通过；agy/opencode 无法被选中，跨项目会漏投或误投。现有断言还未独立证明实际只提交一次。 |
| 主控答复送回 worker，按主控记录，显示“主控已答”，不计等待 | PASS（已测路径） | T-216、T-124 的真实 worker 收件与记录；`answer-as-user` 变异被拒。不能外推到未测 CLI/路由。 |
| 主控附理由交给用户，用户回答记输入并 reply_to 原问题 | PASS（已测路径） | T-216 与 T-132；无理由的转交被拒；静态说明覆盖五类只交用户的问题，不证明模型会自主正确分类。 |
| 无执行主控时排队不丢、15 分钟后等用户 | PASS（已测路径） | 保存 `pending / role_session_missing`；通过既有时钟依赖验证 14 分钟与 15 分钟之后的状态。没有实际等候 15 分钟，也没测排队后主控重新上线。 |
| 角色卡、命令说明写明只交用户类别 | PASS | skill、角色卡、CLI help、MCP 描述均列出权限、范围、验收条件、安全、不可逆操作；门禁没有关键词分类。 |
| agy 独立只读审查无未处理阻塞意见 | **INCOMPLETE** | 尚未执行。本轮额外行为验收审查是新的只读 explorer 上下文，结论 FAIL，不能替代 agy。 |

## 需要主控决定

当前冻结候选的额外只读审查结论为 **FAIL**，详见 [REVIEW.md](REVIEW.md)。发现不是供应商模型判断问题，不能用脚本化模型的绿态覆盖：

1. **P1，agy/opencode 主控投递缺失。** `panes.ts` 要求角色持有者有非空 native session；现有 `terminalCli.ts` 的 agy/opencode 角色申请不提供它，后台原生 hook 记录也只接 Claude/Codex。因此已批准且在线的这两种主控仍被当成没有主控。需要补齐它们真实的会话/进程/回合绑定与不调用供应商的验收方案，不能由 worker 自行把受支持 CLI 排除。
2. **P1，跨项目任务路由错误。** T-193 已允许 A 项目终端主控派发 B 项目任务；当前按 B 项目找执行主控，没有沿已保存的 `parent_launch` 找实际派发者。B 没有主控会漏投，B 有别的主控会误投。需要补来源绑定，并以 A→B、B 另有执行主控的真实反例验收。
3. **P2，先答后关的处理人错误。** 合法执行答复再关闭后，界面仍优先显示历史 answer 的处理人，遗漏关闭者。需要按当前处置展示，保留历史答复，并补该操作序列。

请主控据此安排继续补齐本票或拆分明确依赖，核对与并行 hc 运行时工作的归属；当前不能缩成“只支持单项目 Claude”后标 PASS。上述发现全部保留，未自行修改验收范围、权限或协调其他 worktree。agy 独立审查仍待主控安排。

另外，T-133 家目录终端标题与两组 T-078 紧急中断测试在基线也失败，需主控决定是否另票处理；A13 首个 hook 的失败尚未归因。没有擅自修这些问题。

## 失败现场与未运行项

- `red-01` 是测试字段读取错误，`red-02` 等待钩子超时；`red-03` 遇到外层沙箱拒绝 `sandbox_apply: Operation not permitted` 后被中断（130）。这些不是有效业务红态。外层沙箱外取得的 `red-04` 才是首个有效红态，全部旧输出保留。
- `green-01` 暴露角色确认对没有原生会话记录的主控错误拒绝；已调整就绪检查。`green-03-final` 暴露 Claude Stop 期间提交的 UPS 复用旧 prompt id，导致后续投递不全；已改为用原生 transcript 关联实际完成回合。随后 `green-04-final` 和最终 `green-05-final` 均通过；不把早期绿态或两次运行外推为可靠性保证。
- T-124 的前几轮分别保留角色确认失败、角色说明中“主控答复”被夹具误认、修正夹具时交付标记匹配过严的现场；最终 `regression-t124-04` 通过，原有答复归因反例仍能拒绝错误实现。
- 未运行：Codex/agy/opencode 当前候选投递、跨项目收件人隔离、主控重新上线后的排队恢复、撤销角色与投递竞争、先答再关的界面场景、同一 dispatch 重复实际提交反例、正式打包安装、供应商模型自主判断、agy 审查。没有把这些列为通过。
- 所有测试守护进程和测试 Electron 已通过各自 `finally` 停止；原始夹具保留在各摘要记载的 `/private/tmp` 路径，未删除异常现场。较早错误的辅助基线脚本定位尝试也保留；正式辅助基线以 `regression-domain-baseline-02` 与 `regression-pane-baseline-01` 为准。
- 本轮读取的技能为本机 `project-map`、`evidence-first-testing`、`document-writing`、`frontend-production`、`behavioral-acceptance-review`；这些 SKILL.md 未声明独立版本号，不虚构版本或供应商 tier。额外审查是只读上下文，未改候选。


## 第二轮

**本轮授权子范围：PASS。T-216 整体：INCOMPLETE。** 主控确认第一轮发现 2、3 属本票，已取得本轮修前真实红态并修复；实际 CLI 提交次数已独立核对。发现 1（agy/opencode 投递）按主控指令延期，等待用户确认 T-212 之后的统一 hc 投递方案；本轮未改该机制，不能将整票上调为 PASS。以下是当前状态，第一轮报告正文逐字保留。

### 改了什么

- `workbench/src/gates/core.ts`、`workbench/src/contracts/a2aGates.ts`、`workbench/src/contracts/a2aInbox.ts`：上报时从后台保存的上报会话 `parent_launch` 记录实际执行主控的 `controller_launch`，读取前后复核调用者身份，不接受上报者指定该字段。目标筛选集中在 `inboxTargets`，首次投递和现有排队恢复都用它，跨项目不会借用任务项目的另一位主控。
- `workbench/src/panes.ts`：只在 `controllerThreads` 的目标筛选中加上 launch 精确匹配，共两行。没有改 shell 的队列、drain、钩子回合绑定、transcript 匹配；`daemon.ts` 与第一轮逐字相同。该边界有交付脚本机械核对。
- `workbench/app/IssuesPage.tsx`：按当前状态选择当前处置作为处理人，先答后关显示“主控已关（executor）”；历史答复仍由原来的答复区显示，没有删除或隐藏。
- `workbench/README.md`：把“该项目的执行主控”改为“实际派发上报会话的执行主控”，说明跨项目归属。
- 新增 `workbench/tests/test_t216_round2_e2e.py`：文件头先列失败方式。用真实后台、socket、角色批准、交互式 Claude Code 和本地脚本化接口验证 A→B 两种主控在线情况；A/B 有同名 `T-1`，问题带随机 nonce。界面场景使用真实 Electron。

第二轮只有以上 7 个文件的增量，见 [round2-candidate.patch](round2-candidate.patch)。第一轮候选源码快照的位置见 [round2-baseline.json](round2-baseline.json)，用于同一测试的修前重跑。Deep modules 的边界是统一目标筛选；没有新增重试、双写或平行投递 API。

### 跑了什么

实际命令、输出路径和可重跑参数见 [ROUND2-COMMANDS.md](ROUND2-COMMANDS.md)。全部重跑使用新文件名，第一轮输出没有覆盖。测试仍只连接本地脚本化模型，不调用供应商；后台与测试 Electron 沿用脱离调用者进程组的启动方式。

| 检查 | 修前 | 修后 / 当前结果 |
| --- | --- | --- |
| A 主控派 B 任务，B 另有执行主控 | 退出 1，A 的 CLI 收到 0 次、B 收到 1 次，业务断言拒绝：[红态](round2-red-routing-online-01.json) | 退出 0，A 实际提交 1 次、B 0 次、收据 delivered，3 项 PASS：[绿态](round2-green-routing-online-01.json) |
| A 主控派 B 任务，B 无执行主控 | 退出 1，A 收到 0 次，错误排队 `role_session_missing`：[红态](round2-red-routing-offline-01.json) | 退出 0，A 实际提交 1 次、不排队，3 项 PASS：[绿态](round2-green-routing-offline-01.json) |
| 主控先答，再关闭；显示当前关闭者、保留历史答复 | 退出 1，已关闭仍显示“主控已答”：[红态](round2-red-processor-01.json) | 退出 0，5 项 PASS；实际 Electron 显示“主控已关（executor）”，历史答复可见：[绿态](round2-green-processor-01.json)、[截图](round2-answer-then-close.png) |
| 实际提交次数断言的反例 | 经测试窗口再次提交 CLI 已收到的同一正文，生产机制不变 | 退出 1，预期拒绝；原生 transcript 有两个不同 uuid/prompt_id，`dispatch_queued_count` 仍为 1，`cli_actual_submission_count_is_one` 失败：[反例](round2-duplicate-counterexample-01.json) |
| 原 T-216 主路径回归（含 Electron） | 不复用旧候选通过结论 | 退出 0，15 项 PASS：[摘要](round2-regression-t216-01.json) |
| T-124 主控答复 / run / attach 回归 | 同上 | 退出 0，26 项 PASS：[摘要](round2-regression-t124-01.json) |
| T-132 问题面板回归 | 同上 | 退出 0，6 项 PASS：[摘要](round2-regression-t132-01.json) |
| T-171 修订失效回归 | 同上 | 退出 0，11 项 PASS：[摘要](round2-regression-t171-01.json) |
| 定向只读行为复审 | 只复审本轮授权子范围 | PASS，无本轮未处理发现：[ROUND2-REVIEW.md](ROUND2-REVIEW.md)。不是 agy 审查。 |

实际次数逐条读取 Claude 自己原生 transcript 的 root user 消息行，不去重，不把重复携带历史的模型 API 请求当成新提交，也不以 `dispatch_queued` 代替实际收件。计数正例和真实重复提交反例均已运行。截图已人工读回，关闭者与历史答复均清晰可见。

交付核对命令：`python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2_delivery_check.py`；输出保存在 [round2-delivery-checks.log](round2-delivery-checks.log)，核对禁止改动的机制、第一轮报告前缀、冻结差异、UTF-8、本地链接、`git diff --check`、project-map status 和夹具进程收尾。

### 验收条目的当前状态

| 本轮要求 | 当前状态 |
| --- | --- |
| A→B，B 主控在线，只投 A、不投 B | PASS |
| A→B，B 无主控，仍投 A、不排队 | PASS |
| 主控先答后关，显示当前关闭者，历史答复保留可见 | PASS |
| 同一消息在 CLI 实际只提交一次；断言能拒绝实际重复 | PASS |
| shell 队列/drain、钩子绑定、transcript 匹配不改 | PASS |
| agy/opencode 投递 | INCOMPLETE，按本轮指令延期；未实施待确认的 hc 方案 |
| 不处理范围外基线失败 | PASS，T-133、T-078、A13 本轮没有重跑或修改 |

| 原 T-216 验收条目 | 当前状态与范围 |
| --- | --- |
| 修前真实入口红态 | PASS，第一轮红态保留；本轮另有两条路由和一条界面红态 |
| 非 blocking/blocking 各投递一条、编号原文、不进用户输入 | INCOMPLETE（整项）；已测 Claude 同项目与跨项目子范围 PASS，实际次数有原生记录正反例；agy/opencode 延期缺口仍在 |
| 主控答复送达 worker、归因为主控、显示“主控已答”、不计等待 | PASS（已测 Claude 路径），本轮 T-216/T-124 重新通过，先答后关显示也已修复 |
| 附理由交用户、用户答复记输入并 reply_to | PASS（已测 Claude 路径），本轮 T-216/T-132 回归通过 |
| 无主控时排队不丢、15 分钟兜底 | PASS（既有已测路径），本轮原 T-216 重新通过；仍用门禁时钟依赖验证，未实际等待 15 分钟 |
| 角色卡和命令说明列出五类只交用户 | PASS，说明保留，门禁未加关键词分类；不宣称模型自主判断已实测 |
| agy 独立只读审查无未处理阻塞意见 | INCOMPLETE，仍待主控安排；本轮只读复审不替代该项 |

### 未运行与交接

- 本轮没有修复或实测 agy/opencode 投递，没有切换到 hc `terminal.send`，没有连接用户的 Herdr/hc；这部分继续等待主控与用户确认。
- 没有新增其他 CLI、跨项目 reviewer/monitor、角色撤销/重新上线竞争场景的实测；共享筛选代码不替代这些入口证据。没有用本地脚本化接口证明模型自主判断。
- 范围外基线失败按主控指令交由主控登记，本轮不再处理。没有新建范围外票、改验收条件、写用户全局配置、碰主 checkout 或 T-212。
- 第一轮报告内容逐字保留。本轮未 commit、未 push；独立审查与提交继续由主控安排，T-216 不关闭。


## 第三轮

**第三轮迁移与 hc 复跑子范围：PASS。T-216 整体：INCOMPLETE。** 已把完整候选搬到主控指定的当前 main，并在 hc 托管的项目终端里重新取得所列场景的通过和反例证据。agy/opencode 投递仍按本轮指令延期，agy 独立审查未执行；没有据此将整票标为 PASS。本节记录当前状态，前两轮内容逐字保留。

### 搬迁与改动边界

- 迁移前基线为 `cac1880f0de5bf029abd5838f46f65f2dbe24d67`。先保存了 [round3-before-rebase.patch](round3-before-rebase.patch)，使用 `git diff --binary HEAD`，并追加两个未跟踪测试的完整 diff；迁移前现场及文件清单见 [round3-before.json](round3-before.json)。
- 按指定顺序运行 `git stash push -u` → `git merge --ff-only main` → `git stash pop`。快进到 `9c0e262125edb75ed841609472e32c952adc2bbd`（包含 T-212 的 `8006f37ea`）。stash pop 无冲突、退出 0，并自动删除成功恢复的该条 stash；没有人工丢弃冲突现场。记录见 [round3-migration.txt](round3-migration.txt)。
- 恢复后的完整差异（含未跟踪测试）保存在 [round3-candidate.patch](round3-candidate.patch)。自动合并后没有再改生产源码或业务测试，也没有增加源码提交、push 或修改主 checkout。
- 项目 shell 仅经 T-212 的 `hc.run`、`attachShell` 运行，写入仍经编排后台的 hc attach DATA 通道。没有恢复 node-pty 的项目 shell 路径；受管 worker/reviewer 的原有运行时没有在本轮换掉。
- 原候选的 `controllerThreads` 目标筛选保留在 T-212 之后的同一类位置。`shellInput`、钩子回合绑定/`terminalTurn`、dispatch 队列、`wakeThread`、`drain` 和 transcript 匹配与迁移前候选逐字一致；没有接 `hc terminal.send`。冻结差异与机制核对见 [round3-mechanism-check.json](round3-mechanism-check.json)、[交付检查](round3-delivery-checks.log)。

### 命令与运行结果

全部实际命令及重跑方式见 [ROUND3-COMMANDS.md](ROUND3-COMMANDS.md)。各次都使用新输出名称。以下退出码指业务测试本身；预期反例的退出 1 不算业务正例通过。

| 场景 | 当前结果 | 新证据 |
| --- | --- | --- |
| A 主控派 B 任务，B 另有主控在线 | 退出 0，3 项 PASS；A 的 CLI 实际 1 次、B 0 次 | [业务摘要](round3-routing-online-01.json)、[hc 身份与清理](round3-routing-online-01.hc-recovered.json) |
| A 主控派 B 任务，B 无主控 | 退出 0，3 项 PASS；仍投 A、不排队，实际 1 次 | [业务摘要](round3-routing-offline-01.json)、[hc 身份与清理](round3-routing-offline-01.hc-recovered.json) |
| 主控先答、再关闭 | 退出 0，5 项 PASS；显示当前关闭者，历史答复保留 | [业务摘要](round3-processor-01.json)、[hc 身份与清理](round3-processor-01.hc-recovered.json)、[真实 Electron 截图](round3-answer-then-close.png) |
| 同一正文实际重复提交反例 | 退出 1，预期业务断言拒绝；CLI 原生记录 2 次，队列登记仍 1 条 | [反例原始摘要](round3-duplicate-01.json)、[hc 身份与清理](round3-duplicate-01.hc-recovered.json) |
| 原 T-216 主路径（含界面） | 退出 0，15 项 PASS | [摘要](round3-t216-01.json)、[hc 身份与清理](round3-t216-01.hc.json) |
| T-124 回归 | 退出 0，26 项 PASS | [摘要](round3-t124-01.json)、[hc 身份与清理](round3-t124-01.hc.json) |
| T-132 回归 | 退出 0，6 项 PASS | [摘要](round3-t132-01.json)、[hc 身份与清理](round3-t132-01.hc.json) |
| T-171 回归 | 退出 0，11 项 PASS | [摘要](round3-t171-01.json)、[hc 身份与清理](round3-t171-01.hc.json) |
| `test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen` | 退出 0，7 项 PASS；真实 Electron、尺寸不匹配、重启重接及用户 core 前后不变 | [run.json](round3-t212-01/run.json)、[命令输出](round3-t212-01.log)、[重接截图](round3-t212-01/reattached-terminal.png) |
| 新基线迁移只读行为验收 | PASS，仅限本轮子范围 | [ROUND3-REVIEW.md](ROUND3-REVIEW.md) |
| `git diff --check`、project-map status | PASS；0 problems、0 stale living docs | [交付检查输出](round3-delivery-checks.log) |

**Claude 投递在 hc 项目终端中照常工作，实际提交次数的计数仍成立。** 正例和反例仍使用真实原生交互 Claude CLI，本地脚本化模型，不调用供应商。原生 transcript 的 root-user 行逐条计数，不去重、不用模型 API 反复携带的历史计数，也不以 `dispatch_queued` 代替实际提交。对照 hc terminal 的 launch/pid、角色 native session、dispatch 与原生 prompt id，确认实际收件的主控属于本次测试私有 hc，而不是旧 node-pty 项目终端。截图已读回，关闭者和历史答复可见。

### 外层采集问题与失败归因

- 所有指定业务正例都通过，没有出现候选与 T-212 的结合失败，亦未触发“纯 main 同场景复跑”的对照条件。没有把第一、二轮的绿态当作本轮通过证据。
- 最先四次运行的外层 hc 证据采集使用 Python SQLite URI `mode=ro`，均报 `unable to open database file`。其中三次业务测试已退出 0，重复提交反例按预期退出 1；前三个包装命令因此退出 2。旧 `.hc.json` 的 INCOMPLETE 与错误保留，没有覆盖或改写。
- 修正的是仅位于证据目录的 [run_round3.py](run_round3.py)：对已关闭后台的自有夹具数据库用普通连接执行 SELECT，并保证私有 core 收尾。用 `--existing` 对同一原现场补采，写入新的 `.hc-recovered.json`；没有重跑业务测试、修改事件或变更生产代码。四份补采均 PASS，私有 core 均返回 `stopped:true`。
- 后续四套回归的外层采集及私有 core 停止均一次 PASS。T-212 自身也已停止该次专属 core。私有 hc 的注册表和凭据仍只留在 `/private/tmp` 夹具中，没有复制到证据目录；公开证明只保存选取的 session/socket/terminal/launch 字段。

### agy/opencode 在 hc 之后的现状

**INCOMPLETE，仍收不到本候选的项目主控问题投递；本轮未修、未调用这两家 CLI。** 当前原因由新基线上的可达源码路径确认：

1. `terminalCli.ts` 的角色申请与 MCP 申请仍只给 Claude/Codex 填 `native_session`、`native_home`，agy/opencode 的标准申请不会填这两个字段。
2. 候选的 `controllerThreads` 仍要求获批角色有非空 `held.session`，且与 `pane.nativeReport.session` 相同；agy/opencode 会在收件目标筛选中被排除。
3. T-212 改了 shell 承载、attach 写入、屏幕和持有进程，未改变这些角色字段或收件资格。hc shell 的 OSC 处理更新 `cliTurn`，并没有据此给角色补 native session 或替代现有主控钩子/队列绑定。

因此，迁到 hc 并未消除第一轮发现 1 的阻断。等待用户定的统一 `terminal.send`/OSC 方案没有在本轮偷做；也没有把“hc 已能承载这两家 CLI”写成“本票问题投递已经打通”。此处是当前源码结论，不冒充两家 CLI 的新运行验收。

### 当前交接状态与限制

| 项目 | 状态 |
| --- | --- |
| 候选搬到指定 main，完整差异和未跟踪文件保存 | PASS |
| Claude 同项目/跨项目投递、关闭显示在 hc 上重新证明 | PASS（已测场景） |
| 实际提交次数正例与重复反例在 hc 上仍有效 | PASS |
| 指定 T-124、T-132、T-171 和 T-212 回归 | PASS |
| 不改投递机制、不恢复 node-pty shell、不接 `terminal.send` | PASS |
| agy/opencode 项目主控投递 | INCOMPLETE，继续延期 |
| agy 独立只读审查 | INCOMPLETE，本轮只读行为审查不替代该项 |
| T-216 整票 | INCOMPLETE，不关闭、不提交、不 push |

未扩展为其他 CLI 的投递、跨项目 reviewer/monitor、角色撤销/重上线竞争或真实模型判断测试。没有连接用户的 Herdr/default hc core，没有写用户 `~/.claude`、`~/.codex`，没有改主 checkout；本轮服务仅使用测试专属 `enchanted-*` session 与私有 socket。前两轮报告逐字保留；当前源码无本轮新增提交，后续方案与最终审查交由主控。


## 第四轮

**BLOCKED：hc 0.1.15 的状态条件不能表达 done，无法按本轮契约安全投递给回合结束报 done 的 Claude/agy。** 本轮在实际核对 hc 参数后停止实现，等待主控决定；没有改生产代码、测试或现行说明，没有绕过条件、伪造 idle、增加先查后送路径或修改 hc。T-216 整体验收仍为 INCOMPLETE；第三轮的通过证据仅对第三轮候选有效，不充作本轮新机制的绿态。

### 任务来源与失败方式清单

读取了 main `fc173bf81cd646eee5e1a2bd8e2c92db702fd0b8` 的最新 [票面副本](round4-ticket-main.md) 和 T-211 实测结果；worktree HEAD 保持 `9c0e262125edb75ed841609472e32c952adc2bbd`，没有再次快进。新授权要求四家 CLI 统一走私有 hc 的条件 `terminal.send`，在同一次送入中保证状态条件。

本轮进入行为测试前识别的失败方式（业务断言尚未编写，以下不是已执行覆盖）：

1. hc 的 `if` 不接受 done、多状态条件，或者把 `wait` 误当成等待可接收再送入，导致 Claude/agy 回合结束后一直排队。
2. 目标仍按原生会话号选，agy/opencode 无收件人；跨项目派发又误投给任务项目的主控。
3. 检查状态与输入分开，忙碌或 blocked 竞争中误答权限框、问答框。
4. attach 中的用户草稿未预留，系统消息混入草稿；清空或发出后队列不恢复。
5. hc 成功返回却没进入 working，被误记已确认；未知时自动重发，CLI 实际收到两次。
6. 只数派发登记、API 历史或 hc turn，没数 CLI 原生实际提交；Codex 启动的 working→idle 被当成收件确认。
7. 系统投递进入 user_inputs 或人工介入；记录缺 dispatch、目标终端、hc 返回、确认结果。
8. 忙/无主控排队后丢失、乱序、改写正文，或破坏 15 分钟规则、先答后关与历史答复显示。
9. 连错 core；真实 CLI 测试写入禁止的全局目录、超出获准提示词，或公开 agy 邮箱。

### hc 实际参数与边界结果

证据：[原始 RPC 返回及帮助](round4-hc-probe-01.json)、[二进制导出的 schema](round4-hc-schema.json)、[第一次探针原稿](round4_hc_probe-01.py)。命令、可重跑脚本与不覆盖旧证据的重跑方法见 [ROUND4-COMMANDS.md](ROUND4-COMMANDS.md)。本次进程与 core 都是测试自建的私有夹具，不连接用户 Herdr/default core，也没有使用供应商模型。

- 二进制实际版本是 **0.1.15**。`terminal.send` 语义为粘贴后回车；schema 描述无人键入约 3 秒后送入，等待期间的键入被暂存。此项是 schema 描述，本轮没有测竞态行为。
- `if` 的 schema 引用 `IdleOrWorking`，枚举仅有 `idle`、`working`。RPC `if: "done"` 报 `-32602 invalid_params`，原文 `unknown variant done, expected idle or working`；数组 `["idle","done"]` 和字符串 `"idle,done"` 同样被拒绝。不能传多个状态。
- 夹具程序只发 `OSC 7501 state=done`。`terminal.get` 实际返回 `reported:true`、`status.state:"done"`。随后同一 `terminal.send` 带 `if:"idle"`，返回 `-32000 status_mismatch`：`t1 is done, not idle`，并附 `nothing was typed`。这说明 hc 并没有把 done 当 idle 处理。`if:"working"` 也被拒绝。
- 存在布尔 `wait`、数值 `timeout` 参数；schema 说明 `wait` 是**送入之后等该回合结束**，不是等可接收再输入。`wait:true, timeout:1` 配合不匹配的条件，仍先返回同一 `status_mismatch`；`wait:"idle"` 报类型错误。本轮没有成功送入，因此没有证明 wait 的成功路径或实际等待时长。
- 探针以退出 0 完成：这是能力探针成功采到错误返回，不是产品投递绿态。`terminal.read` 没有收件内容；最后私有 core 返回 `stopped:true`。公开证据只含临时身份和无账号信息的夹具输出。

T-211 的事实是 Claude Code、agy 回合结束报 done，opencode 报 idle。因此，按当前固定版本使用 `if:"idle"` 会让前两者无法在回合结束后接收；改用 `if:"working"` 又违反忙时不送入。去掉条件、先查 done 再无条件送入、写假 OSC 把 done 改成 idle，都不满足本轮授权。没有实施这些路径。

### 改动与检查

本轮只新增证据、探针和报告末尾本节。包含全部未跟踪源文件的 [round4-candidate.patch](round4-candidate.patch) 已保存，与第三轮完整候选逐字相同；没有为“只支持 idle”先做一套部分实现，也没有先删旧机制造成不可运行候选。

| 本轮项目 | 状态与实际结果 |
| --- | --- |
| 读取最新票面、确认固定 hc 能力 | PASS，取得上列真实 RPC 反例及 schema |
| 第三轮候选上 agy/opencode 真实入口红态 | INCOMPLETE，未编写/运行；能力探针不是这一红态的替代 |
| 统一 terminal.send + OSC 确认实现 | BLOCKED，done 无可用的状态条件 |
| Claude 本地接口、Codex/agy/opencode 替身绿态；blocked/草稿/忙/未知界面 | INCOMPLETE，均未编写/运行 |
| 去条件与未知重发的至少两个变异 | INCOMPLETE，未运行 |
| 本轮 T-216、第二轮、T-124、T-132、T-171、T-212 指定回归 | INCOMPLETE，未重跑；生产候选未改，不沿用第三轮结果标本轮通过 |
| 真实 agy/opencode 供应商最小确认 | INCOMPLETE，未启动；应在机制证明后进行，本轮未到该阶段 |
| 真实 Codex、本地接口适用性确认 | INCOMPLETE，未调查/运行，不能声称工装不可用 |
| README、角色卡、a2a 技能改为新投递说明 | INCOMPLETE，未实施新机制，因此未将说明先改成未发生的行为 |
| project-map status、git diff --check | PASS，收尾 0 problems、0 stale living docs；diff 检查退出 0 |
| 完整候选保存、前三轮报告逐字保留 | PASS，见补丁及 [交付核对](round4-delivery-checks.log) |

| 最新 T-216 票面验收 | 当前状态 |
| --- | --- |
| 修前上报不投递、blocking 直接等用户的真实红态 | PASS，首轮既有红态保留；本轮未增加业务红态 |
| 非 blocking/blocking 各一条、编号原文、不进用户输入 | INCOMPLETE，新统一路径未实施/验证；旧 Claude 路径证据不替代它 |
| 四家各只实际提交一次；忙/blocked/草稿排队；未知不重发 | BLOCKED，hc done 条件缺口；其余子场景本轮未测 |
| 主控答复送达 worker、归因为主控、问题状态与等待计数 | INCOMPLETE（本轮未重跑）；第三轮旧机制场景 PASS 记录保留 |
| 附理由交用户、用户答复输入 reply_to | INCOMPLETE（本轮未重跑）；第三轮记录保留 |
| 无主控排队、15 分钟兜底 | INCOMPLETE（本轮未重跑）；第三轮记录保留 |
| 角色卡列五类只交用户 | PASS，既有文本仍在；未宣称模型判断实测 |
| agy 独立只读审查无未处理阻塞意见 | INCOMPLETE，未执行；能力阻断阶段未提交完成候选供审 |

### 需要主控决定

**BLOCKED：需要先解决 hc 的 done 条件能力，再继续本轮实现。** 最小方向是让使用的 hc 构件支持 done 的原子条件送入（单值 done 即可，不必多值）：主控确认可用构件及事实后，明确授权相应的固定版本/构件变更，再继续。当前规格不允许改 hc 源码或 fork；worker 不自行扩大到 hc 实现、升级依赖或改验收。

若继续固定 0.1.15，当前已证事实下无法同时做到“四家回合结束后投递”与“送入同次带状态条件”。主控如要延期其中一项，需要另行明确调整范围/验收；本轮不自行选择。`wait` 的存在不能解除此阻断，因为状态不匹配时输入尚未发生就已被拒。

未知与未跑项已逐项列明，没有新增供应商调用、用户全局配置写入、主 checkout 改动、commit 或 push。前三轮报告未改写，停止在这一能力决定点，等待主控处理。
