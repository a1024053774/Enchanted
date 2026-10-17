# T-089：S3 起点绿态被历史坐标审计阻塞

状态：BLOCKED（仅 S3 抽取；其他独立检查继续）。

在起点 c544b29049861998e11eeb7344b457103fab3c98 的一次性 checkout，运行未改的 `run_s3_regression.main()` CAS 套件，退出 1：`Assertion edit exceeds the approved whitelist`。尚未执行业务测试。失败现场和完整命令见 `s3-baseline-local-01/check.json` 与其中的 checkout；该目录保留。

根因位于 `workbench/tests/run_s3_regression.py:113`：它调用旧版 `audit_s3_assertions.audit_checkout`，使用 pre-T-076 的坐标；现有 `workbench/tests/run_s3_rebased_regression.py` 开头已说明这一问题。本任务禁止修改验收条件或审计器，因此未绕过，也未开始修改 S3 文件。

最小选项：主控允许组合基线（现有 rebased CAS runner + 原 archive_large_files 函数边界的抽取前后同命令对照），或先由主控处理原入口基线。本 worker 不自行改验收口径。

另外：稀疏 worktree 的 project_map status 报 README 和旧 .grilling 文件缺失，共 3 problems；完整主仓库同命令为 0 problems、0 stale。它们不在本次修改边界，未补写。

## 主控裁定（2026-10-17）

主控 #2 同意使用现有 rebased CAS runner 加原归档函数边界的组合基线，抽取前后运行相同检查；原入口的既有失败不在本票修复，也不写成绿态。裁定原话和外置盘验证来源见 `controller-decision-01.md`。本条解除的是组合证据的等待，原入口失败事实与上述现场仍保留。
