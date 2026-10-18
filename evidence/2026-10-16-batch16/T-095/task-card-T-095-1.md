# 任务卡 T-095-1

你是 T-095 的 worker（执行主控派发）。先读 AGENTS.md、CONTEXT.md、.project-map/roles/worker.md、.project-map/tickets/T-095-*.md、收件箱 issue .project-map/inbox/20261017T172907Z-executor-issue-001.md，以及 scripts/dispatch、workbench/src/ 里读取 agent 状态的代码。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-095-1 |
| 来源 | T-095 ready_rev 1（assign，见收件箱最新 ideation assign） |
| 目标 | 把"worker 在 Codex 提问面板里等主控回答"识别为独立状态（等待主控回答），带 worker 与 launch 身份；折叠与展开两种形态都识别；识别不到报"未知"，不报 working |
| 非目标 | 不改 Herdr server；不用正则猜用户意图（只认面板的机械标记）；不自动回答面板；不双写两套状态 |
| 修改边界 | 允许：scripts/（Herdr 期状态读取，如 dispatch 或新的状态读取命令）、workbench/src/（不含 gates/，工作台任务视图的状态投影）、workbench/tests/、scripts/ 下测试、evidence/2026-10-16-batch16/T-095/；禁止：acceptance/、workbench/src/gates/、.project-map/、AGENTS.md、全局配置 |
| 完成条件 | ticket Acceptance：红态（折叠/展开两种形态下当前读出为 working，保留读屏原件）；绿态（两种形态都读出"等待主控回答"并带身份）；反例（普通 working——模型思考或跑命令——不被误报；面板关闭或已回答后状态回落）；status 0 problems |
| 任务类型 | 缺陷修复 |
| 复杂度 | M |
| 执行器 | Codex CLI，gpt-6.1-sol，xhigh，service_tier fast（用户本期临时放宽，launch-4b1abba18e87460da9cbacec04905c78） |
| 起点 | main 3c9016d02（exec/t095，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t095） |
| 唯一写入者 | s16-t095，task T-095 attempt a1 |

先只读决定"以哪个为准"（Herdr 期的脚本还是工作台任务视图），写成一页方向说明交我确认再实现。
要触发真实的提问面板，需要一个受控的 Codex 会话：写成脚本交我在沙箱外跑，只用隔离 CODEX_HOME（只复制 auth.json，结束删除），给它一条会触发提问面板的固定提示，并且不让它执行任何命令、不改文件，跑完关闭自建 pane。这会产生真实模型回合，请在脚本开头列明回合数上限（建议不超过 2），我核对后决定。
约束：沙箱外命令写成脚本交我跑，不请求升级；不用提问面板问我，问题写在回合结束的文字里。可以 git add / git commit 自己的交付（九项尾注），不 push、不 rebase。
交付：方向说明写好回一句 "T-095 DIRECTION READY"；全部完成最后一行写 T-095 READY <sha>。
