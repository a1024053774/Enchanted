STATUS: FAIL

FINDINGS:

- [P1] [gates/cli.ts:229](/Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts:229) — 统一阻断仍覆盖不到钩子超时。后台请求期限为 120 秒（[transport.ts:38](/Users/luckye/Documents/Code/a2a/workbench/src/transport.ts:38)），原生钩子限时却是 10 秒，且未设置 `onFailure: "block"`（[panes.ts:142](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:142)）。后台连接后持续不响应时，钩子会先被 CLI 超时终止，无法返回阻断 JSON；Claude 默认继续提交，仍可能执行没有输入记录和人工介入事件的回合。
- [P2] [t108_answer_lifecycle_contracts.mjs:49](/Users/luckye/Documents/Code/a2a/workbench/tests/t108_answer_lifecycle_contracts.mjs:49) — `unknown_pty_queued` 仍等待 attach 记录回调里的 `entered()`，但 Claude 输入现在跳过该回调（[panes.ts:1611](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1611)）。执行到这里会永久等待，无法检查排队输入和未知 PTY 写入；新增空 `recordUserSubmission` 没有修复这个同步点。

EVIDENCE:

- 开始、结束均逐字比较：`candidate.files` 范围内工作区 diff 等于 `candidate.patch`；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。
- 已读 T-229、T-206、T-216、前三轮审查、REPORT、候选及直接调用路径。第三轮两条意见的同步异常路径已处理：查询／认领失败统一标观察失败并重抛，后台拒绝及连接异常由钩子命令返回阻断。
- `r5-claude-03` 夹具库的 `launch_records.data.argv` 确认 UPS 配置只有 `timeout:10`，没有 `onFailure`；CLI 为 Claude 2.1.316。本机安装文件中，字节偏移 `251690298` 的钩子契约明确说明超时默认继续；偏移 `261533043` 的失败策略检查要求显式 `onFailure==="block"`。
- `r5-unit/{base,cand2}/test_t108_questions.json` 的 `failure_cases` 均为 254/429，通过名称集合相同；均没有进入 `answer_lifecycle_cases`。因此该比较没有覆盖上述 P2。空记录器没有削弱已执行的这些断言。
- `red-{claude,codex}.json` 确在业务断言失败：`after_1` 带 keys、`after_2=[]`。最新主流程各有 `claims=2`、`human_interventions=3`；阻断和观察状态变异也分别失败于对应业务断言。
- agy/opencode 摘要保留 `{text_uncertain:true}` 且没有 keys；`submitHook` 与当前四种 CLI 名称一致。人工介入仍由 `appendUserInput` 在同一事务内派生。
- 已读运行脚本、`runs.log`、相关摘要和单元日志；REPORT 的主要数值一致，但完整 fail-closed 主张受 P1 限制。

LIMITATIONS:

- 未运行测试、启动服务、连接 hc 或供应商；两条发现均来自静态可达路径，未新增复现。
- 未实测旧库恢复、被中断派发、Codex 忙中排队、Tab 补全及受管主控／审查员的全部输入路径。
- agy/opencode 证据使用替身；T-108 后续生命周期场景未取得运行证据。