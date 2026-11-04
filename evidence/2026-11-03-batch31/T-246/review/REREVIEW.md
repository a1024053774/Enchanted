## 阻塞

1. **PID 复用后晚到的旧报告仍可冒充新进程的报告。**  
   [byProcess.ts:19](/Users/luckye/Documents/Code/a2a/workbench/src/byProcess.ts:19)、[byProcess.ts:24](/Users/luckye/Documents/Code/a2a/workbench/src/byProcess.ts:24)：A 的钩子已经取得 A 的 PID，但请求尚未送达；A 退出，B 复用该 PID 并成为前台；随后 A 的报告到达。记录的是**到达时间**，因此 `at >= B.started` 成立，A 的会话会被显示为 B 的；即使 B 已报告，A 的晚到报告也会覆盖它。重启重建同样使用事件到达时间，不能消除这条路径。票面时序是否容易在真实环境发生尚无复现，但现有代码不能保证“报告只属于报告它的进程”。**未运行复现**。

   上一轮较窄的反例——A 的报告先到、A 退出、B 复用 PID、再读取前台——现在被启动时间过滤。运行 `node workbench/tests/test_by_process.ts`：**PASS**，1,111,111 个长度 0～6 的序列；已有 `ignore-start-time` 变异记录对此反例报错。但[test_by_process.ts:11](/Users/luckye/Documents/Code/a2a/workbench/tests/test_by_process.ts:11)明确排除了复用后旧钩子到达，绿态不能证明上述路径安全。

2. **`pane_status.native_session` 的滞后没有得到无条件的时间界限。**  
   [panes.ts:601](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:601)：正常情况下，提交一行后安排 1.5 秒检查，识别到 CLI 后每 5 秒复查一次，因此 CLI 自己退出、没有再输入一行时，已有复查循环通常会清掉缓存。但复查开始时先清除 `wiringCheckAt`；若进程查询或随后读取 argv 失败，`catch` 只记录错误，不重新安排复查，也不清除 `pane.native`。事件顺序：CLI 已报告 → 复查恰逢退出导致查询失败 → 无后续输入或 OSC 报告 → [status](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2034)可以持续返回旧会话。**未运行复现**。

   [nested-green-2.json](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-246/nested-green-2.json)只证明该次输入 `/exit` 后 2.06 秒清除；[测试](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t246_nested_cli_native_e2e.py:152)的退出输入本身重新安排了复查，断言上限也是输入后 10 秒，并未验证无输入自行退出或查询失败。因此“有界滞后”只能作为成功复查条件下的描述，不能作为普遍保证。

3. **同一毫秒内的有效报告可能被误判为旧报告。**  
   [panes.ts:488](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:488)保留了进程启动时间的小数毫秒；[byProcess.ts:19](/Users/luckye/Documents/Code/a2a/workbench/src/byProcess.ts:19)的 `Date.now()` 则取整到毫秒。若进程在某毫秒内启动并在该毫秒内报告，尽管报告实际晚于启动，其整数 `at` 仍可能小于带小数的 `started`，被 [prune](/Users/luckye/Documents/Code/a2a/workbench/src/byProcess.ts:28)删除。穷举模型每个事件递增整数时钟，未覆盖精度差异。**未运行复现**。

## 非阻塞

- **穷举测试对过时前台读数的允许范围偏宽。** [test_by_process.ts:63](/Users/luckye/Documents/Code/a2a/workbench/tests/test_by_process.ts:63)允许显示该 PID 从上次前台读数以来任一持有者的最后状态，包含既不是上次观察到的进程、也不是当前持有者的中间实例；状态值只有 `running`/`idle`，不同实例的同值也无法区分。它能检查“不显示其他 PID”，不能独立证明过时窗口内的实例归属。

- **`started` 缺失时会隐藏报告，但不清除它。** [panes.ts:483](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:483)仅做类型断言；缺失时乘法得到 `NaN`，`shown()` 的比较为假，而修剪比较也为假。当前 [processSnapshot.py:84](/Users/luckye/Documents/Code/a2a/workbench/src/processSnapshot.py:84)中缺少启动时间的特权行的 `tpgid` 为 `-1`，正常不会选为前台；但 [processInfo 的行校验](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1421)没有验证该字段。**未运行复现**。

- **`rememberOpen` 的旧布局回退在活动 shell 上已移除。** [panes.ts:825](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:825)对活动 shell 使用 `pane.native`，不再因其为 `null` 回退旧布局；它仍可能记录上面所述的过期缓存。若 `pane` 不存在而 `previous` 存在，仍会回退，是否构成问题取决于该恢复场景的预期；本轮未运行复现。

- **重启后的状态断言存在，但不是独立的首次读取。** [测试:142](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t246_nested_cli_native_e2e.py:142)先调用 `link()`，它刷新前台，然后才断言 `after_restart_native_is_outer`。该证据证明刷新后的状态，不证明重启后直接读 `pane_status` 的结果。

- **变异证据的范围清楚，但不能替代上述反例。** 两个 nested 变异补丁分别模拟取最后报告和重启只恢复最后一条；已有结果分别在内层运行及重启后失败。T-242 的 `keep-turn` 补丁串已指向新模块，已有结果在第二个 Claude 首次提交前检测到旧状态。它们均未覆盖复用后晚到、查询失败或时间精度差异。本轮按要求没有重跑这些会启动进程的端到端测试；终端主控身份场景也未重跑。

**NO_GO**：正常路径和部分反事实有证据，但 PID 复用后的晚到报告仍可跨进程归属，且缓存清除的时间界限在查询失败时不成立。
