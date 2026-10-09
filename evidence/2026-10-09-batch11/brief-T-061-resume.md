# Worker 任务书：T-061 恢复（ready_rev 2）
你是 a2a 的 worker（Codex）。主控是执行主控（Claude Code，Herdr pane wF:pM）。接手 T-061（`.project-map/tickets/T-061-native-prompt-digit-tool-names.md`，**依据 ready_rev 2**：第 3 项已改为"其余 113 个工具前后逐项一致，已在目录中的 `synara_e2e_review` 同样修复并补红绿"；用户逐字"T-056 同意 T-061 选 1"）。
- 上一位 worker 已保留红态与目录探针：先读 `evidence/2026-10-09-batch11/T-061/RESULTS.md`、`decision-needed.md`、`catalog-baseline.json`、`native-catalog-probe.ts`、`run-check.py`。新证据追加在同一目录，旧文件不覆盖。
- 工作区：worktree `~/Documents/Code/synara-t045`，分支 `a2a-t061`（当前 `1ec64d8`，红态测试快照）。在其上实现解析修复；不要动 `~/Documents/Code/synara`（T-056 在用）。
- 只改该解析与其测试；免确认范围仍只由网关工具名目录决定。补 `synara_e2e_review` 的红绿；修复后用同一探针给出 116 个工具前后对照表。
- Herdr 期交付：提交、RESULTS、终端 DONE 行，不走门禁 submit。不需要真实模型调用。
## 共同规则
- 先读 a2a 的 `AGENTS.md`（含"构思主控与执行主控"一节）、`CONTEXT.md`、你的 ticket（验收以它为准，依据 `ready_rev: 1`）、`.project-map/specs/controller-split-user-input-2026-10-09.md` 中 ticket 指向的章节，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 发现 spec 与已建成的行为不符：停下，向主控说明（主控写 needs-decision），不绕开。
- 正式工作台在运行：不得停止、重启、读写 `~/Library/Application Support/a2a-workbench`；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 fork 的 `a2a/scripts/bun`。不碰用户 Herdr、`~/.codex`、`~/.claude`。不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；额度紧，只跑相关测试。不用正则或关键词规则判断内容含义。
- 证据 `evidence/2026-10-09-batch11/T-0xx/`，中文 `RESULTS.md`；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）；fresh-context 只读独立审查一次。最后终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit 或 none>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有该标记的输入来自用户本人。
