---
id: T-203
title: 审查员手写嵌套 JSON 回包易错，审查卡死要人工重开
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：真实用户式试用第 2 轮（[RESULTS](../../evidence/2026-10-27-batch28/UAT-02/RESULTS.md) 发现 1）。同一次交付的两次审查，审查员（Claude Code `claude-sonnet-5-5`）最后一条回复都是深层嵌套的 JSON，末尾都少一个 `}`，门禁按 `review_json` 拒收，任务暂停；问题页两张卡都显示“问题 1”。重派后的第三次审查才通过。

门禁拒收格式不对的回包是对的，不放宽。要定的是审查员怎么交回包才不靠模型数括号：例如经 `a2a` 命令或 T-194 的 MCP 工具按字段提交，由工具拼成协议对象；或其他做法。先定方案再做；同时查清两张卡为何同号。

## 方案（2026-10-27 定）

用户选“工具按字段提交”。做法：

- 审查员用工具 `review_submit` 交结论，只填 `verdict`、`findings`、`report` 三项。身份字段（task、attempt、session、fence、spec_rev、review_id、request_id、candidate_commit）与 `review_requirements` 由门禁在开审查时写进该审查会话请求目录的模板，工具照模板补齐，模型不再手写 14 个字段的嵌套 JSON。
- 工具当场用门禁同一份校验（`reviewRequest`）核对；不合格就返回出错字段和怎么改，审查员在同一回合里改了再交，以最后一次成功提交为准。工具只写请求目录里的结果文件；门禁照旧在审查员回合结束（Stop）时读它、做同样的校验与转交，检查不放宽。
- 入口：Claude Code、Codex、opencode 审查员经本会话的 MCP 服务器拿到这个工具（启动参数挂上）；agy 的交互会话不把 MCP 工具给模型（T-194 实测），改用同一实现的命令，参数是只含这三项的 JSON 文件。
- 结束回合时没有成功提交的结论：门禁按协议失败暂停（`review_result_missing`），问题页说明原因并照旧提供“为同一次交付新开审查”。原来“最后一条回复必须是 JSON”的协议删掉，不并存。
- 问题编号：同号的原因是编号按会话（thread）计数，每次审查都是新会话。改为按 attempt 计数，worker、审查员与系统问题统一。

## Acceptance

- [x] 方案定下并写进本票。
- [x] 修前版本经真实入口：审查员的回包少一个括号时审查卡死；修后同样的审查意见能被门禁收下，格式真不对时仍拒收并说明。
- [x] 同一 attempt 的多张问题卡编号不重复。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

放宽门禁对回包内容的检查；改审查判断本身。

## Resolution

2026-10-27 PASS。按“方案”一节实现：审查员经 `review_submit` 只交三项（agy 用同一实现的命令），工具当场用门禁同一校验；后台在回合结束时读结果文件并再核对一遍，旧的“最后一条回复是 JSON”协议已删。问题编号改按 attempt 计。

- 证据：`evidence/2026-10-27-batch28/T-203/RESULTS.md`
  - 真实 Claude Code 主测试：修前红、修后绿，3 个变异体
  - 真实 Codex、opencode 探针
  - 真实 opencode 主控派 agy worker 与审查员的完整运行
  - 改过的旧测试全部回归通过
- 独立审查：agy `gemini-3.8-flash-high` 结论“可合并”，见 `review-1.md`；两条 P3 证据记录问题已改。
- 没做：真实模型在 Electron 界面里的完整审查流程没有重跑；少数单元测试没跑；`test_t112_reviewer_startup` 原有的失败没修。
