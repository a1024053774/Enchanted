# T-212 第六轮：主控复跑（2026-10-31）

候选：基线 `4cb88bba7` 加 worker 的 `candidate-round6-final.patch`，树 `31b9dde51`，与 worktree 当前内容相同。脚本 `run-ctl-r6.sh`，汇总 `r6-runs.log`。

| 入口 | 结果 | 原始输出里的关键值 |
| --- | --- | --- |
| `r6-mismatched-01` | PASS，7 项 | 强制 hc 193×120（重启前实际 200×120，Electron 拟合后 159×49）；pid 18808、shell_pid 18805 存活；hc 与 xterm 各 460 行，missing、extra 为空 |
| `r6-screen-01` | PASS，7 项 | pid 19008；466 行一致 |
| `r6-burst-01` | PASS，8 项 | 24 次布局变化、24 种尺寸，只新增 1 次 reset（预算 3）；最终 hc 与 xterm 都是 149×19；继续输出后 488 行一致 |
| `r6-trace-resize-01` | PASS，6 项 | 坏窗格明确拒绝不挂起、记为 trace 失败；另一个终端未失败且仍可用；后续请求明确拒绝；core socket 仍在 |
| `r6-trace-initial-01` | PASS，5 项 | 初次 attach 的 trace 失败同样明确拒绝，不影响另一个终端 |
| `r6-mutant-no-catch-01` | 预期失败，4/6 项不过 | paint 处理不再捕获写入错误（`r6-mutant-no-catch.diff`）：请求返回 `orchestration_failed`（EACCES），另一个终端也变成 `pane_unavailable`。没有挂住，是因为 `hc.ts` 的修正先 reject 了这次调用；整条连接仍被断开。两处修正各自起作用 |
| `r6-mutant-no-check-01` | 预期失败，1/6 项不过 | resize 后不再检查窗格失败（`r6-mutant-no-check.diff`）：坏窗格的 resize 返回 `{'ok': True, 'output_offset': 0}`，即带旧偏移的成功，正是失败方式第 3 条 |

两个变异的失败现场保留在 `/private/tmp/t212-trace-wu5_hzce`、`/private/tmp/t212-trace-xawsfevg`；变异用的临时源码副本已删，改动见对应 `.diff`。

worker 报告第六轮的数值（mismatched 490、466 行，screen 487、535 行，burst 531、506 行）来自它自己的运行，与主控这次的行数不同属正常：每次运行输出量不同，比较的是同一次运行里 hc 与 xterm 是否逐行一致。
