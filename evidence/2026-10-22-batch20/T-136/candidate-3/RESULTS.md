# T-136 候选 3 结果

- **候选**：`077b83728`。
- **起因**：候选 2 的独立审查 02（`../candidate-2/review-02.md`）结论 INCOMPLETE。F1、F3 确认修好；F2、F4 修了，但各引出一个新问题。
- **结论**：**PASS**（独立审查 03 PASS，无新发现）。

## 审查 02 的处理

| 发现 | 处理 | 证据 |
| --- | --- | --- |
| P2：某次复盘没能启动后，下一次复盘的默认范围从那次的结束时间算起，那次的范围永远没人复盘 | 默认起点取最后一次真正启动了的复盘的结束时间 | 新检查 `retry_after_failed_start_keeps_range`：把目录放回去再启动，范围仍从头开始（`since` 为空）。候选 2 代码与变异 `since-after-failed-run` 都失败在这一项。 |
| P3：找 Codex 复盘会话时，某个别的会话的文件打不开会让整轮归档中断 | 打不开、已消失或首行还没写完的文件，都当作“不是这个会话”跳过 | 只有代码，没有端到端（夹具不跑 Codex）。 |

## 端到端（`e2e/commands.sh`）

运行在 `077b83728` 的干净分离 worktree 里进行。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，13 项 | — |
| red-candidate-2（`--revision 338c51b4f`） | 失败 | `retry_after_failed_start_keeps_range`（`since` 等于没能启动那次的结束时间） |
| mutant-since-after-failed-run | 失败 | 同上 |

候选 1、2 的其余运行覆盖的代码本轮没有改，没有重跑。夹具已归档，见 `fixtures.archive.json`。

## 未覆盖

同候选 2：Codex 复盘会话没有端到端；导入事务的回滚没有端到端；打包后的应用。
