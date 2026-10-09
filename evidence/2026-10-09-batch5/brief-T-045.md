# Worker 任务书：T-045 工作台"用量与限额"显示失败（build）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-045（`.project-map/tickets/T-045-usage-limits-display.md`，验收以它为准）。

## 先读
a2a：`AGENTS.md`、T-045、T-041 报告中 S2–S5（Synara 读取凭据的方式）。fork：`apps/server/src/providerUsage/`（`providers/codex.ts`、Claude 对应文件、`http.ts`、`rateLimitResilience.ts`）、`a2a/WORKBENCH.md`、`a2a/scripts/workbench`。

## 范围与安全（务必遵守）
- 工作区：主控已建 worktree `~/Documents/Code/synara-t045`（分支 `a2a-t045`，起点 `28e2f1b`）；先经 `a2a/scripts/bun install --frozen-lockfile` 安装依赖（缓存在外置盘）。不要动 `~/Documents/Code/synara`（T-044 在用）。不 push。
- 用户的正式工作台正在运行。你可以**只读**它的日志与状态（`~/Library/Application Support/a2a-workbench/userdata/logs`、`provider-status/`、`workbench-launch.log`），不得停止、重启它，不得改它的设置或数据库，不得读取或复制 `secrets/`、endpoint token。
- 凭据：可以只读地确认 `~/.codex/auth.json`、`~/.claude` 凭据**是否存在、结构字段名、过期时间**，不得把 token 内容写进证据、日志或终端输出。任何可能兑换 refresh token 或写回凭据的代码路径（例如 usage fetch 遇 401 后的刷新）都不能用真实凭据运行；需要真实请求验证时先停下问主控。
- 不调用模型。严禁移动、替换或链接构建输出与依赖目录。

## 要做的
1. 定位"Could not reach the … usage endpoint"的真实异常：从源码追到抛出点，判断是工作台启动环境（例如 HOME、PATH、代理、钥匙串访问、Electron 子进程环境）、凭据读取、网络还是上游缺陷；Codex、Claude、Cursor 是否同一原因。用不含真实凭据的复现（例如假的 auth 文件加本地 mock 服务器）证明异常路径；日志里看不到细节的原因也要查明。
2. 给出最小修复（优先修工作台启动器或 a2a 自己的代码；必须改上游 providerUsage 时列清单，按"通用修复"整理成独立提交）。先红后绿。
3. 正式工作台中的最终显示由主控在合并后重启工作台时让用户确认；你只交付修复与离线证据。

## 交付
证据 `evidence/2026-10-09-batch5/T-045/`，中文 `RESULTS.md`；fork 在 `a2a-t045` 分支提交；a2a 只提交你的证据与 T-045 Resolution（保持 open）。最后终端回复一行：`T-045 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。需要决定的事停下说明。
