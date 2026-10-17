# 任务卡 T-094-1

你是 T-094 的 worker（执行主控派发）。先读 AGENTS.md、.project-map/roles/worker.md、.project-map/tickets/T-094-launch-worker-sparse-start-failure.md（文件名以实际为准，用 ls .project-map/tickets/T-094*）、scripts/launch-worker、收件箱 issue .project-map/inbox/20261017T104229Z-executor-issue-001.md。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-094-1 |
| 来源 | T-094 ready_rev 1（assign 20261017T172126Z-ideation-assign-001） |
| 目标 | 找出 launch-worker 在稀疏 worktree 里间歇启动失败的根因并修复：失败带可读错误身份（保存 herdr stderr），半成功（进程起来但没命名）记成独立结果，不留悬空 pane |
| 非目标 | 不改 Herdr server，不动用户正在用的 Herdr 会话或窗格；不加盲目重试；不靠加长时限掩盖；不改用户的 zsh/提示符配置 |
| 修改边界 | 允许：scripts/launch-worker 及其测试（scripts/ 或 workbench/tests/ 下）、evidence/2026-10-16-batch16/T-094/；禁止：acceptance/、.project-map/（除本卡不改）、AGENTS.md、全局配置、~/.zshrc 等用户配置 |
| 完成条件 | ticket Acceptance 五条：红态（能触发失败的 worktree 里复现，保留 herdr stderr 与启动记录）；绿态（同条件连续多次全部成功，或失败带可读原因）；反例（半成功被记为独立结果）；不影响用户 Herdr；status 0 problems |
| 任务类型 | 缺陷修复 |
| 修复对象 | scripts/launch-worker（issue 20261017T104229Z） |
| 复杂度 | S |
| 执行器 | Codex CLI，gpt-6.1-sol，xhigh，service_tier fast（用户 2026-10-17 临时放宽，launch-efca9e180a594c2e98ec594874eaf253） |
| 起点 | main 617863704（exec/t094，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t094——本身就是可能触发问题的环境） |
| 唯一写入者 | s16-t094，task T-094 attempt a1 |

已知线索（未证实）：失败的 pane 里 zsh 提示符显示 git 状态"!132980"、"!173205"（稀疏 worktree 被提示符算成大量改动），推测提示符异步 git 状态慢，shell 未就绪 herdr 就启动，或超过 30 秒默认时限；手动 `herdr agent start --timeout 60000` 成功过。先只读读 herdr 的命令说明（herdr agent start 的行为、agent_not_ready 等错误码），再设计复现。
约束：复现要启动 Herdr pane 和 Codex——这类沙箱外命令写成脚本交我跑；复现中新建的 pane 一律由脚本自己关闭，只关自己建的；复现时启动的 Codex 只到首屏、不发任何提示，不产生模型回合；每次复现都记启动次数。可以 git add / git commit 自己的交付（九项尾注），不 push、不 rebase。语义拿不准就停下报我。
交付：最后一行写 T-094 READY <sha>。
