STATUS: PASS
SUMMARY: 本次 21 个扫描命中对应 16 个异常边界；未确认结构性缺陷。结论限于这些边界的调用可达性与恢复职责，不替代三个任务的业务验收。
TARGET: 2026-11-09 用户提供的新增 hook 清单。审阅 T-260 external-test-01.py、T-262 两份 test-before 快照以及 T-249 review-v9/reviewer-input-01/originals 中两份源码。T-249 两份原件与产品候选 63304e0fcb3510d9cf4b1cbea5c3064fbb8286dd 按字节相同。
FINDINGS:
- 无确认发现；保留全部原始异常处理与历史失败，不修改快照来消除扫描提示。
LIMITATIONS:
- 本次通过源码中的实际调用链确认边界可达，没有重新注入每一种操作系统、存储或进程故障。下表区分可达的输入与已保存的运行事实。
- T-260 external-green-01.json 虽然文件名含 green，实际为 FAIL；重新打开问题被 IPC 拒绝。修正测试等待与期望别名后的 external-red-02.json 仍以 ui-reopen-operation 业务断言失败。本次审阅不提升这些运行结果。
- T-262 两份 test-before 文件是历史版本；其中页面启动和导航失败仍按原结果保留。最终产品验收使用任务中记录的新版本，不能用本次边界审阅替旧版本证明通过。
- T-249 的存储偏好写入失败会丢失下次打开的列宽偏好，当前 React 状态仍可用；监听或状态增量刷新失败会推迟更新到已有的 15 秒全量读取。全量读取失败显示错误。这里没有增加第二套数据、重试策略或成功结论。
RULE:
- 测试脚本的业务断言失败须为 FAIL，基础设施或清理失败须为 INCOMPLETE；两者都退出非零。原始现场与新运行分别保存。

| 文件与行 | 命中数 | 实际调用者和可到达失败 | 恢复职责与结论 |
| --- | --- | --- | --- |
| T-260/controller/external-test-01.py:219–220 | 2 | main 创建 Desktop 后调用 ready；新 Electron 尚未监听调试端口时 socket.create_connection 抛 ConnectionRefusedError，连接超时抛 TimeoutError。 | ready 拥有端口就绪等待；False 只表示本轮未就绪。wait 有 20 秒界限，超时抛出；进程退出在连接前直接报错。没有把失败当成功。 |
| 同文件:240 | 1 | main 重连场景及 finally 调用 stop；自己启动的 Electron 对 terminate 未在 10 秒内退出，wait 抛 TimeoutExpired。 | Desktop 拥有其子进程清理；升级为 kill 后再有界等待。第二次等待仍失败会被外层记录并标 INCOMPLETE，不清除失败夹具。 |
| 同文件:403 | 2 | main 中构建、后台请求、页面等待、JSON 读取等真实调用抛异常；业务检查的正常不等比较则进入 failed 列表。 | 顶层测试运行器拥有结果归类及 finally 清理；保存异常类型、文本，置 INCOMPLETE，退出 1。已保存的 reopen 业务失败仍为 FAIL。 |
| T-262/worker/test-before-navigation-07.py:362 | 1 | Fixture.start、choose、reset 及 main 页面条件调用 until；Runtime.evaluate 的页面异常或 CDP 命令失败可抛 AssertionError / RuntimeError。 | 页面等待器负责有界轮询；保留最后异常，持续错误最后抛 RuntimeError。成功读取但业务条件一直不成立才抛 BusinessFailure。不会凭捕获直接返回通过。 |
| 同文件:641 | 1 | main 的真实点击、筛选和页面条件可由 click / until 抛 BusinessFailure。 | 测试运行器把业务失败追加 failed，置 FAIL，退出 1；不将业务反例归为环境失败。 |
| 同文件:652 | 2 | prepare/start/CDP/文件读取等其余异常从 main 的场景传出。 | 顶层保存类型与错误文本，置 INCOMPLETE；finally 留诊断、尝试自己夹具的清理，非零退出。 |
| T-262/worker/test-before-window-06.py:325 | 1 | start、choose、reset 与页面场景调用同一 until；页面求值或 CDP 失败可到达。 | 与 navigation-07 的有界等待归属相同；异常持续存在不会变绿。 |
| 同文件:604 | 1 | 场景的 click / until 抛 BusinessFailure。 | 顶层记业务 FAIL；保留错误，非零退出。 |
| 同文件:615 | 2 | 构建、启动、页面求值、文件读取等其余异常。 | 顶层记 INCOMPLETE 并执行自有夹具清理；没有吞掉失败变 PASS。 |
| T-249/.../gitHost.ts:181 | 1 | GraphView 的 host.git.watch 经 PanelDock、a2a:git-watch IPC 调用 watchRepo；仓库目录被移除或无权限时 fs.watch 可同步抛错。 | Git 宿主拥有 watcher 的创建与释放；记录 root 与错误。界面原有 15 秒全量读取仍独立运行，失败会由 load 显示错误。这里不伪造事件或修改仓库。 |
| T-249/.../GitGraphPanel.tsx:15 | 1 | GraphView 的 useState(readColumns) 在挂载时读取 localStorage；存储被禁止或保存文本不是有效 JSON 时抛错。 | 视图拥有列宽偏好，回到明确的默认列宽；不修改仓库或业务结果。 |
| 同文件:60 | 2 | 列宽状态改变触发 effect；localStorage 禁用或额度不足时 setItem 抛错。 | 视图的便利偏好持久化失败；当前状态和拖拽仍存在。与读取默认值成对，缺失的是跨打开保存，不是 Git 数据。保留处理。 |
| 同文件:76 | 1 | 挂载、选项改变、ref 监听和 15 秒定时器调用 load；readGraph 的 Git / IPC 失败可到达。 | 视图拥有读取错误展示；只允许当前 generation 更新错误，避免旧目录回包污染当前视图，不返回伪造 graph。 |
| 同文件:90 | 1 | 工作区监听经 statusOnly 的 1.5 秒节流调用 loadStatus；readStatus 的 Git / IPC 失败可到达。 | 增量刷新层记录错误并保留上次图；已有全量定时读取继续校正。没有把失败写成新的状态，也不自动重放写操作。 |
| 同文件:127 | 1 | 仓库菜单右键调用 openRepoMenu；Git 状态命令非零或 IPC 拒绝会抛错。 | 菜单层用 host.notify 展示读取错误，阻止基于缺失状态生成操作菜单。 |
| 同文件:146 | 1 | 用户确认操作调用 confirm；host.git.action 的校验、只读保护或 Git 非零结果会拒绝。 | 对话框保留错误并解除 busy，让用户判断后续动作；不自动重发仓库写入，不把失败显示为成功。 |

路径前缀：T-260、T-262 位于 evidence/2026-11-08-batch34/；T-249 两份原件位于 evidence/2026-11-09-batch35/T-249/review-v9/reviewer-input-01/originals/workbench/app/。
