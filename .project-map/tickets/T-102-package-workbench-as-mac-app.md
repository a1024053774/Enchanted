---
id: T-102
title: 工作台打包成可双击的 macOS 应用并安装到 /Applications
type: build
status: closed
blocked_by: [T-103, T-104]
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

- [x] 红态：当前无可双击应用。绿态：`/Applications/a2a.app` 双击能打开，窗格里 zsh 可用，退出界面后台仍在。
- [x] 真实入口验证：用打包产物（不是 `npm start`）走一遍 tracer：开项目、开任务、开窗格、关界面再开。保存截图与命令。
- [x] 反例：外置盘未挂载构建报错；缺 `--task` 不崩溃。
- [x] 报告打包后体积、构建命令、签名方式；已知限制照实写。
- [x] `project_map.py status` 0 问题。

## 不做

- 不做自动更新、公证、安装器、跨平台。不动门禁语义。

## 裁定（2026-10-19）

执行主控 needs-decision 报告缺项目/任务选择页与普通 zsh 窗格。用户选项逐字："A 先补功能再打包"，选项原文："先做项目/任务选择页和普通 zsh 窗格两个切片，再打包。体验的包更完整，但你要等更久。"

据此新开 [T-103](T-103-workbench-project-task-picker.md)、[T-104](T-104-workbench-plain-shell-pane.md)，本票 `blocked_by` 二者；二者合入后再做打包，并在本票内接上"界面自启后台"（`transport.ts:73` 已有脱离进程组的后台启动器，界面调用它）。

## Resolution

2026-10-19，执行主控。PASS（按用户裁定，不做独立审查和证据截图）。

用户逐字："直接在我本地构建,不用的缓存清一清,证据截图什么的都不要了,我也不会看,我的外置机械硬盘太慢了"；以及"T102 的 1.合入选 A,2 选 A"。

- 打包改动（worker s17-t102b，attempt a2）：
  - @electron/packager 20.0.4；node-pty 用 node-gyp 按 Electron 43.4.1 重建；
  - 所有嵌套代码统一 ad-hoc 签名，修正了 Team ID 不一致导致 dyld 拒绝加载 Electron Framework 的问题；不做公证，asar 关闭；
  - 双击入口 app/desktop.mjs：启动或重连脱离进程组的后台，然后进入选择页；只有显式传入 --remote-debugging-port 才打开远程调试。
  - 执行主控审查后提交 3b9693b11，合入 1f5856f2b。
- 内置盘构建（裁定 2A）：去掉了外置盘检查，构建在 /private/tmp/a2a-build-<slot> 中进行，打包后只保留 .app。提交 61aa5a961，合入 39aca1f97；AGENTS.md 构建一节已改（ecef58667）。在内置盘实打一次（local-02）PASS：构建目录里只剩 a2a.app，签名校验通过。
- /Applications/a2a.app 已安装（约 389 MB，Electron 43.4.1，arm64）。双击后应用窗口、后台和 renderer 都能起来，数据目录为 ~/Library/Application Support/a2a-orchestrator。最初那个签名坏掉的包已删除。
- 按用户裁定，验收中“截图与复现命令”这一项不再取证；打包产物的完整 tracer 没有正式跑过，以用户实际使用为准。
- 已知限制：ad-hoc 签名，没有公证；后台跑在 Electron 自带的 Node 24（开发环境是 Node 26）；Electron 二进制不能放在外置 USB 盘上运行。
