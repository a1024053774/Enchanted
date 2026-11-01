# 第二轮重跑

基线来源与 `git archive a09da15f9`、`cp -cR` 命令见 `baseline.json`；没有在主 checkout 增加 worktree。`compare.py` 在独立进程组里执行每个测试，逐项强制 1800 秒上限，固定 TMPDIR/TMP/TEMP=/private/tmp。

`import-audit.json` 给出完整 23 项及导入链；`import-grep.txt` 是补充 grep 原件；`COMPARISON.md` 的每项链接指向当次完整入口命令、同目录原始 stdout/stderr 和 meta。请用新输出目录保留旧证据。

重跑一项（将文件名、baseline/candidate 和最后的唯一标签替换为需要的值）：

```sh
TMPDIR=/private/tmp TMP=/private/tmp TEMP=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-219-evidence/round2/compare.py test_daemon_recovery_e2e.py candidate rerun-01
```

重新发现导入方：

```sh
cd /Users/luckye/Documents/Code/a2a-worktrees/T-219
python3 /Users/luckye/Documents/Code/a2a-worktrees/T-219-evidence/round2/audit-imports.py
grep -R -n -E 'test_task_cards_e2e|legacy_quality_driver|legacy_review_runtime|controlled_quality_pty' workbench/tests --include='*.py' --include='*.ts' --include='*.mjs' --include='*.mts'
```

两边都失败但推进到不同位置的诊断见 `unmasked-existing-failures.json`：两个 CLI 都拒绝旧 pane_release 命令；产品源码及对应旧调用者与基线无差异。该诊断不代替完整套件通过。
