# Worker 任务书：T-054 派发包装、派发日志与会话副本（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。只做 T-054（`.project-map/tickets/T-054-dispatch-wrapper-and-session-copy.md`，依据 ready_rev 1）。改动在 a2a 仓库 `scripts/`、测试与 `.gitignore`；不改 fork，不改 `scripts/inbox`（T-060 在改）。
- 测 `dispatch` 只用明确标注的 `herdr` 替身（PATH 前置的假命令）；不得对用户的 Herdr server 或任何真实 pane 发送内容。"下一次真实派发用包装发出首条提示词"这一项由执行主控在你交付后亲自完成，你只需在 RESULTS 写清用法。
- `session-copy` 的真实会话文件只读复制；查明 Codex 原生会话文件的定位方式（`herdr agent get` 输出、Codex 会话目录），不凭记忆写死；Claude 对话文件在 `~/.claude/projects/<项目目录>/<会话 id>.jsonl`。不读取或输出其中的内容。
- 权限规则建议只写成文件，不修改任何 Claude Code 设置。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 `ready_rev: 1`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch9/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本暂未经 `scripts/dispatch`（T-054 尚未完成），由主控经 Herdr 直接投递。
