---
id: T-102
title: 工作台打包成可双击的 macOS 应用并安装到 /Applications
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

用户 2026-10-19 说（逐字，会话"a2a-构思主控"）："打包吧,打完包我在体验"，并要求把软件放到 `/Applications`。

现状：`workbench/` 是开发式启动（`npm start` 需 `--build`、`--task`，编排后台要另起，构建输出在外置盘），不能直接拷贝成应用。

做一个**最小**可用的打包，按 tracer bullet：先打通"双击 → 起编排后台 → 进入界面 → 能选项目和任务 → 能开一个窗格里跑 zsh"，再扩。

1. 选打包工具前先看 `workbench/package.json` 已有依赖和 electron 43 的文档；评估 `@electron/packager` 与 electron-builder，选改动最小的。node-pty 原生模块要为打包后的 Electron 重建并签名可运行（本机自用，ad-hoc 签名即可，不做公证）。
2. 启动入口：双击时自动起编排后台（常驻，界面关掉不影响 agent），缺省 `--task` 时进入项目/任务选择，不再要求命令行参数。数据目录放内置盘（沿用现有约定）。
3. 构建缓存与 Electron 下载放外置盘（AGENTS 构建约束）；产物 `.app` 本身装到 `/Applications/a2a.app`（内置盘，约几百 MB）。外置盘未挂载构建须报错。
4. 不写用户 `~/.claude`、`~/.codex`；打包不得改变门禁入口与操作锁语义。
5. 如果某个必需功能（项目/任务选择、后台自启）在现有代码里不存在而非薄薄一层，停下上报缺口，不就地发明设计。

## Acceptance

- [ ] 红态：当前无可双击应用。绿态：`/Applications/a2a.app` 双击能打开，窗格里 zsh 可用，退出界面后台仍在。
- [ ] 真实入口验证：用打包产物（不是 `npm start`）走一遍 tracer：开项目、开任务、开窗格、关界面再开。保存截图与命令。
- [ ] 反例：外置盘未挂载构建报错；缺 `--task` 不崩溃。
- [ ] 报告打包后体积、构建命令、签名方式；已知限制照实写。
- [ ] `project_map.py status` 0 问题。

## 不做

- 不做自动更新、公证、安装器、跨平台。不动门禁语义。
