# T-262 记录页导航测试修订

INCOMPLETE：已补齐真实导航旅程与页面诊断，待主控运行 `green-outside-04.json`。本轮只修改测试及 worker 证据，未修改产品。

**Works**：主控 `green-outside-03.json` 已通过前 26 项检查，包含真实 900×700 窗口、长内容不溢出、details 键盘收起与焦点、刷新哨兵。随后等待 beta 输入 `i-b` 超时，原始状态为 FAIL；core 已停止，夹具已删除。原摘要原样保留为 `controller-green-outside-03.json`，没有将该轮改称 PASS。
**No regression**：`static-navigation-07.json` 证明原始数据、四个 mutant、业务断言、超时和后续流程不变，延迟 alpha 响应仍在 beta 记录出现后才释放。旧 Fixture 方法除诊断采集外不变；产品文件、共享启动器、renderer、README 和地图未改。本轮没有启动测试窗口、后台、模型、ps 或构建。
**Risk / undo**：修订后仍需真实页面运行。原 03 证据没有保存失败时的 DOM 页面状态，不能把“当时显示终端”写成已读回的事实；源码与缺失操作已明确，下一轮新增读回用于实证。修订前脚本为 `test-before-navigation-07.py`，可对照撤回本轮测试修改；保留原失败及诊断证据。

## 导航入口与修改

`renderer.tsx:826` 的 `navigate()` 在切换成功后调用 `applySelection(value)` 和 `setPage('terminal')`；`selectProject()` 也走这一入口，同一项目的快速路径同样切回终端。项目/独立终端按钮使用 `aria-current="page"` 标识选择；标题来自项目目录名或“独立终端”。本夹具项目目录明确为 alpha、beta、empty，因此这些标题是独立场景输入。

旧脚本点击 beta 后直接等记录，没有重进“记录”。同样的遗漏位于切回 alpha、切 empty 和切独立终端；初次 alpha 则紧接着点“记录”，没有等待项目导航完成，可能被导航完成后的 `setPage('terminal')` 覆盖。

本轮新增一个被五个入口共同使用的 `open_records(project)`：

1. 等目标侧栏按钮启用，再通过原有真实鼠标驱动点击。
2. 等目标按钮被选中、导航不再禁用按钮、标题为预期项目/独立终端。
3. 保存 `project_ready` 的真实页面快照，再点击“记录”标签。
4. 确认项目身份和标题仍正确、记录标签为当前页、RecordsPage 已挂载，保存 `records_ready` 快照。
5. 返回原场景，使用原来的记录身份/数量条件等待数据，再运行原业务断言。

没有改 renderer，没有增加页面切换重试、延长超时或修改期望数据。Ubiquitous language 继续使用项目、任务、会话、用户输入、门禁回执。Deep modules：一个入口封装完整的选择与进入记录旅程，供五处真实使用，不建立平行筛选逻辑。

## 迟到响应与诊断

真实 alpha 读取仍由隔离代理截住，beta 的项目身份、记录页面和 `i-b` 都就绪，并完成原 beta 行断言后，才释放 alpha 响应；释放后仍执行原来的 beta 内容不被覆盖检查。失败路径的 finally 释放仅用于收尾，不能算该场景已通过。切回 alpha、empty、独立终端也使用相同旅程。

页面快照只读真实 DOM，包含当前标题、侧栏项目 ID、独立终端选中状态、导航忙状态、当前页面、RecordsPage 是否挂载、终端是否可见、读取状态、筛选值、记录数量与最多 12 个 ID，以及最多 4 条各 500 字的错误。既不注入页面状态，也不复制长原文或完整回执。

每次导航的两次读回写入 `navigation`；清理前再将页面读回写入 `diagnostics.before_cleanup.page`。若 Electron/CDP 本身不可读，将错误显式写入 `page_capture_error`，保留原失败并继续清理。由此可区分“停在终端”“已到记录但仍加载”“选错项目”“记录读取报错”。

## 异常边界核对

按仓库对 design-integrity-review 的自查规则核对本次诊断边界和 Stop hook 标出的历史快照：

- `test-before-window-06.py` 是修正前证据快照，不是当前默认执行入口，不删除或改写其中的异常处理来消除扫描命中。
- 测试 `main()` 的 `except Exception` 是运行器的失败分类边界：真实 `green-outside-02` 中不存在的 Browser CDP 命令到达该边界，记录错误、置 INCOMPLETE，最终非零退出；不是吞错后成功。
- `except BusinessFailure` 是同一运行器的业务等待/断言分类边界：真实 `green-outside-03` 的 beta 等待到达该边界，记录 FAIL 并非零退出。此次保留原结果，修复的是前置导航步骤。
- `until()` 由启动、导航和记录等待实际调用；它在只读 CDP 轮询中捕获 RuntimeError/AssertionError，保留最后错误，受原期限限制，最终仍抛 RuntimeError。该层拥有等待页面/CDP 就绪的责任，未增加期限、回退或忽略失败的路径。现有 03 摘要没有记载此分支的逐次异常，不声称本轮实跑了该分支。
- 新增的诊断捕获只包住页面快照读取。CDP 不可读时记录具体异常，不覆盖主失败、不伪造页面、不跳过清理；它属于运行器的取证职责。本轮只做静态核对，真实诊断结果留待外部运行。

结论：这些处理具有明确调用路径和运行器职责，保留；没有因为 locator 命中删除处理。此核对不替代主控的独立验收审查。

## 下一步命令与边界

静态复核命令为 `python3 evidence/2026-11-08-batch34/T-262/worker/check-navigation-07.py`，结果已保存；这是 AST 与语法检查，未启动真实应用。

主控外部运行命令为 `controller-runs-07.command`。下一轮候选使用 `green-outside-04.json`，全绿后运行四个既有 mutant；父版 `red-outside-05` 继续作为有效排序/筛选红态，不重复构建。失败时保留原状态、精简页面诊断、退出码和清理事实，不以驱动失败冒充产品缺陷或变异检出。

README 已由主控接手；旧 base 的 stale 不改变 worker 写入边界。正式 Enchanted 和 T-249 Test 未操作。受管身份仍为 attempt `64d48cf7-0cfc-4078-8a13-6f0067297990`、fence 2、spec_rev 2。未提交、未 submit；额外可写目录 []，无额外目录改动。完整绿态、变异、原生 select 键盘 CU 和独立审查后，继续完成本次身份下的提交与显式交付。

本轮集中交接 issue 请求为 `75b5d449-8b64-4ae5-a2a1-c8062cf05c9f`，返回 `queued=true, delivered=false`；排队不等于受理。原回显见 `issue-queued-07.txt`，请求文件留在本 attempt 请求目录，不进 Git。
