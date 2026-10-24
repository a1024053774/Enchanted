# T-157-1 / a1 调查检查点

状态：INCOMPLETE。红态复现 PASS；主控 #61 已转述用户新原则，语义不再阻塞。后端根因修复及隔离身份测试已完成，真实 Electron 绿态等待 RUN-OUTSIDE-02；renderer.tsx 仍未修改，等待 T-159 合并与执行主控给出的 rebase/写入窗口。调查与探针提交为 `0e09483e95f841475d33811d475c060e52cec28e`，红态证据提交为 `e16817974244537cd633ae1dd1c8469fe82d9c46`。当前不是 T-157 验收通过或修复完成结论。

调查与被测产品基线：`ef99842b35e17c4cd69e1e58d5afca0689bf88b1`；探针运行时 checkout 为 `0e09483e95f841475d33811d475c060e52cec28e`，经 --revision 使用前述基线产品源码。task 为 T-157-1，attempt 为 a1，worker 为 b24-t157；提交钩子记录 session `abac2361-ec4f-4eca-bc68-ff22c9081137`、launch `launch-f02b8466dd9a48fbbd146a0293ef858b`，本会话未取得 fence，不补造。规格为 T-157 ready_rev 1 与本目录 card.md。开始时工作树干净，project-map status 为 Problems 0 / Stale living docs 0。

## 调查结果

人工 Enter 会换掉 pane 当前 submission/prompt；旧 Stop 转交内的进程与 submit 核对存在异步边界。新运行已复现：原 Stop 收到 submit 后，人工输入替换 submission，随后同一请求被 `worker_not_active` 拒绝，旧 Stop 留下 after_transfer 的 stop_not_matched。relay 保留明确拒绝，同 request_id 重放返回原拒绝。侧栏与窗格头使用不同状态投影，缺少结构化交付原因和恢复入口。运行时未采集拒绝调用栈，不声称定位到了哪一次 assertActive，详见 DESIGN-QUESTION.md。

交付顺序及恢复动作此前按任务卡停在决定门；主控 #61 转述 answer `20261024T030734Z-001` 后，按用户“原生 CLI 自己处理输入”的新原则实施。没有采纳旧选项 1/2，也没有选择自动重试、改写拒绝、直接代交付或放宽身份核对。

## 后端修复检查点

Tracer bullet：保留终端原样输入路径 → 由原生 UserPromptSubmit 更新身份 → Stop 用原 caller 走既有门禁。先证明这条路径，再接界面事实；不另造交付入口。Ubiquitous language 沿用人工介入、原生 turn、attempt、submit；Deep modules 取舍为在 Panes 内直接修身份拥有者，不增加转交包装层或门禁例外。

`panes.ts`：Claude 输入的 Enter 不再清空 prompt 或替换 submission，字节仍在原 serializeWrite 路径即时写入 PTY。经过已有 envelope、session、时间与未复用 prompt 核对的新 UserPromptSubmit，才创建下一次用户 submission 并切换 prompt。已登记注入的正文检查保留，旧 caller 的严格 prompt 核对保留；原生新 turn 的旧 Stop 不得清空新回合。Codex 路径未改。

worker 的 pane snapshot 增加只读 delivery 事实，从既有 relay 事件取原 attempt、session、fence、spec_rev、commit、request_id 与结果。处理中、明确通过、明确拒绝、结果未知分开；没有重试或状态改写。此投影尚未接入界面。

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

## 验收逐条状态

| 条件 | 状态与证据 |
| --- | --- |
| Stop 批次期间输入原样送达、同 attempt 原 turn submit 通过 | INCOMPLETE；隔离状态正例 PASS，真实 Electron 绿态等待 RUN-OUTSIDE-02 |
| 原生新 turn 后拒绝旧 caller，界面显示最后事实与原因 | INCOMPLETE；隔离身份反例 PASS，真实 Electron 反例与界面等待 renderer 写入窗口 |
| 修前同序列 worker_not_active 且界面无说明 | PASS（仅红态复现）；RED-01.json、RED-01.png、RED-01-menu.png；测试退出 1，两个界面期望断言按预期失败 |
| 拒绝后的最小恢复绑定原 attempt，无重复/过期交付 | INCOMPLETE；仅真正旧 turn 失效才需入口，不做常规暂停再交付路径；尚未实现界面 |
| 已知坏实现 | 隔离身份的忽略 turn、吞输入、延后输入均被拒；Electron submit-never-active 变异等待 RUN-OUTSIDE-02 |

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

交付并非修复完成；真实红态已保留，语义已按主控 #61 更新，等待 RUN-OUTSIDE-02 的结果以及 renderer 的 rebase/写入窗口。完成候选后还需独立行为验收，当前未宣称独立审查已通过。
