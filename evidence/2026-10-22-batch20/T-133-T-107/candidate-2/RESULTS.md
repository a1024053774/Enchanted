# T-133 方案 A 与 T-107 #2、#4、#5 候选 2 结果

- **候选**：代码 `fbf68c404`；测试与夹具到 `cb6e7d75c`。
- **起因**：独立审查 01（`../candidate-1/review-01.md`）结论 INCOMPLETE，没有代码缺陷级发现（P0/P1）。
- **结论**：Claude Code 一侧 **INCOMPLETE**：复审 02（`review-02.md`）没有阻碍项，结论 INCOMPLETE 只因下面两项未完成；另有 2 条 P3，处理见 T-133 ticket。Codex 一侧仍 **BLOCKED**，等用户定（`../codex-hook-probe/RESULTS.md`）。T-107 #3 仍等用户回答。

## 审查 01 的处理

| 发现 | 处理 | 证据 |
| --- | --- | --- |
| P2：T-133 验收第一条的三种输入不在同一次运行 | 新测试在同一次运行里加上受管 worker：桌面操作员派出 T-1，用户在问题面板答复它的上报、在它的窗格里打一段字 | 新检查 `three_kinds_in_one_view`：记录页同时列出主控终端提交、面板答复、窗格键入；后两条标人工介入，主控终端的不标；派发文字不出现 |
| P2：Claude Code 被 Esc 中断后最长 60 秒仍显示运行中 | 不改。Claude Code 没有中断事件可接；已写进 README 与侧栏缺口说明 | — |
| P3：`source_ref` 缺失时记录页读取报错 | 改为 `source_ref?.label` | 只有代码 |
| P3：侧栏每次读全部 `terminal_turn` | 不改。只取两个字段，量与回合数同级；量大时再按角色申请过滤 | — |

## 端到端（`../../T-137/candidate-2/e2e/commands.sh`，与 T-137 同一脚本）

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | 失败（保留） | `answer_issue` 返回 `operation_busy`：门禁操作锁当时被 worker 自己的调用占着，测试没重试。属于测试问题，之后测试只对这个错误重试（`cb6e7d75c`） |
| green-02 | PASS，11 项 | — |
| red-parent（`--revision 836b9eeb0`） | 失败 | 构思主控一直不是“空闲” |
| mutant-recorded-without-role、-02 | 失败 | `only_approved_prompts_recorded` |
| t133-t134-green | PASS，14 项 | — |
| t107-live-green | PASS，7 项 | — |

- **摸底运行**：`probe-01`、`02` 原样保留。
  - `01`：操作员没有自己的项目，写任务名时门禁报 `unknown_task`。之后改用完整 id。
  - `02`：通过。
- **夹具**：已归档，见 `e2e/fixtures.archive.json`。
