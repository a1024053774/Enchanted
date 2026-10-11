# 任务卡 T-078-1

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。T-078 分两步：
- **本卡**：不需要真实 Claude 模型回合的部分；
- 主控窗格的真实 Claude 验证：在用户答复认证方式与额度（needs-decision `20261011T101958Z`）之前不做，另开一张卡。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-078-1 |
| 来源 | ticket T-078，`ready_rev: 1` |
| 目标 | 实现 ticket T-078 What to build 的第 2～6 项，以及第 1 项中不依赖真实模型的骨架：(2) Electron 窗口里的窗格可以输入，所有输入都经后台写进 node-pty；(3) 用户输入记录：亲手输入记为用户输入，注入的文字不算，落进 worker 窗格的记为人工介入；(4) 主控窗格只在空闲时注入，回合中排队，Esc 之后由用户放行；(5) 收件箱进库，加上库版 `scripts/inbox` 的后台客户端，按角色限定可写条目，只在夹具项目上使用；(6) 紧急停止流程（stop、ack，2 分钟无 ack 时只中断），记录真实调用者；(1) 主控窗格的启动参数与启动记录（Claude 的 `--session-id`、`--model`、`--effort`、`--settings`）。 |
| 非目标 | 真实 Claude 模型回合；本仓库日常使用的文件版 `scripts/inbox`（保持不动，S7 才退役）；T-076 的质量串；T-077 的 worktree；面板与通知（S5）。 |
| 修改边界 | 允许：你 worktree 里的 `workbench/`（src、app、hooks、tests、README）；为库版收件箱新增的客户端文件（放在 `workbench/` 下，例如 `workbench/bin/inbox`，**不要覆盖** `scripts/inbox`）；本卡证据目录 `evidence/2026-10-11-batch13/T-078/`；ticket T-078 的 Resolution。禁止：`scripts/` 下的现有文件、`acceptance/test_*.py` 的断言、spec、地图、全局配置、`~/.claude`、`~/.codex`。 |
| 完成条件 | 见 ticket T-078 的 Acceptance。除“真实 Claude 回合”外逐条对应；主控窗格的 Claude 行为先用不消耗模型的夹具（终端与 hook 层）证明，并在 RESULTS 里标明“待真实 Claude 复核”。 |
| 红态命令 | 每条新行为都先在起点上失败，再在候选上通过。 |
| 任务类型 | 后端逻辑 |
| 修复对象 | — |
| 复杂度 | L |
| 执行器 | Codex CLI，`gpt-6-astra`，xhigh，Fast 请求。选用理由：横跨 Electron 输入、后台忙闲状态、收件箱权限和紧急停止的身份来源，属于复杂任务。 |
| 起点 | `main` 的 `14b57d22`（worktree 创建时） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s13-t078`），worktree `/Users/luckye/Documents/Code/a2a-wt-t078`，分支 `exec/t078` |

## 依据
- spec 第 5、6、9 节；
- T-074 的结论：忙闲由后台自己判断，Esc 之后由用户放行，注入用 bracketed paste 后单独回车；
- T-075-4 的只读窗口；
- 原 T-059、T-066 的目标；
- ticket T-078 的失败方式清单。

## 先交计划，停下等我
写 `evidence/2026-10-11-batch13/T-078/PLAN.md`，内容包括：
1. 输入通路，以及如何区分用户输入与注入；
2. 主控窗格的忙闲与排队；
3. 收件箱库表和角色权限；
4. 紧急停止时调用者身份从哪里来（凭据，而不是参数）；
5. 失败方式清单逐条处理；
6. 红态与反例；
7. 不消耗模型的 Claude 夹具方案：真实 Claude Code CLI 加本地伪造的 Messages API，或者其他方案。注意：方案本身也要等用户答复后才能用，答复前只能写方案、不能运行；
8. 需要在沙箱外运行的项；
9. 与 T-076-1、T-077 可能冲突的位置（`daemon.ts`、`panes.ts`、`gates/core.ts`）。

写完回复 `T-078 PLAN READY`，然后停下等我。

## 审查与交付
- 做一次 fresh-context 只读独立审查。审查发现的问题，先取得红态再修复，修复部分的 diff 由我审。
- 交付物：分支提交（带尾注）、`T-078/RESULTS.md`、ticket Resolution（保持 open）。
- 终端最后一行：`T-078 DONE <PASS|INCOMPLETE|BLOCKED> <exec/t078 的完整提交号>`。
## 并行规则（本批第二轮起有 2～3 个 worker 同时工作）
- 你在**自己的 git worktree** 里工作，不碰主 checkout `/Users/luckye/Documents/Code/a2a`；那里归执行主控和另一个 worker 使用。你的 worktree 路径和分支名写在任务卡的“唯一写入者”一栏。`workbench/node_modules` 已经由执行主控装好（离线安装，缓存在外置盘），你不需要也不要重新安装。
- 只在你的分支上提交。git add、git commit 各自单独执行，不加前缀。
- 交付前，先把分支变基到最新的 `main` 上：`git -C <你的 worktree> rebase main`。冲突由你解决：只能保留双方的意图，不能删掉对方的行为来让冲突消失。变基之后，在变基后的代码上重跑本卡的完成条件和 8/9/18 回归，然后再交付。最后由执行主控把你的分支快进合并进 `main`。
- 下面这些文件只由执行主控写：本批的 `dispatch.jsonl`、`panes.txt`、`controller-poll.log`，以及 `.project-map/MAP.md`。ticket 你只写自己那一张的 Resolution。
- 沙箱外的 `outside-sandbox.sh` 放在你本卡的证据目录里，脚本里的路径一律用你自己 worktree 的绝对路径。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 本卡不需要真实 Codex 被测回合；如确需，先问我。不运行任何真实 Claude 回合。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-11-batch13/T-078/`（在你的 worktree 里），中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
- 证据大小：单个证据文件超过 5 MB 的原始输出（大 JSON、trace、tar）不直接提交。要么压缩后提交，要么放外置盘 `/Volumes/WD-Elements/a2a-evidence/<批次>/<票>/` 归档；仓库里只留摘要、重放命令和归档路径。提交前用 `find <证据目录> -size +5M` 检查。
- 需要在沙箱外运行的部分（Unix socket、ps、真实 Codex、Electron、自建进程信号），统一写进本卡的 `outside-sandbox.sh`，然后回复 `T-0xx OUTSIDE-SANDBOX READY` 并停下，由执行主控执行。不要申请提权。
- git 写操作：`git add`、`git commit` 各自单独执行，不和别的命令串联，也不加环境变量前缀。
- 探针或测试本身的错误可以直接修，但要记录；真实的协议失败或产品失败、无法判定的情况、需要改业务断言的情况，都要停下来交给我。
