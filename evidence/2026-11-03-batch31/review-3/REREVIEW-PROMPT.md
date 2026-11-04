你是只读复审员。不改任何文件，不运行会启动后台、Electron 或 CLI 的测试；只读代码与证据，可运行只读命令（git diff、grep、cat、python3 -m py_compile）。

仓库 /Users/luckye/Documents/Code/a2a，工作区改动相对 HEAD 20f1d8581。上一轮审查报告：evidence/2026-11-03-batch31/review-3/REPORT.md（NO_GO，3 条阻塞、若干非阻塞）。只复审针对这些意见的修复，范围限于：

1. 阻塞 1、2（T-243）：workbench/tests/electron_client.py 的 `capture_and_stop`，workbench/tests/test_electron_e2e.py 与 workbench/tests/test_t078_input_entry.py 的清理段；证据 evidence/2026-11-03-batch31/T-243/forced-capture-fails-red、forced-capture-fails-green、forced-sample-fails-green，以及 T-243/RESULTS.md 末节。核对：窗口步骤（close、记现场、sample）任一失败后，停后台与停 core 是否都仍会尝试；残留是否如实报出。
2. 阻塞 3（T-242）：workbench/src/panes.ts 的 `foregroundPid`、`hookTurn` 与 `status` 里 `hook_turn` 的判断，workbench/tests/test_t242_shell_hook_turn_e2e.py 的变异体；证据 T-242/hook-turn-green-2.json、hook-turn-mutant-keep-turn-2.json 与 RESULTS.md 的“第三轮审查”节。核对：是否还有让别的进程的状态显示在当前前台上的路径，或让当前前台的状态一直不显示的路径。
3. 非阻塞（T-244）：workbench/src/hcDistribution.mjs 的 rename 失败处理与 T-244/partial-install-*.json；以及 RESULTS 与票（.project-map/tickets/T-242～T-245）里有没有仍高于证据的说法。

每条写成缺陷声明（文件:行、具体失败场景、依据），分 阻塞 / 非阻塞。最后给总结论 PASS 或 NO_GO。中文，输出到标准输出。
