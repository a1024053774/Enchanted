# T-157-1 / a1 调查检查点

状态：INCOMPLETE。红态复现 PASS；NEEDS-DECISION，交付语义实现 BLOCKED。未修改产品代码，未修改 renderer.tsx。调查与探针提交为 `0e09483e95f841475d33811d475c060e52cec28e`；本检查点补存执行主控回传的真实 Electron 红态，不能作为 T-157 验收通过或修复完成证据。

调查与被测产品基线：`ef99842b35e17c4cd69e1e58d5afca0689bf88b1`；探针运行时 checkout 为 `0e09483e95f841475d33811d475c060e52cec28e`，经 --revision 使用前述基线产品源码。task 为 T-157-1，attempt 为 a1，worker 为 b24-t157；提交钩子记录 session `abac2361-ec4f-4eca-bc68-ff22c9081137`、launch `launch-f02b8466dd9a48fbbd146a0293ef858b`，本会话未取得 fence，不补造。规格为 T-157 ready_rev 1 与本目录 card.md。开始时工作树干净，project-map status 为 Problems 0 / Stale living docs 0。

## 调查结果

人工 Enter 会换掉 pane 当前 submission/prompt；旧 Stop 转交内的进程与 submit 核对存在异步边界。新运行已复现：原 Stop 收到 submit 后，人工输入替换 submission，随后同一请求被 `worker_not_active` 拒绝，旧 Stop 留下 after_transfer 的 stop_not_matched。relay 保留明确拒绝，同 request_id 重放返回原拒绝。侧栏与窗格头使用不同状态投影，缺少结构化交付原因和恢复入口。运行时未采集拒绝调用栈，不声称定位到了哪一次 assertActive，详见 DESIGN-QUESTION.md。

交付顺序及恢复动作涉及验收语义，按任务卡停在决定门。没有选择自动重试、改写拒绝、直接代交付或放宽身份核对。

## 验收逐条状态

| 条件 | 状态与证据 |
| --- | --- |
| Electron 中原因和恢复入口一致可见 | INCOMPLETE；修前运行中的两个界面期望断言均失败，尚未修复 |
| 修前同序列 worker_not_active 且界面无说明 | PASS（仅红态复现）；RED-01.json、RED-01.png、RED-01-menu.png；测试退出 1，两个界面期望断言按预期失败 |
| 恢复绑定原 attempt，无重复/过期交付 | BLOCKED；需要 DESIGN-QUESTION.md 裁定，没有实现或声称验证 |
| 新探针已知坏实现 | INCOMPLETE；提供 submit-never-active 变异入口，尚未执行；不能称回归证明 |

## 重放与证据

执行主控已运行：`zsh evidence/2026-10-23-batch24/T-157/RUN-OUTSIDE-01.sh`。回传来源：主控 #58；TEST_EXIT=1，red_reproduced=true，errors=[]。本 worker 核对 summary 并查看两张截图，未自行重跑。

原路径 `/private/tmp/t157-outside-01.5xMLfp/`；复制后的文本与截图为 [RED-01.json](RED-01.json)、[RED-01.log](RED-01.log)、[窗格截图](RED-01.png)、[菜单截图](RED-01-menu.png)。复制后逐字节核对相同，不改原始 summary 中的路径。fixture 为 `/private/tmp/t157-stop-input-xp2t69mt`，不复制进仓库；归档仍由执行主控按 T-088 处理。

关键时序（2026-10-24 UTC）：02:57:13.815 Stop（seq 93）→ 13.821 relay_received（95）→ 13.825 人工 turn_submit_intent / terminal_input_written（99/100）→ 13.889 worker_not_active（104）→ 13.890 after_transfer 的 stop_not_matched（106）。原 attempt `c2b87762-f145-4cad-8e46-6055f56b1ca6`、session `f312fa98-89e5-483d-8fc5-157f868d8023`、fence 1、spec_rev 1；submit request_id 为 `aab44131-6c4e-47de-959f-cec54a6f56e9`，候选字段仍为空。截图显示 CLI 已回复完成，窗格头仍“忙”，菜单无交付恢复动作；summary 记录侧栏状态 unknown。

脚本每次创建新的 `/private/tmp/t157-outside-01.*`，打印 SUMMARY、LOG、TEST_EXIT。测试创建真实 Electron、后台、Git 仓库、PTY 和 Claude CLI，用本地脚本化 Messages 接口；通过只读 relay journal 定位 submit 转交，再经 Electron 的 xterm 输入桥提交一条不改范围的说明。未修改产品来扩大竞态窗口；未命中不得当作红态，也不自动重跑。

修前预期测试退出 1；只有 `red_reproduced=true` 且时间线表明输入在原 Stop relay 收到与拒绝之间、人工介入和原 attempt 绑定、候选为空、界面仍“未知/忙”，才称取得本票红态。完整运行的 PASS 还不能证明恢复语义；恢复验收要在决定后补齐。此探针通过 Electron 输入桥，不声称测试了真实键盘/IME 路径。

summary 保留产品版本、attempt、timeline、门禁事件、pane/sidebar/DOM、截图路径、异常和清理结果；原始隔离 fixture 留在 /private/tmp，按 T-088 由执行主控归档。不得提交整个 fixture。脚本化模型的固定文字只驱动时序，不作真实模型理解或可靠性证明。

真实供应商模型回合：本检查点 0 / 12；RUN-OUTSIDE-01 也为 0，不连接供应商接口。没有复制用户登录凭据，没有修改全局配置。

## 本地检查与后续回归

本地仅检查 Python/嵌入 JS 语法、CLI help、zsh 语法、diff 与 UTF-8；具体结果见 STATIC-CHECKS.txt。Electron 和后台由执行主控在沙箱外运行，未在 worker 沙箱运行。既有 e2e 未运行，因为没有产品行为改动；新运行仅证明指定红态，不证明恢复和修复。

决定后若修改 panes 的 Stop/输入或身份核对，需要同时覆盖正常 submit、无输入的 Stop、无请求 Stop、旧 turn/attempt 拒绝、重复 request_id、未知结果不得重放，以及已合并 T-160 的 reviewer Stop/恢复路径。最小已有回归优先 `workbench/tests/test_t160_review_recovery_e2e.py` 和 `workbench/tests/test_t133_t107_terminal_controller_e2e.py`；在修复候选的下一份 RUN-OUTSIDE 脚本一起运行。未取得新候选前不重复这些外部运行。

交付并非修复完成；真实红态已保留，等待语义决定和 renderer 写入窗口。主控 #58 已将 DESIGN-QUESTION 转交构思主控（needs-decision `20261024T025739Z`），推荐选项 2；推荐不等于用户裁定，本 worker 未据此实施。
