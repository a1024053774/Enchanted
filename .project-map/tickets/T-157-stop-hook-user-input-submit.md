---
id: T-157
title: F01：Stop hook 期间用户输入后交付停住，界面不说明
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

报告 F01（阻断）：worker 运行 Stop hook 时用户在窗格输入，之后同一 attempt 的 `submit` 被 `worker_not_active` 拒绝；侧栏“未知”、窗格头仍“忙”，界面没有拒绝原因和恢复入口。
目标：先明确 Stop 与用户输入相交时的交付语义（用户输入记为人工介入，不应无声使交付失效）；界面显示最后确定事实、拒绝原因与下一步；提供绑定原 attempt 的可核对恢复操作。不用自动重试掩盖结果未知；若语义选择涉及验收条件，经 needs-decision 交构思主控。
证据：findings/2026-10-23-real-user-dogfood.md F01 与 evidence/2026-10-23-batch24/T-155/。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [x] 真实复现：Stop hook 期间输入后，侧栏与窗格头一致显示原因与可操作恢复，不再“未知/忙”并存。
- [x] 红态：修前同序列得到 `worker_not_active` 且界面无说明。
- [x] 恢复后交付绑定原 attempt，不产生重复或过期交付。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。用户定原则（构思主控 answer 20261024T030734Z-001 转述）：“我在 agent 工作过程中输入内容这个他自己 cli 会处理的吧,他会在此次工具执行完成后加入这句话再做思考,这个不用我们处理吧”——输入原样直达 CLI、只记人工介入；工作中的输入不让进行中的 Stop 交付失效；新 turn 确已开始才明确拒绝并说明，给绑定原 attempt 的最小恢复入口；不做暂停后点重新交付的常规路径。验收第 1 条据此理解为：正常情况下不再出现“未知/忙”并存，交付照常通过；仅在拒绝时说明原因与恢复入口。
根因：人工 Enter 清空并替换仍有效的 Claude turn 身份，旧 Stop 的 submit 在异步核对后被拒为 worker_not_active；另在 outside-04 暴露第二处：排队输入复用原 prompt_id 被误判为重复，CLI 随后开始的新 turn 未登记，最终 Stop 无法匹配而停在“未知”。修复在 `panes.ts`（保留原 Stop 身份；凭原生 queued human 转录登记实际新 turn）、`renderer.tsx`/`sidebar.ts`（拒绝时写明最后事实与原因、恢复入口）、README。门禁 turn/attempt/版本核对未放松。
沙箱外 outside-01 修前红态；outside-05 共 13 项（0 个真实模型回合，真实 daemon/PTY/Claude CLI/Electron）：Stop 期间输入后原 submit 通过且回到空闲、新 turn 拒绝后恢复、attempt 失效时恢复禁用均 PASS；两个修前基线与 4 个坏实现（执行旧 Stop、隐藏原因、隐藏恢复、坏调用方）只在预期断言失败；T-159/T-160/T-133 回归 PASS。03/04 的失败为夹具问题（整块粘贴被 CLI 当粘贴确认）与上述第二处缺陷，证据保留。独立审查 agy PASS（P3：转录逐行解析遇坏行抛错由外层记录；不加吞异常保护）。合并 167d2c803。证据 `evidence/2026-10-23-batch24/T-157/RESULTS.md`。
