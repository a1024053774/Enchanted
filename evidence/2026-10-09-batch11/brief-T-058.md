# Worker 任务书：T-058 服务端收件箱、能力预设与写条目即唤醒（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。只做 T-058（`.project-map/tickets/T-058-server-inbox-capabilities-wake.md`，依据 ready_rev 1）。开工前按 ticket 说明对照 T-055、T-056、T-057 的实际结果（`evidence/2026-10-09-batch8/T-055/RESULTS-03.md`、`evidence/2026-10-09-batch11/T-056/RESULTS-05.md`、`evidence/2026-10-09-batch11/T-057/RESULTS-02.md`）重读 spec 第 1、5 节，不符就停下说明。
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `e9545960c`，含 T-056、T-057 冻结候选、T-061）。改动以 `packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a` 为主。已知需要的上游接入：`apps/server/src/agentGateway/Layers/AgentGateway.ts`（注册工具，T-055/T-057 已有同类先例）。凭据/能力相关的其他上游文件（例如能力预设落在 Synara 凭据签发处）先停下说明位置与最小接入，主控批准后再改。**不改 `computerToolPermission.ts`**（免确认目录变更未获用户授权）。
- 收件箱的 Herdr 期参照实现是本仓库 `scripts/inbox` 与 `acceptance/test_inbox_e2e.py`（含 T-060：ack 是终结，blocking 问题只能由 sender=user 关闭）；服务端行为与之一致，字段同 spec 第 5 节。不迁移旧文件条目，不读写真实 `.project-map/inbox/`。
- T-057 冻结的问题处置里，已结束会话的 `forward/session-ended` 发给 executor；本票的服务端收件箱建成后，补一条证据：该转交在 executor 的未确认列表中可见（这是 T-057 留给本票的边界，等用户最终确认，先做不影响）。
- 写条目即唤醒、`a2a:stop` 用真实服务与受控会话验证；真实 Codex 只在确实需要真实 turn 时用（唤醒起新 turn 一项可能需要），遵守隔离 CODEX_HOME 规则，turn 尽量少。
- Herdr 期交付：fork 提交 + a2a 证据提交 + RESULTS + 终端 DONE 行，不走门禁 submit，不需要 attempt/session/fence。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准）、spec 中 ticket 指向的章节、`.project-map/roles/`，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-058/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。若审查 FAIL：修复后不自行追审，交付 INCOMPLETE 由主控决定。最后终端回复一行：`T-058 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
