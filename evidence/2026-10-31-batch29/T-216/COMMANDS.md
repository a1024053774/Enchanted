# T-216 运行命令

全部命令的工作目录：`/Users/luckye/Documents/Code/a2a-worktrees/T-216`。重跑时把输出路径改为一个尚不存在的新名称；测试有意拒绝覆盖证据。以下为本轮实际使用的命令。

## green-01.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-01.log 2>&1
```

## green-02.json

记录状态：`PASS`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-02.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-02.log 2>&1
```

## green-03-final.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-03-final.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-03-final.log 2>&1
```

## green-04-final.json

记录状态：`PASS`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-04-final.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-04-final.log 2>&1
```

## green-05-final.json

记录状态：`PASS`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-05-final.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/green-05-final.log 2>&1
```

## red-01.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-01.log 2>&1
```

## red-02.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-02.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-02.log 2>&1
```

## red-03.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-03.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-03.log 2>&1
```

## red-04.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-04.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-04.log 2>&1
```

## red-05-final-test.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --revision cac1880f0de5bf029abd5838f46f65f2dbe24d67 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-05-final-test.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/red-05-final-test.log 2>&1
```

## regression-t124-01.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-01.log 2>&1
```

## regression-t124-02.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-02.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-02.log 2>&1
```

## regression-t124-03.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-03.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-03.log 2>&1
```

## regression-t124-04.json

记录状态：`PASS`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-04.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-04.log 2>&1
```

## regression-t124-answer-mutant-01.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t124_controller_e2e.py --mutant answer-as-user --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-answer-mutant-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t124-answer-mutant-01.log 2>&1
```

## regression-t132-01.json

记录状态：`PASS`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t132-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t132-01.log 2>&1
```

## regression-t133-01.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t133-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t133-01.log 2>&1
```

## regression-t133-baseline-01.json

记录状态：`INCOMPLETE`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --revision cac1880f0de5bf029abd5838f46f65f2dbe24d67 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t133-baseline-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t133-baseline-01.log 2>&1
```

## regression-t171-01.json

记录状态：`PASS`。红态或变异的 INCOMPLETE 是预期拒绝，不能当作候选绿态。

```sh
python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t171-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-t171-01.log 2>&1
```

## 相关隔离测试与基线

```sh
node workbench/tests/test_t078_inbox_domain.ts /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-inbox-domain-01 > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-inbox-domain-01.log 2>&1
node workbench/tests/test_t078_pane_runtime.ts /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-pane-01 > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-pane-01.log 2>&1
node workbench/tests/test_t078_a13_rehearsal.ts /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-inbox-rehearsal-01 --recipient-offline > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-inbox-rehearsal-01.log 2>&1
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_baseline_aux.py test_t078_inbox_domain.ts /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-domain-baseline-02 > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-domain-baseline-02.log 2>&1
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_baseline_aux.py test_t078_pane_runtime.ts /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-pane-baseline-01 > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/regression-pane-baseline-01.log 2>&1
git diff --check
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```
