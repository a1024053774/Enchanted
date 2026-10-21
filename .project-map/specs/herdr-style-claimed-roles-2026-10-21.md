# Spec: Herdr 式终端、认领身份与按 CLI 派发（2026-10-21）

## Problem

用户要像在 Herdr 里一样工作：添加项目，在项目目录的终端里自己启动想用的 CLI，告诉某个 agent “你去做主控”，它就能派发其他 agent、互相通信、安排身份、设置边界；同时要有 Herdr 没有的权限管理。

现在的工作台做不到。主控只能由编排后台按任务启动，入口只有测试脚本在用，界面上没有；普通终端里的 agent 没有门禁身份，也不知道系统的用法；worker 只能是 Codex。

## Solution

- 添加项目后，新建的终端在项目目录里，和一般终端一样，用户自己敲命令启动任何 CLI。
- 终端里有 `a2a` 命令，并为支持的 CLI 自动挂上使用说明（skill）。agent 读了就知道怎么申请角色、派发、通信、设边界。
- agent 申请角色时，Enchanted 显示批准请求；用户批准后，这个会话以该角色出现在侧栏的 agent 树里，它的 a2a 操作按角色经门禁核对。没有批准的身份，门禁不受理。
- 主控派发 worker 时，指定 CLI、模型、强度和任务卡；后台在新窗格里带着 worker 角色的权限参数启动它。worker 的交付、审查、集成沿用现有门禁检查串。
- 主控之间、主控与 worker 之间的消息，经 a2a 命令写入对方窗格并记录，沿用现有派发标记与收件箱语义。

## Decisions

- [T-119 普通终端里认领身份、a2a 命令与 skill、按主控选的 CLI 启动 worker](../tickets/T-119-herdr-style-terminals-claimed-roles.md)
- 沿用：[T-069](../tickets/T-069-third-stage-direction.md)（其中 D19 的“worker 只用 Codex”由 T-119 取代）、[T-070](../tickets/T-070-gates-task-cards-quality.md)、[T-071](../tickets/T-071-permissions-signals-dispatch-data.md)、[T-072](../tickets/T-072-traceability-scoring-retrospective-metrics.md)、[T-107](../tickets/T-107-workbench-sidebar-projects-agent-tree.md)（agent 树显示认领后的角色与层级）

## Test seam

打包后的 Enchanted 测试版（独立 bundle id 与数据目录）加真实 CLI：在项目终端里启动真实 Claude Code，让它按 skill 申请执行主控，经界面批准，再派发一个 worker（Claude Code 或 Codex，按主控所选）到夹具仓库，走完交付、独立审查、集成。证据：界面截图、后台库的事件读回、Git 引用读回，以及重现命令。

## Out of scope

- 把已经在跑的普通终端会话转成受管 worker（启动时没带权限参数，无法强制）。
- Claude Code 与 Codex 以外的 CLI 适配（按需另开票）。
- MCP 形式的系统接口。
- 往用户项目仓库或 `~/.claude`、`~/.codex` 写配置。
