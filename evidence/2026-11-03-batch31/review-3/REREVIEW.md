**NO_GO。** T-243 的两处清理结构已修正；T-242 仍有一个未被现有证据排除的状态覆盖时序，需要先验证。

**阻塞**

1. **T-242：旧进程的延迟钩子可能覆盖当前前台进程的状态。** [panes.ts:503](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:503) 无条件用最后到达的钩子覆盖唯一的 `hookTurn`；[panes.ts:2029](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2029) 只在读取时比较 PID。具体时序：新前台进程 B 已报告状态并被识别为前台，旧进程 A 的延迟钩子随后到达，将 B 的状态覆盖；此后 PID 不匹配，B 显示未知，即使后台继续确认 B 为前台也不会恢复，直到 B 再发钩子。

   这是**只读代码推导，尚未运行复现**。[变异体测试](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t242_shell_hook_turn_e2e.py:29) 验证去掉 PID 判断后会沿用旧状态，但没有安排上述事件顺序；启动后还等待了前台检查，不能证明该交错安全。需要按“状态只属于报告它的当前前台进程，旧事件不能抹掉新进程状态”建模并验证。

**非阻塞**

- **T-243 第二调用点缺少运行证据。** [test_t078_input_entry.py:239](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t078_input_entry.py:239) 中，`close` 和现场采集的异常现在各自记录，后台停止后的 `finally` 会尝试停止 core；但该测试在夹具准备阶段失败，未运行到清理段。[RESULTS](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-243/RESULTS.md:129) 已如实说明这一限制。

T-243 的另一调用点已有针对性证据：采集整体失败时后台与 core 停止、残留 Electron 被报告；`sample` 超时时记录错误并停止进程组，结果无残留。T-244 的不完整安装反例从返回不存在路径改为抛错；并发首次安装仍只有代码判断，报告已注明，丢失的异常摘要也无法恢复。T-242 的 Codex 端到端和上述事件交错均未验证。

本次未修改文件，未启动测试、Electron、后台或 CLI；项目地图状态报告 Problems 0、Stale living docs 0。
