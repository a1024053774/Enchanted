# 第二轮实际运行命令

工作目录：`/Users/luckye/Documents/Code/a2a-worktrees/T-216`。重跑时换用未存在的输出名称，保留所有既有红态、绿态与反例。

## round2-duplicate-counterexample-01.json

记录状态：`INCOMPLETE`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-duplicate-counterexample-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-duplicate-counterexample-01.log 2>&1
```

## round2-green-processor-01.json

记录状态：`PASS`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-green-processor-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-green-processor-01.log 2>&1
```

## round2-green-routing-offline-01.json

记录状态：`PASS`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-green-routing-offline-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-green-routing-offline-01.log 2>&1
```

## round2-green-routing-online-01.json

记录状态：`PASS`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-green-routing-online-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-green-routing-online-01.log 2>&1
```

## round2-red-processor-01.json

记录状态：`INCOMPLETE`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case processor --source /private/tmp/t216-r2-before-ilfz7fmn --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-red-processor-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-red-processor-01.log 2>&1
```

## round2-red-routing-offline-01.json

记录状态：`INCOMPLETE`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --source /private/tmp/t216-r2-before-ilfz7fmn --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-red-routing-offline-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-red-routing-offline-01.log 2>&1
```

## round2-red-routing-online-01.json

记录状态：`INCOMPLETE`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --source /private/tmp/t216-r2-before-ilfz7fmn --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-red-routing-online-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-red-routing-online-01.log 2>&1
```

## round2-regression-t124-01.json

记录状态：`PASS`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t124-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t124-01.log 2>&1
```

## round2-regression-t132-01.json

记录状态：`PASS`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t132-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t132-01.log 2>&1
```

## round2-regression-t171-01.json

记录状态：`PASS`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t171-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t171-01.log 2>&1
```

## round2-regression-t216-01.json

记录状态：`PASS`。红态与 duplicate-submit 反例的退出码 1 是预期拒绝。

```sh
python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t216-01.json > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round2-regression-t216-01.log 2>&1
```
