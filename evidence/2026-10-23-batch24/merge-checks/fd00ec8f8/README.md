# 合并后核对 fd00ec8f8（T-158/T-160/T-162/T-163/T-159 已合入）

在 /Users/luckye/Documents/Code/a2a-merge-check 检出 fd00ec8f8 后运行，全部退出 0：

```zsh
node workbench/app/build.mjs --slot merge-check-t159
python3 workbench/tests/test_t159_split_e2e.py --summary t159.json
python3 workbench/tests/test_t160_review_recovery_e2e.py --summary t160.json
python3 workbench/tests/test_t162_role_records_metrics_e2e.py --summary t162.json
```

另在 main 上运行 test_t158_revise_retry_e2e.py --check instructions：PASS（c444fc82e 合并后）。完整波次回归在 T-157/T-161 合入后进行。
