# T-262 候选与外部运行交接

INCOMPLETE：候选标准构建通过，完整行为验证待主控运行。

**Works**：主控 `red-outside-03.json` 已通过真实 Electron/后台复现排序缺陷，原件的副本为 `controller-red-outside-03.json`。候选统一了双区索引、过滤与倒序；隔离标准构建通过，见 `build-01.json`。
**No regression**：Python 语法、CLI 参数入口和 diff 空白检查通过。旧 T-133/T-179 脚本依赖 Claude，未启动；它们要求的人工介入、原文与完整回执行为已纳入新无模型场景，尚待实跑。没有改后台、API、schema、依赖或其他页面。
**Risk / undo**：键盘驱动修正和新增传输故障场景尚未经真实 Electron 验证。未提交、未 submit，不能把构建通过当作页面验收通过。

## 红态解释

主控外部运行的排序断言有效失败：alpha 输入实际为 i-old、i-z、i-ctrl2、i-a、i-ctrl1、i-two、i-loose，明显不按原始时间倒序；回执相同时间的 r-z/r-a 也未按选定的稳定身份顺序排列。后续选择 alpha+T-1 超时保留在原报告中，但尚无证据证明是产品筛选缺陷；旧版确有这个选项。

## 页面实现

Ubiquitous language 使用用户输入、门禁回执、任务、会话。Deep modules：页内一个记录索引同时供应任务、会话选项和两类可见行，删除独立的 Receipts 加载/筛选路径。两路读取一起发布；前次请求未完成时不再发轮询；刷新、切换或卸载使旧结果失效。

两个记录区都按原始时间倒序，同时间按原始记录 id/key 排列。输入与回执按已有 launch 关联，无 launch 的输入按 thread 保留。项目级有独立选项；会话按任务/角色分组，同名主控标签显示首条记录时间和可区分的身份前缀。原文和追溯信息、完整回执都用原生 details 按需展开。CSS 新规则限定在 user-input-page，沿用现有颜色和边距，不改变共享样式的其他页面行为。

## 键盘驱动与故障场景

核对了 [CDP Input 协议](https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/pdl/domains/Input.pdl) 及 [Playwright 的 Chromium 键盘实现](https://raw.githubusercontent.com/microsoft/playwright/main/packages/playwright-core/src/server/chromium/crInput.ts)。驱动不再把 Windows 键码填进 macOS nativeVirtualKeyCode；非文本键使用 rawKeyDown，补齐 code，Enter 携带回车文本。选项从当前 selectedIndex 用方向键移动，Enter 后 Tab 离开。只观察 DOM 键盘/input/change/blur 事件；不设置 select.value，不触发伪造 change，不替换 window.a2a 或页面数据。若仍不能选择，报告事件轨迹与 INCOMPLETE，继续查夹具，不为测试修改产品交互。

新增代理只转发本次隔离后台的真实响应。后台完成原始 SQLite 读取后，代理按场景延迟交付或断开连接，测试跨项目迟到响应和读取失败/恢复。它不生成记录或门禁结果，也不连接正式后台。

## 下一轮命令与边界

精确命令在 `controller-runs-04.command`，要求外层 cwd 为当前 gate worktree。先跑父版 --smoke，核对原生 select 操作是否成立；再跑无 --smoke 的候选完整场景；候选全绿后跑四个变异。父版和变异应在业务断言失败（FAIL，非零），环境异常不计作变异检出。文件已存在就使用新编号，不覆盖。

默认完整场景包含三个项目、两个有输入的任务及一个只有回执的任务、同名主控、多 worker、无 launch 输入、长文本/特殊字符、乱序/同时间数据；还会追加不可预知的哨兵记录，测试刷新是否读到真实新增记录。检查双区筛选、单一来源空态、项目级、清空、完整内容、人工介入、900px 实际窗口、键盘展开/收起、刷新保留筛选、旧项目迟到响应、错误与恢复、空项目和清空项目。

四个变异均只改自有临时复制品：取消排序、回执忽略任务、忽略会话筛选、丢弃完整回执。不会修改 gate worktree 或冻结验收文件。

本轮 worker 没有启动 Electron、后台或 /bin/ps。隔离构建目录和缓存已删除；没有额外可写目录改动。安装 T-258 不触发 worker 自行重试或权限调整。独立审查仍由主控另开只读会话完成。

收尾 project-map status：Problems 0，Stale living docs 1。`workbench/README.md` 因两个前端覆盖文件变动被标 stale；README 和地图均不在本卡写入范围，交主控核对并更新，worker 未越界改动。
