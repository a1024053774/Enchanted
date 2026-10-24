# T-157-1 / a1 调查检查点

状态：INCOMPLETE。红态复现 PASS；根因、拒绝事实与 renderer 候选均已实现，真实 Electron 绿态/反例/恢复等待 RUN-OUTSIDE-03，独立行为验收尚未进行。主控 #61 已裁定语义，#63 给 renderer 写入窗口，#65 在沙箱外无冲突变基到包含 T-159/T-160 的 main，worker 确认 HEAD `c6725344ae81dce51656b2e44d1035a247df6604` 后开始写 renderer。变基基线为 `37c42f17aa5e0dc0b27272ba2363d713cf14f2b6`；当时 main 后续变化未涉及 workbench。初次调查与红态提交保留旧号：`0e09483e95f841475d33811d475c060e52cec28e`、`e16817974244537cd633ae1dd1c8469fe82d9c46`；变基映射见 DESIGN-QUESTION.md。当前不是 T-157 验收通过或修复完成结论。

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

真实 Electron 新反例由 test_t157_stale_turn_e2e.py 驱动：先通过真实 CLI 结束首轮并保存候选提交，再实际启动不同 prompt_id 的新用户回合；向真实认证 hook 入口重放已捕获旧 Stop 和一个原 attempt 的迟到 submit 文件（对抗输入，不伪造“当前 turn”，不改 DB）。核对明确拒绝、界面事实与原因、无自动执行；然后通过 UI 的显式核对入口让真实 CLI 发出唯一新 submit，检查 attempt/session/fence/spec/commit 保持、实际新原生 turn 和交付次数为 1。独立 expired 场景在新回合期间撤销原 attempt，核对入口禁用且点击无字节发送。此脚本尚未执行。

## 验收逐条状态

| 条件 | 状态与证据 |
| --- | --- |
| Stop 批次期间输入原样送达、同 attempt 原 turn submit 通过 | INCOMPLETE；隔离状态正例 PASS，真实 Electron 绿态等待 RUN-OUTSIDE-03 |
| 原生新 turn 后拒绝旧 caller，界面显示最后事实与原因 | INCOMPLETE；隔离身份反例 PASS，真实 Electron 反例与界面验证等待 RUN-OUTSIDE-03 |
| 修前同序列 worker_not_active 且界面无说明 | PASS（仅红态复现）；RED-01.json、RED-01.png、RED-01-menu.png；测试退出 1，两个界面期望断言按预期失败 |
| 拒绝后的最小恢复绑定原 attempt，无重复/过期交付 | INCOMPLETE；入口已实现，真实恢复/撤销反例尚未运行；不做常规暂停再交付路径 |
| 已知坏实现 | 当前隔离身份的忽略 turn、吞输入、延后输入均被拒；新 Electron 的执行旧 Stop、隐藏原因/入口变异等待 RUN-OUTSIDE-03 |

## 重放与证据

执行主控已运行：`zsh evidence/2026-10-23-batch24/T-157/RUN-OUTSIDE-01.sh`。回传来源：主控 #58；TEST_EXIT=1，red_reproduced=true，errors=[]。本 worker 核对 summary 并查看两张截图，未自行重跑。

原路径 `/private/tmp/t157-outside-01.5xMLfp/`；复制后的文本与截图为 [RED-01.json](RED-01.json)、[RED-01.log](RED-01.log)、[窗格截图](RED-01.png)、[菜单截图](RED-01-menu.png)。复制后逐字节核对相同，不改原始 summary 中的路径。fixture 为 `/private/tmp/t157-stop-input-xp2t69mt`，不复制进仓库；归档仍由执行主控按 T-088 处理。

关键时序（2026-10-24 UTC）：02:57:13.815 Stop（seq 93）→ 13.821 relay_received（95）→ 13.825 人工 turn_submit_intent / terminal_input_written（99/100）→ 13.889 worker_not_active（104）→ 13.890 after_transfer 的 stop_not_matched（106）。原 attempt `c2b87762-f145-4cad-8e46-6055f56b1ca6`、session `f312fa98-89e5-483d-8fc5-157f868d8023`、fence 1、spec_rev 1；submit request_id 为 `aab44131-6c4e-47de-959f-cec54a6f56e9`，候选字段仍为空。截图显示 CLI 已回复完成，窗格头仍“忙”，菜单无交付恢复动作；summary 记录侧栏状态 unknown。

脚本每次创建新的 `/private/tmp/t157-outside-01.*`，打印 SUMMARY、LOG、TEST_EXIT。测试创建真实 Electron、后台、Git 仓库、PTY 和 Claude CLI，用本地脚本化 Messages 接口；通过只读 relay journal 定位 submit 转交，再经 Electron 的 xterm 输入桥提交一条不改范围的说明。未修改产品来扩大竞态窗口；未命中不得当作红态，也不自动重跑。

修前预期测试退出 1；只有 `red_reproduced=true` 且时间线表明输入在原 Stop relay 收到与拒绝之间、人工介入和原 attempt 绑定、候选为空、界面仍“未知/忙”，才称取得本票红态。完整运行的 PASS 还不能证明恢复语义；恢复验收要在决定后补齐。此探针通过 Electron 输入桥，不声称测试了真实键盘/IME 路径。

summary 保留产品版本、attempt、timeline、门禁事件、pane/sidebar/DOM、截图路径、异常和清理结果；原始隔离 fixture 留在 /private/tmp，按 T-088 由执行主控归档。不得提交整个 fixture。脚本化模型的固定文字只驱动时序，不作真实模型理解或可靠性证明。

真实供应商模型回合：本检查点 0 / 12；RUN-OUTSIDE-01 也为 0，不连接供应商接口。没有复制用户登录凭据，没有修改全局配置。

## 本地检查与后续回归

初次调查的静态检查见 STATIC-CHECKS.txt；后端改动后已运行上表隔离测试及 Python/嵌入 JS、zsh 语法检查。Electron 和后台只由执行主控在沙箱外运行，未在 worker 沙箱运行。既有真实 e2e 与新 Electron 绿态都还未运行，不能用隔离状态测试替它们背书。

RUN-OUTSIDE-02 包含修改后的同一 Electron 竞态测试在修前版本失败、候选通过、submit-never-active 坏实现失败；正例核对输入在原批次结果前即时写出、字节不改、真实 CLI 模型请求收到 sentinel、人工介入与原 attempt 绑定、原提交号与原 native turn、唯一 submit 且无自动重试。一起运行 `test_t160_review_recovery_e2e.py` 与 `test_t133_t107_terminal_controller_e2e.py`。脚本中的 PASS 仅指后端检查点，不包含尚未完成的真实原生新 turn / 界面反例。每场写新 summary，失败不重跑。

RUN-OUTSIDE-03 是变基后完整候选检查点：同一 Stop 输入正例，新 turn 反例在 c6725344a 修前失败、候选恢复与 expired 场景、执行旧 Stop/隐藏原因/隐藏入口的坏实现，以及 T-159 分屏、T-160 审查恢复、T-133/T-107 主控的三项既有 e2e 回归。每项写新 summary/截图/日志，失败不重跑，不用旧候选 verdict 背书新候选。两份外部脚本的结果都尚未由主控回传，本报告不推测它们已运行或通过。

交付并非修复完成；等待 RUN-OUTSIDE-03 回传后核对真实绿态、反例和截图，再交执行主控独立验收。后续 rebase/merge 等 Git 操作交主控处理，不再申请提权；本次只做普通 git add/commit。
