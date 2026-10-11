# T-075-5：daemon.ts 未提交改动触发 README 覆盖检查

状态：INCOMPLETE（非阻塞探针交接，阻止最终交付宣称地图健康）。

主控 #47 批准的 D1 已实现，产品 diff 只在 `workbench/src/daemon.ts`。最后运行地图检查，退出 1，0 problems、1 stale：`workbench/README.md: uncommitted changes to covered files without a doc edit: workbench/src/daemon.ts`。

README 当前的产品 CLI、启动参数与运行时边界说明仍符合代码；新增的是仅供测试代码调用的内部构造参数。任务卡的正文修改边界不包括 README/MAP，decision 01 也指定覆盖登记由主控处理，因此 worker 未越界修改。

建议由主控在 README“运行时边界”补充下列说明并处理地图登记；worker 保留失败检查，不把本轮写成 0 stale：

> `daemon.ts` 导出内部 `serve`，允许测试启动器提供门禁构造函数；默认构造仍使用 `Panes`，产品 `daemon_start` 调用默认值。T-075-5 的隔离线程探针借此经过同一个后台请求处理器与最终 CLI；证据仍标为隔离编排，不证明真实 Codex 或 PTY。

三个探针的沙箱外脚本已经准备好；本问题无需改变它们的业务断言或运行时。最终地图检查须等主控处理后重跑。

重现：`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
