---
id: T-030
title: 工作台改为基于 Synara 的 fork
type: decide
status: superseded
blocked_by: []
claimed_by:
supersedes: T-017
---

## Question

第二阶段的工作台用什么底座、代码放在哪里、怎么跟进上游？

## Resolution

2026-10-07 grilling 确认（[ledger](../../.grilling/synara-fork.md) 的 C1、D1～D4、D8）。用户原话："咱们从0做UI还是不现实，简直灾难。所以咱们复用https://github.com/Emanuele-web04/synara的仓库吧"。

- 底座：fork Synara（MIT），GitHub `a1024053774/synara`，起点 v1.0.1-beta.2，单独 clone，不放进 a2a 仓库。
- agent 以 Synara 的原生协议会话为主（Codex app-server、Claude Agent SDK、ACP、OpenCode SDK），终端为辅。
- 持续跟进上游：我们的功能做成独立 package 或模块，对核心只做少量接入，通用修复回馈作者。
- 构建：checkout 放内置盘，Bun 全局缓存与 Electron 下载放外置盘，缺盘即报错；首个任务实测占用与耗时。

取代 T-017（Herdr 引擎硬分叉 + GPUI）与 T-022（Muster 名称与"代码在 a2a 文件夹下"）。被否决：Synara 界面 + Muster 引擎（两套运行模型，改动最深）；只用 Synara 终端（放弃其核心价值）；硬分叉 Synara（其迭代极快，会迅速落后）。

2026-10-10 由 [T-069](T-069-third-stage-direction.md) 取代：工作台改为本仓库里的轻量应用，fork 只作组件来源，不再跟进上游。
