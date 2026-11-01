# T-221 重跑命令索引

从 T-221 worktree 运行；每条 replay 会创建新的输出路径，不覆盖旧证据。原始 cwd、argv、TZ、TMPDIR、起止时刻与退出码见同名 `.command.json`。

红态通过 `extracted-codexScanDays.ts` 恢复修前计算到隔离源码副本，执行同一份产品测试。变异包装退出 0 只表示已确认子测试按业务断言退出 1；原始子测试 JSON 保留 INCOMPLETE。

## diagnostic-t136

- 原始退出码：`0`。日志：`diagnostic-t136.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py diagnostic-t136`。

## final-diff-check-doc-synced

- 原始退出码：`0`。日志：`final-diff-check-doc-synced.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py final-diff-check-doc-synced`。

## final-diff-check

- 原始退出码：`0`。日志：`final-diff-check.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py final-diff-check`。

## final-fixture-inspection

- 原始退出码：`0`。日志：`final-fixture-inspection.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py final-fixture-inspection`。

## final-project-map-doc-synced

- 原始退出码：`0`。日志：`final-project-map-doc-synced.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py final-project-map-doc-synced`。

## final-project-map

- 原始退出码：`1`。日志：`final-project-map.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py final-project-map`。

## final-scan

- 原始退出码：`0`。日志：`final-scan.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py final-scan`。

## green-days

- 原始退出码：`0`。日志：`green-days.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py green-days`。

## mutant-drop-previous

- 原始退出码：`0`。日志：`mutant-drop-previous.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py mutant-drop-previous`。

## mutant-miss-archive-cwd

- 原始退出码：`0`。日志：`mutant-miss-archive-cwd.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py mutant-miss-archive-cwd`。

## mutant-miss-archive-id

- 原始退出码：`0`。日志：`mutant-miss-archive-id.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py mutant-miss-archive-id`。

## mutant-miss-native

- 原始退出码：`0`。日志：`mutant-miss-native.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py mutant-miss-native`。

## mutant-miss-panes

- 原始退出码：`0`。日志：`mutant-miss-panes.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py mutant-miss-panes`。

## mutant-original-helper

- 原始退出码：`0`。日志：`mutant-original-helper.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py mutant-original-helper`。

## red-extracted

- 原始退出码：`1`。日志：`red-extracted.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py red-extracted`。

## regression-discovery

- 原始退出码：`0`。日志：`regression-discovery.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-discovery`。

## regression-t135

- 原始退出码：`0`。日志：`regression-t135.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-t135`。

## regression-t136-baseline

- 原始退出码：`1`。日志：`regression-t136-baseline.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-t136-baseline`。

## regression-t136

- 原始退出码：`1`。日志：`regression-t136.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-t136`。

## regression-t195

- 原始退出码：`0`。日志：`regression-t195.log`。
- 重跑：`TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-t195`。

## 辅助文件的对应运行

- `extraction.patch`、`extracted-codexScanDays.ts`：red-extracted 与 mutant-original-helper。
- `safe-t195-native.py`：regression-t195；只将 T-219 原件的 ROOT 指到 T-221。
- `mutate.py`：全部 mutant-*；源码副本只在 /private/tmp。
- `diagnose-t136.py`：diagnostic-t136；日期诊断不冒充产品验收。
- `inspect-evidence.py`：final-fixture-inspection；SQLite 以 immutable 只读，后台已停止。
- `candidate.patch`、`candidate.json`：绑定本次未提交候选；可在基线 d72a7746be0b737849bcd97caae05b1ac8689ece 的隔离 checkout 应用补丁后重跑。
- `REPORT-before-implementation.md`：首个产品／测试编辑之前写入的失败方式清单。
- 各日期测试 JSON 的 `root` 指向保留的真实目录夹具；回归 JSON 的 `fixture` 指向原生记录、后台日志和界面截图。未归档或清理失败现场。
