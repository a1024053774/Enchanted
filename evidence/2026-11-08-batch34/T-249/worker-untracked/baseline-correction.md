# 主控 #110：恢复基线更正

PASS（恢复结果核对）。C 的唯一父提交为 `05002a377914d52372a4cd46a08fa40229d70e1f`；`c89b8ca4739f2a4106feeda8665f4e1aa8cec688` 是任务创建基线，不是该候选的父提交。

本次没有从大差异筛选文件：直接使用准确 B→C 的完整 binary diff。在请求目录新建普通临时文件快照，以本 attempt 原基线 `3577086056eb33e4a0c3bd2d16bbc3b30862778c` 的对应文件作为起点，依次 dry-run 与应用准确 patch，两次退出 0，没有冲突；没有新 worktree、没有移动引用。

完整准确 patch 含 15 个 workbench 文件和 135 份 T-249 证据。逐文件比较：145 份与当前文件原始字节相同；另五份恰是允许改动的 gitHost.ts、GitGraphPanel.tsx、gitGraphModel.ts 与两份开发测试。执行位亦与 C 一致。当前提交相对 attempt 原基线的变更，没有落在准确 patch 与本票 worker 证据之外的路径。

原恢复记录还列过 controller/review-01.md，但该文件与 attempt 原基线本来就相同，没有形成提交改动。README 的现状与准确 patch 应用结果一致，保留 T-258/T-259 等当前后台说明；src/ 后台未修改。无需纠正产品或测试。

机器记录、完整路径清单、逐文件结果与清理状态见 corrected-baseline-verification.json。原错误 B 的操作和冲突记录保持原样，以免改写历史。此次文档更正并入后续证据交接，不另发 issue，不产生独立无工作提交，不重复构建或测试。原沙箱外窗口请求继续等待。
