# 任务卡 T-096-1

你是 T-096 的 worker（执行主控派发）。先读 AGENTS.md、CONTEXT.md、.project-map/roles/worker.md、.project-map/tickets/T-096-*.md、T-091 与 T-093 的 ticket（多窗格与 profile 记录）、workbench/README.md、workbench/src/（panes.ts、daemon.ts、claudeLaunch.ts 等）与 workbench/app/。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-096-1 |
| 来源 | T-096 ready_rev 1（assign，见收件箱最新 ideation assign） |
| 目标 | 工作台保存"当前打开的窗格集"（task、role、launch、session、位置；窗格创建/关闭时落盘），重启后按启动记录里的完整 argv 续接原会话；记录缺 argv、CLI 版本不符、session 不存在时明确报错并保留该窗格为"未恢复"，不静默换配置或开新会话；恢复本身不产生模型回合 |
| 非目标 | 不改 Herdr；不写 ~/.claude、~/.codex；不用裸 resume 或默认配置补位；不另造一套状态（沿用 T-091 多窗格与 T-093 的 profile 记录）；不做真登录 |
| 修改边界 | 允许：workbench/src/（不含 gates/）、workbench/app/、workbench/tests/、workbench/README.md、evidence/2026-10-16-batch16/T-096/；禁止：acceptance/、workbench/src/gates/、.project-map/、AGENTS.md、全局配置 |
| 完成条件 | ticket Acceptance：红态（main 上重启后窗格集为空、不续接）；绿态（假 API 起三个窗格，杀掉整个后台与 Electron，重启后三个窗格回来，进程身份、task、role、launch、argv 与重启前一致，模型回合 0）；四个反例各在真实入口失败并保留现场（缺 argv、版本不符、session 不存在、某窗格失败不影响其余且不记成已恢复）；argv 逐字段相等；status 0 problems |
| 任务类型 | 后端逻辑 |
| 复杂度 | L |
| 执行器 | Codex CLI，gpt-6.1-sol，xhigh，service_tier fast（用户本期临时放宽，launch-14dcc6be543a483ab0b03021f573d028） |
| 起点 | main 3c9016d02（exec/t096，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t096，node_modules 已 APFS 克隆） |
| 唯一写入者 | s16-t096，task T-096 attempt a1 |

注意：T-093 正在并行修改 workbench/src 里的 Claude 启动与 profile 相关文件（claudeLogin*、claudeLaunch.ts 等），尽量不改这些文件；如必须改，先停下报我协调。先做 tracer bullet（单窗格的保存→杀后台→恢复→读回），再扩到三格与反例。夹具沿用 T-078/T-091：loopback 假 API、隔离 HOME，Claude CLI 用配置值 2.1.302，受控 receiver 代替真 Codex，模型回合 0。
约束：沙箱外命令（Electron、daemon、PTY、ps、截图）写成脚本交我跑，脚本开头列清会启动的 CLI、按键和预算，限制输出量，跑完收尾；同时最多一个 Electron。不用提问面板问我。可以 git add / git commit 自己的交付（九项尾注），不 push、不 rebase。
交付：最后一行写 T-096 READY <sha>。
