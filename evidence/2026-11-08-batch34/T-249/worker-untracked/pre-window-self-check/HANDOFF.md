# T-249 沙箱外窗口运行交接

INCOMPLETE：worker 已完成限定修复及本地检查；以下窗口运行由主控执行，尚未运行。

在本 worktree **外层的主控 cwd** 执行（脚本会为被测子进程指定正确 cwd，所有夹具全新）：

```sh
/usr/bin/python3 '/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-249-1-a6/evidence/2026-11-08-batch34/T-249/worker-untracked/run_windows.py' --output '/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-249-1-a6/evidence/2026-11-08-batch34/T-249/worker-untracked/external-01'
```

运行前可在相同命令中加入 `--preflight`。它只读打印 ROOT、模块目录、模块是否已有及清理归属、输出目录是否全新，不创建目录、不复制依赖、不启动进程。已在 worker 外层 cwd 实跑，准确 ROOT 为本任务 `T-249-1-a6`；当前模块目录不存在，external-01 未创建。`parents[5]` 变异在任何目录操作前被 ROOT 断言拒绝。见 driver-preflight-01.json；正例退出 0，变异退出 1。

ROOT 定位在先前提交中已是 `parents[4]`；本次另加执行前检查，要求任务 worktree 的 `.git` 文件和产品入口存在。已有模块目录由原所有者管理，本脚本不清理；依赖路径若是符号链接直接拒绝，避免接管链接目标。只有本次复制的目录才在确认清理安全后删除。

脚本一次依次运行：旧 C app + 当前已集成后台（必须命中未跟踪内容断言）、完整候选、no-untracked、no-resize、no-reset、deferred-candidate、stale-diff，以及原 no-panel/no-details/no-diff/parents/order。实际完整 argv 记入每项 `run.json` 与顶层 `summary.json`。每项首个异常即保留结果并停止，不自动重复构建；输出目录必须新建，旧失败结果不覆盖。

每项仍走真实 Electron 和本仓库后台的隔离 state/私有 hc，不启动模型 CLI。`deferred-*` 在测试副本里把真实 Git 读取后的返回挂起，再通过可见控件关闭或改选，最后释放原结果；它是指定事件顺序的探针，不能混称未插桩候选。完整 candidate 项不带插桩。

列宽由 `Input.dispatchMouseEvent` 走浏览器输入通道，测量表头与首行日期列的实际前后宽度，双击后与原宽度比较；结果保存 `column_geometry`。no-resize 和 no-reset 必须分别命中拖动、双击的几何断言。它不替代后续 Terra Computer Use。

只在需要时真复制既有 `workbench/node_modules`；所有新夹具与构建槽在本次 mkdtemp 下。清理前记录目录、时间、文件数、字节数和状态。进程清理未证实时保留夹具，不据此判红；已确认清理时移除自有依赖副本、截图和临时构建，仅留文本。脚本不打包、不替换正式应用、不操作现有 Test 窗口。

请将完成的 summary 路径与首个异常（如有）通过本 attempt 回执交回。worker 收到结果后补齐自查及最终提交，显式 submit 一次。主控随后负责限定独立审查、标准 Test 打包、新 Terra 验收、门禁集成与安装。

项目地图当前报告 REVIEW.md stale：原因是恢复 C 的 RUN-OUTSIDE-T249.sh，而非本次扩写脚本。该文件已逐字节等于 C，冻结 REVIEW.md 和地图未修改；主控在有权限的治理范围处理核对状态。
