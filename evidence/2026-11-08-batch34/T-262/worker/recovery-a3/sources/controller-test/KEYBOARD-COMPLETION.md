# T-262 原生键盘验收补齐

状态：PASS（本次窗口行为检查）。候选仍为 6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5，没有改代码、包或夹具。

前次 CUA-RESULTS.md 的下拉展开方式未得到结果，完整保留。随后仅通过 Computer Use 原生 pressKey 操作当前已聚焦的 HTML select：输入 t、minus、1、Return，任务成为 T-1，两个区变为输入 4 / 回执 3；Tab 到会话，输入 w、Return，worker-one 会话成为输入 3 / 回执 3；Shift-Tab 回任务，输入 t、minus、3、Return，任务成为 T-3，输入 0 / 回执 1，会话重置为全部。四次 Tab 到完整回执后 Return 展开原始 JSON，包含 r-only 和特殊长文本。没有执行脚本设置 value、dispatchEvent、React 状态或模拟 API。

逐步 AX 原文：keyboard-task-t1.txt、keyboard-session-worker-one.txt、keyboard-task-t3.txt、keyboard-full-receipt.txt；本地截图 keyboard-receipt-window.png。菜单点击/方向键展开的操作仍不能由这组证据证明；任务卡要求的键盘筛选与详情访问已通过原生字符选择 + Tab/Enter 证明。两种路径明确区分。

结束时 super+q 关闭该隔离 Test GUI，cua.listApps 确认仅正式 Enchanted 保持运行。后台与专属测试数据随后按所有权清理。

Works：真实包经原生键盘完成任务/会话的联合过滤、空分类提示、完整回执展开。
No regression：沿用同一候选此前 38 项行为绿态与四个已知坏实现判红，源码逐字节绑定见 source-binding.json。
Risk / undo：实际下拉菜单展开未证实；本次不将其判断为产品故障。仍等待独立审查和门禁集成，正式包未改变。
