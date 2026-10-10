# Worker 任务书：T-066 紧急停止的核心记录写实际调用者（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code）。只做 T-066（`.project-map/tickets/T-066-*.md`，依据 **ready_rev 1**）。用户原话见 ticket："你建议改的一处我同意"。

## 起点
- fork `a2a` 分支 HEAD `49cae984f`，在 RESULTS 记下基线。背景：T-064 的 `49cae984f` 让 `apps/server/src/a2a/tools.ts` 里的 a2a_stop 以 `address: "ideation"` 调用核心，避免 operate 能力遮蔽 stop；核心事件 `emergency_interrupt_requested`（`packages/a2a-gates/src/core.ts` 约 1701 行）只存 stop_id、目标 thread、actor。证据：`evidence/2026-10-09-batch11/T-064/codex-good44-real/stop-address-record.json`、`cap-composition-*`。
- 改动应只在 `packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a`。需要别的上游文件时，先停下列出文件、行号和最小改动，等我批准。
- 核心的 stop 放行条件（stop 条目超过 2 分钟无 ack、只中断）不变。stop 的授权来自凭据里的 `a2a:stop` 能力，记录里的地址写实际角色；不要再靠伪装成 ideation 地址来过检查。若核心某处确实依赖"只有 ideation 地址才能 stop"，把它改成看 stop 能力，并在 RESULTS 说明。

## 模型调用
本票不需要真实模型 turn：调用者和目标都可以用真实服务端、真实 MCP、真实核心 SQLite，再加受控的活跃事实。如果你认为必须要真实 provider，先停下说明理由和 turn 数，等我批准。

## 要做
按 Acceptance 逐条做：在 `49cae984f` 上先取得红态（执行主控被授予 stop 后调用，核心记录地址为 ideation、没有调用者 thread）；修复后地址为实际角色并带调用者 thread/turn，目标 thread 不变，构思主控自己的 stop 记录不变；参数里伪造调用者身份被忽略；既有 stop 用例照常通过；旧事件不改写，读取端对缺字段的旧事件显示"未记录"。失败方式清单逐条写处理方式。

## 独立审查
- 冻结候选 = fork 提交 + 你的 a2a 证据提交。审查请求写明：审查者**不得读** `RESULTS*.md`、ticket 的 Resolution、inbox 条目正文、旧审查；只读 ticket 的 What/Acceptance/说明、diff、原始机械输出和重放命令。`evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是主控持续追加的日志，不属于候选。
- 审查一次。FAIL 时修复后不自行追审，交 INCOMPLETE，我审修复 diff。

## 交付
Herdr 期：fork 提交 + a2a 证据提交 + `T-066/RESULTS.md` + ticket Resolution（保持 open，写"待主控关闭"）+ 终端一行 `T-066 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。不走门禁 submit。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
