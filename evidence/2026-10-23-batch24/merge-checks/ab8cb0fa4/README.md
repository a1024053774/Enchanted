# 合并后检查：ab8cb0fa4（T-161 合并）

执行主控在 `/Users/luckye/Documents/Code/a2a-merge-check` 检出 ab8cb0fa4，`node workbench/app/build.mjs --slot merge-check-t161` 构建通过，然后运行（0 个真实模型回合）：

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| T-161 | `python3 -B workbench/tests/test_t161_readonly_role_e2e.py --summary t161.json` | PASS |
| T-159 分屏 | `python3 -B workbench/tests/test_t159_split_e2e.py --summary t159.json` | PASS |
| T-157 恢复 | `python3 -B workbench/tests/test_t157_stale_turn_e2e.py --scenario recover --summary t157-recover.json` | PASS |

未在此处重跑 `test_t157_stop_input_e2e.py`：它在合并前的 main 上已因时序缺陷失败，由 T-165 跟进。
