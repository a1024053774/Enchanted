# Worker 任务书：T-059 两个主控进入工作台，端到端跑通（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code）。只做 T-059（`.project-map/tickets/T-059-*.md`，依据 **ready_rev 1**）。这是 spec 第 8 节的 S5，前面 T-055～T-058、T-064 已关闭，见各自的 `RESULTS.md` 与主控决定。

## 范围提醒
- 用户原话："我要的是synara软件层面的，不是让你在Claude code和codex里改权限ok？"——不读写 `~/.claude`、`~/.codex` 或任何 Claude Code / Codex 权限配置。
- ticket 要求"开工前对照 T-055～T-058 的实际结果重读 spec"：不符就停下说明，不绕开。T-064 已把角色能力做成用户级设置，免确认目前只对 Codex、Claude 会话生效。
- 用户亲自试用那一条只由用户勾选，你不勾，也不改 AGENTS.md 的"日常派发"。

## 起点
从 fork `a2a` 分支当前 HEAD（`49cae984f`）开始，在 RESULTS 记下基线。逻辑放 a2a 模块（`packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a`）。需要改别的上游文件时，先停下列出文件、行号和最小改动，等我批准。

## 真实模型调用：两道闸
1. **Claude 主控会话：在第一次真实 Claude 模型调用之前停下。** 两个主控是 Claude 会话，需要真实模型。决定 02 的"假 Messages API"只适用于 T-064 的权限边界，不能用来代替本票的主控行为。先查清并写进 `needs-decision`：隔离的 Synara 实例里 Claude provider 用什么认证（实际读哪里、会不会写 `~/.claude`），有哪些不碰用户 Claude 配置的做法，本票端到端预计需要多少个 Claude turn。只做查文档、类型定义和不调用模型的探针。认证与预算由用户决定，我经构思主控转达。
2. **Codex worker：** 按 AGENTS.md 的隔离 CODEX_HOME 规则（/tmp 下，只复制 auth.json，只有 git add/commit 两条规则，无 hook，用完删整个 home；Synara 的 native home 也必须在 /tmp，见 T-064 的 `isolation-correction-53.md`）。预算先报，同样等批准后再跑。

闸前能做的：红态（父修订不能用预设建出这两个会话，端到端脚本失败）、"控制"任务和两个角色会话的预设与角色卡注入、任务窗口显示角色、端到端驱动脚本、失败方式清单的处理设计，以及所有不需要模型的部分。

## 要做（闸后）
按 Acceptance 逐条做：一次完整的分发→执行→汇报，转述的状态逐字、不上调；两个问题（一个关闭附理由、一个"等你决定"由测试驱动者答复后打包送回 worker）；三种紧急停止各一次，其中 `a2a:stop` 用 2 分钟放行且只中断；真实模型调用次数和用量写进 RESULTS。失败方式清单逐条写处理方式。面板截图作证，外观由用户判断。经工作台门禁的真实派发本票明确要求，可用；只操作你自建的隔离实例。

## 独立审查
- 冻结候选 = fork 提交 + 你的 a2a 证据提交。审查请求写明：审查者**不得读** `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文、旧审查；只读 ticket 的 What/Acceptance/说明、spec 相关章节、diff、截图、原始机械输出和重放命令。`evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控持续追加的日志，不属于候选。
- 审查一次。FAIL 时修复后不自行追审，交 INCOMPLETE，我审修复 diff。

## 交付
Herdr 期：fork 提交 + a2a 证据提交 + `T-059/RESULTS.md` + ticket Resolution（保持 open，写"待主控关闭"）+ 终端一行 `T-059 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。不走门禁 submit。用户试用那一条不勾，所以整票最多交到"除用户试用外通过"。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
