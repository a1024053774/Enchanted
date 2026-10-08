---
id: T-041
title: 各 provider 登录方式的条款核实
type: research
status: closed
blocked_by: []
claimed_by: Codex worker T-041 (2026-10-08)
supersedes:
---

## Question

工作台经 Codex app-server、Claude Agent SDK、ACP、OpenCode SDK 运行 agent。逐家核实：自用、本地、开源发布时，使用订阅登录（ChatGPT、Claude.ai 等）是否被条款允许；哪些用法会被视为第三方转发或共享凭据。初步检索（2026-10-07）：Anthropic 不允许第三方产品提供 Claude.ai 登录、要求用 API key；OpenAI 对本地或开源的 app-server 使用 ChatGPT 登录未禁止，但商用或托管不允许。需以官方文档原文为准，并核实 Synara 各 provider 的实际认证路径。

2026-10-08 用户补充：研究 [yetone/magpie](https://github.com/yetone/magpie) 如何接入 Claude，判断它是否比 Synara 现有做法（Claude Agent SDK 启动本机官方 `claude` CLI，`apps/server/src/provider/Layers/ClaudeAdapter.ts`）更合理、能否降低封号风险。要回答：magpie 的实际调用链（是否启动官方 CLI、是否转发或改写请求、凭据如何使用）；与 Anthropic 条款的关系；与 Synara 现有链路的差异；是否值得在 fork 中采用，以及最小接入方式。只做调查，不安装或运行带凭据的 magpie，不改代码。

## Resolution

2026-10-08 worker 研究交付 **PASS，待主控关闭**。保持 `status: open`；本结论不替代独立主控验收或 provider 的发布许可。

- 中文报告：[T-041/REPORT.md](../../evidence/2026-10-08-batch3/T-041/REPORT.md)；固定源码摘录、版本/技能来源和交付检查均在同目录。
- magpie 在外置盘浅克隆，固定为 `de3b1c646afb156b6b35c1dd7a13b5c11187421b`。订阅推理经本机 Claude CLI、stream-json 和 MCP；它还读取、保存和复制订阅凭据。未安装、运行或读取用户凭据。
- 对照 Synara `3566ef4eb34b18c480c7a49e4b5d741681b72426` 的 SDK/CLI、app-server、ACP、OpenCode 及账号环境，建议不移入 magpie 的 Claude 订阅网关（**NO_GO**）；没有封号概率改善证据。
- 初步检索需细化：OpenAI 明确允许现有本地/开源 app-server 认证，商用/托管排除的是该认证方式；Anthropic 有未修改官方 CLI 的有条件路径，不能简化成所有第三方使用一律禁止，也不能凭启动官方 CLI 宣称 Synara 满足例外。
- 事实门 **INCOMPLETE**：Synara 的 Claude SDK 包装/登录及凭据读取边界、Antigravity 普通条款的第三方访问限制、其余 provider 的实际计划/插件/商业合同仍需主控核实。官方链接、核实日、生效/更新日与 unknown 均见报告。无代码修改或外部发布。

**主控关闭（2026-10-08，Claude Code）：研究交付 PASS。** 见 [调研报告](../../evidence/2026-10-08-batch3/T-041/REPORT.md)。结论：不把 magpie 的 Claude 订阅网关并入 fork（NO_GO）——它虽启动本机 `claude`，但作为通用模型网关读取、保存并复制 claude.ai 凭据，而 Anthropic 的 Claude Code Legal and compliance 明确禁止第三方收集、保存或中介 claude.ai 凭据；Synara 现有 Agent SDK 启动本机官方 CLI 的路径更接近官方允许的用法，Claude 优先用用户自己的 API key。Codex 经本机官方 app-server 的本地/开源用法有 OpenAI 明确许可，商用托管除外。Synara 读取凭据文件判断登录状态等细节是否满足 Anthropic 的"未修改 CLI"例外仍为 unknown，未取得 Anthropic 书面说明前不对外承诺订阅用法。

用户决定（2026-10-08）："那就用 Synara 的方式吧"；Synara 读取凭据文件判断登录状态，用户认为没问题（用于读取用量限额）。
