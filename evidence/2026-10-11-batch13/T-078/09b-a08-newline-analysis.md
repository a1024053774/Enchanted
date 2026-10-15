# A-08 I1 尾换行红态出处与收回分析

## 实测出处

- A-08 trace 原件：`/private/tmp/t078-2-09b-run-4_qt67n9/roles/ideation/hooks/16e93a7a-da62-4193-8f63-9970ccdfacd5/stdin.bin`。其中 `UserPromptSubmit.prompt` 为 `⟦主控 #2⟧\nI1 A-08 ideation prompt; acknowledge this registered turn exactly once, do not call tools, and stop.`，末尾没有换行。
- A-08 登记正文来自 `i1-prompt.txt`，文件末尾有换行；旧 live daemon 在修复前把该换行保存在 dispatch record，触发 `injected_prompt_blocked`。
- 产品写入路径是 [store.ts](../../../../workbench/src/store.ts) 的 `register` 与 [panes.ts](../../../../workbench/src/panes.ts) 的 `drain`：登记文本进入 `dispatch_records`，随后以 bracketed paste 写入 PTY，再单独写入 CR。旧 live 进程加载的版本没有登记规范化，所以 Claude 去掉终端尾换行后与登记正文不同。
- 独立真实 signal 红态：`09b-newline-red-02/results.json`；修复后的同一入口绿态和正文中间变异反例：`09b-newline-green-01/results.json`。绿态只接受尾换行差异，中间正文改变仍 block。
- slice1 green-3 原始链路的 API/Hook 记录同样显示提交正文按 CLI 实际 prompt 读取；本修复只规范化登记末尾 CR/LF，不放宽中间正文、seq、身份或预算校验。

## A-08 active 收回选项

A-08 当前 active 在 UserPromptSubmit 阻断前没有有效 Claude `prompt_id`，因此 Stop hook 无法匹配清理 active；直接伪造 Stop、operator 代写业务或重送都不合规。现有 worker-only emergency stop 也不适用于 controller。

唯一保留 A-08 的路径是主控批准的认证窗口用户动作：通过窗口输入送出 Esc，观察 interruption/input generation，再由用户声明输入框已空并放行；该动作会作为真实 user action 记录。若不允许该动作，必须走 A-09：先按 owner-bound 流程关闭 A-08、归档读回 root，再以尾换行修复后的代码重建 Stage A/B1，成本是一次完整的 7 进程清理与新现场逐屏审批。当前不操作现场，等待裁定。
