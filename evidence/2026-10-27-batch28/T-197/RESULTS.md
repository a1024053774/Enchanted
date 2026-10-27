# T-197 结果：认领时的路径重叠交主控判断，accepted 不占路径

日期：2026-10-27。状态：PASS。

## 改动

- `workbench/src/gates/core.ts` `checkClaimPaths`：同仓库、路径相交的 accepted attempt 记入事件的 `not_counted`，不算占用；其余未释放的重叠照旧进 `conflicts`。拒绝时 `path_overlap` 的 `details` 带清单（任务、attempt、快照、路径）和下一步提示；带非空 `overlap_reason` 放行，理由与清单记入 `claim_path_check` 事件。空白理由由 `text()` 拒为 `invalid_text`。
- `workbench/src/gates/taskHistory.ts`：有冲突的 `claim_path_check` 在任务页显示“路径重叠”，放行时附理由；干净检查不显示。
- 说明：SKILL.md 第 4 步第 3 条、`a2a help`、README 改为“看清单判断，放行必须写理由；已验收的不算”。

## 证据（真实后台、socket、真实 Claude Code CLI，模型为本地脚本服务）

测试：`workbench/tests/test_t131_parallel_workers_e2e.py` 新增 T-197 段与变异 `accepted-still-counted`。

| 文件 | 版本 | 结果 |
| --- | --- | --- |
| `red-head.json` | 修前工作区 | 失败于 `accepted_attempt_holds_no_paths`（`path_overlap`） |
| `red-bb447be50.json` | `--revision bb447be50` | 同一业务断言失败 |
| `green-01-test-keyerror.json` | 候选 | 测试自身错误（认领回执没有 `task`），已改为读 `status`；保留 |
| `green.json`、`mutant.json` | 活动工作区 | PASS 15 项；变异在同一断言失败 |
| `frozen-green.json`、`frozen-mutant.json` | 冻结副本 `bb447be50 + T-197.diff` | PASS 15 项；变异失败于 `accepted_attempt_holds_no_paths` |
| `history_check.ts`、`history_check.out.json` | 活动工作区 | 任务页投影：无理由拒绝与带理由放行各一条“路径重叠” |

复跑（冻结副本或提交后的 `workbench/` 下）：

```sh
python3 tests/test_t131_parallel_workers_e2e.py --summary <新路径>
python3 tests/test_t131_parallel_workers_e2e.py --mutant accepted-still-counted --summary <新路径>
python3 tests/test_t131_parallel_workers_e2e.py --revision bb447be50 --summary <新路径>
```

## 独立审查（Codex gpt-6.1-sol high，只读）

- 第 1 轮 `review-1.md`：INCOMPLETE。审查期间工作区候选因 T-198 开发而变化，审查员按规则停止；未发现 T-197 业务缺陷。由此改为冻结副本审查。
- 第 2 轮 `review-2.md`：PASS，FULL_GO。冻结副本与“基线加补丁”逐文件一致；另做 5 个坏实现变异与独立输入检查，均被拒。

## 未覆盖

- 未做 Electron 实机界面检查；任务页显示只经 `task_history` 投影与既有渲染代码链核对。
- 模型回合为脚本化接口，没有真实模型理解“看清单判断”的说明。
