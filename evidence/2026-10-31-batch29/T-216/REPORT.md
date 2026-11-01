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


## 第五轮

**本轮行为实现与工程验收：PASS。最新正式验证的私有路径检查：PASS；早期路径偏差仍为 INCOMPLETE，详见“需要主控决定”。T-216 整票：INCOMPLETE，还需路径边界复核及 agy 独立只读审查。** 四家项目终端主控统一走私有 hc 0.1.15 的 `terminal.send`；当前候选的正例、指定业务反例、恢复场景和回归均已完成。没有 commit、push 或再次快进 main。前四轮正文逐字保留。

### 依据与 hc 成功路径

读取了 `9e23109b6` 的[最新票面](round5-ticket.md)。采用的是**执行主控第五轮决定**，不是追加用户裁定：idle 带 `if:"idle"`，done 不带 `if`，一律不带 `force`。源码仍基于 `9c0e262125edb75ed841609472e32c952adc2bbd`；本轮 main 对照运行时已到 `4a31cf3e09afabd095e99c6bd74eee87f2479090`，其 `workbench/src` 与该基线没有差异。

[hc 原始探针](round5-hc-probe-02.json)使用测试自建 core、真实终端与按键读取程序，实际观察到：

| 输入与状态 | hc 实际返回及独立收件 |
| --- | --- |
| done，无 if，`caller` 为本次目标终端，`wait:true, timeout:1` | `started:true, status:done, turn:0`；`wait.reason:status, ended:true, status:done, turn:1`；程序实际收到 1 次 |
| idle，`if:idle`，同样 caller/wait | `started:true, status:idle, turn:0`；关联 wait 的 turn 为 1；实际 1 次 |
| blocked，不带 force、不带 if | `-32000`、`kind:blocked`，提示输入会回答对话框；程序没有任何输入 |
| idle，程序收到后故意不开始回合 | 实际 1 次，`started:false`、`wait.reason:not_started`、`ended:false`，约 6 秒返回 |

`wait` 等的是**这次送入关联的回合**，不是等待可接收再输入。`timeout:1` 不把 hc 内部判断开始回合的时间缩成 1 秒。客户端总 RPC 期限仍为 15 秒；异常或不能确认都进入未知，不重发。第四轮已证明 `if` 只能 idle/working，不能 done 或多值；版本未改、hc 未改。

代码以同次 send 的 `started`、关联 wait 终端和 turn 判定确认，不拿一条独立 working 或全局 turn 递增作证，Codex 启动的 working→idle 不会充作收件确认。done 的窄竞态及未来支持 `if:done` 后的移除条件已写进代码注释。

### 失败方式清单与改动

沿用第四轮清单，并将第 1 条改为 idle/done 两路状态条件与关联确认；补充 idle→working 的原子拒绝、hc 自身拦 blocked、角色变化、后台重接、送入中断窗口。当前测试覆盖的失败方式是：

1. 条件用错、带 force，或把任意 working 当成本次送入确认。
2. 按 native session 选人；跨项目投错；终端/前台 CLI/批准角色已换还送旧通知。
3. auth、权限框、问答框、忙碌时误送；idle 临送入变 working 仍被输入。
4. 草稿与通知混在同一次提交；草稿发出/清空后不恢复；后台重接丢草稿预留。
5. 送入但未开始回合仍称已确认，未知时自动重发，或只数队列不数 CLI 实际提交。
6. 重启丢掉尚未发送的队列；hc 已收件但确认未落盘时退出，重接不显示未知或重复输入。
7. 系统通知进入用户输入或人工介入；记录缺派发号、目标终端、hc 返回或确认结果。
8. 原生提问的用户答复漏记，或破坏主控答复、交用户、关闭历史和 15 分钟规则。

本轮新增/修改的文件（完整补丁仍含前几轮未提交的候选）：

| 文件 | 原因 |
| --- | --- |
| `workbench/src/hc.ts` | 目标私有终端的单一 `terminal.send` 调用，传 caller/wait，不传 force |
| `workbench/src/panes.ts` | 目标按批准角色/终端/项目/前台 CLI；OSC 顺序事件驱动；草稿预留；关联确认与未知；按持久结果恢复队列和中断意图 |
| `workbench/src/store.ts` | 派发记录保留原收件角色；排队后切成 ideation 不会收 executor 通知 |
| `workbench/src/daemon.ts` | 角色就绪接回既有收件箱；保留独立的 Codex 结构化用户答复记录路径 |
| `workbench/src/sidebar.ts`、`workbench/app/renderer.tsx` | 显示“投递确认未知”，暴露对应派发号；不删除原有用户提问状态用途 |
| `workbench/README.md`、`.project-map/roles/executor.md`、`workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md` | 改写为现行 hc 投递、排队和未知处理说明，保留五类只交用户规则 |
| `workbench/tests/test_t216_hc_delivery_e2e.py` | 真实后台/门禁/私有 hc，替身实际输入计数，状态竞争、草稿、恢复、身份与变异 |
| `workbench/tests/test_t216_real_cli_delivery_e2e.py` | Codex 真实 CLI 加本地接口，以及原生供应商 CLI 最小确认和原生记录计数 |
| `workbench/tests/test_t216_issue_push_e2e.py` | Claude 原生 root-user 记录逐条计数，覆盖非 blocking 与 blocking；等待原生日志实际落盘 |
| `workbench/tests/test_t133_codex_terminal_controller_e2e.py` | 同步既有变异的定位文本，确认失败落到业务断言 |

项目终端投递用的 Claude transcript 匹配、原生会话筛选、shell 钩子回合绑定已经删除；没有保留第二条终端投递路径。**仍保留的其他用途**：Claude/Codex 原生会话链接、额度读取、用户提问及答复记录、原有侧栏提问状态，以及受管 worker/reviewer/monitor 的身份和回合验证。这些不决定项目终端的收件资格或投递确认。本轮没有迁移受管窗格运行时。

草稿只保存在应用私有状态快照，不成为用户输入记录。写入意图尚未闭合或快照损坏时不猜空；正常重接保留原草稿。派发恢复只把“未尝试”或 hc 明确拒绝、确定没有输入的项重新入队；未闭合的 send intent 追加未知记录，保持不重发。

### 红绿态与最终复跑

全部实际命令见 [ROUND5-COMMANDS.md](ROUND5-COMMANDS.md)，最终运行索引见 [28 项清单](round5-confined-accepted-runs.json)。输出均另起文件名。以下是**当前候选**的结果；退出 1 的反例没有被改写为正例 PASS。

| 场景 | 修前/反事实 | 当前结果 |
| --- | --- | --- |
| agy/opencode 上报即送 | 当前同一测试跑保留的第三轮源码，两者都在 `issue_reaches_cli` 失败，实际 0 次、`role_session_missing`：[agy](round5-final-red-agy.json)、[opencode](round5-final-red-opencode.json) | 两家 states 各 19 项 PASS，覆盖 auth blocked、done/idle、忙碌、问答、草稿发出和清空：[agy](round5-confined-states-agy.json)、[opencode](round5-confined-states-opencode.json) |
| idle 临送入变 working | 真实 hc 在同次输入内拒绝，无任何实际输入 | [race](round5-confined-race.json) 7 项 PASS，随后可接收时仅送 1 次 |
| 角色/前台 CLI 变化 | [角色红态](round5-red-role-change-01.json)：ideation 误收 executor 队列 | [角色](round5-confined-role.json) 7 项、[前台 CLI](round5-confined-identity.json) 6 项 PASS |
| 后台重接前已有草稿 | [红态](round5-red-restart-draft-02.json)：草稿与通知同次提交 | [绿态](round5-confined-restart.json) 7 项 PASS，草稿与通知分开 |
| 重启恢复未送队列 | [红态](round5-red-restart-queue-01.json)：两条都未送、队列丢失 | [绿态](round5-confined-restart-queue.json) 6 项 PASS，两条按原序各 1 次 |
| 已送入、确认未落盘时退出 | [红态](round5-red-restart-unknown-01.json)：收据 unknown，界面仍空闲无提示 | [绿态](round5-confined-restart-unknown.json) 6 项 PASS，实际仍 1 次；[真实 Electron](round5-confined-restart-unknown.png)显示未知 |
| 普通未开始回合 | 替身收到后不发 working | [unknown](round5-confined-unknown.json) 6 项 PASS，未知且不重发；[截图](round5-confined-unknown.png)已读回 |
| 原 T-216 Claude 主路径 | 首轮真实业务红态保留；本轮另加原生计数 | [18 项 PASS](round5-confined-t216.json)：三条问题各实际 1 次，含非 blocking、blocking、处置与用户答复 |
| 第二轮跨项目/先答后关 | 不复用旧候选结论 | [B 在线](round5-confined-r2-online.json) 3、[B 不在线](round5-confined-r2-offline.json) 3、[先答后关](round5-confined-r2-processor.json) 5 项 PASS |
| T124 / T132 / T171 | 失败与对照见下节，原记录保留 | [T124](round5-confined-t124.json) 26、[T132](round5-confined-t132.json) 6、[T171](round5-confined-t171.json) 11 项 PASS |
| T212 指定命令 | 真实 Electron、`--electron-screen --mismatched-screen` | [7 项 PASS](round5-confined-t212/run.json)，私有 core 与用户 core 边界不变 |
| 用户原生提问记录 | [T133 红态](round5-t133-codex-01.json)：选项答复漏记 | [当前 T133](round5-confined-t133-codex.json) 16 项 PASS，answer/原问题/非空 reply_to 均读回 |

### 必须守住的变异

| 变异 | 实际结果 |
| --- | --- |
| 仅去掉后台 blocked 过滤 | [PASS，20 项](round5-confined-mutant-blocked.json)：hc 返回 blocked，替身没有输入，证明不是仅靠后台判断 |
| 在此基础上加 force | [预期退出 1](round5-confined-mutant-force.json)，`startup_auth_no_input` 失败，实际输入进入 blocked 终端 |
| 去掉后台 working 过滤 | [预期退出 1](round5-confined-mutant-working.json)，`working_no_input` 失败，忙时实际收件 |
| 未确认后自动重发 | [预期退出 1](round5-confined-mutant-resend.json)，`unknown_never_resent` 失败，实际收件 2 次 |
| 同一正文再实际提交给 Claude | [预期退出 1](round5-confined-r2-duplicate.json)，CLI 原生 2 次、队列仍仅登记 1 次 |
| T133 去掉结构化答复解析 | 原靶点先在夹具定位失败，不计作业务反例；修正后[业务运行](round5-confined-t133-mutant.json)通过前 12 项，再在 `only_approved_prompts_recorded` 失败；API 健康、hc 收尾正常 |

### 真实 CLI 与原生计数

| CLI | 当前最终确认 | 模型/强度与限制 |
| --- | --- | --- |
| Claude Code | 原主路径用真实交互 CLI、本地脚本化接口；每个 issue 的原生 root-user 行逐条计数，三条各 1 次 | 未调用 Claude 供应商；不把本地返回的脚本标签当真实模型证明 |
| Codex 0.164.0 | [本地接口](round5-confined-codex-local.json)与[供应商](round5-confined-codex-vendor.json)均 PASS，各 1 次 | 原生 turn_context 为 gpt-6.1-sol、high；不是供应商实际 tier 证明 |
| agy 1.4.12 | [真实供应商确认](round5-confined-agy.json) PASS，原生 steps 中该用户提交仅 1 条 | 模型、强度 unknown；本次信任只新增测试目录 1 条 |
| opencode 2.1.4 | [真实供应商确认](round5-confined-opencode.json) PASS，原生 session_message 中仅 1 条 | 原生模型配置字段为 deepseek-v4.1-flash-free、provider=opencode、variant=max；a2a 未取得可核对的强度，仍 unknown，不推断实际服务 tier |

[原生事实摘要](round5-confined-native-facts.json)。agy/opencode 在真实 HOME 下由产品 shim 启动；本地 worker/Claude 接口仍是隔离 HOME，不调用真实供应商。真实提示只要求申请角色及固定回复 T216_OK，不派其他工作。原生计数不去重，不数 API 重复历史，也不以 hc turn 总数代替提交次数。

Codex 供应商确认只复制 auth.json 到测试 CODEX_HOME，生成仅信任本次夹具的配置与两条 git add/git commit allow 规则；明确选择隔离 home 的钩子信任，遇本地 socket 权限时只批准单次 `a2a request executor`，不批准前缀。首次单次批准另有 [记录](round5-codex-vendor-01.manual-approval.json)，最终夹具将相同核对纳入脚本。每次结束都删除整个 CODEX_HOME，仅保留自己的 rollout，不保存 auth 副本。

agy 的信任先核对本次目录和选中 Yes 的画面，再按回车，最后比较设置仅多本目录；没有直接改全局配置。第五轮不同候选/驱动的 4 次真实 agy 确认各新增 1 个测试目录，[累计清单](round5-agy-trust-total.json)为 4 条，不把多次运行说成只写过一次。对外交付的摘要和终端副本已遮邮箱，不发布 agy 账号截图，不复制用户凭据或完整全局数据库。原生 CLI 最小确认不证明模型会正确判断五类只交用户的问题。

### 审计、异常与未抹掉的失败

- [审计 01](ROUND5-REVIEW-01.md) FAIL：T133 用户答复漏记，已有真实红绿修复。[审计 02](ROUND5-REVIEW-02.md) FAIL：队列/未确认中断恢复缺口，随后新增上述真实红态再修复。[审计 03](ROUND5-REVIEW-03.md) PASS，余一条 P2 变异靶点；[最终限定核对](ROUND5-REVIEW-04.md) PASS，确认只有该一行测试定位变化，P2 已关闭。前三个冻结快照分别保存在 review1/2/3.patch；最终完整差异为 [round5-candidate.patch](round5-candidate.patch)。这些审计都不是 agy 审查。
- 早期 hc 探针没有等首次 done 被解析，返回 started:null；保留为 probe-01，不能作成功 done 证据。probe-02 等实际 reported 后重跑取得上表结果。
- race 首次夹具在同步函数里插入 await，导致启动语法错误；仅改测试副本屏障后同场景通过。restart-draft 首次 operator 文件未换名而 EEXIST，收尾另有记录；均非业务红态。
- Claude 首次原生计数抢在第三条日志落盘前；改为等待完整原生日志可见，断言仍要求每条仅 1 次。第二次暴露 hc wait 持上报操作锁的问题，已改成先登记队列、异步送入，使主控收到后可以立即答复；当前 18 项通过。
- T124 两次在 attach 遇 operation_busy。纯 main 首次又因副本缺 hc 缓存启动超时，保留原错误并停止该测试 core；同一测试/断言在预放同一固定构件的 main 两次 26 PASS、候选一次 26 PASS，原候选命令后来也有 26 PASS。没有据此宣称时序稳定性已证明，没有改门禁锁或重试 attach。
- 当前 verified 矩阵的 T124 则在角色已成功释放后，CLI 写 release.json 遭 **ENOSPC**，因此退出 1；这个失败仍保留。只清理已结束自有夹具中的可重建 Claude 安装副本，未删会话、DB、日志或失败现场：[清单](round5-fixture-binary-cleanup.json)、逐文件 journal。完整清单列 28 个副本、8,683,196,928 字节；首次清理因漏列本轮 T132/T171 前缀 guard 中止，前期删除数未确切记录，原稿和说明保留，不补称精确数。剩余空间恢复后，只对失败/未跑项另名续跑；T124-02 及剩余项目均通过。
- 最后收尾检查发现：三次预放 hc 构件的历史 T124 对照，外层采集器只找 state/hc/bin，未找到副本的 workbench/hc 构件，旧 .hc.json 因而 INCOMPLETE，私有 core 曾未停。失败检查输出保留为 delivery-checks-01/02.log；按每次 .source.json 和私有 manifest 明确定位后，已全部停止：[补充清理](round5-packaged-control-cleanup.json)。首次 main 启动失败留下的一处 control.sock 为 ECONNREFUSED，保留原文件；不是活后台。当前规定矩阵的 core 收尾均有独立记录，最终进程检查无存活夹具进程。
- 第一份新矩阵与续跑合并后为 27 项符合预期退出码；4 个预期退出 1 都核对了实际业务失败位置。不能把定位失败、语法错误、下载超时或 ENOSPC 算成反例捕获成功。

### 最新票面验收状态

| 验收条目 | 当前状态 |
| --- | --- |
| 修前真实入口红态：不上报投递、blocking 立即等用户 | PASS，首轮原始业务红态保留；本轮另外保留两家旧候选收不到的红态 |
| 非 blocking/blocking 各收到单条完整通知，不进用户输入 | PASS，当前真实 Claude、本地接口与原生计数证明；五种实测主控配置另有实际收件 |
| 四家各只实际提交一次，忙/blocked/草稿等待，未知不重发 | PASS（已列实测范围），含 hc 原子拒绝、明确未输入、重接恢复、未知 Electron 与反例 |
| 主控答复送回 worker、主控归因、状态与等待计数 | PASS，当前 T216/T124/T132；先答后关仍显示当前关闭者并保留历史答复 |
| 附理由交用户、用户输入 reply_to | PASS，当前 T216/T132；T133 原生用户问题答复回归也通过 |
| 无主控排队、不丢问题、15 分钟兜底 | PASS；使用既有门禁时钟依赖验证 14 分钟/超过 15 分钟，未实际等 15 分钟 |
| 角色卡与命令说明列五类只交用户 | PASS；提示词管判断，门禁没有关键词分类 |
| agy 独立只读审查无未处理阻塞意见 | INCOMPLETE，本轮未执行，不用其他只读审计冒充 |
| project-map status、git diff --check、完整候选与报告保护 | PASS，0 problems、0 stale living docs；见交付检查 |
| 本轮文件路径边界 | 历史 INCOMPLETE，早期资源用了系统 TMPDIR；最新正式 28 项及 33 条终端绑定 PASS，仍保留早期偏差供主控复核 |

### 需要主控决定与已知限制

**需要主控复核一项实际路径偏差。** 第五轮边界原文是“只写 T-216 worktree、T-216-evidence，以及测试自己在 /private/tmp 下建的夹具”。本轮沿用既有 Fixture 的 TMPDIR，daemon.ts 的终端专用 socket 使用 os.tmpdir()，实际在 /var/folders/.../T/enchanted-*/terminal.sock 创建自有 IPC 文件：[路径与状态清单](round5-temp-scope.json)。没有把这项写成符合边界，也不把该路径问题当成投递业务通过。清单中的终端专用 socket 均已随后台退出移除，没有活服务；另有一处原失败的 control.sock 位于自有 /private/tmp 夹具，确认 ECONNREFUSED 后保留作故障现场。同一继承的系统 TMPDIR 也用于 app/build.mjs 的 a2a-build-* 临时构建/缓存，Electron 夹具结束时自动删除。源码、补丁、报告、测试仓库和会话根目录均在要求的工作目录或 /private/tmp。

已在原授权内修正正式验证驱动：使用全新 confined 前缀，显式设置 TMPDIR=/private/tmp，按同一测试与断言完整重跑 28 项，全部符合预期退出码；其中 5 项是被业务断言拒绝的反例。对保留的 33 条终端绑定读回实际 A2A_TERMINAL_SOCKET，均为 /private/tmp；构建驱动使用同一显式环境，T212 成功后按其原策略删除了夹具。[正式路径核对](round5-confined-scope.json)、[矩阵](round5-confined-matrix.json)。没有为了修这个路径问题改产品源码或放宽断言，也没有请求扩大路径授权。早期偏差仍是偏差，不能改写为全程符合，交主控在接收审查时复核。

另请主控安排 agy 独立只读审查及最终提交，worker 不关票、不 commit、不 push；本轮供应商授权只用于最小确认，没有额外调用供应商做代码审查。

未穷举终端编辑快捷键、IME、所有身份变更竞争及全部断电/文件系统故障；已覆盖正常重接、实际送入后确认落盘前终止自有后台、未知不重发与状态竞争。done 的窄竞态按票面接受，不宣称原子条件已支持 done。没有收益、可靠性或吞吐改善主张。没有重跑主控另行登记的 T078、A13、T133 家目录标题基线问题，也没有修范围外 ticket。

业务代码和交付文件写在 T216 worktree、T216-evidence，自建会话/仓库夹具在 /private/tmp；另有上述系统临时 IPC 路径偏差和获准的原生 CLI 自身数据、agy 单目录信任。没有改主 checkout、T212 worktree、用户 ~/.claude 或 ~/.codex，没有连接用户 Herdr/default hc。测试 core 的停止、进程与凭据收尾、最终补丁、前四轮报告前缀和 UTF-8 链接检查见 [round5-delivery-checks.log](round5-confined-delivery-checks.log)。

## 第六轮

**当前候选：NO_GO。阻塞 2（未知后永久停队）已修复并通过；阻塞 1 的历史、补全与通常来源记录已修复，但崩溃窗口仍有一条真实入口复现的来源错误，不能提交为通过。** 此外，本轮真实供应商 Codex 最小确认是 INCOMPLETE。主控已在第六轮明确认可第五轮系统临时 socket 的处理，该历史路径项不再等待决定；前五轮原文保留。

### 范围、事实与失败方式

本轮依据[当前票面](round6-ticket.md)与第六轮任务书，源码仍在 `9c0e262125edb75ed841609472e32c952adc2bbd`，没有快进、commit 或 push。目标是保住 T-133 的完整用户提示词、一次性排除已送系统派发，并在新事实出现后恢复未知之后的队列；不改 hc 0.1.15、不加重发、不改变 agy/opencode 的用户输入记录。使用 Tracer bullet 经后台、私有 hc、原生 CLI、钩子与用户输入记录验证，沿用统一术语。

先列并逐项写入测试的失败方式：

1. ↑ 历史调用没有 attach 原文，或 `@` 补全改变原文，导致整条用户提交漏记。
2. 系统正文进入用户输入；排队未发时吞掉无关用户提交；同一派发被认领两次。
3. 仅落发送意图、尚未发送便退出，恢复后误吞用户提交的相同正文。
4. 实际已送、结果尚未落库便退出，恢复后迟到的系统钩子误记用户。
5. 未知永远堵住后续派发；或未等 CLI 消费遗留文字便续送，混为一次提交。
6. 恢复条件仅在内存中，后台重启后失效；未知原条被重发或被改成已确认。
7. 记录的参数和实际 `terminal.send` 参数分开构造、发生漂移。

第 1 条主控推断与实测一致，没有为迁就推断修改断言。第 3、4 条由本轮独立只读审查提出，均追加真实入口故障注入证据。

### 红态与基线对照

所有运行显式使用 `TMPDIR=/private/tmp`，完整重跑命令见 [ROUND6-COMMANDS.md](ROUND6-COMMANDS.md)，每次使用新文件名，未覆盖失败输出。

| 场景 | `9c0e26212` 基线 | 第五轮候选红态 |
| --- | --- | --- |
| Claude ↑ 历史两次提交 | [PASS](round6-base-history-claude-01.json)，原生钩子 2 条、用户记录 2 条 | [红态](round6-red-history-claude-01.json)，钩子 2 条、用户记录仅 1 条 |
| Codex ↑ 历史两次提交 | [PASS](round6-base-history-codex-01.json)，同上 | [红态](round6-red-history-codex-01.json)，同样漏第二条 |
| Claude `@` 文件名补全 | [PASS](round6-base-completion-claude-01.json)，钩子与记录均含补全后的完整文件名 | [红态](round6-red-completion-claude-01.json)，原生已补全、用户记录缺失 |
| Codex `@` 文件名补全 | [PASS](round6-base-completion-codex-01.json) | [红态](round6-red-completion-codex-01.json)，同上 |

以上均是真实交互 CLI 加本地脚本化接口，没有供应商调用；独立用户钩子的原始 `UserPromptSubmit` 保存在各夹具 `out/own-hooks.jsonl` 及摘要中。补全用唯一 nonce 文件名，非固定输出。

阻塞 2 的[红态](round6-red-recover-01.json)：替身保留第一条文字、不开始回合，hc 返回 `started:false / not_started`；第二条排队。替身实际消费第一条并报 working→idle 后，第二条仍一直排队，失败于 `later_dispatch_resumes`。提取的[原始状态与提交证据](round6-recovery-fact-red.json)保留了真实 hc 返回、按序 OSC 事件和替身自己的提交日志。

### 实现与文件

本轮改动如下；候选补丁仍包含此前各轮未提交的完整改动。

- `workbench/src/panes.ts`：删除 `shellUserPrompts` 和 `terminalUserPrompt()` 的 attach 白名单判断；改为原生钩子与本终端已发送收件箱派发的全文来源核对，持久化一次认领事件。只有 Claude 已知的尾部换行去除和 `<pasted_content>` 包装会规范化，注释标明 T-122 实测与 `store.register` 依据；Codex 按原文比对，不做内容含义分类。
- `workbench/src/daemon.ts`：未认领为系统派发的原生提交一律沿用 T-133 用户记录路径；`codexQuestionReply` 结构化答复路径不变。attach 继续管理草稿，不决定是否记用户输入。
- `workbench/src/panes.ts`：未知之后要求持久化 OSC 事件中有一个新的 working→idle/done 对，记录 `hc_unknown_consumed` 后只释放后面的队列。未知原条、收据和界面标记保持未知；没有重发、计时恢复或伪造状态。重启可从数据库事件恢复该事实。
- `workbench/src/hc.ts`、`panes.ts`：同一个 `params` 对象既写入 `hc_send_intent`，又传给实际 `terminal.send`，包含全文、目标、caller、wait、timeout 与 idle 条件。
- `workbench/tests/test_t216_prompt_provenance_e2e.py`：新增真实 Claude/Codex 历史、补全、来源、认领及两个崩溃窗口测试；`test_t216_hc_delivery_e2e.py` 扩展保留输入、恢复、重启及提前续送变异，更新参数对象改变后的原有变异定位。
- `workbench/README.md`、执行主控角色卡、终端 a2a 技能：改为现行用户输入来源与未知后续队列恢复说明。

### hc 恢复事实与来源探针

恢复事实实测：替身暂存通知文字时，hc 是 idle、turn 0，通知尚未进入替身的提交日志；消费之后报 working，再报 idle/done。随后第二条单独提交，最终 hc turn 为 2，第一、第二条各只有一次实际提交。重启场景把 working 事件留在旧后台数据库，重接后再报告 idle，仍能释放第二条。因此不依赖纯内存标记。见[最终恢复](round6-verified-recover.json)、[跨后台重启](round6-verified-recover-restart.json)、[done 路径](round6-green-recover-done-01.json)。这是按任务书允许的新回合事实恢复后续队列，不把它当成未知原条的送入确认。

来源崩溃窗口尚未解决，进一步只读 schema 与私有 hc 实测如下：

| 探针 | 实际返回与结论 |
| --- | --- |
| [随机 caller，不带 terminal 的 wait](round6-caller-probe-01.json) | 发送前后都返回 `invalid_params: give a terminal, or children`；不是可用的逐派发查询 |
| [带目标与随机 caller](round6-caller-probe-02.json) | idle 下未发送时 `reason:status, ended:true`；已送但未开始回合后 `reason:timeout, ended:false`。被 `status_mismatch` 拒绝的 caller 仍是前一种。新连接能保留部分关联，但该差别依赖当前状态 |
| [working 下有无发送关联](round6-caller-probe-03.json) | 已发送 caller 与从未发送 caller 都返回 `timeout / ended:false / working / turn:0`，返回完全相同。因此不能把该返回当成通用的发送来源证明 |

没有据此改 caller、投递参数、hc 版本或投递协议，也没有新增恢复猜测路径。**REALITY GATE：BLOCKED（下一步来源恢复方案）；当前代码已知违约则为 NO_GO。** 尚未找到经实测支持、可在所有相关状态下恢复逐派发实际送入事实的现成接口，不把缺事实填成兼容分支或重试。

### 绿态、变异与完整复跑

完整矩阵分为[首次 26 项](round6-verified-matrix.json)与[剩余 14 项](round6-verified-resume-matrix.json)，[合并清单](round6-verified-runs.json)共 40 项：31 项成功、8 项在预期业务断言退出 1、1 项真实供应商 Codex 确认为 INCOMPLETE。包括第五轮的全部 28 项和第六轮新增 12 项，没有用第五轮旧 PASS 替代本轮运行。第二份驱动只补未运行项，没有覆盖或重试失败的 Codex 通知。

- Claude、Codex 的历史与补全最终均 PASS；排队期间无关用户输入、系统正文排除、用户从历史第二次提交同正文各 PASS。见 [Claude 来源](round6-verified-provenance-claude.json)、[Codex 来源](round6-verified-provenance-codex.json)。每次均核对 CLI 自己的钩子原文和用户记录，不只数派发队列。
- 原 T-216 主路径、第二轮全部场景、T-124、T-132、T-171、T-133 Codex 原生答复回归均 PASS；T-212 的 `--electron-screen --mismatched-screen` [PASS](round6-verified-t212/run.json)，真实 Electron 未显示为假屏幕，用户 core 的目录与进程未改。未知界面的两次 Electron 场景也 PASS。
- 已有 5 项业务反例与本轮 3 项变异逐项核对失败断言。恢复 attach 判断的 Claude/Codex [变异](round6-verified-mutant-attach-codex.json)均失败于 `history_user_recorded_twice`；[去掉未知等待](round6-verified-mutant-early.json)失败于 `separate_submissions`，替身实际一次提交里同时包含两条通知。blocked 无后台判断变异仍通过（hc 拒绝），加 force 则失败；忙时误送、未知重发、原生重复提交与 T-133 答复误分类均被业务断言拒绝。
- [未知恢复](round6-verified-recover.json)与[跨后台重启恢复](round6-verified-recover-restart.json)均 PASS：第二条恢复后实际一次，第一条没有新发送意图、不重发、仍显示 unknown。额外 agy 替身 done 恢复 PASS。

真实 CLI 最小确认本轮各实际重做一次，范围仍仅申请角色及固定回复。见[原生事实](round6-verified-native-facts.json)：

| 主控配置 | 当前结果 |
| --- | --- |
| Claude Code，真实 CLI + 本地 Messages | PASS；主路径三个问题各实际一次，系统正文通常不进用户输入；不能外推到下述崩溃窗口 |
| Codex 0.164.0，本地 Responses | PASS，原生 rollout 1 条；原生回合配置 `gpt-6.1-sol / high` |
| agy 1.4.12，真实 HOME 与供应商 | PASS，原生记录实际 1 条；模型/强度 unknown；仅新增本次夹具的 1 条信任 |
| opencode 2.1.4，真实 HOME 与供应商 | PASS，原生 user 记录实际 1 条；原生选择字段 `deepseek-v4.1-flash-free / opencode / max`，不将其写成已证明的供应商实际模型/强度 |
| Codex 0.164.0，隔离 CODEX_HOME + 供应商 | [INCOMPLETE](round6-verified-codex-vendor.json)：角色获批，但 hc `started:false / not_started`；独立 rollout 未找到该通知，收件等待超时。没有重发、放宽断言或宣称只是供应商问题；现场保留。原生回合配置仍为 `gpt-6.1-sol / high`，不证明实际 served 模型/层级 |

真实 CLI 导出的终端文本与摘要遮罩邮箱，不导出认证文件或真实 agy 截图。Codex 的隔离 home 都已删除；仅保留本次原生 rollout。供应商只用于上述获准的最小确认，没有供应商代码审查。

### 审查发现与当前阻塞

[独立审查 1](ROUND6-REVIEW-01.md)为 FAIL：只有意图便排除系统输入，可能吞掉尚未实际发送正文的用户提交。随后[真实入口红态](round6-red-unsent-01.json)复现：在 RPC 前屏障处终止自有后台，重启后用户提交原文被吞。改为发送中的同步 RPC 加钩子核对，或已有成功 hc 返回，之后[绿态](round6-green-unsent-01.json)与最终矩阵该场景均通过。

[独立审查 2](ROUND6-REVIEW-02.md)仍为 FAIL：相反的窗口会污染用户记录。最终追加[真实 Claude 迟到钩子红态](round6-red-late-hook-01.json)，在本地接口、私有 hc 中：

1. hc 确实把通知送进原生 Claude；独立用户钩子已见到 1 条通知。
2. 将 Enchanted 的该条钩子暂缓，在 `hc_send_result` 落库前终止**自有后台**，原 CLI 和私有 core 保持运行。
3. 重启后台并释放原生钩子。数据库只有发送意图与恢复的未知记录，没有 hc 成功返回。
4. 当前候选把这条系统通知追加成了用户 message，失败于 `late_system_not_user`。不是 setup、模型失败或假钩子输入。[数据库与原生计数证据](round6-late-hook-event-proof.json)确认 1 条原生系统提交、1 条错误用户记录。

因此现有 40 项矩阵不能覆盖或洗掉这个额外反例。最终补丁只在第二份冻结审查候选之上新增该失败测试，产品代码与矩阵运行时相同。两份审查均为 fresh explorer 只读审查，**不是 agy 审查**。

### 每条验收的当前状态

| 票面／第六轮验收 | 状态 |
| --- | --- |
| 原修前真实入口不投递、blocking 立即等用户红态 | PASS，前轮原始证据保留；本轮新增来源及未知阻塞红态 |
| 非 blocking / blocking 单条完整通知，不进用户输入 | **NO_GO**；通常路径 PASS，但迟到系统钩子的崩溃反例仍污染用户记录 |
| 四家统一 hc、实际一次、忙/blocked/草稿等待、未知不重发 | INCOMPLETE；替身、真实 Claude、本地 Codex、真实 agy/opencode PASS，供应商 Codex 本轮未完成确认 |
| 主控回答送回 worker、处理人、状态与等待计数 | PASS，当前主路径与回归；先答后关仍保留历史答复 |
| 附理由交用户、用户 answer 的 reply_to | PASS，当前 T-216 / T-132 / T-133 |
| 无在线主控排队、不丢、15 分钟兜底 | PASS；门禁既有时钟依赖，未实际等 15 分钟 |
| 五类只交用户写入角色与命令说明 | PASS；门禁不按关键词判断 |
| T-133 历史、补全、排队无关输入、一次认领与 Codex 结构化答复 | PASS（已列正常入口与未发送意图场景）；完整来源契约因迟到钩子仍 NO_GO |
| 未知后续队列恢复，跨后台重启有效，原条仍未知且不重发 | PASS，idle 与 done，含真实 hc 和混合提交变异 |
| 记录参数与实际发送使用同一对象 | PASS |
| agy 独立只读审查无阻塞 | INCOMPLETE，未执行；两份其他审查均有过 FAIL，不冒充 agy |
| project-map status、diff check、完整候选与报告前缀 | PASS，见最终交付核对；不代表候选业务通过 |
| 路径与私有 core 收尾 | PASS，本轮全部显式 TMPDIR；45 条正式终端绑定均在 /private/tmp；第五轮路径偏差已获主控认可 |

### 需要主控决定

**需要决定崩溃后无法核对实际发送事实时的输入来源语义或证据方案。** 目前已分别复现两侧错误：只凭 intent 会吞掉未发正文的用户输入；要求结果已落库，又会把已送但未落结果的系统输入记给用户。不能靠 attach 按键来裁决，也不能仅凭 working 或当前 `terminal.wait` 返回猜来源。当前 P1 不应集成。

最小后续选项：继续现契约时，先明确并证明一种后台退出后仍可核对的逐派发实际送入事实；目前 hc 探针尚不足以支持该结论。若这需要改 hc 能力、版本或协议，超出本轮“不改 hc”授权，另行决定。另一条是新增“来源未决”记录并显式展示、核对之后再归类，不直接算用户或已确认系统输入；这会改变记录语义与验收，也须先批准。worker 没有自行选一条或降低验收。

还需主控处置本次真实供应商 Codex 未收到通知的现场；没有做其 main 对照，也没有证明根因属于供应商、基线或本候选。独立 agy 审查仍待主控安排。本轮到此停止实现。

### 证据保护、异常和未跑检查

- 四个基线副本预放固定 hc，既有清理 helper 不识别 packaged 路径；随后用[明确私有 manifest 清理](round6-packaged-control-cleanup.json)停止四个 core。没有残留活动服务。首个 Codex attach-only 变异曾因钩子信任选择的时序卡在角色申请，记为 setup INCOMPLETE，不算业务反例；驱动改为核对已选“Trust all and continue”再回车，最终同一变异已被业务断言拒绝。
- 首份候选被审查发现 P1 后，只向自有矩阵调用者发 SIGINT，允许正在运行的测试完成，保留[中止记录](round6-first-matrix-stop.json)及全部原输出。两个旧冻结补丁、失败报告、红态与 setup 失败均未覆盖。
- 仅删除本轮已结束夹具中的 **20 个**可重建 Claude 安装副本，共 **6,202,283,520 字节**；[逐项追加清单](round6-fixture-binary-cleanup.jsonl)。先检查后台/core socket 和文件占用，数据库、原生会话、日志、仓库均保留。本轮未发生 ENOSPC。
- 未穷举所有 CLI 编辑方式、IME、全部崩溃／I/O 故障；没有重跑主控另行登记的 T-078、A13、家目录标题基线。真实供应商 Codex 的失败没有补称通过。
- [最终候选](round6-candidate.patch)包含全部新增文件。前五轮 REPORT 字节前缀不变；UTF-8、链接、补丁与工作树一致性、所有私有服务退出及预期业务失败断言见[最终交付核对](round6-delivery-checks-final.log)。核对脚本退出 0 只表示证据与当前现状一致，其结论仍为 **NO_GO**。
- 没有写主 checkout、T-212 worktree、用户 ~/.claude 或 ~/.codex，没有连接用户 Herdr/default core，没有 commit、push。只有获准的真实 CLI 自身数据与 agy 单目录信任例外。

## 第七轮（主控在本会话自己写，2026-11-01）

用户改分工：建造由 Claude Code 主控写，GPT 只读审查。候选冻结为 [round7-candidate.patch](round7-candidate.patch)（基线 `9c0e26212`，含未跟踪的新测试）；复跑命令见 [ROUND7-COMMANDS.md](ROUND7-COMMANDS.md)，脚本 [run-round7.sh](run-round7.sh)，顺序记录 [round7-runs.log](round7-runs.log)。本节结论 **PASS**：运行证据齐全，GPT 只读审查 PASS（[ROUND7-REVIEW-01.md](ROUND7-REVIEW-01.md)，主控核对引用见 [ROUND7-REVIEW-01-controller-check.md](ROUND7-REVIEW-01-controller-check.md)）。

### 改动

1. 来源规则（执行主控决定）：`panes.ts` 的 `claimShellInboxPrompt` 不再要求 hc 成功返回。已写下 `hc_send_intent`、未被认领的派发，提交全文与它相同即认领为系统，只认领一次；最新事件是 `hc_send_rejected` 时不认领。已接受的代价：意图写下后、RPC 之前后台崩溃，正文没进终端，之后用户逐字提交同一段（含序号与 UUID）会被认领为系统。README 与 daemon 注释随之改写。
2. 项目终端的 Codex（`terminal/bin/codex`）加 `-c notice.hide_rate_limit_model_nudge=true`，与受管 worker（T-167）相同。原因见下。

### 真实 Codex 丢通知的原因

第六轮 `round6-verified-codex-vendor` 的现场 pty.raw：回合结束后 Codex 弹出 “Approaching rate limits / Switch to gpt-6-luna?” 选择框，OSC 仍报 `state=done`，不是 blocked。hc 把通知粘进选择框，正文丢失，选择框按第一项关闭，主控模型被切成 GPT-6-Luna medium，之后才报 idle。

`test_t216_real_cli_delivery_e2e.py` 新增 `--quota-warning`：本地 Responses 工装回 `x-codex-secondary-used-percent: 92`（周窗口）等头，不经供应商。

| 运行 | 结果 |
| --- | --- |
| [修前](round7-red-quota-warning-codex-01.json) | 退出 1，`超时：CLI 原生记录收件`；画面里有 “Approaching rate limits”“Keep current model”“luna” |
| [修后](round7-green-quota-warning-codex-01.json) | 退出 0；“weekly limit” 横幅仍出现 5 次，选择框与 luna 都没出现；原生记录正文一次，不记用户 |

中途两次作废，原样留在 [round7-aborted-shim-space/](round7-aborted-shim-space/) 和 `round7-aborted-quota-warning-codex-unfixed.log`：一次是改 shim 的 Edit 没生效就启动了；一次是 shim 的 `set` 行少一个空格（`"true"-c`），Codex 报 `invalid type: string "true-c"`。后一次连带停掉了已开始的复跑，只保留不经 Codex shim 的 history-claude。

### 来源规则的红绿与变异

| 运行 | 结果 |
| --- | --- |
| [迟到钩子绿态](round7-green-late-hook-claude-01.json)（真实 Claude） | 退出 0 |
| [变异 require-hc-return，迟到钩子](round7-mutant-require-hc-return-delayed-hook-claude-01.json) | 退出 1，预期拒绝：`late_system_not_user` 失败，迟到的派发被记成用户输入 |
| [never-sent 新期望](round7-green-never-sent-claude-01.json) | 退出 0：`unsent_body_claimed_as_system`、`intent_only_claimed_once`、`second_identical_submit_is_user` 都通过 |

### 复跑

| 运行 | 结果 |
| --- | --- |
| history、completion、provenance（Claude、Codex 各一） | 六项退出 0 |
| attach-only 变异（Claude、Codex） | 退出 1，预期拒绝：`history_user_recorded_twice` |
| T-216 主路径 `--gui`、T-133 Codex | 退出 0 |
| T-133 变异 reply-as-message | 退出 1，预期拒绝：`only_approved_prompts_recorded` |
| r2 routing-online | 退出 0 |
| r2 duplicate-submit 反例 | 退出 1，预期拒绝 `cli_actual_submission_count_is_one`，与第六轮相同 |
| 真实 CLI 本地 Codex | 退出 0 |
| T-212 规定命令（`--electron-screen --mismatched-screen`） | run.json `PASS` |
| recover-unknown、recover-restart、unknown `--gui` | 退出 0 |

本轮没有重跑 agy、opencode 的真实供应商运行与 hc 送法矩阵的其余项：本轮只改了认领条件和 Codex 启动参数，这些运行不经过这两处。额度预警由本地复现覆盖；审查之后又补跑一次真实供应商 Codex（隔离 CODEX_HOME，只复制 auth.json）：[PASS](round7-verified-codex-vendor.json)，原生记录正文一次、不记用户，结束后隔离 home 已删除。这次供应商没有出额度横幅，所以它只证明正常路径，不证明额度预警路径。

合入 main（`889033ef8`）后，在 main 上复跑 [Codex 来源](round7-main-provenance-codex.json) 与 [T-216 主路径 `--gui`](round7-main-t216.json)，都退出 0。
