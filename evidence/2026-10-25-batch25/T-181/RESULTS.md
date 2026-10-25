
## 独立审查第一轮（`review-agy-01.md`，候选 468cde5b2）：`T-181 REVIEW NO_GO`

- P1：候选分支切在 T-178 合并之前，相对现在的 main 看起来像回退了 T-178。处置：把 main 合并进 `exec/t181`（24e8ca053），现在相对 main 只有 T-181 自己的 6 个文件；合并后 `green-02` PASS（深色像素 12004 / 866，开局说明在模型上下文里）。
- P2：真实复跑的回合结束检测失效。审查员推测是最后一条 assistant 记录没有 message；用归档的原生记录离线重放（`detector-replay-01/result.txt`）核对，最后一条 assistant 记录就带 `stop_reason: end_turn`，真正原因是测试隔 20 秒重读文件后用 `is` 比较两个不同的 Python 对象，永远为假。已改为比较记录的 `uuid`；重放显示旧判断为 False、新判断为 True。没有为此再跑一次真实模型。
- P3：haiku 写的 `check_readme.py` 只查关键字，没有机械核对 T-2 卡里约定的示例格式（卡的目标里写了“- 物品名：库存 X，最低 Y，需补 Z。”）。这是模型写验收的行为，记入报告，不在本票改。

## 独立审查第二轮（`review-agy-02.md`，候选 6e180178a）：`T-181 REVIEW PASS`

确认 P1 已消除（相对 main 只剩 T-181 的改动）、P2 根因更正成立。一项 P3：认为没有独立的 ticket 文件。实际 ticket 在 `.project-map/tickets/T-181-controller-guidance-l08.md`，审查员看错了目录，不改。
