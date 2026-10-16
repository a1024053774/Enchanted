⟦主控 #1⟧
# 任务卡 T-087-1

你是 T-087 的 worker（执行主控派发）。先读 AGENTS.md、.project-map/roles/worker.md、.project-map/tickets/T-087-explicit-graph-view.md、CONTEXT.md，以及 .project-map/inbox/20261016T082147Z-ideation-assign-001.md。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-087-1 |
| 来源 | .project-map/tickets/T-087-explicit-graph-view.md，ready_rev 1（ready_by ideation）；用户 2026-10-16 原话（逐字，会话"a2a-构思主控"）："T-088 的六条细节和 T-087开工" |
| 目标 | 一份带图的文档加生成它的脚本：从真实来源（ticket 字段、收件箱条目类型、任务卡检查串、门禁拒收码与恢复路径、持久化边界）推出 ticket 生命周期与门禁检查串的图；每个点和边带来源引用（文件:行 或 ticket），查不到来源的标"隐式/靠主控判断"；单列隐式边清单（后果、T-081/T-082 覆盖与未覆盖） |
| 非目标 | 不改 workbench/ 或任何产品代码；不做图执行器/策略引擎；不让图驱动派发；不把 Graph Engineering 写进 CONTEXT.md；不放进工作台界面 |
| 修改边界 | 允许：findings/ 下新文档、scripts/ 或 findings/ 下的生成脚本（只读来源、输出文本）、evidence/2026-10-16-batch16/T-087/；禁止：workbench/、.project-map/roles/、AGENTS.md；CONTEXT.md 只有在图完成后确需总称、并在 T-087 内定下含义时才改，改前先报我 |
| 完成条件 | 生成脚本可重跑、输出确定（同一来源两次运行 diff 为空）；文档里每个点/边的来源引用可机械核对存在；隐式边清单单列；project_map.py status 0 problems / 0 stale |
| 任务类型 | 调研 |
| 复杂度 | M |
| 执行器 | Codex CLI codex-cli 0.162.1，gpt-6.1-sol，xhigh，service_tier default（启动记录 launch-81bf2744649b42f2bc780ace08c32634） |
| 起点 | fc362ab44054bc82afe8a2f56eef17972ece7bc5（exec/t087，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t087；含 workbench/src、hooks、bin、scripts、acceptance、.project-map、.grilling、findings） |
| 唯一写入者 | s16-t087（wF:p4H），task T-087 attempt a1 |

约束：只在本 worktree 工作；只读分析，不启动服务、不调模型 API、不写全局配置；你可以用 git add / git commit 提交自己的交付（用户规则允许），不 push、不 rebase；沙箱外命令一律写脚本交我，不请求升级。术语：先用现有词（门禁检查、agent 会话、人工决定点）作图，不在代码和文档里各自发明新词。来源抽查会由另一个不写图的会话做，你不要自称已核对。证据尽量小（文本），不放大块原始输出。

交付：文档、脚本、两次生成 diff 为空的证据、来源引用存在性检查结果；最后一行写 T-087 READY。
