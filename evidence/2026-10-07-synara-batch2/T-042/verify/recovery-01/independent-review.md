# 独立只读验收审查

来源：`recovery_acceptance_review`，acceptance-auditor，新上下文，不继承执行对话。以下保留审查返回内容；没有再次执行产品测试。

STATUS: INCOMPLETE
TARGET: `/Users/luckye/Documents/Code/synara`, branch `a2a`, frozen HEAD `3566ef4eb34b18c480c7a49e4b5d741681b72426`
EVIDENCE:
- 候选 HEAD 与所有 command/result JSON 的 candidate 一致；tracked diff 为空，仅有已记录的 `.grok/` 未跟踪目录。
- `lint`、typecheck、桌面构建及锁文件安装均退出 0；日志分别显示 0 errors、8/8、4/4、1635 packages。
- `orchestration-trace.json`：18 项、0 failures、0 errors；`delivery-trace.json`：17 项、0 failures、0 errors。入口经生产 `packages/a2a-gates/src/cli.ts`，使用隔离 subprocess/真实 Git；trace 含 sentinel、边界与无效输入。
- `desktop/membership.jsonl` 的 8 个真实 HTTP 请求、两个跨项目拒绝、`preflight.json` 的 4 个 OPTIONS 检查均符合预期；输入来自隔离 fixture 和真实 backend。
- `gate-dispatch.json`、`membership-managed-worker.json`、`managed-events-after-ui.json` 证明 worker 是真实 gate dispatch thread；Electron 截图/AX 显示 `/#/a2a`、任务窗口及 observer `healthy`。
- `03-managed-send-blocked.jpg/.txt` 与事件回读显示 provider disabled、消息仍是草稿，HTTP/CLI events 中无 `human_intervention`；报告在 `RESULTS.md:19-20` 明确标为 INCOMPLETE。
FINDINGS:
- 无额外可复现的 P1/P2/P3 违规；报告没有把未完成的人工介入或非受管反例冒称为通过。
COUNTEREXAMPLE:
- 固定输出、忽略输入或总是成功的门禁实现会被 18/17 项外部入口场景、未知/重复/跨项目 membership 输入及边界断言拒绝。
- “始终不写入 `human_intervention`”的实现尚未被拒绝，因为 provider-disabled 使真实用户消息未提交；该关键反事实仍未执行。
LIMITATIONS:
- provider 按任务书保持关闭；没有真实 `thread.message-sent`，因此缺少受管人工介入事件的 `thread_id`、`message_id`、`dispatch_origin=user` 及对应 UI 标记。
- 非受管会话发送反例未运行，不能由“消息没发出去”推断无事件。
- 18/17 项证明隔离门禁状态与恢复行为，不证明真实模型调用或 provider 边界行为。

转存说明：审查中“没有真实 thread.message-sent”应限定为本次手工输入的 user-origin 消息。实际 dispatch 的 agent-origin 分派消息已经存在并在截图中显示 Sent by agent；本轮未把它当成人工介入。审查的反事实说明来自对断言的只读检查，本轮没有另行修改产品做 mutant 运行。
