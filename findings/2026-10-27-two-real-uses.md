# Enchanted 0.1.5 两次真实使用的问题记录（2026-10-27）

范围：用户 2026-10-26 至 10-27 在 Enchanted 0.1.5 里的两次使用（github.io 首页加“项目”栏、翻译发布 claude.dev 文章），以及用户截图和反馈。截止点：2026-10-27 本记录写成时编排后台 `~/Library/Application Support/a2a-orchestrator/state.sqlite3` 的状态。来源是只读查询该库和读源码，没有改动后台数据，也没有重跑。

总体结论：**NO_GO**。产品页宣称的“派发 → 审查 → 集成”主流程，在用户自己的两次使用里都没有按宣称走通：第一次完全绕开了 Enchanted，第二次被一个与当前项目无关的缺陷卡住，靠主控伪造空仓库才绕过去。

## 问题与根因

| 编号 | 用户看到的现象 | 根因（已核对） | 证据位置 |
| --- | --- | --- | --- |
| U01 | 项目无法从侧栏移除 | 移除命令在项目“有任何门禁任务”或“有打开的窗格”时直接拒绝；任务永不删除，所以用过门禁的项目永远移不掉。界面只在菜单项上灰掉，没有给出办法 | `workbench/src/daemon.ts:562-568`，`workbench/app/renderer.tsx:999-1000` |
| U02 | 第二次派发 T-1 报 `spawn git ENOENT`，路径是已删除的 `/private/tmp/a2a-lcu-demo` | 认领前的路径冲突检查遍历**所有项目**里未回收的 attempt，对每个 attempt 的仓库跑 `git rev-parse`。a2a-lcu-demo 有两个 `accepted` 但未回收的 attempt（`26d464e3…`、`ae6e7d93…`），仓库目录已被删，于是任何项目的认领都失败 | `workbench/src/gates/core.ts:1285-1302`；`attempts` 表 |
| U03 | 主控为绕过 U02 在 `/private/tmp/a2a-lcu-demo` 建了空 git 仓库 | U02 的直接后果；用户选了绕行，派发才成功。这个空仓库仍在，真正的修复是 U02 | 第二次会话记录 |
| U04 | 侧栏出现一个“worker T-1 · 未知”，用户以为派发没成功、agy worker 没进侧栏 | 这个“未知”就是 agy worker（launch `f6d10a54…`，`cli: agy`，argv 含 `gemini 4 argon`）。侧栏的 CLI 标签只认 Claude Code 和 Codex，其余一律写“未知” | `workbench/src/sidebar.ts:185-186`；`launch_records` |
| U05 | 该 worker 一直显示转圈（运行中） | worker 行的状态只看窗格是否存活，不看 agy 报的 OSC 7501 回合信号；后台记录显示它 04:27:11 已交付候选提交 `a2cf105` 并回到 idle | `sidebar.ts:225` 一带；`orchestration_events` seq 68022-68038 |
| U06 | 第一次使用时 agy 审查员不在侧栏 | 执行主控用 `herdr pane split` 在 Herdr 里起了 agy，完全没经过 Enchanted。原因有两层：①这次的终端开在 a2a 项目目录（launch `ee3ade8e…`，cwd `~/Documents/Code/a2a`），角色申请随终端绑到 a2a 项目（role request `6433c5a5…`），而活在 github.io，门禁不让跨项目建任务（会话原话“门禁身份只覆盖 a2a 项目”）；②本仓库 `AGENTS.md` 写着“日常派发继续经 Herdr”，在 a2a 目录里启动的主控会照着做。第二次终端开在 github.io（launch `ca06bd3d…`），角色绑到 github.io，派发经门禁，worker 进了侧栏。用户指出：主控身份由启动目录决定、不能跨项目，这本身就是问题 | 第一次会话记录；`orchestration_events` 的 role_requested；`AGENTS.md` 第三阶段约束“切换”一条 |
| U07 | 点项目进入任务格，再点 T-138，里面什么都没有 | 任务页只渲染**存活的窗格**。attempt 回收后窗格没了，页面只剩一行“待认领 / T-138”；任务卡内容、历次 attempt、检查结果、审查报告、打分都不显示。产品页写的是“点一张票，进入 agent 分屏：worker 和独立审查并排，底部是这张票在门禁里的状态”，对已结束的票不成立 | `renderer.tsx:1078-1100`；`docs/index.html` 第 1 节第 3 步 |
| U08 | T-138 已关闭，任务格却写“待认领” | 门禁里任务没有“关闭”状态：attempt 被回收后任务回到 ready，地图上的关闭不会同步给门禁 | `attempts` 表 `a2a+T-138` 为 revoked/removed |
| U09 | 不同 worker 分不清是哪家 CLI | 同 U04，侧栏只有文字标签，没有图标，且只认两家 | `sidebar.ts:185-186` |
| U10 | 想像 Codex 的“复制深度链接”一样，复制某个会话的原生 ID 交给 AI 去读 | 后台只为 Claude Code 记录真实的原生会话 ID；agy、opencode 记的是 `osc7501:<launch id>`，是我们自己造的，不是 CLI 的会话 ID；Codex 绑定后才有。界面上没有复制入口 | `launch_records.native_session`；`panes.ts:537-613` |
| U11 | 想跨多个路径完成一件事，路径拦截太死；项目“额外目录”不太能用 | 三处限制叠在一起：①任务只属于一个仓库，主控身份只绑一个项目（见 U06）；②额外目录虽然给了写权限，但启动说明明写“其中的改动不进门禁的审查与集成”，也就是改了也不会被审查、提交或合并；③认领时任务卡路径与其他未回收 attempt 重叠就拒绝（`path_overlap`），跨任务协作只能排队 | `panes.ts:893`；`gates/core.ts:1285-1302` |

## 用户提出的方向（待决定，未实现）

1. **项目管理参照 Claude Code**：项目只是“打开过的目录”，从列表移除不受任务约束，历史留着可以找回；目录没了也不应拖垮其他项目。
2. **每个 agent 前加 CLI 图标**（Claude Code、Codex、agy、opencode）。
3. **复制会话 ID / 深度链接**：右键复制该会话所属 CLI 的原生 ID，并标明是哪家，便于让 AI 读对应记录。已知：Claude Code 的会话可用 `claude --resume <id>` 恢复，记录在 `~/.claude/projects/<目录>/<id>.jsonl`；Codex 用 `codex resume <id>`。agy、opencode 能否拿到并按 ID 读取，**待实测**。
4. **派发走项目命令或 MCP，确定性的事用钩子**：用户的判断是模型经固定指令派发，软件一定能识别；尾注、让主控打分这类确定性的事由钩子保证。现状补充：派发其实已经经 `a2a call` 命令走门禁（第二次就是），失败来自 U02 这类缺陷；第一次没走是因为 U06。尾注已由门禁装进 worktree 的 `prepare-commit-msg` 钩子写入并在交付时核对，打分已是验收命令的必填项（`gates/core.ts:2261-2281`、`2819-2834`）。agy、opencode 没有按会话的钩子，钩子方案对它们需另想办法。
5. **跨路径工作**：见 U11，需要决定是放开“一个任务多个仓库”，还是让主控可跨项目建任务，或者让额外目录里的改动也进审查与集成。

## 没有做的检查

- 没有在界面上复现 U01、U07（只读了代码和库）。
- 没有核对 claude.ai、Codex 的深度链接格式，也没有实测 agy、opencode 的会话 ID。
- 第二次会话的 T-1 候选提交 `a2cf105` 还没经 verify 和审查，本记录不判断它的质量。
