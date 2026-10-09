# Worker 任务书：T-060 收件箱：ack 是终结（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。只做 T-060（`.project-map/tickets/T-060-inbox-ack-is-terminal.md`，依据 ready_rev 1；T-053 已关闭）。改动在 `scripts/inbox` 与 `acceptance/test_inbox_e2e.py`；不改 `scripts/` 下其他文件（T-054 在改）、不改 fork。参考 T-053 的 RESULTS 与 REVIEW。真实 `.project-map/inbox/` 只读。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 `ready_rev: 1`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch9/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本暂未经 `scripts/dispatch`（T-054 尚未完成），由主控经 Herdr 直接投递。
