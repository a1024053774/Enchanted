## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、你的 ticket，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 正式工作台在运行（用户数据在 `~/Library/Application Support/a2a-workbench`）：不得停止、重启、读写它的数据或 endpoint/token；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或任何改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 `a2a/scripts/bun`。界面或真实服务验证用隔离实例（外置盘数据目录、provider 关闭）。
- 不调用模型，不改用户 `~/.codex`、`~/.claude`，不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket，不来自实现输出；失败原样保留。只跑与改动相关的测试，不跑全仓（额度紧张）。
- 证据放 `evidence/2026-10-09-batch7/T-04x/`，中文 `RESULTS.md`；a2a 只提交你的证据与 ticket Resolution（保持 open，写"待主控关闭"）。最后终端回复一行：`T-04x DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。需要决定的事停下说明，完成前不要结束回合。
