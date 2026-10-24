# 第三次运行与 CDP 返回值修正

RED / INCOMPLETE。`red03-20261024T034323Z.json` 已走通 Stop 交付、门禁启动审查员、隔离 Electron 构建和界面操作。revision_export_matches 全部为 true，构建 source 指向该版本隔离源码。

F02 已复现：审查员和历史 worker 均为只读、无输入凭据，却因 focus-observation 显示输入错误横幅，且被请求了终端焦点。F07 已复现：隐藏侧栏、重命名后，已确认执行主控的窗格头仍只有普通终端标签。上述六条缺陷断言为 false，相关截图、summary、log 保留。

随后等待真实输入错误的表达式返回了 alert DOM 节点。CDP 使用 returnByValue，无法序列化该对象，报 Object reference chain is too long。这是测试表达式错误，不是输入提示断言失败；该项和末尾的零模型请求检查尚未完成。

本次只将该等待表达式的 querySelector 结果显式转成 Boolean。核对其余等待表达式均最终返回原始值：ready 返回 paneKey 字符串，其余为布尔值。缺陷与输入错误断言均不变，产品文件不变。

重跑 `RUN-OUTSIDE-04.sh`，仍只运行 `--revision 3c56f743f`。脚本额外核对六条已知缺陷断言失败、无 error/cleanup_errors，且真实输入错误正例与零模型请求检查通过，才输出 RED / PASS。测试本身保留 exit=1 和 INCOMPLETE，因为修前产品不满足验收；不会把产品状态改写为 PASS。
