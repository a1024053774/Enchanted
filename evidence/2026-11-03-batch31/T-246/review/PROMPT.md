你是只读审查员。不改任何文件，不运行会启动后台、Electron 或 CLI 的测试；可以读代码与证据，运行只读命令（git diff、grep、cat）以及 `node workbench/tests/test_by_process.ts`（纯内存穷举，不起进程）。

仓库 /Users/luckye/Documents/Code/a2a，审查对象是工作区相对 HEAD 的改动，范围限 T-246：
- 票：.project-map/tickets/T-246-shell-native-report-late-hook.md
- 代码：workbench/src/byProcess.ts（由 shellTurns.ts 改名泛化）、workbench/src/panes.ts 中 nativeReports / shellTurns / noteNativeReport / noteShellForeground / noteShellHook / shellNative / watchWiring / 构造时的重建 / status 的 hook_turn；workbench/README.md 深度链接一节
- 测试：workbench/tests/test_t246_nested_cli_native_e2e.py、workbench/tests/test_by_process.ts、workbench/tests/test_t242_shell_hook_turn_e2e.py 的变异体串
- 证据：evidence/2026-11-03-batch31/T-246/（RESULTS.md 与各 json/log）

要核对的不变式：普通终端里，深度链接与后台给终端的 native_session 只取当前前台 CLI 进程自己报的会话；其他进程（已退出的、前台 CLI 里再跑的）的报告既不显示在前台上，也不顶替前台的；后台重启后能按记录重建；已退出进程的报告不累积。另核对：pane.native 语义改变（无前台报告时为 null）是否有调用方依赖旧语义（普通终端 role=shell 的 pane.native、pane_status.native_session、pane_layout_opened、终端主控 T-121/T-133 的身份核对等）；RESULTS 是否有高于证据的说法；红态、绿态、变异体是否真的打到所声称的检查。

每条写成缺陷声明：文件:行、具体失败场景（输入或事件顺序）、依据；能用实际运行的反例（如穷举测试、git show）证明的附命令与结果，只读推导的写明“未运行复现”。分 阻塞 / 非阻塞。最后给总结论 PASS 或 NO_GO。中文，输出到标准输出。
