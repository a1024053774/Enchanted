# T-262 打包窗口核对

状态：INCOMPLETE（原生下拉菜单选择尚未得到证明）。

候选 6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5，经标准 package.mjs 打包为 Enchanted Test，独立 /private/tmp/t262-vi9oamr5 状态；未修改正式数据库。fixture-manifest.json、package-command.json、package-result.json 和 launch_fixture.py 可重建该环境。source-binding.json 逐字节确认三个已测试文件等于候选。

Computer Use 看到 alpha 的用户输入 7 条、门禁回执 5 条、人工介入 3 条；两个区按时间倒序，两个同名主控显示不同 launch 后缀。Tab 在任务、会话、刷新和原文详情之间移动，Enter 真实收起详情。AX 文本保存在 all-records-ax.txt 和 native-keyboard-ax.txt，窗口截图 records-window.png 本地保留。

限制：点击任务/会话 select、Space、Down/Return、alt+Down 均未观察到选择变化；Tab/Enter 对其他控件有效。没有将此次结果写成键盘选择 PASS，也没有把此前程序化 selectOption 等价路径改称原生输入。尝试 Raise 未改变结果；Dock 观察超时，工具未提供 launch_app 方法。该现象尚不能区分工具的原生菜单限制与产品缺陷，独立审查应核对 select 逻辑，并在最终接收前补足实际选择证据。完整业务过滤的 38 项绿态及 4 个已知坏实现证据见 ../controller/behavior-results-08.json。

Works：真实包显示分类、排序、明确的会话身份；已有真实后台/Electron 的过滤、原文与异常状态行为证据。
No regression：38 项正例和四个破坏版本的对应失败均已保存；不是完整仓库全套测试。
Risk / undo：原生选择器这一项仍未决；当前未集成该候选，正式包未更换。
