# T-090 独立复核 02

STATUS: PASS

TARGET: `exec/t090`，`e89ccaa346a0f66f61e8759418f661973304a209`；产品与测试候选仍为审查 01 的 `ca6ac9aa3d998fd376dc4693bb06a6f05cd77f46`。

2026-10-16。按本次派发，只读复核审查 01 的变异执行缺口与 README stale 项。本报告是本轮唯一写入；未重新执行受沙箱限制的运行、未申请升级权限、未改产品、测试或地图。开始及写报告前核对 HEAD，均为上述 e89ccaa34 完整提交号。

两项缺口均已补齐，未发现新问题。最终结论为 T-090 独立审查 PASS。审查 01 的 INCOMPLETE 保留为当时的证据记录，由本报告记录补证后的结论。

## EVIDENCE：候选同一性

实际执行：

```sh
git diff ca6ac9aa3 e89ccaa34 -- workbench/src workbench/tests acceptance
```

输出为空，退出 0。此次新增的说明、diff 与归档记录没有改变先前审查过的产品逻辑或测试条件。因此沿用审查 01 对冻结候选的代码分析与已逐项核实的回归证据，只复核新增证据及 README 文本。

## COUNTEREXAMPLE：完成条件与变异检查

原始归档根目录：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/controller-mutants-01/`，由 `controller-mutants-01.archive.json` 指向。

本 reviewer 从冻结候选的 `core.ts` 重建 M1/M2/M3 应有改动，比较差异内容；同时逐字节比较仓库的三份 `controller-mutant-*.diff` 与归档中的对应 diff。三份均一致，且没有额外改动：

| 变异 | 与审查 01 设计的对应关系 | 归档原件的结果 |
| --- | --- | --- |
| M1-omit-worker | 删除 `core.ts:2347–2351` 整个 worker 状态 requireGate，保留其余检查。 | `M1-omit-worker-result/run.json`：`worker_head_changed` 为 `contract_failure`，`failure_id=T090-WORKER-HEAD`。 |
| M2-omit-clean-status | 删除 `:2350` 当前 status 比较，将前一行末尾 `&&` 改成逗号；保留起始干净状态、HEAD 和分支检查。 | `M2-omit-clean-status-result/run.json`：`worker_became_dirty` 为 `contract_failure`，`failure_id=T090-WORKER-DIRTY`。 |
| M3-omit-current-branch | 仅删除 `:2349` 当前 symbolic-ref 比较行。 | `M3-omit-current-branch-result/run.json`：`worker_branch_changed` 为 `contract_failure`，`failure_id=T090-WORKER-BRANCH`。 |

上述结果逐项交叉核对了归档的 `run.json`、逐场景 `case.json`、顶层 `.log`、`worker-boundary-readback.json` 与 `cleanup.json`，没有只接受主控 Markdown 摘要：

- 原版 `baseline-worker/run.json` 为 PASS，计划及实际均为 HEAD、dirty、branch 三场景，全部 `passed`，没有失败断言。
- 三个变异均通过 `T090-EXTERNAL-MUTATION` 前置断言；实际共享 refs 等于审查开始时的 refs，排除了共享 refs 变化造成的干扰。各自唯一失败断言就是上表对应的业务 failure_id，没有 harness_error。
- 三个变异的原始读回均为 task verified、review passed，副本和审查目录已删除，有 `review_reclaimed`、没有 `review_lifecycle_failed`。这正是故意遗漏 worker 检查会造成的错误放行。
- 原版三个场景的原始读回均为 task paused、review unknown，副本和审查目录保留，有 `review_lifecycle_failed`、没有 `review_reclaimed`。修复版本保留了应有的拒绝能力。
- 四次测试调用共对应六份逐场景 `cleanup.json`，全部 `failures: []`、`host_exit: 0`；各 case 的 cleanup_failures 也均为空。

变异由 reviewer 在审查 01 中设计并已构造；此次由执行主控在允许 `/bin/ps` 的宿主中按该设计重建、代跑，再由 reviewer 独立读取原件核验。主控所记原版 exit 0、三个变异 exit 1 与原始运行状态及 runner 返回规则一致。有效证据是业务断言捕获了错误行为，不能将变异 run.json 的 INCOMPLETE 当成补证失败，也没有把第一次 zsh 参数拆分错误的非零退出计入证明。本次没有声称 reviewer 自己在沙箱内跑通了它们。

## EVIDENCE：README 与地图

`workbench/README.md:116` 明确写明 worker worktree 比较的是审查开始时 `review_requested` 记录的 HEAD、分支和干净状态，不要求等于候选；`:194` 的 worker 目录核对补上“相对审查开始时的快照”。

两处描述与 `core.ts:2220–2232` 的快照保存及 `:2344–2351` 的结束比较一致，且没有改写候选 C、审查目录或共享 refs 的要求。代码仍额外要求起始状态干净、起始分支为预期 worker 分支，因此补注没有把脏状态或 detached 基线表述为可以接受。

开始及报告前均执行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

两次均退出 0，`Problems (0)`、`Stale living docs (0)`。审查 01 的 P2 stale 完成条件缺口已解决。

## FINDINGS 与结论范围

未确认新的产品或验收缺陷。审查 01 的两项未完成条件均已解决，T-090 独立审查最终 PASS。

既有证据的范围保持原样：各套件是在同一产品与验收文件的不同运行中分别通过；未出现一次整组全绿。本次没有重写此前失败运行，也没有将短时限失败的负载推断升级为已排他证明的因果结论。缺快照、错 review_id、起始脏与起始 detached 的判断仍来自审查 01 的控制流分析，本次没有补称动态验证。这些已披露限制不构成本次两项补证之外的新验收条件，也不支持可靠性或性能收益主张。

T-090 REVIEW 02 DONE
