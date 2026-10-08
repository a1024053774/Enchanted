# T-038 界面沿用依据（2026-10-07）

这屏服务于核对任务与 agent 分工。主行动是打开一个任务窗口；唯一强调是当前门禁状态。沿用 Synara 的侧栏行、分栏聊天区域与 Badge，不新增主题、字体、CSS 文件或独立卡片系统。

代码族卡（`apps/web/src/index.css:489/494/527/607`，运行后还需截图核对）：

| 角色 | 既有值 |
| --- | --- |
| 底 | light `#fcfcfc`；dark `#0e0e0e`（用户主题可覆盖） |
| 字 | light neutral-800；dark neutral-100 |
| 强调 | primary：light neutral-900；dark neutral-100；门禁沿用 info/success/warning/destructive 语义色 |
| 边线 | black 5% / white 4% |
| 字体栈 | `--font-ui-family` 继承用户主题，否则 -apple-system、BlinkMacSystemFont、Segoe UI、system-ui、sans-serif；文字用 text-ui tokens |
| 圆角 | 根 radius `0.625rem`（10px），复用 Button/Input/Badge 各自已有变体 |

需要的模块：项目/任务导航、任务标题、状态与失败详情、角色归属编辑、并列 agent 会话。导航和状态沿用 Button/Badge；表单沿用 Input/Select；会话沿用现有 ChatView（不复制 transcript 或 composer）。本页只记实现依据，不是外观通过证明；外观由用户判断。
