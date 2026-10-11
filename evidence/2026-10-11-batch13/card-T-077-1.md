# 任务卡 T-077-1

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-077-1 |
| 来源 | ticket T-077，`ready_rev: 1` |
| 目标 | 实现 S3 的 worktree 生命周期与冲突处理，即 ticket T-077 的 What to build 第 1～6 项：命名；按清理表清理并保留隐藏引用；认领时检查路径交集；文本冲突写回 worker；R8 重新验收上限；集成时检查检出工作区里的未提交改动。 |
| 非目标 | T-076 的质量串（红态、规则式检查、独立审查、打回回写、打分）；T-078 的主控窗格与收件箱；面板 UI（S5 之前，上报改用 issue 条目）；不改存储结构（另有切片）。 |
| 修改边界 | 允许：你 worktree 里的 `workbench/src/`（门禁核心、后台、窗格中与 T-077 直接相关的部分）、`workbench/tests/`、`workbench/README.md`、本卡证据目录 `evidence/2026-10-11-batch13/T-077/`、ticket T-077 的 Resolution。禁止：`acceptance/test_*.py` 的断言、`scripts/`、spec、地图、全局配置、Synara fork。 |
| 完成条件 | 见 ticket T-077 的 Acceptance，逐条对应，外加本卡下方的条款。 |
| 红态命令 | 每条新行为都要先在起点（main 当前 HEAD）上取得失败，再在候选上通过。 |
| 任务类型 | 后端逻辑 |
| 修复对象 | — |
| 复杂度 | L |
| 执行器 | Codex CLI，`gpt-6-astra`，xhigh，Fast 请求。选用理由：门禁生命周期、并发 CAS、冲突回写与恢复语义交织，属于复杂任务（用户 2026-10-11 规定复杂任务用 astra）。 |
| 起点 | `main` 的 `14b57d22`（worktree 创建时） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s13-t077`），worktree `/Users/luckye/Documents/Code/a2a-wt-t077`，分支 `exec/t077` |

## 先交计划，停下等我
在 `evidence/2026-10-11-batch13/T-077/PLAN.md` 写清楚以下内容：
- 命名与清理表的实现位置；
- 隐藏引用；
- 路径交集的判定方法和“理由”的记录方式；
- 冲突回写的流程（worker 会话已结束时开新 attempt）；
- R8 的计数与沿用审查结论的规则（T-076-2 还没做审查会话，本卡只预留接口，说明怎么衔接）；
- 检出工作区的检查；
- 红态与反例清单；
- 至少一个由真实 Codex 完成冲突整理并重交的场景；
- 真实回合预算（上限 4，用 `gpt-6.1-sol` xhigh Fast 作被测 worker）；
- 需要在沙箱外运行的项。

注意：T-076-1 正在主 checkout 里改 `gates/core.ts`、`daemon.ts`、`panes.ts`。请在 PLAN 里列出你预计会和它冲突的位置。

写完回复 `T-077 PLAN READY`，然后停下等我。

## 审查与交付
- 做一次 fresh-context 只读独立审查。审查发现问题，先取得红态再修，修复部分的 diff 由我审。
- 交付物：分支上的提交（带尾注）、`T-077/RESULTS.md`、ticket Resolution（保持 open）。
- 终端最后一行：`T-077 DONE <PASS|INCOMPLETE|BLOCKED> <exec/t077 的完整提交号>`。
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
- 真实 Codex 调用：/tmp 下隔离 CODEX_HOME，只复制 auth.json，只信任夹具根，只有 git add/commit 两条规则，无 hook，用完删整个 home；启动参数带 `-c 'service_tier="fast"'` 和 `check_for_update_on_startup=false`。turn 数尽量少，实际用量写进 RESULTS。本卡被测 worker 用 `gpt-6.1-sol`，上限 4 个主 turn。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-11-batch13/T-077/`（在你的 worktree 里），中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
- 证据大小：单个证据文件超过 5 MB 的原始输出（大 JSON、trace、tar）不直接提交。要么压缩后提交，要么放外置盘 `/Volumes/WD-Elements/a2a-evidence/<批次>/<票>/` 归档；仓库里只留摘要、重放命令和归档路径。提交前用 `find <证据目录> -size +5M` 检查。
- 需要在沙箱外运行的部分（Unix socket、ps、真实 Codex、Electron、自建进程信号），统一写进本卡的 `outside-sandbox.sh`，然后回复 `T-0xx OUTSIDE-SANDBOX READY` 并停下，由执行主控执行。不要申请提权。
- git 写操作：`git add`、`git commit` 各自单独执行，不和别的命令串联，也不加环境变量前缀。
- 探针或测试本身的错误可以直接修，但要记录；真实的协议失败或产品失败、无法判定的情况、需要改业务断言的情况，都要停下来交给我。
