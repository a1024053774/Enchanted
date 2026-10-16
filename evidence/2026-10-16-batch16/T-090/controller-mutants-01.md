# T-090 审查变异的沙箱外执行（执行主控，2026-10-16）

独立审查 01 的 reviewer 在沙箱内无法调用 `/bin/ps`，原版与三个变异都停在夹具启动，未到业务断言（它没有把这些退出码算作抓住错误实现）。执行主控在沙箱外按审查报告中写明的精确改动重建变异并运行，变异由 reviewer 设计，主控只执行。

- 隔离副本：从 `/Users/luckye/Documents/Code/a2a-wt-t090` `git clone --shared --no-checkout`，稀疏检出后 checkout 冻结候选 `ca6ac9aa3d998fd376dc4693bb06a6f05cd77f46`，依赖链接既有 `workbench/node_modules`；不改共享 worktree。
- 变异改动（diff 见同目录 `controller-mutant-*.diff`）：M1 删除 `core.ts:2347–2351` 整个 worker 状态检查；M2 删除 `:2350` 当前 status 比较、前一行 `&&` 改逗号；M3 删除 `:2349` 当前 symbolic-ref 比较。三者 `node --check` 均 0。
- 命令：`python3 -B <source>/workbench/tests/test_t090_review_worker_boundary_e2e.py --source <副本> --output <新目录> [--case <场景>]`。

| 运行 | 结果 | outcome / failure_id |
| --- | --- | --- |
| 原版，三场景 | exit 0 | worker_head_changed、worker_became_dirty、worker_branch_changed 均 passed |
| M1，worker_head_changed | exit 1 | contract_failure / T090-WORKER-HEAD |
| M2，worker_became_dirty | exit 1 | contract_failure / T090-WORKER-DIRTY |
| M3，worker_branch_changed | exit 1 | contract_failure / T090-WORKER-BRANCH |

四次 cleanup.json 均 `failures: []`、`host_exit: 0`。原始输出归档外置盘（见 `controller-mutants-01.archive.json`，701 文件、7,564,907 字节，删除临时目录前逐项核对文件数与字节数一致）。

主控第一次运行变异时因 zsh 不拆分 `set -- $pair` 导致三条命令未真正执行（cd 失败），该次 rc=1 不计入，改用两个参数的函数重跑，上表为重跑结果。

另：独立审查 P2（`workbench/README.md` stale）由主控核实——README 115–116 与 194 行的描述仍成立，补注 worker worktree 比较的是审查开始时 `review_requested` 记下的 HEAD、分支和干净状态（T-090），不要求等于候选。
