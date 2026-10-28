# T-208 任务页底部在审查中显示“门禁 未知”（2026-10-28）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，见 `review-1.md`；唯一一条 P2（覆盖检查只认 `task.state = "x"`，漏掉三元式与建任务时的状态）已改，改后 `green-3.json` 通过。

## 根因

界面的状态名表 `gateStateNames`（`workbench/src/gateReceipts.ts`）缺门禁实际会写的 `reviewing`、`rework`。任务页底部查不到名字就显示“未知”，门禁记录标题和任务标签则直接显示英文代码。

## 修复

`gateStateNames` 补上 `reviewing: '审查中'`、`rework: '返工中'`。门禁状态本身不改。

## 主测试

`workbench/tests/test_t208_gate_state_names_e2e.py`。环境：
- 真实 Electron 窗口，真实后台与门禁。
- worker、审查员是真实 Claude Code，模型换成本地脚本化接口，零真实模型调用。

场景：worker 交付，`verify` 通过后门禁进入 `reviewing`；审查员 `sleep 40`，保持审查中。这时点侧栏的 worker 行打开任务页，读底部的门禁状态。

检查（预期来自需求）：
- `still_in_review_when_read`：读页面后门禁仍是 `reviewing`，看到的确实是审查中的页面。
- `review_state_named`：底部 `data-gate-state=reviewing`，文字是“审查中”。
- `every_gate_state_named`：从门禁源码 `src/gates/core.ts` 里列出任务能被写成的状态，逐个在 `gateStateNames` 里查名字（不手抄状态清单）。
  - `task.state = ...;` 右边能取到的值：三元式取两个结果，不取条件里比较的字面量；
  - 新建任务记录时的初始状态（`state`、`spec_rev`、`fence`、`current_attempt` 一起出现的那个对象）。
  - 共 15 个。第一版只认 `task.state = "x"`，得到 12 个，漏了 `creating`、`abandoned`、`upgraded`（审查 P2）。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | `--revision f5ae30f78`（修前） | 失败：底部显示“未知”；缺 `reviewing`、`rework` |
| `green-1.json`、`mutant-rework-unnamed.json` | 无效：替换没匹配上（缩进不对），修复没落盘就跑了；变异体报“变异定位必须唯一”。保留为记录 |
| `green-2.json` | 修后 | 通过，3 项；底部“审查中” |
| `mutant-rework-unnamed-2.json` | 只补 `reviewing`、去掉 `rework` | 只在 `every_gate_state_named` 失败（缺 `rework`） |
| `green-3.json` | 修后，按审查 P2 放宽状态提取之后 | 通过，3 项；提取到 15 个状态，无缺 |
| `mutant-rework-unnamed-3.json` | 同上测试，去掉 `rework` | 只在 `every_gate_state_named` 失败（缺 `rework`） |
| `mutant-upgraded-unnamed-1.json` | 去掉只由三元式写入的 `upgraded` | 只在 `every_gate_state_named` 失败（缺 `upgraded`）；第一版测试看不到这个状态 |

`red-1`、`green-2` 的截图与界面日志在外置盘，清单见 `red-1-screenshot.archive.json`、`green-2-screenshot.archive.json`。

复现（在 `workbench/tests` 下）：`python3 test_t208_gate_state_names_e2e.py --summary <新路径> [--revision f5ae30f78 | --mutant rework-unnamed|upgraded-unnamed]`

## 顺带查过：顶部任务标签

`green-2` 的截图里，底部是“审查中”，顶部任务标签却是“验收中”。探针 `probe_t208.py` 每 4 秒同时读标签、底部和门禁状态，输出见 `probe-tab-refresh.json`：
- 第 0 秒：标签“已认领”，底部“审查中”，侧栏数据已是 `reviewing`。
- 4 秒后：两处一致。

标签来自每 3 秒一次的侧栏轮询，比打开任务页时读的状态晚一拍，下一轮就对上了。这不算本票缺陷，没有改。

审查结束后门禁转为 `paused`，是因为夹具里的审查员只 sleep、不交结论，与本票无关。

## 没做

- `rework` 的中文名只经源码覆盖检查证明，没有在界面上走一遍返工流程。

## 独立审查

`review-1.md`：agy `gemini-3.8-flash-high`，只读，结论“可合并”。
- P2：覆盖检查的提取式漏掉三元式与建任务时的状态。已按上文改，补变异体 `upgraded-unnamed` 证明新提取能看到它。
- 审查也核对了：界面里没有别的状态名表缺 `reviewing`、`rework`；探针数据支持“顶部标签只是轮询滞后”的判断。
