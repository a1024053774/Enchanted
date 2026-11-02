---
id: T-239
title: 后台重启后，历史窗格报 TextDecoder 解码错误并显示“窗格未连接”
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---
## What to build

2026-11-02 T-237 的 Computer Use 复验（[报告](../../evidence/2026-11-02-batch30/cu-fixcheck-r2/REPORT.md) 场景三）范围外发现：打包应用（`a2a-build-t236-tcc2`，工作区代码）在“从菜单退出、结束后台与 core、重新启动”之后，原来的历史窗格显示 `TypeError: Failed to execute 'decode' on 'TextDecoder': The encoded data was not valid.` 和“窗格未连接”；切到新终端后显示“后台已连接”。没有截图，原因未查。

推测（未核实）：窗格输出的 UTF-8 多字节字符被截断在分块边界，界面用 `fatal` 模式的 `TextDecoder` 一次性解码时出错；或重启后读到的历史字节本身不完整。要先复现，再查是哪一层。

## Acceptance

- [ ] 先写下可能出错的方式。
- [ ] 修前红态：经真实入口复现这条错误，记下触发它的输出字节。
- [ ] 修后：同一场景历史窗格正常显示（或明确提示历史不完整），不再报解码错误。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

（未开始）
