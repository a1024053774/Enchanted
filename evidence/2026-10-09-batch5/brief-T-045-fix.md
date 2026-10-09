# Worker 任务书：T-045 修复（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-045 的修复，规则以 `evidence/2026-10-09-batch5/T-045/controller-decision-01.md` 为准；诊断已在 `evidence/2026-10-09-batch5/T-045/RESULTS.md` 完成，复用其离线复现夹具（`offline-red-*`、`raw-boundary-*`）。

- 工作区：`~/Documents/Code/synara-t045`（分支 `a2a-t045`，依赖已装）。不动 `~/Documents/Code/synara`，不碰正式工作台及其数据、`~/.codex`、`~/.claude` 凭据，不发真实网络请求，不 push。严禁移动、替换或链接构建输出与依赖目录。
- 预算紧张：只读必要文件，只跑相关测试与离线复现。
- 交付：证据追加到 `evidence/2026-10-09-batch5/T-045/fix/`，中文 `RESULTS.md`（改动清单、红绿、反例、上游文件清单）；fork 在 `a2a-t045` 独立提交；a2a 只提交你的证据与 T-045 Resolution（保持 open）。最后终端回复一行：`T-045 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。需要决定的事停下说明。
