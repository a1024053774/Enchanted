核对 T-108 后续真实模型计划时发现起点已有的 Codex 启动规则冲突。

workbench/src/panes.ts:500 的 worker_executor_mismatch 仍要求 effort === "xhigh"，而当前 AGENTS.md 明确要求所有 Codex 会话 gpt-6.1-sol high、普通速度。workbench/README.md:465 同样仍写 xhigh。

影响：不能在不绕过用户规则的情况下，用当前生产 dispatch 创建 high 的 Codex 受管 worker。T-108 当前未改这条规则，不通过 xhigh 或直接绕开门禁运行新的真实 worker。本轮计划沿用已有原生 CLI hook 原件回放，新增 Codex 真实模型预算 0；若需要补同步提问的真实模型正例，应先由主控处理启动约束冲突，再单独批准根回合。建议单独分票修正启动与相关合同，保留模型／身份拒绝检查。
