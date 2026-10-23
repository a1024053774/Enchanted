# 合并后回归 09（main 51266ed33，含 T-150～T-154 与 HISTORICAL.md 更新）

命令：`zsh RUN-MERGE-REGRESSION-07.sh 51266ed33`（回归 06 的 32 项，加迁移后的 t091、t078）。

- 33 项 exit=0：回归 06 的 32 项与 t078-migrated。
- t091-migrated 首次 exit=1，`TypeError: vm.SourceTextModule is not a constructor`（`t091-migrated.json`/`.log` 原样保留）：执行主控写脚本时漏了 T-150 RUN-LOCAL-01 使用的 `--experimental-vm-modules`。脚本已改，同一检查 worktree（51266ed33）单独重跑 exit=0、PASS、33 个检查组（`t091-migrated-rerun.json`）。
