# 单角色切片的请求文件 helper 所有权

非 blocking；不影响当前真实入口红态材料准备。

观察：`workbench/src/gates/cli.ts:205` 的会话 inbox 命令调用 `queueWorkerRequest`，实际函数位于 `workbench/src/relayFiles.ts:28`；第 30 行只允许 `A2A_ROLE=worker`，是 controller 到达 Stop 前的最早拒绝。该文件未列入主控 #163／#172 的写入范围。后面的 `controller_relay_not_enabled`、nullable controller 与角色 caller 仍是其它待真实探针界定的缺口。

建议：主控将 relayFiles.ts 的会话请求文件写入 helper 纳入 T-078 本切片所有权，后续最小修改沿用它，避免在 cli.ts／relay.ts 另添并行 writer、复制 worker JSON 或伪造 attempt。当前未写 relayFiles.ts，未改变任何请求／转交产品行为；先按已批准顺序取得真实工具入口红态，再实现。若主控另有已分配写入者，可由其提供该处修改并共同冻结候选。
