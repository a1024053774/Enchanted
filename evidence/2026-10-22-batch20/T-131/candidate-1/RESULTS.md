# T-131 候选 1 结果

- **候选**：`8f584d45c`。README 随后在 `5d4fcd26c` 改了两段。证据运行期间源码未改动。
- **修前版本**：`03b2d66a3`。
- **结论**：**PASS**（待独立审查）。

## 改了什么

- **`workbench/src/panes.ts`**：去掉 `createThread` 里的 `single_worker_slice` 检查。这条检查是 S1 留下的，限制全后台同时只能有一个 worker 窗格。
- **`workbench/src/gates/core.ts`**：审查结束时的共享引用核对改为 `reviewRefsUnchanged`。

### 为什么要改审查的引用核对

去掉限制后第一次试跑时，发现了这个缺陷，现场见 `../discovery/`。

- **原来的做法**：审查开始时，记下仓库全部引用的快照；回收审查会话时，要求全部引用与快照逐字相同。
- **出了什么问题**：两个任务并行时，T-2 验收新建了自己的引用 `refs/a2a/verifications/demo+T-2/a1/v1`。T-1 的审查明明已经通过，回收时却报 `review_shared_refs_changed`，任务停在 `paused`。

现在放过两类改动，其余任何改动仍然拒绝：

- **别的任务自己的引用**：须是同一仓库里登记过的另一个任务。具体是它的 attempt 分支 `refs/heads/a2a/<任务>-a<N>`，以及 `refs/a2a/attempts/<任务>/`、`refs/a2a/verifications/<任务>/`。
- **工作分支经门禁集成的推进**：审查开始之后，门禁记下了别的任务的 `integrated`、`integrated_reconciled` 事件；从审查开始时的值起，按这些事件的 G→M 一路推进，推进到的值必须等于当前值。

## 端到端（`e2e/commands.sh`）

运行环境：真实后台、socket、经角色申请批准的终端主控，真实 Claude Code（node-pty 交互模式）；Messages 接口是本地脚本。

场景如下：

1. **两个 worker 同时运行**：两张卡路径不相交，T-1 改 `a.txt`，T-2 改 `b.txt`。脚本化接口设了屏障：两个 worker 都发出第一次请求之前，不给任何一边下发工具调用，所以两者必然同时在跑。
2. **路径相交的反例**：第三张卡与 T-1 路径相交，不给理由时派发被拒。
3. **两份审查同时开始**：T-2 的审查员扣住结论，直到 T-1 集成完。这样 T-2 审查期间，既有别的任务新建验收引用，也有工作分支经门禁集成被推进。
4. **T-2 集成时重新验收**：T-2 当初是在旧头上验收的，集成时 CAS 落空，门禁在新头上重新验收后再推进。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，10 项 | — |
| foreign-ref（T-2 审查期间，测试直接写入一个不属于任何门禁操作的 `refs/heads/foreign`） | PASS，8 项：T-2 回收时报 `review_shared_refs_changed`，任务 `paused` | — |
| red-parent（`--revision 03b2d66a3`） | 失败 | `dispatch_T-2_starts_worker`：`single_worker_slice` |
| mutant-strict-ref-equality（还原为逐字相同） | 失败 | T-1 审查会话回收超时：回收被拒 |
| mutant-integration-chain-ignored（不跟随集成推进） | 失败 | T-2 审查 `unknown`、任务 `paused` |
| mutant-any-ref-accepted（--foreign-ref 场景，什么改动都放过） | 失败 | `foreign_ref_during_review_refused`：没有拒绝 |
| t122-green（T-122 正常流程回归） | PASS，23 项 | — |

green 的关键读回：

- **同时运行**：两个 worker 第一次请求相差 0.2 秒。
- **交付各归各**：两份交付的文件、提交尾注（Task、Launch、Native-Session、Model）、worktree 都只对应自己的任务。
- **重新验收**：T-2 集成时记下一次 `integration_compare_failed`，actual 等于 T-1 集成后的头；两个任务最终都是 `accepted`，`a.txt`、`b.txt` 都在 main 上。
- **侧栏**：两个 worker 都挂在终端主控下。

夹具已归档，见 `fixtures.archive.json`。

## 已知边界

- 审查期间，用户自己往工作分支提交，仍按引用被改拒收（T-131 之前就是这样）。
- 不设并发上限。
