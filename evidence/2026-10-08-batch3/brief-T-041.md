# Worker 任务书：T-041 provider 登录条款与 magpie 调研（research）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-041（`.project-map/tickets/T-041-provider-auth-policy.md`，问题以它为准，含 2026-10-08 的 magpie 补充）。

## 先读
- a2a：`AGENTS.md`、`CONTEXT.md`、T-041。
- fork `~/Documents/Code/synara`（只读）：`apps/server/src/provider/Layers/ClaudeAdapter.ts`（Claude Agent SDK、`pathToClaudeCodeExecutable`）、`CodexAdapter.ts`（Codex app-server）、ACP 与 OpenCode 的 adapter，以及它们的认证与 CODEX_HOME overlay 处理。

## 要做的
1. magpie（https://github.com/yetone/magpie）：在外置盘临时目录浅克隆源码只读阅读（`/Volumes/WD-Elements/dev-cache/` 下新目录），画出它接入 Claude 的实际调用链：是否启动官方 `claude` CLI，是否经本地代理转发或改写请求、改写 headers/UA/系统提示，凭据从哪来、如何保存与使用。每条结论标注 observed（附文件与行号）/ inferred / unknown。
2. 对照 Synara 现有链路（同样标注证据），说明二者差异，以及哪一种更接近各家官方允许的用法。
3. 条款：以官方原文为准，核实 Anthropic（Claude Agent SDK、claude.ai 订阅登录用于第三方或自用工具）、OpenAI（Codex app-server、ChatGPT 登录），以及 ACP、OpenCode 涉及的 provider。区分"自用本地""开源发布""商用托管"。引用原文链接与日期；查不到的写 unknown。
4. 结论：magpie 的做法是否值得在 fork 中采用；若值得，给最小接入方式与风险；若不值得，说明理由。不要把"降低被检测概率"当作合规理由——判断标准是条款是否允许。

## 禁止
- 不安装或运行带凭据的 magpie，不读取用户 `~/.claude`、`~/.codex` 的凭据，不发送任何请求到模型 API。不改 fork 或 a2a 的代码。不 push。

## 交付
- 中文报告 `evidence/2026-10-08-batch3/T-041/REPORT.md`，ticket 写 Resolution（保持 open，写"待主控关闭"）。只提交你的文件。最后终端回复一行：`T-041 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。遇到权限请求或需要用户决定的事，停下说明。
