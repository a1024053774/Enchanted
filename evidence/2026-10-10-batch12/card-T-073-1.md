# 任务卡 T-073-1

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-073-1 |
| 来源 | ticket T-073，`ready_rev: 1` |
| 目标 | Herdr 期用上三样：任务卡 markdown 模板；经新启动入口起的 worker，提交自动带 `A2A-*` 尾注；验收打分写进追加式文件。做完后，执行主控能用模板写卡、用新入口起 worker，worker 的每个提交都看得出任务、会话和执行器，每次验收留下一行打分。 |
| 非目标 | 不写任务卡的生成或校验脚本（D31）；不改角色卡、不改 AGENTS.md 里的规则（只改指向模板的路径，规则交构思主控）；不碰 Synara fork；不做编排后台和数据库（S1）。 |
| 修改边界 | 允许：`scripts/dispatch`；`scripts/` 下新增的启动脚本、打分脚本和钩子目录（建议 `scripts/git-hooks/`）；`.project-map/templates/task-card.md`；`records/`（新目录，放 Herdr 期的启动记录 `records/launches.jsonl` 和打分 `records/scores.jsonl`）；`acceptance/` 下相关测试；`AGENTS.md`、`.project-map/roles/` 里指向任务卡的路径；本卡证据目录。禁止：`~/.codex`、`~/.claude`、全局或仓库级 git 配置、用户的 Herdr server 设置、`.project-map/specs/`。 |
| 完成条件 | 见下方"完成条件"。 |
| 红态命令 | 在当前 `main` 上用现有方式（`herdr agent start --kind codex`）起一个 Codex worker，在夹具仓库提交一次，然后执行 `git -C <夹具仓库> log -1 --format=%B`，输出里没有 `A2A-` 开头的行。 |
| 任务类型 | 构建与基础设施 |
| 修复对象 | — |
| 复杂度 | M |
| 执行器 | Codex CLI，`gpt-6.1-sol`，xhigh，Fast 请求 |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s12-t073`） |

## 启动入口由我定
- 新建 `scripts/launch-worker`。它负责：建一个 Herdr pane，在 pane 的 shell 里设置 spec 第 5 节的环境变量（项目、任务、attempt、会话、角色、启动记录号）和 `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0`（`core.hooksPath` 指向 `scripts/git-hooks/`），再用 `herdr agent start` 起 CLI。启动参数整串、CLI 版本、模型、强度、角色、项目提交号写一条启动记录到 `records/launches.jsonl`，尾注里只写记录号。
- `scripts/dispatch` 仍然只负责发文本；如需改它（例如校验 agent 由新入口起），在 RESULTS 写理由。
- Codex 默认会滤掉名字里带 KEY/SECRET/TOKEN 的环境变量。用每会话的 `-c shell_environment_policy...` 启动参数放行，不写 `~/.codex`，并用红绿证明确实需要、确实有效。
- 钩子用 `prepare-commit-msg` 追加尾注（`--no-verify` 时照样追加），然后调用项目原有的钩子：原钩子失败就传出失败，项目没有原钩子就跳过。
- 如果你在 Codex 沙箱里调用 `herdr` 被拦住，停下告诉我，由我在外面执行你写好的启动命令，不要绕开沙箱。

## 完成条件（我写好的，交付前跑一遍并保存输出）
1. `git -C <夹具仓库> log -1 --format=%B | grep -E '^A2A-(Task|Attempt|Session|Role|Tool|Model|Effort|Native-Session|Launch):' | wc -l` 输出 9；`A2A-Launch` 的值在 `records/launches.jsonl` 里能找到，并且其它尾注的值与那条记录一致。
2. 同一会话用 `git commit --no-verify` 再提交一次，第 1 条照样成立；夹具仓库原有钩子留下的痕迹文件多了一行。
3. 不经新入口、直接在普通终端里提交：没有 `A2A-` 行，也不报错。
4. 打分：用打分脚本写一行后读回，字段齐全（spec 第 8 节打分表）；缺执行主控必填项时退出码非 0、文件不变；"放弃"只有结果和理由。
5. `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a` 没有 problems。

ticket 里的失败方式清单逐条写进 RESULTS 的处理方式。真实 Codex worker 用隔离 CODEX_HOME（见共同规则），turn 数尽量少。

## 交付
a2a 提交 + `T-073/RESULTS.md` + ticket Resolution（保持 open，写"待主控关闭"）+ 终端一行 `T-073 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。交付前做一次 fresh-context 只读独立审查：审查者不得读 `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文；只读 ticket 的 What/Acceptance/说明、本卡、diff、原始输出和重放命令。`evidence/2026-10-10-batch12/` 下的 `controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控日志，不属于候选。只审一次；FAIL 时修好后不再追审，交 INCOMPLETE，由我审修复的 diff。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 真实 Codex 调用：/tmp 下隔离 CODEX_HOME，只复制 auth.json，只信任夹具根，只有 git add/commit 两条规则，无 hook，用完删整个 home；启动参数带 `-c 'service_tier="fast"'` 和 `check_for_update_on_startup=false`。turn 数尽量少，实际用量写进 RESULTS。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放本批目录 `evidence/2026-10-10-batch12/T-0xx/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
