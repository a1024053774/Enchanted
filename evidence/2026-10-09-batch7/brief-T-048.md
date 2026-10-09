# Worker 任务书：T-048 门禁自动建项目的标题与启动器身份格式（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-048（`.project-map/tickets/T-048-project-title-and-legacy-identity.md`，含主控补充）。
工作区：`~/Documents/Code/synara`，分支 `a2a`（当前 `09fc57f8`）。不要动 `~/Documents/Code/synara-t045`（T-047 在用）。
- 项目标题：`apps/server/src/a2a/service.ts:101` 写死 "a2a pagination"。若需要在 create 请求中新增字段，改 `packages/contracts/src/a2aGates.ts` 并保持现有字段兼容。
- 启动器：写入侧 `a2a/scripts/launch-workbench.mjs` 与读取侧 `a2a/scripts/workbench_runtime.py` 统一为 locale 无关格式；删除 T-046 加的遍历 locale 兼容分支，保留对其他进程记录的拒绝与已退出进程的"未运行"。删除兼容分支后正在运行的工作台（旧格式记录）将无法被新代码识别——这由主控在合并时先停后合处理，你不要停止或重启正式工作台。更新 `acceptance/workbench_identity_oracle.py` 的用例时，说明旧格式用例为何改变；新增"写入侧在不同 locale 下产生的记录可被读取"的用例（用临时数据目录和受控子进程模拟写入，不启动 Electron）。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、你的 ticket，以及 fork 的 `AGENTS.md`、`CLAUDE.md`、`a2a/WORKBENCH.md`。
- 正式工作台在运行（用户数据在 `~/Library/Application Support/a2a-workbench`）：不得停止、重启、读写它的数据或 endpoint/token；不得在 `~/Documents/Code/synara` 运行 `build:desktop` 或任何改写 `apps/*/dist` 的命令。严禁移动、替换或链接构建输出与依赖目录。Bun/Node 只经 `a2a/scripts/bun`。界面或真实服务验证用隔离实例（外置盘数据目录、provider 关闭）。
- 不调用模型，不改用户 `~/.codex`、`~/.claude`，不 push。只停你启动的进程，只删你创建的文件。
- 先红后绿；预期来自 ticket，不来自实现输出；失败原样保留。只跑与改动相关的测试，不跑全仓（额度紧张）。
- 证据放 `evidence/2026-10-09-batch7/T-04x/`，中文 `RESULTS.md`；a2a 只提交你的证据与 ticket Resolution（保持 open，写"待主控关闭"）。最后终端回复一行：`T-04x DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。需要决定的事停下说明，完成前不要结束回合。
