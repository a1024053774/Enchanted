---
id: T-181
title: L08/L09：主控用问答框代替角色申请、找不到 a2a 入口、写死主仓库路径、长轮询；问答框正文空白
type: build
status: open
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

- [ ] 用真实 haiku 主控复跑报告同一句请求：直接执行 a2a request；验收脚本无绝对路径；无长轮询。
- [ ] L09 复现与结论。

## 不做

范围外的问题经问题上报，不顺手改。
