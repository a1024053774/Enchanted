---
id: T-041
title: 各 provider 登录方式的条款核实
type: research
status: open
blocked_by: []
claimed_by:
supersedes:
---

## Question

工作台经 Codex app-server、Claude Agent SDK、ACP、OpenCode SDK 运行 agent。逐家核实：自用、本地、开源发布时，使用订阅登录（ChatGPT、Claude.ai 等）是否被条款允许；哪些用法会被视为第三方转发或共享凭据。初步检索（2026-10-07）：Anthropic 不允许第三方产品提供 Claude.ai 登录、要求用 API key；OpenAI 对本地或开源的 app-server 使用 ChatGPT 登录未禁止，但商用或托管不允许。需以官方文档原文为准，并核实 Synara 各 provider 的实际认证路径。

2026-10-08 用户补充：研究 [yetone/magpie](https://github.com/yetone/magpie) 如何接入 Claude，判断它是否比 Synara 现有做法（Claude Agent SDK 启动本机官方 `claude` CLI，`apps/server/src/provider/Layers/ClaudeAdapter.ts`）更合理、能否降低封号风险。要回答：magpie 的实际调用链（是否启动官方 CLI、是否转发或改写请求、凭据如何使用）；与 Anthropic 条款的关系；与 Synara 现有链路的差异；是否值得在 fork 中采用，以及最小接入方式。只做调查，不安装或运行带凭据的 magpie，不改代码。

## Resolution
