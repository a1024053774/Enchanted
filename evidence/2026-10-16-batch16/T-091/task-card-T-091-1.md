# 任务卡 T-091-1

你是 T-091 的 worker（执行主控派发）。先读 AGENTS.md、CONTEXT.md、.project-map/roles/worker.md、.project-map/tickets/T-091-single-window-multi-pane.md、spec .project-map/specs/native-cli-orchestration-2026-10-10.md（第 5、9、12 节）、.project-map/tickets/T-078-controllers-in-workbench.md 的 Resolution，以及 workbench/README.md、workbench/app/（main.ts、renderer.tsx 等）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-091-1 |
| 来源 | T-091 ready_rev 1（ready_by ideation；assign 20261017T092953Z-ideation-assign-001） |
| 目标 | 同一个 Electron 窗口里、同一任务下同时显示多个会话窗格，至少两个主控窗格加一个受管 worker 窗格；每个窗格有独立的窗口身份、输入序号和输出流，复用现有输出/输入通路与唯一门禁，全局 IPC handler 随之调整 |
| 非目标 | 不改门禁、紧急停止、收件箱语义；不另造业务接口；不做项目/任务导航的其他界面；不做系统 IME；不做真登录（T-093） |
| 修改边界 | 允许：workbench/app/、workbench/src/（仅窗格与窗口身份/IPC 相关，不含 workbench/src/gates/）、workbench/tests/、workbench/README.md、evidence/2026-10-16-batch16/T-091/；禁止：acceptance/、workbench/src/gates/、.project-map/、AGENTS.md、全局配置 |
| 完成条件 | ticket Acceptance：红态（当前 main 同一任务不能一窗三格，读回现状并保存）；绿态（一窗同任务两主控+一 worker 同时可辨，三份真实 workbench_snapshot 与进程身份核对、各自绑定正确 task/角色/launch，不靠标题）；反例（第三窗格绑错 task 或旧 launch 被拒；不得拼图或顺次切换冒称同时显示）；原始单帧截图或不剪辑短视频，只含隔离窗口；T-074/T-075 正反例与 T-078 主控窗格/输入行为不退化（列出所跑命令与结果） |
| 任务类型 | 前端界面 |
| 复杂度 | L |
| 执行器 | Codex CLI，gpt-6.1-sol，xhigh，service_tier default（launch-a818e11600754e8b8ad79aab63a17f83） |
| 起点 | main 44bbb7828459d81fab0d46069a19d3dd515a7732（exec/t091，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t091，workbench/node_modules 已从主仓库 APFS 克隆复制） |
| 唯一写入者 | s16-t091，task T-091 attempt a1 |

**第一步只做界面方向，停下等我确认后再实现**（ticket 要求开工前过界面方向）：按 frontend-production 与 same-visual-family 两个 skill 的约束（文件在 /Users/luckye/.claude/skills/ 或 ~/.codex/skills 下，只读），读现有工作台与借用的 Synara 组件/样式，写 evidence/2026-10-16-batch16/T-091/UI-DIRECTION.md：三窗格的布局（同一任务下怎么排、窗格标识怎么显示角色/task/launch、焦点与输入归属怎么让用户看清在给谁打字）、复用哪些现有组件与样式、窗口尺寸变化时的行为、与 IPC/窗口身份改动的对应关系、红态读回计划与截图方式。界面文案按 frontend-less-ai-tone（如有）不写营销腔。写完回一句 "T-091 DIRECTION READY"，不要开始改代码。

约束：只在本 worktree 写；沙箱外命令（启动 Electron、受控 daemon/PTY、/bin/ps、Computer Use 截图）一律写成脚本交我跑，不请求升级。Computer Use 仅限你自己启动的隔离 Electron 窗口；缺屏幕录制或辅助功能权限时停下报我（由用户在系统设置里给），不要自己去系统设置。测试中启动的后台服务必须脱离调用者进程组。不移动、替换或链接构建输出目录。可以 git add / git commit 自己的交付（九项尾注，launch-a818e11600754e8b8ad79aab63a17f83），不 push、不 rebase。证据按 T-088：仓库只留文本摘要，大块原始输出（截图/视频可留小的原始单帧在仓库，视频放外置盘）归档外置盘留 *.archive.json。语义拿不准就停下报我。
