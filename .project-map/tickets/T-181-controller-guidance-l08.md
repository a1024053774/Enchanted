---
id: T-181
title: L08/L09：主控用问答框代替角色申请、找不到 a2a 入口、写死主仓库路径、长轮询；问答框正文空白
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：findings/2026-10-25-lcu-real-use.md；用户 2026-10-24 逐字：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

现象见报告 L08、L09（模型行为为主，不归协调缺陷）。目标：提示词管判断——Enchanted 插件给项目终端里的 CLI 提供的说明（skill/role）明确：做主控时直接 `a2a request <角色>`，不用问答框代替；`a2a help` 可发现；验收脚本只用当前工作目录相对路径；交付后等门禁通知而不是循环轮询（若已有通知通道，说明里写清）；并行任务共享的约定（如输出格式）在派发前写进两张卡。L09：核对 AskUserQuestion 正文为何空白（渲染或宽度），能修则修。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [x] 用真实 haiku 主控复跑报告同一句请求：直接执行 a2a request；验收脚本无绝对路径；无长轮询。
- [x] L09 复现与结论。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch25/T-181/RESULTS.md)。L09：问答框正文是 Claude Code 按深色背景写的 256 色 231 纯白，落在浅色终端上看不见（PTY 与缓冲区都有，渲染层问题）；终端加 minimumContrastRatio 4.5，修前问题行深色像素 32/0，修后 12004/866。L08：实测 Haiku 没有加载 a2a skill；插件加 SessionStart 钩子（a2a session-context）开局告诉它 a2a 在 PATH、a2a help、当主控直接 a2a request 不用问答框、先读 skill；SKILL 补相对路径、不写 sleep 轮询（run 放后台）、并行卡写共用约定。真实 haiku 复跑 L08 原句（1 个根提示）：直接 a2a request、不搜入口、验收脚本无绝对路径、无 sleep 轮询、不问分支直接派出两张卡，全部通过；haiku 写的 README 验收只查关键字未查约定格式（模型行为，已记录）。复跑发现 T-180 缺陷，另建 T-183 修复。agy 审查两轮，第二轮 PASS。
