# T-139 ticket 的普通终端说明尚未同步用户新裁定

状态：非阻塞上报。T-159 实现继续按执行主控消息 #54 的明确授权进行。

读取 main 的 `.project-map/tickets/T-159-split-keeps-original-pane.md`，验收已新增“允许任务视图并排普通终端”；同一 main 的 `.project-map/tickets/T-139-view-model-split-screen.md` 目标仍写：“项目的普通终端（含用户自己启动、经角色申请成为主控的终端）作为项目层的会话；它只在‘它自己’的视图里出现，不再混进任务视图。”

当前实现与测试按用户 2026-10-24 新裁定区分：普通终端不成为任务 agent，但可被明确加入任务布局；未选择的其他项目终端不自动加入。T-139 的单 agent 视图隔离仍保留。

worker 已在授权范围内同步 `workbench/README.md` 和与该规则相关的 `test_t139_*`。治理文件不在 worker 修改边界内，请执行主控经构思主控同步 T-139 ticket 的相关说明；此处不自行修改地图、ticket、AGENTS.md 或 CONTEXT.md。
