# Worker 任务书：T-047 门禁 CLI 经 HTTP 调用 run 时提前超时（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-047（`.project-map/tickets/T-047-gate-run-http-timeout.md`）。
工作区：worktree `~/Documents/Code/synara-t045`（依赖已装）。先在其中执行 `git switch -c a2a-t047 09fc57f8a67ea2a1ed70397c04e49e9bb4849a5b`（该 worktree 原分支 a2a-t045 已合并，工作树应干净；不干净则停下问主控）。不要动 `~/Documents/Code/synara`（T-048 在用）。
复现材料：`evidence/2026-10-09-batch6/T-046/run-stderr.txt`、`run-started.txt`/`run-ended.txt`、`events-final.json`（含控制字符）。复现超时请用你自己启动的隔离服务端与受控夹具（参照 T-037/T-044 的 thread 边界替身），不要用正式工作台。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、你的 ticket，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 正式工作台在运行（用户数据在 `~/Library/Application Support/a2a-workbench`）：不得停止、重启、读写它的数据或 endpoint/token；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或任何改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 `a2a/scripts/bun`。界面或真实服务验证用隔离实例（外置盘数据目录、provider 关闭）。
- 不调用模型，不改用户 `~/.codex`、`~/.claude`，不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket，不来自实现输出；失败原样保留。只跑与改动相关的测试，不跑全仓（额度紧张）。
- 证据放 `evidence/2026-10-09-batch7/T-04x/`，中文 `RESULTS.md`；a2a 只提交你的证据与 ticket Resolution（保持 open，写"待主控关闭"）。最后终端回复一行：`T-04x DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。需要决定的事停下说明，完成前不要结束回合。
