# T-271 结果：任务条不横向滚动，全部任务在条首下拉框

状态：PASS

- `python3 workbench/tests/test_t261_task_strip_e2e.py --summary <新路径>` → `green-01.json`：12 个任务时条上是最近 3 个、下拉框按创建顺序最新在前列出全部；选最旧任务后它在条首并标为当前；任务条压到 360px 无横向滚动、下拉框完整可见；刷新后顺序不变。
- 红态：`--mutant by-id` → `red-mutant-by-id.json`，`newest_first_visible` 失败（条上是 T-01、T-02、T-03）。
- 测试截图留在本机临时目录，不入仓库。
