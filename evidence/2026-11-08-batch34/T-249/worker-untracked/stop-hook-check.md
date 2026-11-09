# Stop hook 定位项核对

时间边界：下文为窗口结果收到前的核对记录，保留当时的等待状态。当前窗口组已完成，见 RESULTS.md；合法异常处理的归属结论不变。治理 Verified 仍由主控负责。

PASS（原候选处理来源与职责核对）。hook 所列 13 个定位项（含两个重复位置的 swallowed-exception 标签）都来自原 C，相关语句逐行相等，见 stop-hook-existing-handling.json。本次没有改这些处理；不为消除扫描提示删除它们，也不重新展开原面板整体审查。这是对 hook 的来源核对，不是新一轮独立审查或故障注入通过结论。

| 位置 | 可达调用与失败 | 本层职责及结论 |
| --- | --- | --- |
| gitHost.ts:181 | 主进程 watchRepo → add → fs.watch，目录删除、不可读或平台监听错误会抛异常 | 宿主拥有 watcher 的创建、登记与关闭，记录监听失败；保留原处理。界面既有定时刷新独立存在，此处没有新增补救路径。 |
| main.ts:424 | PanelDock 每两秒 panelDirectory → IPC → processCwd，shell 退出或 lsof 读不到 cwd 时拒绝 | 主进程拥有运行时目录解析，记录失败并采用 launch 目录的原策略；属于 C 已有行为，本次未改变或重新证明该降级精度。 |
| GitGraphPanel.tsx:15 | GraphView 初始 readColumns，localStorage 不可读或 JSON 损坏 | 组件拥有列宽偏好，采用默认宽度，不替代 Git 内容；保留。 |
| GitGraphPanel.tsx:60（含 swallowed 标签） | 列宽改变后的 effect 写 localStorage，配额或访问限制可抛异常 | 偏好持久化失败不撤销当前 React 列宽，也不改变仓库；该可选偏好边界由组件拥有，保留。 |
| GitGraphPanel.tsx:76 | 初载、范围切换、刷新调用 load → readGraph，Git 读取失败 | 当前 generation 的错误显示在本视图；过期请求不覆盖新状态，保留。 |
| GitGraphPanel.tsx:90 | watcher 节流后 loadStatus → readStatus，Git 状态读取失败 | 组件拥有状态刷新的生命周期，记录失败且不把失败结果替换成成功数据；这是原 C 的错误展示策略，本轮不扩改。 |
| GitGraphPanel.tsx:127 | 用户打开仓库菜单 → openRepoMenu → git.read REPO_STATUS | 菜单所需状态失败由该动作通知用户；不继续以伪造状态打开菜单，保留。 |
| GitGraphPanel.tsx:146 | 用户确认操作 → confirm → git.action，主进程拒绝或 Git 命令失败 | 对话框解除 busy 并显示失败，用户可修正或取消；不自动重试、不伪报成功，保留。 |
| PanelDock.tsx:70 | 面板初始开关、宽度、活动面板读取 stored，localStorage 访问失败 | 宿主拥有视图偏好，返回缺省供其初始状态使用；不涉及业务数据，保留。 |
| PanelDock.tsx:71（含 swallowed 标签） | 面板开关、宽度或活动面板变化调用 store，localStorage 写入失败 | 当前内存交互仍有效，只有可选偏好未持久化；宿主拥有该边界，保留。 |
| gitGraphCli.ts:55 | CLI main 顶层，参数、Git 读取或写动作验证失败 | 命令入口把异常转成 stderr 和退出码 1；不会以退出 0 掩盖失败，保留。 |

## Living docs

INCOMPLETE（治理状态待主控核对）。status 报 workbench/README.md 与 REVIEW.md 两项 stale，均指向 RUN-OUTSIDE-T249.sh。脚本内容与 C 相同，最后一次变化只是恢复 C 的 100755 执行位；README 的运行说明和 REVIEW 的敏感路径规则没有因此失真。

Verified 单元格位于 `.project-map/MAP.md`，不在 worker 卡写入范围；REVIEW.md 被任务卡明确冻结。任务卡还要求 README 只恢复原候选，因此本会话不以无实质内容的正文编辑绕过状态检查。请主控在其治理范围将已核对文档的 Verified 更新到最终候选/集成提交并重跑 status。此前已请求的外部运行不因此重复派发；worker 仍等待同一 blocking issue 的结果。

无产品或测试变更，不重跑已经通过的三条机械检查。真实窗口证据仍为 INCOMPLETE。
