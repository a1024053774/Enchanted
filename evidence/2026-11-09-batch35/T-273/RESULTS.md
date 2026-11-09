# T-273 结果：指标页与 Reflect 页在数据多时易读

状态：INCOMPLETE

- 正式数据（52 个会话、11 行按模型、Reflect 54 个节点）经后台只读命令 `metrics`、`reflect_tree` 取出，灌进本机临时页面壳（stub `window.a2a`，同一份 MetricsPage/ReflectPage 源码），在 1100×800 视口逐页核对：指标页首屏是四块总数（会话 52、已记录回合 98、一次到位率 60%、打回 4）与章节跳转，会话按任务分组、只展开最新一组；Reflect 开头一行状态计数，最新的执行主控在上，任务分组收起并显示会话数、进行中数与最近时间。截图不入仓库。
- 端到端回归未取得：`test_t137_reflect_e2e.py`、`test_t133_t134_records_metrics_e2e.py` 在本次改动与改动前的 HEAD 上都报 `plan: StopIteration`（脚本模型的计划用尽），`test_t162_role_records_metrics_e2e.py` 在两个版本上都报“超时：记录页读取结束”（`stale-tests.json`）。这些失败与本次改动无关，但三条测试因此不能作为本票的不回归证据。
- 下一步：T-274 修这三条过期测试，再用它们复验本票。
