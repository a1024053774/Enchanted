T-165-1 / a1，worker b24-t165。

在已获准的 workbench/src/panes.ts 最小修复后，project_map.py status 报 workbench/README.md stale：uncommitted changes to covered files without a doc edit。README 及地图不在任务卡允许写入范围内，本 worker 未改它们。

建议：执行主控负责同步 README 的 Claude Stop/排队输入说明，并按项目规范处理 living doc Verified；若认为当前文档仍准确，则由主控核对后更新 Verified。此项默认不阻塞本票的实现、03 脚本准备与提交，但整体文档健康不能报告 PASS。

位置：workbench/src/panes.ts 的 scan、claudeStop；.project-map/MAP.md 的 Living docs 表。
