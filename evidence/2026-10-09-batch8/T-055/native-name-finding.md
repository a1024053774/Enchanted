# 范围外发现：原生提示文本中的数字工具名

状态：待执行主控判断；非阻塞当前 T-055 的 Codex 0.162.0 实测路径。未关闭、未修改解析器。

受控原生协议帧省略 `_meta.tool_name`、只提供完整生成提示 `Allow the synara MCP server to run tool "a2a_raise"?` 时，`codexAppServerManager.ts:4990` 的 `[a-z_]+` 不接受数字，工具名返回 undefined。full-access、活跃 turn、有效 lease 也会保留批准提示。相同帧中的既有 `a2a_submit` 同样失败；该解析器相对父修订无变化。

本次真实 Codex 0.162.0 full-access worker 已无人批准上报成功，因此不能把这个受控格式探针冒称为当前真实 CLI 失败。它不属于本票获批的“只改网关工具名目录”，没有改其他上游文件或权限策略。

证据：`permission-native-shape-01.log`、`permission-native-shape-source.ts.txt`、`native-shape-same-policy.json`、`native-shape-same-policy-01.log`。13 项探针中仅此格式失败，其他 12 项通过；完整失败测试源码保留为证据，正式目录测试保留本票的 12 项权限契约。不是删除失败证据，也不把该探针写成通过。

请执行主控判断是否另开修复票；如修改解析器会改变哪些现有工具的免确认范围，须按权限边界取得授权。worker 不在 T-055 内扩大这项修改。
