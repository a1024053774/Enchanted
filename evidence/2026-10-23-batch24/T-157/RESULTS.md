# T-157-1 / a1 调查检查点

状态：INCOMPLETE。NEEDS-DECISION；交付语义实现 BLOCKED。未修改产品代码，未修改 renderer.tsx。此提交只交付调查、未执行的红态探针及沙箱外运行脚本，不能作为 T-157 验收通过或修复完成证据。

调查基线：`ef99842b35e17c4cd69e1e58d5afca0689bf88b1`。task 为 T-157-1，attempt 为 a1，worker 为 b24-t157；session/fence 由主控门禁记录，本会话未取得这些值，不补造。规格为 T-157 ready_rev 1 与本目录 card.md。开始时工作树干净，project-map status 为 Problems 0 / Stale living docs 0。

## 调查结果

人工 Enter 会换掉 pane 当前 submission/prompt；旧 Stop 转交内的进程与 submit 核对存在异步边界，可能在输入后以 `worker_not_active` 拒绝。relay 保留明确拒绝，同 request_id 重放返回原拒绝。侧栏与窗格头使用不同状态投影，缺少结构化交付原因和恢复入口。以上是源码事实与竞态推断，新运行仍待核对，详见 DESIGN-QUESTION.md。

交付顺序及恢复动作涉及验收语义，按任务卡停在决定门。没有选择自动重试、改写拒绝、直接代交付或放宽身份核对。

## 验收逐条状态

| 条件 | 状态与证据 |
| --- | --- |
| Electron 中原因和恢复入口一致可见 | INCOMPLETE；未改产品，未运行 |
| 修前同序列 worker_not_active 且界面无说明 | INCOMPLETE；旧 T-155 证据存在，新基线红态等待 RUN-OUTSIDE-01 |
| 恢复绑定原 attempt，无重复/过期交付 | BLOCKED；需要 DESIGN-QUESTION.md 裁定，没有实现或声称验证 |
| 新探针已知坏实现 | INCOMPLETE；提供 submit-never-active 变异入口，尚未执行；不能称回归证明 |

## 重放与证据

主控运行：`zsh evidence/2026-10-23-batch24/T-157/RUN-OUTSIDE-01.sh`。

脚本每次创建新的 `/private/tmp/t157-outside-01.*`，打印 SUMMARY、LOG、TEST_EXIT。测试创建真实 Electron、后台、Git 仓库、PTY 和 Claude CLI，用本地脚本化 Messages 接口；通过只读 relay journal 定位 submit 转交，再经 Electron 的 xterm 输入桥提交一条不改范围的说明。未修改产品来扩大竞态窗口；未命中不得当作红态，也不自动重跑。

修前预期测试退出 1；只有 `red_reproduced=true` 且时间线表明输入在原 Stop relay 收到与拒绝之间、人工介入和原 attempt 绑定、候选为空、界面仍“未知/忙”，才称取得本票红态。完整运行的 PASS 还不能证明恢复语义；恢复验收要在决定后补齐。此探针通过 Electron 输入桥，不声称测试了真实键盘/IME 路径。

summary 保留产品版本、attempt、timeline、门禁事件、pane/sidebar/DOM、截图路径、异常和清理结果；原始隔离 fixture 留在 /private/tmp，按 T-088 由执行主控归档。不得提交整个 fixture。脚本化模型的固定文字只驱动时序，不作真实模型理解或可靠性证明。

真实供应商模型回合：本检查点 0 / 12；RUN-OUTSIDE-01 也为 0，不连接供应商接口。没有复制用户登录凭据，没有修改全局配置。

## 本地检查与后续回归

本地仅检查 Python/嵌入 JS 语法、CLI help、zsh 语法、diff 与 UTF-8；具体结果见 STATIC-CHECKS.txt。Electron 和后台未在沙箱运行。既有 e2e 未运行，因为没有产品行为改动，当前不能拿它们替未执行探针背书。

决定后若修改 panes 的 Stop/输入或身份核对，需要同时覆盖正常 submit、无输入的 Stop、无请求 Stop、旧 turn/attempt 拒绝、重复 request_id、未知结果不得重放，以及已合并 T-160 的 reviewer Stop/恢复路径。最小已有回归优先 `workbench/tests/test_t160_review_recovery_e2e.py` 和 `workbench/tests/test_t133_t107_terminal_controller_e2e.py`；在修复候选的下一份 RUN-OUTSIDE 脚本一起运行。未取得新候选前不重复这些外部运行。

交付并非修复完成；等待执行主控回传真实红态、语义决定和 renderer 写入窗口。
