# Worker 任务书：T-056 用户输入记录覆盖全部范围，观察器改名（build）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。只做 T-056（`.project-map/tickets/T-056-user-input-coverage.md`，依据 ready_rev 1）。开工前按 ticket 说明对照 T-055 的实际结果（`evidence/2026-10-09-batch8/T-055/RESULTS-03.md`、`acceptance-review-final.md`）重读 spec 第 3 节，不符就停下说明。
- fork `~/Documents/Code/synara`，分支 `a2a`（当前 `2330534`）。改动以 `packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a` 为主；ticket 要求的 WS RPC `dispatchCommand` 观测点若在这些目录外，先停下说明位置与最小接入，主控批准后再改。不要动 `~/Documents/Code/synara-t045`（T-061 在用）。
- 迁移只在旧格式夹具库的副本上验证；绝不读写正式工作台数据目录。
- 真实 Codex 只有在覆盖矩阵确实需要真实 provider 事件（例如 Codex 异步提问）时才用，遵守隔离 CODEX_HOME 规则，turn 尽量少。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 `ready_rev: 1`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
