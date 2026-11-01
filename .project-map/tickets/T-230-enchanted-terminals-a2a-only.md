---
id: T-230
title: Enchanted 终端里不带私有 core 地址，终端之间只经 a2a 命令；inexact 窗格提示“历史不完整”
type: build
status: open
blocked_by: [T-228]
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

T-220 的决定（用户 2026-11-01：“确认”）：Enchanted 终端里只用 a2a 命令，a2a 命令建在 hc 上，身份取终端令牌。agent 若用裸 hc 往别的终端发字，后台没有记录，那段文字会被记成用户输入；终端里的 hc 调用还能在 core 崩溃后抢先拉起外来 core（T-220 第 2、3 点）。

- 项目终端启动时去掉 `HC_SOCKET`、`HC_SESSION`、`HC_TERMINAL_ID`、`HC_TERMINAL_SOCKET`，做法同现在去掉 XDG 变量（`/usr/bin/env -u`）。编排后台与私有 core 仍用受控环境。
- 终端里敲 `hc` 用的是用户自己的 hc 设置，看不到 Enchanted 的终端；这是已接受的代价，不另做兼容。
- 终端之间发字、查看，都经 a2a 命令走后台，后台留记录（T-216 的派发与认领规则）。
- 标 inexact 的窗格在界面上显示“历史不完整”；后台对 inexact 屏幕照常复位并接回，不改。

依赖 T-228：先让后台按身份认 core、能接回 holder 重拉的 core。

## Acceptance

- [ ] 先写下可能出错的方式，测试对着它写。
- [ ] 修前经真实入口留下红态：项目终端里读到私有 core 的 `HC_SESSION`、`HC_SOCKET`（`test_t212_hc_boundaries_e2e.py` 现在断言二者等于私有身份，第 134–135 行）；core 被杀后，终端里的 `hc` 调用拉起外来 core（T-220 run-01 的情形）。
- [ ] 修后：终端里四个 `HC_*` 变量都不存在；core 被杀后终端里的 `hc` 调用不碰私有 core，后台或 holder 按受控环境接回，原终端还在。T-212 边界测试的这两行改成断言不存在。
- [ ] 经 a2a 命令从一个终端往另一个终端发字，后台有记录，目标终端的提交不记为用户输入。
- [ ] 标 inexact 的窗格在界面上显示“历史不完整”（截图留证），复位与接回行为不变。
- [ ] T-212、T-216 的既有 e2e 仍通过。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## 不做

改 hc 源码；改用户自己的 hc 设置；崩溃后自动续跑 agent 回合。

## Resolution

（未开始）
