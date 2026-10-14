# P1 材料 07：只读诊断与目录信任停点

2026-10-13，主控 #95。**BLOCKED**：材料 07 是诊断与待决提案，不是可执行或已通过的候选。原材料 06 的失败、数据库、原始请求、终端和 cleanup 均保留。本轮没有启动 CLI／API，没有发输入、signal、ps 或模型调用。

## hook：已观察与未知

原归档数据库含已登记的 paste／turn_submitted，但没有 hook_received 或 turn_start_signal；后台没有收到 signal 请求。daemon stdout/stderr 为空；隔离 CLI 没有 debug 文件，也没有 hook 原始 stdin、stdout、stderr、退出或耗时记录。因而不能断定是 3 秒超时、signal 拒收或 Claude payload 字段不符；这些证据不能事后伪造。只读数据见 [summary](p1-diagnosis-07/summary.json)、[完整事件](p1-diagnosis-07/events.json)、[终端原文](p1-diagnosis-07/pty.raw)。SQLite 仅复制到 worker 自建临时目录再打开，原归档没有改动。

CLI 自己保存的本实例目录信任状态为 false，见 [isolated-project-trust](p1-diagnosis-07/isolated-project-trust.json)。[官方 hooks 的 workspace trust 说明](https://code.claude.com/docs/en/hooks#workspace-trust) 要求交互会话接受目录信任后才运行设置中的 hooks；IS_DEMO 跳过可见引导，没有为这里留下已接受的信任。它是当前最直接的前提缺口。没有 native debug，不能声称已观察到 CLI 某一具体跳过分支，也不能用不存在的 stdin 来比较字段。

当前禁止按键穿提示或预置未文档化信任状态，不能自行填 hasTrustDialogAccepted、改身份检查或调大 timeout。需要决定的方案与范围见 [blocking issue 正文](p1-trust-question-07.md)，已提交 `20261013T182412Z-worker:s13-t078s-issue-001`。建议允许主控审核只含 value.txt 的隔离 repo 后，通过明确指定、逐次审批的原生 UI 操作完成信任；移除 IS_DEMO 以显示实际停点，任何其他引导都停下读回。若继续禁止，交互 hooks 验证维持 BLOCKED。

## 假 API：已确认的串行等待

[原请求](p1-diagnosis-07/api-request.json) 是标题侧请求，其 output_config.format 明确要求只有 title 字段的 JSON schema。这里由人工读回请求用途；没有程序按文字关键词判断内容含义。

原代码使用串行 HTTPServer；第一条 Messages 请求写 api-request 后，要等 api-release 才发 HTTP 200 与 SSE。runner 把该标题请求当成主请求，在 hook 缺失处立即停下，尚未写 release。归档没有 api-release 或 api-response.sse，stderr 为空。因此可以确认标题请求占住了唯一 handler；不能从 API 日志未出现第二条，推断 CLI 没有排出主请求，也不能归咎于已经发送的非法 SSE——根本尚未发送。

原计划回应是普通 P1_ACK 文本，若送给标题请求，也不满足它要求的 title JSON。最小修改是只在假服务 P1 profile 设置文档化的 [CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1](https://code.claude.com/docs/en/env-vars)：官方说明它还跳过标题模型请求。保留一条主请求预算及原主响应屏障，避免增加线程、侧请求分类、并行回应、预算或重试。此变量同时关闭终端标题与状态报告；本探针只用 hooks 证明忙闲，不据此外推 OSC 状态报告。

## 下一候选的准确提案与审批点

[proposed-start.json](p1-materials-07/proposed-start.json) 给出了新隔离实例绑定的完整建议 argv/env，明确标为未实现、未批准：Bearer 假 token、Haiku 5.5／low、manual、Bash/Read、空 MCP 和角色卡不变；新增 TITLE 变量与 --debug-file，移除 IS_DEMO 和信任 UI 操作属于待决部分。仍不用 --bare、-p、SDK、真实凭据或内部预置。

获准后还应给实际 hook 命令加入只保存本实例原始 stdin／stdout／stderr／退出／耗时的诊断，保持调用唯一 cli.ts signal，不记录环境或私有 capability，不合成事件，不改变 payload 或调用者。不增加 timeout，除非实际记录证明 3 秒触发超时。[官方 debug 说明](https://code.claude.com/docs/en/hooks#debug-hooks) 支持 --debug-file 并在固定 2.1.296 中记录 hook 状态与耗时。

当前 [approval.json](p1-materials-07/approval.json) 仅为未运行的原构造骨架；它不是 proposed-start 的实现，也不能审批为完整 hooks 成功。生成状态 PASS 只指文件构造；[readiness.json](p1-materials-07/readiness.json) 明确 BLOCKED／unconfirmed。启动记录没有写进后台库。真实登录阶段不改变；后续候选需重新冻结参数并单独审批真实启动和信任操作。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-07
```

本阶段只打印 BLOCKED 并退出 2，不启动 API／CLI；continue-07 同样被阻止。材料生成命令为 `python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-07`；重放必须用新编号，不能覆盖原材料。

cleanup-06 的 fixture.tar.gz 超过 5 MiB，尚未外置。另备 `outside-sandbox.sh p1-archive-07`，只使用既有归档器移到外置盘并逐字节读回，留 summary／manifest；该阶段不启动 API／CLI，不依赖信任决定，必须由主控在沙箱外运行。归档的事实源绑定材料 06 与其 source snapshot；不把归档器通用 source_snapshot 提示字段当作不存在的 cleanup/sources.tar.gz 的证明。

此停点来自目录信任权限与验收前提，而不是尚未观察到的 timeout。T-078 整票仍 INCOMPLETE；真实协议、双主控唤醒与真登录复核都没有上调为 PASS。
