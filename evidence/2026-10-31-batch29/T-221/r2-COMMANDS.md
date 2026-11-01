# T-221 第二轮重跑命令

工作目录为 T-221 worktree。`run.py` 固定 TMPDIR=/private/tmp、PYTHONDONTWRITEBYTECODE=1，进程 start_new_session；旧文件不会覆盖。下列 replay 生成新的输出名。

第二轮所有原始 argv、TZ、cwd、起止时刻与退出码见对应 `.command.json`。主控已接受第一轮日期与回归证据，本轮只修测试时钟，产品第一轮改动没有再次修改。

- `r2-audit-decisions`：原退出码 `0`；日志 `r2-audit-decisions.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/r2_write_inventory.py /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay-r2-audit-decisions-01.json`。
- `r2-audit-shell`：原退出码 `1`；日志 `r2-audit-shell.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-audit-shell`。
- `r2-audit-wide`：原退出码 `0`；日志 `r2-audit-wide.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-audit-wide`。
- `r2-audit`：原退出码 `0`；日志 `r2-audit.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-audit`。
- `r2-calendar-clocks`：原退出码 `0`；日志 `r2-calendar-clocks.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-calendar-clocks`。
- `r2-final-diff-check`：原退出码 `0`；日志 `r2-final-diff-check.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-final-diff-check`。
- `r2-final-inspection`：原退出码 `0`；日志 `r2-final-inspection.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-final-inspection`。
- `r2-final-project-map`：原退出码 `0`；日志 `r2-final-project-map.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-final-project-map`。
- `r2-green-t136`：原退出码 `0`；日志 `r2-green-t136.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-green-t136`。
- `r2-green-t137`：原退出码 `0`；日志 `r2-green-t137.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-green-t137`。
- `r2-helper-callers`：原退出码 `0`；日志 `r2-helper-callers.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-helper-callers`。
- `r2-mutant-fixed-offset`：原退出码 `1`；日志 `r2-mutant-fixed-offset.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-mutant-fixed-offset`。
- `r2-product-due-audit`：原退出码 `1`；日志 `r2-product-due-audit.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-product-due-audit`。
- `r2-red-t136`：原退出码 `1`；日志 `r2-red-t136.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-red-t136`。
- `r2-red-t137`：原退出码 `1`；日志 `r2-red-t137.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-red-t137`。
- `r2-status-start`：原退出码 `0`；日志 `r2-status-start.log`；重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-status-start`。

## 红态的重跑口径

r2-red-t136 是真实 ENOSPC 基础设施失败，不是日历红态；再次运行不保证复现磁盘状态，不制造磁盘耗尽。T-136 日历红态沿用第一轮 regression-t136 与 regression-t136-baseline。
r2-red-t137 是修前固定偏移时钟的真实失败。原命令现在使用已修复时钟，因此正常应转绿；要恢复同一测试中的旧时钟，使用下列包装（产品与断言不变，需仍处在相应跨 DST 日期条件）：

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/run.py replay-r2-legacy-t136-01 python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/r2_legacy_e2e.py 136 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay-r2-legacy-t136-01.json
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/run.py replay-r2-legacy-t137-01 python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/r2_legacy_e2e.py 137 --summary /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay-r2-legacy-t137-01.json
```

上面的 legacy E2E 包装本轮为重放保留，未另启动两轮大夹具；真实旧时钟红态来自已有三份实际运行。全年确定性反事实是 r2-mutant-fixed-offset：它对相同六组硬编码日历 oracle 运行旧时钟，四组 DST 断言失败，退出 1。

## 其他文件

- `r2-audit-decisions.md/.json`：逐行判定，由 r2_write_inventory.py 生成；重跑需使用未存在的新输出路径。
- `r2-date-broad-search.log`：早期直接 rg 的额外搜索输出，与 r2-audit-wide 的搜索模式相同。
- `r2-candidate.patch/.json`：第二轮完整未提交候选，基线 d72a7746be0b737849bcd97caae05b1ac8689ece；第一轮 candidate.patch/.json 原样保留。
- `round1-report-preserved.md`：本轮开始时保存的首轮报告；最终报告以其完整字节为前缀，只追加第二轮。
- `round2-ticket-readonly.md`：按主控要求只读取得的主 checkout 更新票面；worktree 的 .project-map 未改。
- `round2-plan.md`：改测试之前记录的失败方式与边界。
- `r2_probe_due.ts`：对产品真实 due() 的审计探针；输出存 r2-product-due-audit.log，第三个用例是待主控决定的产品缺陷。
- `r2_inspect.py`：核对第二轮四个真实回归夹具无活进程、两个完整绿态的检查数量、UTF-8、地图不变和首轮报告前缀。
