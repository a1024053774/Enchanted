# T-198 结果：交付里卡外改动的文件交主控判断

日期：2026-10-27。状态：PASS。

## 改动

- `workbench/src/gates/core.ts`：`checkPaths` 把任务卡以外的改动记为 `verification.out_of_card` 与 `path_check` 事件的 `out_of_card`，不再以 `path_boundary_failed` 结束验收。新命令 `out_of_card`（执行主控，任务须为 `verified`）：`accept` 带理由，记 `out_of_card_judged`，存为 `task.out_of_card_judgement`；`reject` 带理由，撤销此前的放行，按打回（计入 `path_boundary`）发回 worker。`integrate` 在未判断时返回 `out_of_card_unjudged`。放行只对一次交付有效：新交付、`invalidate`、打回都清除它；工作分支前进后重验同一候选仍有效（审查第 1 轮 P1 的修复）。审查员提示里列出卡外清单。验收文件（T-080）与 Git 元数据守护照旧硬拒。
- `workbench/src/panes.ts`：主控打回卡外改动时，发给 worker 的反馈开头说明“主控没有放行”。
- `workbench/src/gates/taskHistory.ts`：路径检查显示“卡外改动待主控判断”，新增“放行卡外改动”“打回卡外改动”步骤。
- 契约 `a2aGates.ts`：`out_of_card` 命令、`decision`、`A2AVerification.out_of_card`、`A2ATask.out_of_card_judgement`。
- 说明：SKILL.md 第 4 步第 5、6 条，`a2a help`，README 卡外段与 run 段（自动 run 遇未判断的卡外改动会暂停，审查第 1 轮 P2）。

## 证据（真实后台、socket、终端主控、真实 Claude Code CLI；模型为本地脚本服务）

测试：`workbench/tests/test_t198_out_of_card_e2e.py`，8 项检查，变异 `boundary-still-fails`、`integrate-unjudged`。

| 文件 | 版本 | 结果 |
| --- | --- | --- |
| `red-01-oracle-order.json` | `bb447be50` | 首次红态先卡在验收文件检查（断言顺序问题），已调整；保留 |
| `red-bb447be50.json` | `bb447be50` | 失败于 `out_of_card_waits_for_judgement`：验收直接 `path_boundary_failed` |
| `green.json`、`mutant-*.json`、`frozen-*.json` | 第 1 轮候选 | 7 项 PASS；两个变异各在业务断言失败 |
| `red-withdrawn-prefix.json` | 第 1 轮冻结候选 | 新增场景被审查收尾的 `review_end_check_required` 先挡住，测试改为等收尾；保留 |
| `red-withdrawn-prefix-02.json` | 第 1 轮冻结候选 | 失败于 `withdrawn_accept_does_not_return`：放行后打回、重交原提交仍集成，`notes/extra-2.txt` 进入 main |
| `green-02/03/04-withdrawn.json` | 修复中 | 测试夹具问题：worker 沙箱只放行单独的 `git add`/`git commit`；审查收尾占用操作锁；保留 |
| `green-05.json` | 修复后工作区 | 8 项 PASS |
| `frozen2-green.json`、`frozen2-mutant-*.json` | 冻结候选 `4a5e1f3fc + T-198.diff` | 8 项 PASS；两个变异各在业务断言失败 |

复跑（`workbench/` 下）：

```sh
python3 tests/test_t198_out_of_card_e2e.py --summary <新路径>
python3 tests/test_t198_out_of_card_e2e.py --mutant integrate-unjudged --summary <新路径>
python3 tests/test_t198_out_of_card_e2e.py --revision bb447be50 --summary <新路径>
```

## 独立审查（Codex gpt-6.1-sol high，只读）

- 第 1 轮 `review-1.md`：NO_GO。P1 打回不撤销放行，旧候选重现可集成；P2 自动 run 暂停没写进说明。两条都已修复。
- 第 2 轮 `review-2.md`：PASS，审查冻结候选；独立复验 C1→C2→C1、revoke/revise 重派、同候选重验等场景。

## 未覆盖

- 未做 Electron 实机界面检查；任务页只核对 `task_history` 投影。
- 模型回合为脚本化接口。
