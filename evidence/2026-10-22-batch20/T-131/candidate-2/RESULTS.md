# T-131 候选 2 结果

- **候选**：`c6921bf44`。README 随后在 `85b212a60` 改了共享引用一段。
- **起因**：候选 1（`8f584d45c`）独立审查 01 结论为 PASS，附一条 P2：凡是带别的任务前缀的引用，候选 1 都放过。只要名字前缀对得上，伪造的引用（例如 `refs/a2a/attempts/<别的任务>/rogue`）也会被当成别的任务的合法改动。
- **结论**：**PASS**（待复审）。

## 改了什么

`reviewRefsUnchanged` 收紧了两点：

- 别的任务的引用，只认门禁给它起的三种名字：`refs/heads/a2a/<任务>-a<N>`、`refs/a2a/attempts/<任务>/a<N>`、`refs/a2a/verifications/<任务>/a<N>/v<K>`；
- 其中 N 不能超过该任务当前的 attempt 序号（`fence`）。

审查 01 的另外两条处理如下：

- 同仓库两个项目有同名任务时会误拒，这条记为已知边界，写进 README；
- “T-131 票文件不存在”是误报：票已在 `03b2d66a3` 提交。

## 端到端（`e2e/commands.sh`）

所有运行都在候选提交的干净分离 worktree 里进行，主 checkout 里未提交的改动进不来。场景与候选 1 相同，另加一个反例 `foreign-other-task`：T-2 审查期间，测试写入 `refs/a2a/attempts/demo+T-1/rogue`。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，10 项 | — |
| foreign-plain（`refs/heads/foreign`） | PASS：T-2 回收时报 `review_shared_refs_changed` | — |
| foreign-other-task | PASS：同样被拒 | — |
| mutant-other-namespace-prefix-only（还原候选 1 的前缀放行） | 失败 | `foreign_ref_during_review_refused`：没有拒绝 |
| mutant-strict-ref-equality | 失败 | T-1 审查会话回收超时 |
| mutant-integration-chain-ignored | 失败 | T-2 审查 `unknown` |
| mutant-any-ref-accepted | 失败 | 没有拒绝 |
| red-parent（`03b2d66a3`） | 失败 | `single_worker_slice` |
| t122-green | PASS，23 项 | — |

夹具已归档，见 `fixtures.archive.json`。
