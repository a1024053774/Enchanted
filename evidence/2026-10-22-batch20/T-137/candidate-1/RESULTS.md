# T-137 候选 1 结果

- **候选**：代码 `e58d30957`。正式运行用 `1f7dac8b9`：其中的 README 与打分行左对齐样式在这个提交里。
- **修前版本**：`c24d58955`。
- **来源**：用户 2026-10-22 逐字（第 6 条），见 ticket。
- **结论**：**INCOMPLETE**，等独立审查。

## 改了什么

- **定期复盘默认关闭**：只改出厂默认值。已有数据目录里的设置是只追加的行，不改写。
- **Reflect 页**（页签名 Reflect）：替换原“复盘”页签。内容分两块：
  - **会话树**：
    - 来自只读命令 `reflect_tree`（`src/reflect.ts`）。
    - 列出本项目历来生效过的终端主控角色（含已结束的）和全部启动记录。
    - 层级来源：启动记录的 `parent_launch`，以及批准执行主控时选的上级。
    - 同一终端先后拿到的角色是不同的主控。终端里启动的会话，归到它启动时那个终端持有的角色。
    - 每行显示角色、任务、CLI、模型、强度、起止时间与状态。
    - worker 上显示门禁 `score_recorded` 里交付的 launch 对应的打分，含结果、两项分数、理由与备注。
  - **复盘**：原页面的立即复盘、定期复盘、建议与记录。
    - 定期复盘多了执行者（CLI、模型、强度）的选择与保存。
    - 批准的建议只记录，不再写“交构思主控”。
- **T-136 测试随之改动**：
  - 改点 Reflect 页签；
  - 它的定期复盘场景改为由测试自己开启。原场景以“默认开启”为前提。

## 端到端（`e2e/commands.sh`）

- **测试**：新测试 `test_t137_reflect_e2e.py`。
  - 真实后台、门禁、项目终端；
  - 真实 Claude Code worker、审查员与复盘会话，模型是本地脚本化接口；
  - 真实 Electron。
- **期望来源**：ticket 与场景。场景见测试文件开头。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，8 项 | — |
| red-parent（`--revision c24d58955`） | 失败 | `schedule_off_by_default`（修前默认开启，也没有 Reflect 页） |
| mutant-schedule-on-by-default | 失败 | `schedule_off_by_default` |
| mutant-ended-not-listed（只列在跑的） | 失败 | 会话树不到 6 行 |
| mutant-role-by-terminal-only（终端的会话归到它的第一个角色） | 失败 | `sessions_under_the_role_held_when_they_started` |
| mutant-score-on-attempt（按 attempt 挂分，审查员也挂上） | 失败 | `score_on_scored_worker_only` |
| t136-green | PASS，13 项 | — |
| t133-t107-green（终端主控，在本候选代码上） | PASS，10 项 | — |
| t107-live-green | PASS，7 项 | — |

- **摸底运行**：`probe-01`（`e58d30957`）通过，原样保留。截图里打分行被全局 `dl` 样式推到右侧，之后改为左对齐（`1f7dac8b9`）。夹具已归档，见 `e2e/fixtures.archive.json`。
- **截图**：`01-reflect-tree.png`、`02-schedule.png`、`03-retrospective.png`，在 green 的夹具 `out/` 里，已随夹具归档。

## 未覆盖与已知边界

- 夹具里的终端主控经 socket 批准，没有 CLI，显示“CLI 未知”。终端主控的模型与强度目前都记为未知：后台不知道用户自己启动的 CLI 用的什么模型。
- 受管主控（`controller_start`）之间经收件箱建立的关系没有纳入 Reflect，只用 `parent_launch`。第三阶段的主控都是终端角色。
- Codex 复盘会话、打包后的应用。
