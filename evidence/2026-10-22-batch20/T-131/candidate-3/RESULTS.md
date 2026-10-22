# T-131 候选 3 结果

- **候选**：`d436fd390`（代码、README 与测试同一提交）。
- **起因**：候选 2 的独立复审 02 结论为 INCOMPLETE，附一条 P1：另一个任务验收合并冲突时，门禁把现场保留在 `refs/a2a/verifications/<任务>/a<N>/v<K>-candidate` 与 `…-base`（`core.ts` 的 `verification_conflict`）。候选 2 只认 `…/v<K>`，这两个引用一出现，正在进行的审查就会在回收时被拒（`review_shared_refs_changed`）。
- **结论**：**PASS**（待复审）。

## 改了什么

- `reviewRefsUnchanged` 认验收引用时，允许名字带 `-candidate` 或 `-base` 后缀，其余规则不变（N 仍不能超过该任务当前的 attempt 序号）。
- README 共享引用一段补上这两个名字。
- 测试加 `--retained-ref`：T-2 审查期间，按门禁的命名写入 `refs/a2a/verifications/demo+T-1/a1/v1-candidate` 与 `…-base`，期望 T-2 审查照常通过。这两个引用由测试用 `update-ref` 写入，不是真造一次合并冲突；命名取自门禁源码。

复审 02 另两条：

- P3（README 未列冲突引用）：已随 P1 一并补上。
- P3（T-131 票文件不存在）：误报。`.project-map/tickets/T-131-parallel-workers-one-project.md` 已在 `03b2d66a3` 提交，`git ls-files` 可查。

## 端到端（`e2e/commands.sh`）

红态先跑：修正前，用主 checkout 的新测试以 `--revision ea68df9d9`（候选 2 的代码）跑 `--retained-ref`。其余运行都在 `d436fd390` 的干净分离 worktree 里进行。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| red-candidate-2-retained（修正前） | 失败 | T-2 审查回收被拒，任务 `paused`，审查 `unknown` |
| green | PASS，10 项 | — |
| retained-ref | PASS，10 项 | — |
| foreign-plain（`refs/heads/foreign`） | PASS：T-2 回收时报 `review_shared_refs_changed` | — |
| foreign-other-task（`refs/a2a/attempts/demo+T-1/rogue`） | PASS：同样被拒 | — |
| mutant-other-namespace-prefix-only | 失败 | 没有拒绝 |
| mutant-strict-ref-equality | 失败 | T-1 审查会话回收超时（与候选 2 相同） |
| mutant-integration-chain-ignored | 失败 | T-2 审查 `unknown` |
| mutant-any-ref-accepted | 失败 | 没有拒绝 |
| t122-green | PASS，23 项 | — |

修前（`03b2d66a3`）没有多 worker 的红态见候选 2，本轮没有重跑。夹具已归档，见 `fixtures.archive.json`。
