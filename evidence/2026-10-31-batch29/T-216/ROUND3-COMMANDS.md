# 第三轮命令

工作目录：`/Users/luckye/Documents/Code/a2a-worktrees/T-216`。重跑换用尚不存在的输出名称；前两轮证据及本轮失败记录均保留。

迁移：`git stash push -u -m "T-216 round3 before main fast-forward"` → `git merge --ff-only main` → `git stash pop`。没有冲突。完整迁移前差异见 round3-before-rebase.patch。

## round3-routing-online-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-online-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-online-01.json -- python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-online-01.json
```

初次外层采集失败保存在 `.hc.json`；对同一已结束现场补采并停止私有 core：

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --existing --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-online-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-online-01.json --proof /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-online-01.hc-recovered.json
```

## round3-routing-offline-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-offline-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-offline-01.json -- python3 workbench/tests/test_t216_round2_e2e.py --case routing-offline --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-offline-01.json
```

初次外层采集失败保存在 `.hc.json`；对同一已结束现场补采并停止私有 core：

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --existing --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-offline-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-offline-01.json --proof /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-routing-offline-01.hc-recovered.json
```

## round3-processor-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-processor-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-processor-01.json -- python3 workbench/tests/test_t216_round2_e2e.py --case processor --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-processor-01.json
```

初次外层采集失败保存在 `.hc.json`；对同一已结束现场补采并停止私有 core：

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --existing --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-processor-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-processor-01.json --proof /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-processor-01.hc-recovered.json
```

## round3-duplicate-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-duplicate-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-duplicate-01.json -- python3 workbench/tests/test_t216_round2_e2e.py --case routing-online --duplicate-submit --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-duplicate-01.json
```

初次外层采集失败保存在 `.hc.json`；对同一已结束现场补采并停止私有 core：

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --existing --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-duplicate-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-duplicate-01.json --proof /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-duplicate-01.hc-recovered.json
```

## round3-t216-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t216-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t216-01.json -- python3 workbench/tests/test_t216_issue_push_e2e.py --gui --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t216-01.json
```

## round3-t124-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t124-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t124-01.json -- python3 workbench/tests/test_t124_controller_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t124-01.json
```

## round3-t132-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t132-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t132-01.json -- python3 workbench/tests/test_t132_issues_panel_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t132-01.json
```

## round3-t171-01.json

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/run_round3.py --log /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t171-01.log --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t171-01.json -- python3 workbench/tests/test_t171_superseded_issue_e2e.py --summary /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t171-01.json
```

## T-212 项目终端

```sh
python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t212-01 > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-t212-01.log 2>&1
```

## 完成检查

```sh
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3_delivery_check.py > /Users/luckye/Documents/Code/a2a-worktrees/T-216-evidence/round3-delivery-checks.log 2>&1
```

完成检查内部逐字比较完整 diff、禁止改动的投递方法和报告前缀，并运行 `git diff --check`、项目地图 status。没有计算校验值。
