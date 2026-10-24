# T-157-1 / a1 调查检查点

状态：INCOMPLETE。红态复现 PASS；根因、拒绝事实与 renderer 候选均已实现，RUN-OUTSIDE-03 的真实新 turn 反例、恢复、失效与三项回归 PASS；修正粘贴夹具后，RUN-OUTSIDE-04 证明原 submit 与原文送达，但暴露原生排队身份相关的产品收尾缺陷，仍 INCOMPLETE。当前已修正 panes.ts，等待 RUN-OUTSIDE-05 全部 13 项复验。独立行为验收尚未进行。主控 #61 已裁定语义，#63 给 renderer 写入窗口，#65 在沙箱外无冲突变基到包含 T-159/T-160 的 main，worker 确认 HEAD `c6725344ae81dce51656b2e44d1035a247df6604` 后开始写 renderer。变基基线为 `37c42f17aa5e0dc0b27272ba2363d713cf14f2b6`；当时 main 后续变化未涉及 workbench。初次调查与红态提交保留旧号：`0e09483e95f841475d33811d475c060e52cec28e`、`e16817974244537cd633ae1dd1c8469fe82d9c46`；变基映射见 DESIGN-QUESTION.md。当前不是 T-157 验收通过或修复完成结论。

调查与被测产品基线：`ef99842b35e17c4cd69e1e58d5afca0689bf88b1`；探针运行时 checkout 为 `0e09483e95f841475d33811d475c060e52cec28e`，经 --revision 使用前述基线产品源码。task 为 T-157-1，attempt 为 a1，worker 为 b24-t157；提交钩子记录 session `abac2361-ec4f-4eca-bc68-ff22c9081137`、launch `launch-f02b8466dd9a48fbbd146a0293ef858b`，本会话未取得 fence，不补造。规格为 T-157 ready_rev 1 与本目录 card.md。开始时工作树干净，project-map status 为 Problems 0 / Stale living docs 0。

## 调查结果

人工 Enter 会换掉 pane 当前 submission/prompt；旧 Stop 转交内的进程与 submit 核对存在异步边界。新运行已复现：原 Stop 收到 submit 后，人工输入替换 submission，随后同一请求被 `worker_not_active` 拒绝，旧 Stop 留下 after_transfer 的 stop_not_matched。relay 保留明确拒绝，同 request_id 重放返回原拒绝。侧栏与窗格头使用不同状态投影，缺少结构化交付原因和恢复入口。运行时未采集拒绝调用栈，不声称定位到了哪一次 assertActive，详见 DESIGN-QUESTION.md。

交付顺序及恢复动作此前按任务卡停在决定门；主控 #61 转述 answer `20261024T030734Z-001` 后，按用户“原生 CLI 自己处理输入”的新原则实施。没有采纳旧选项 1/2，也没有选择自动重试、改写拒绝、直接代交付或放宽身份核对。

## 后端修复检查点

Tracer bullet：保留终端原样输入路径 → 由原生 UserPromptSubmit 更新身份 → Stop 用原 caller 走既有门禁。先证明这条路径，再接界面事实；不另造交付入口。Ubiquitous language 沿用人工介入、原生 turn、attempt、submit；Deep modules 取舍为在 Panes 内直接修身份拥有者，不增加转交包装层或门禁例外。

`panes.ts`：Claude 输入的 Enter 不再清空 prompt 或替换 submission，字节仍在原 serializeWrite 路径即时写入 PTY。经过已有 envelope、session、时间与未复用 prompt 核对的新 UserPromptSubmit，才创建下一次用户 submission 并切换 prompt。已登记注入的正文检查保留，旧 caller 的严格 prompt 核对保留；原生新 turn 的旧 Stop 不得清空新回合。Codex 路径未改。

worker 的 pane snapshot 增加只读 delivery 事实，从既有 relay 事件取原 attempt、session、fence、spec_rev、commit、request_id 与结果。处理中、明确通过、明确拒绝、结果未知分开；没有重试或状态改写。补充原请求对应的 Stop 与拒绝前最后一个原生 turn 事实，只有实际 prompt/turn 已不同才标 native_turn_changed。迟到的已知旧 Claude 根 Stop 经原生 session/cwd/transcript 校验后只转交 matched=false，原 relay 给明确拒绝，不能执行新门禁操作；不吞掉输入，也不放松 turn/attempt/版本检查。

隔离身份测试的失败方式在 `test_t157_turn_identity.ts` 文件头先列出；只控制 native hook 与 processInfo 的异步边界，不冒称真实 CLI/PTY 或真实 submit。证据：

| 检查 | 结果 |
| --- | --- |
| 修前 `--revision ef99842b35e17c4cd69e1e58d5afca0689bf88b1` | 退出 1；Enter 错换 submission、原生手动 UPS 不建立身份；IDENTITY-RED-01.json |
| 修后原样即时输入、保留 Stop 身份、新 UPS 拒绝旧 caller、旧 Stop 不清新回合、空闲手动 UPS | 3 场 PASS；IDENTITY-GREEN-01.json；UPS 由隔离 host 提供，不是真实 CLI 证据 |
| ignore-turn 变异 | 退出 1；旧 caller 被错误接受的断言拒绝它；IDENTITY-MUTANT-ignore-turn-01.json |
| swallow-input 变异 | 退出 1；PTY 字节缺失断言拒绝它；IDENTITY-MUTANT-swallow-input-01.json |
| delay-input 变异 | 退出 1；Stop 身份核对未释放时，输入须已写出的断言拒绝它；IDENTITY-MUTANT-delay-input-01.json |
| 既有 T-160 Codex Stop 隔离状态回归 | 7 场 PASS；T160-STATE-REGRESSION-01.json |

以上变异的原始 summary 保留 INCOMPLETE，表示被测坏实现没有通过；本报告只把“按期望拒绝坏实现”记作反证成立。原始 fixture 在 summary 的 /private/tmp 路径，归档由执行主控按 T-088 处理。

## 变基后的界面候选

renderer 只在明确拒绝且有原生新 turn 证据时显示“旧回合交付被拒”，侧栏使用同一事实。窗格显示原提交、原 attempt、最后结果、原因与可展开原记录；不把活动状态“忙”和交付结果混为一项。正常 Stop 输入正例不出现暂停/恢复流程。没有改 app/main.ts、preload、daemon、门禁合同或全局配置，保留 T-159 的分屏与菜单改动。

“请原 worker 核对交付”在当前回合结束、同 attempt/session/fence/版本仍有效、尚无候选且窗口可输入时启用。点击后重读快照，核对原 launch/window/request，再通过现有 window_input 给该 worker 发送核对说明，沿用终端输入和人工介入记录；这是按钮产生的核对请求，不是用户逐字编写的说明。worker 核对后才经普通 CLI 使用新的稳定 request_id 显式 submit。GUI 不代交付、不重放旧请求、不自动重试；重复的核对说明仍受原 CLI 请求文件的排他创建与 relay 日志约束。失效 attempt、已有候选或未知身份不给发送入口。恢复按钮等待空闲不影响用户直接输入，直接输入仍原样直达 CLI。

变基后局部证据：IDENTITY-FACT-RED-02.json 在旧投影上拒绝“缺少原生 turn 变化事实”；IDENTITY-FACT-GREEN-02.json 与 IDENTITY-FINAL-GREEN-03.json 为 3 场隔离状态 PASS，包含迟到旧 Stop 明确拒绝且不执行。当前隔离测试对 ignore-turn/swallow-input/delay-input 三个变异仍分别退出 1，见 IDENTITY-FINAL-MUTANT-*-03.json。构建证据见 BUILD-03.json、BUILD-04.json、加入异步前置检查防双击保护后的最终 BUILD-05.json；只代表当次构建，不代表真实界面可用或性能改善。恢复操作也会在已知草稿、正在写入或已有待处理消息时禁用，不清草稿、不代发草稿。

真实 Electron 新反例由 test_t157_stale_turn_e2e.py 驱动：先通过真实 CLI 结束首轮并保存候选提交，再实际启动不同 prompt_id 的新用户回合；向真实认证 hook 入口重放已捕获旧 Stop 和一个原 attempt 的迟到 submit 文件（对抗输入，不伪造“当前 turn”，不改 DB）。核对明确拒绝、界面事实与原因、无自动执行；然后通过 UI 的显式核对入口让真实 CLI 发出唯一新 submit，检查 attempt/session/fence/spec/commit 保持、实际新原生 turn 和交付次数为 1。独立 expired 场景在新回合期间撤销原 attempt，核对入口禁用且点击无字节发送。RUN-OUTSIDE-03 已执行，恢复与 expired 场景 PASS；逐项结果见下。

## 验收逐条状态

| 条件 | 状态与证据 |
| --- | --- |
| Stop 批次期间输入原样送达、同 attempt 原 turn submit 通过 | INCOMPLETE；RUN-OUTSIDE-04 原 submit 通过且原文进入真实 CLI 请求，但排队回合结束后仍 unknown。修正产品相关身份处理后待 RUN-OUTSIDE-05 |
| 原生新 turn 后拒绝旧 caller，界面显示最后事实与原因 | INCOMPLETE（当前候选待 RUN-OUTSIDE-05）；历史 710a72060 候选在 OUTSIDE-03/stale-recover.json 与截图上 PASS |
| 修前同序列 worker_not_active 且界面无说明 | PASS（仅红态复现）；RED-01.json、RED-01.png、RED-01-menu.png；测试退出 1，两个界面期望断言按预期失败 |
| 拒绝后的最小恢复绑定原 attempt，无重复/过期交付 | INCOMPLETE（当前候选待 RUN-OUTSIDE-05）；历史 710a72060 候选恢复/失效场景 PASS，见 OUTSIDE-03 对应摘要 |
| 已知坏实现 | 当前隔离身份的忽略 turn、吞输入、延后输入均被拒；历史 OUTSIDE-03 的执行旧 Stop、隐藏原因/入口变异均被拒；新候选将在 RUN-OUTSIDE-05 重跑 |

## 重放与证据

执行主控已运行：`zsh evidence/2026-10-23-batch24/T-157/RUN-OUTSIDE-01.sh`。回传来源：主控 #58；TEST_EXIT=1，red_reproduced=true，errors=[]。本 worker 核对 summary 并查看两张截图，未自行重跑。

原路径 `/private/tmp/t157-outside-01.5xMLfp/`；复制后的文本与截图为 [RED-01.json](RED-01.json)、[RED-01.log](RED-01.log)、[窗格截图](RED-01.png)、[菜单截图](RED-01-menu.png)。复制后逐字节核对相同，不改原始 summary 中的路径。fixture 为 `/private/tmp/t157-stop-input-xp2t69mt`，不复制进仓库；归档仍由执行主控按 T-088 处理。

关键时序（2026-10-24 UTC）：02:57:13.815 Stop（seq 93）→ 13.821 relay_received（95）→ 13.825 人工 turn_submit_intent / terminal_input_written（99/100）→ 13.889 worker_not_active（104）→ 13.890 after_transfer 的 stop_not_matched（106）。原 attempt `c2b87762-f145-4cad-8e46-6055f56b1ca6`、session `f312fa98-89e5-483d-8fc5-157f868d8023`、fence 1、spec_rev 1；submit request_id 为 `aab44131-6c4e-47de-959f-cec54a6f56e9`，候选字段仍为空。截图显示 CLI 已回复完成，窗格头仍“忙”，菜单无交付恢复动作；summary 记录侧栏状态 unknown。

脚本每次创建新的 `/private/tmp/t157-outside-01.*`，打印 SUMMARY、LOG、TEST_EXIT。测试创建真实 Electron、后台、Git 仓库、PTY 和 Claude CLI，用本地脚本化 Messages 接口；通过只读 relay journal 定位 submit 转交，再经 Electron 的 xterm 输入桥提交一条不改范围的说明。未修改产品来扩大竞态窗口；未命中不得当作红态，也不自动重跑。

修前预期测试退出 1；只有 `red_reproduced=true` 且时间线表明输入在原 Stop relay 收到与拒绝之间、人工介入和原 attempt 绑定、候选为空、界面仍“未知/忙”，才称取得本票红态。完整运行的 PASS 还不能证明恢复语义；恢复验收要在决定后补齐。此探针通过 Electron 输入桥，不声称测试了真实键盘/IME 路径。

summary 保留产品版本、attempt、timeline、门禁事件、pane/sidebar/DOM、截图路径、异常和清理结果；原始隔离 fixture 留在 /private/tmp，按 T-088 由执行主控归档。不得提交整个 fixture。脚本化模型的固定文字只驱动时序，不作真实模型理解或可靠性证明。

真实供应商模型回合：本检查点 0 / 12；RUN-OUTSIDE-01 也为 0，不连接供应商接口。没有复制用户登录凭据，没有修改全局配置。

## 本地检查与后续回归

初次调查的静态检查见 STATIC-CHECKS.txt；后端改动后已运行上表隔离测试及 Python/嵌入 JS、zsh 语法检查。Electron 和后台只由执行主控在沙箱外运行，未在 worker 沙箱运行。RUN-OUTSIDE-03 的既有真实 e2e 与新 turn / 恢复检查已运行；核心 Stop 输入正例仍未通过，不能用其他绿态替代。

RUN-OUTSIDE-02 包含修改后的同一 Electron 竞态测试在修前版本失败、候选通过、submit-never-active 坏实现失败；正例核对输入在原批次结果前即时写出、字节不改、真实 CLI 模型请求收到 sentinel、人工介入与原 attempt 绑定、原提交号与原 native turn、唯一 submit 且无自动重试。一起运行 `test_t160_review_recovery_e2e.py` 与 `test_t133_t107_terminal_controller_e2e.py`。脚本中的 PASS 仅指后端检查点，不包含尚未完成的真实原生新 turn / 界面反例。每场写新 summary，失败不重跑。

RUN-OUTSIDE-03 是变基后完整候选检查点：同一 Stop 输入正例，新 turn 反例在 c6725344a 修前失败、候选恢复与 expired 场景、执行旧 Stop/隐藏原因/隐藏入口的坏实现，以及 T-159 分屏、T-160 审查恢复、T-133/T-107 主控的三项既有 e2e 回归。每项写新 summary/截图/日志，失败不重跑，不用旧候选 verdict 背书新候选。RUN-OUTSIDE-02 未收到结果，不推测通过。RUN-OUTSIDE-03 的结果由主控 #70 回传，见下方记录。

交付并非修复完成；等待 RUN-OUTSIDE-05 全组回传并核对，再交执行主控独立验收。后续 rebase/merge 等 Git 操作交主控处理，不再申请提权；本次只做普通 git add/commit。


## RUN-OUTSIDE-03 回传与正例夹具修正

主控 #70 回传 `/private/tmp/t157-outside-03.S3A29D`，被测产品提交 `710a7206084b4173a338b84bf130109d861e30c0`，供应商模型回合 0。原始小摘要及截图逐字节复制到 [OUTSIDE-03](OUTSIDE-03/RESULT.json)，不改其中的 /private/tmp 引用，不复制整个 fixture 或令牌。原始目录仍留给主控归档。

| 场景 | 结果 |
| --- | --- |
| stop-input-positive | INCOMPLETE；30 秒未观察到原说明进入后续 Messages 请求，旧探针在等候后才采集断言，因而 checks 为空；不能忽略 |
| stale-recover / stale-expired | PASS；实际新 turn、旧请求拒绝说明、原身份显式恢复一次、失效禁用 |
| stale-baseline（c6725344a） | INCOMPLETE，按预期在明确拒绝与界面说明/入口断言失败；errors=[] |
| execute-old-stop 变异 | INCOMPLETE，按预期失败于 unmatched_stop_never_enters_execution；errors=[] |
| hide-reason / hide-recovery 变异 | INCOMPLETE，按预期失败于说明或入口断言；errors=[] |
| T-159 分屏 / T-160 审查恢复 / T-133/T-107 主控回归 | PASS；相应原摘要均保留 |

正例现场 `/private/tmp/t157-stop-input-fh8_u2ub` 的停止后数据库以 `mode=ro&immutable=1` 只读核对（无 WAL 文件），连同原生转录与 PTY 尾部摘要保存在 [POSITIVE-FAILURE-DIAGNOSIS-03.json](POSITIVE-FAILURE-DIAGNOSIS-03.json)。事件顺序：Stop seq 93 → relay_received 95 → 输入意图/写入 98/99 → relay_processed 105（ok=true，原 attempt/原 turn/原提交）→ pane_idle 107。输入内容含完整 sentinel，未被本次身份保留逻辑吞掉或等到交付结束才写出。

原生 PTY 最后显示原说明仍在编辑区，并出现 `Removed 1 invisible character · review and press Enter to send`。原生转录只有初始用户请求和四个工具结果；最后是首轮 stop_hook_summary，没有下一次 UserPromptSubmit 或 Messages 请求。证据指向探针把整块 `note + CR` 作为未框定粘贴输入：CLI 把 CR 作为待复核的不可见字符，而非单独 Enter。不能把这次失败归为脚本化 API 的第二次回复未生成；CLI 尚未发出请求。其后门禁反馈也粘到了未提交编辑区。

本次只修本票夹具：观察器通过同一 Electron 输入桥先送标准括号粘贴包（正文不变），再单独发送 Enter；不追加第二次 Enter、不暂停产品、不重试、不改 CLI 设置或产品代码。断言仍要求两个包均在原 Stop 的 relay_received 与处理结果之间写出，逐包字节相同，且随机 sentinel 原文确实进入真实 CLI 的后续 Messages 请求。原 submit 与人工介入的身份核对保持。探针现在在等待前保存 submit 断言，finally 保存 API Messages、最终事件/任务/pane 和截图，超时不会再仅有空 checks。

[RUN-OUTSIDE-04.sh](RUN-OUTSIDE-04.sh) 请主控运行：核心正例，加同一修正探针在原缺陷基线和 always-inactive caller 变异上的反证。产品文件与 `710a72060` 相同，所以当次脚本只重复核心正例与其反证。主控 #71 已回传，见下一节；当前仍不是独立验收或发布结论。


## RUN-OUTSIDE-04 产品红态与排队回合修正

主控 #71 回传 `/private/tmp/t157-outside-04.FeAsXA`，供应商模型回合 0。小摘要及截图逐字节复制到 [OUTSIDE-04](OUTSIDE-04/RESULT.json)，保留失败原样。已查看 stop-input-positive-final.png：门禁“已交付”，候选 `da16f7809477983e413b6a88f9687450e20e7d6f`、attempt `f813c39c-878a-42da-9f3d-3f75e5ace92d`；随机 sentinel 原样出现在真实 CLI 后续请求，CLI 回复后停在空提示符，但窗格“未知”、底栏“执行：运行中”。正例退出 1，等待空闲超时。基线 red_reproduced=true；always-inactive caller 变异在 submit 接受等断言上失败，二者 errors=[]。这次不再是粘贴夹具问题。

[QUEUED-TURN-DIAGNOSIS-04.json](QUEUED-TURN-DIAGNOSIS-04.json) 保留原生排队记录和相关事件。原 Stop 的 prompt_id 为 `ce78588d-2d21-4aa6-abdf-dcec228412be`。说明已写入后，CLI 的 UserPromptSubmit 仍带此 ID（seq 109）；旧实现将它判成 claude_prompt_id_reused，追加 native_question_unverified（110）。原 submit 仍通过（114），但原 Stop 的第二次信任检查因此失败（116：stop_transfer_failed / current_turn_untrusted）。随后原生转录 dequeue 说明，并以新 promptId `96252177-30a3-4e59-a936-a0e02312d6b4` 记录 queued human 用户消息。其 Stop 到达（122）时后台没有该 turn 身份，留下 stop_not_matched（123）。这解释了 CLI 结束而工作台 unknown 的完整链条。

本次产品变更仅在 panes.ts，README 同步事实；未写 renderer.tsx、questions.ts、daemon 或门禁合同。Stop 转交期间，同原生 prompt 的排队 UPS 必须有此前未消费的终端 Enter 写入收据，并通过既有 envelope 与唯一原生转录路径核对。它只记 claude_prompt_queued，保持原 submission/prompt 和信任事实。后台不会把原输入延后、重发或交给恢复按钮处理。

实际新 turn 由该原生会话的 queued human 转录建立：核对同会话、工作目录、根线程、来源、原说明正文、时间、未用过的新 promptId 与消息 UUID。完整行才算证据；工具结果、子线程、错正文/会话/目录/时间和旧 promptId 都不建立 turn。processInfo 的既有 scan 和 hook 匹配前均会采集这条事实，因此实际新 turn 开始后，旧 caller 的严格 turn 核对仍失败。没有合格转录就不补造新身份或空闲。原 Stop 收尾时若仍有原生排队输入，保留 busy，等新 turn 的真实匹配 Stop；门禁反馈在 CLI 队列结束后才走既有注入队列，避免抢入用户排队回合。

Tracer bullet 保持为用户输入即时写入 → 原 Stop 交付 → CLI 原生排队转录 → 新 turn Stop → 空闲 → 原门禁反馈。没有新交付 API、自动重试或成功改写。Ubiquitous language 区分原生排队输入与实际新 turn，不把 Enter 当成 turn。Deep modules 仍由 Panes 的 scan/signal 持有身份，不另造转交包装层。

| 本地检查 | 结果与边界 |
| --- | --- |
| 新增 queued-input 隔离状态红态 | IDENTITY-QUEUED-RED-04.json，修前退出 1，失败于 claude_prompt_id_reused；其余原有 3 项 PASS |
| 修后最终状态检查 | IDENTITY-QUEUED-FINAL-GREEN-05.json，4 项 PASS；原 Stop 通过、实际新 turn 拒旧 caller、人工介入 turn Stop 回到 idle；只控制 hook/observer，不冒称真实 CLI |
| 错正文、会话、目录、时间、子线程、工具结果和旧 ID | 上述 queued 场景内均不能建立新 turn |
| ignore-turn / swallow-input / delay-input 变异 | IDENTITY-QUEUED-MUTANT-*-05.json，全部退出 1，分别被旧 caller、字节、即时性断言拒绝；坏实现摘要保留 INCOMPLETE |
| 既有 Codex Stop 状态回归 | T160-STATE-REGRESSION-05.json，7 项 PASS |
| 标准构建 | BUILD-QUEUED-05.json，退出 0；仍有 Vite >500 kB chunk 提醒；只清理本次自己的成功构建槽位 |

真实正例保留空闲等待与侧栏/窗格头断言，并补充人工介入 turn 没有 failed/active、若观察到原生排队事实则必须有新 turn 与匹配 idle 事件。不放宽失败断言。

[RUN-OUTSIDE-05.sh](RUN-OUTSIDE-05.sh) 请主控运行，重跑 03 的 10 项和 04 的 3 项，共 13 场；两场正例使用不同的一次性 state/sentinel，是预先列明的独立场次，不因失败自动重试。所有场景仍是真实 Electron/后台/PTY/交互 Claude CLI 加本地 Messages，供应商模型回合 0。新候选的真实绿态、反例和回归全部待此次运行，旧候选 verdict 不替新变更背书；独立审查待执行主控安排。
