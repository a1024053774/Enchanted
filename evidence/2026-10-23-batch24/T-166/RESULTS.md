# T-166 工作回合中的用户输入被判 prompt_id 复用：结果

- 写入者：执行主控（Claude Code），按构思主控 answer 20261024T070244Z-ideation-answer-001 转述的用户决定：“让执行主控修,然后做完每个票让 agy 审查”。
- 基线：main `a808c1137`。全部运行使用本地脚本化 Messages，真实厂商模型回合 0。
- 逐项结果见 `CHECKS.json`；完整运行目录已按 T-088 归档，清单见 `*.archive.json`。

## 根因

T-164 中 worker A 的原生转录显示，用户输入发生在原回合仍在生成最终回复时（06:26:12），早于原回合 Stop（06:26:13）。CLI 把输入排队，并以运行中回合的 prompt_id 发出 UserPromptSubmit。T-157 只在 `pane.stopInProgress` 时把这种复用记为排队输入；工作回合中的复用因此被判 `claude_prompt_id_reused`，回合变得不可信，原回合 Stop 随后以 `current_turn_untrusted` 被拒，交付不转交，worker 停在未知。

## 修改

`workbench/src/panes.ts`：
1. 排队输入分支去掉 `pane.stopInProgress` 条件；仍要求当前回合存在、prompt_id 等于当前回合、此前有该窗格真实写入的 Enter、转录路径一致。
2. `scan()` 在当前回合未结束时不登记排队转录回合，等原回合 Stop 完成后再建立新回合。

`workbench/README.md` 对应段落同步。

## 证据

| 项 | 命令 | 结果 |
| --- | --- | --- |
| 红态（端到端） | `test_t166_busy_input_e2e.py`，修前源码（worktree 未改，等于 `a808c1137`） | red-3、red-4：`red_reproduced=true`，事件序列与 T-164 相同：UPS `claude_prompt_id_reused` → Stop `current_turn_untrusted` → `stop_not_matched`，提交未落地 |
| 红态前的测试脚本问题 | 同上 | red-1、red-2：产品同样复现，但测试在“submit 回执”等待上超时（被拒的 Stop 不产生回执），未出判定；修正等待条件后重跑为 red-3/4。原记录保留 |
| 绿态（端到端） | 同上，修后 | green-1/2/3：PASS（原交付被门禁接受、输入原样进 CLI、记人工介入、排队回合由原生转录登记并完成、回到空闲、只有一次 submit） |
| 主机级 | `test_t166_queued_input.py` | 修后 PASS；`--revision a808c1137` 只在 `busy-input-queued` 失败（`claude_prompt_id_reused`） |
| 反例 | 同上 `no-enter-reused` | 没有 Enter 的 prompt_id 复用仍被拒并记录，修前修后都通过 |
| 已知坏实现 | `--mutant scan-ignores-active` / `--mutant accept-without-enter` | 各自只在对应场景失败 |
| 回归 | `RUN-REGRESSION-01.sh` | build、T-157 identity/stop-input/recover/expired、T-165 ordered/unrelated、T-159、T-160 recovery、T-133/T-107、T-161 全部 PASS；T-157 两个 mutant 与 T-165 mutant 按预期失败 |

## 未覆盖

- 未用真实厂商模型复验；真实 Claude CLI 与 PTY 已参与端到端运行。
- T-164 整轮重跑按构思主控 answer 20261024T072734Z-ideation-answer-001，在 T-166～T-168 修完并过审查后进行。

状态：agy 独立审查 PASS（`review-agy-01.md`，两条 P3 观察，无需改动）。
