# 第五轮第二份冻结候选只读审计

STATUS: FAIL
TARGET: `round5-candidate-review2.patch`（审计时为 round5-candidate.patch，移名保留）；基线 9c0e262125edb75ed841609472e32c952adc2bbd。

EVIDENCE:
- 24 项最终矩阵符合预期退出码；审计结束时 T133 尚在跑（其后 16 PASS，另见原结果）。
- Claude 三条原生记录各一次；真实 Codex 本地接口及 Codex、agy、opencode 供应商确认各一次。
- 正常未知场景的 Electron 提示可见，hc 原始 RPC 与变异均已核对。

FINDINGS:
- [P1] panes.ts:359：attachShell 只读 dispatch_unknown 恢复未知标记，queue 初始化为空。若后台在 hc_send_intent 与结果记录之间退出，hc 可能已经提交；readWakeDelivery 返回 unknown，但 pane.inboxUnknown 仍空，Electron 不提示。未尝试的排队项也不恢复。应按每条 dispatch 的最后持久状态恢复：未尝试项恢复排队；未闭合意图记未知，界面显示且不重发。

COUNTEREXAMPLE:
- force/working/resend 变异分别在实际输入的业务断言失败；R2 实际重复提交计数拒绝；仅移除 blocked 过滤仍由 hc 拦住，符合契约。

LIMITATIONS:
- 审计只读，未跑供应商、hc 或新测试，不替代 agy 独立审查。
- 此恢复发现当时来自可达源码路径，worker 随后另取真实入口红态；不补称审计时已做运行复现。

RULE:
- 排队后重启必须实际提交一次并保序；已收件、确认前退出必须显示未知且不重发。用 CLI 实际收件记录和 Electron 共同验证。
