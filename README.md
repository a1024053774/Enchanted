# Enchanted

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/brand/logo-on-dark.png">
  <img src="docs/assets/brand/logo-on-light.png" alt="Enchanted 标志" width="160" height="160">
</picture>

Enchanted 是面向 macOS 的多 agent 协作工作台，a2a 是它的编排内核。它在交互终端里运行 Claude Code、Codex、Antigravity CLI（`agy`）和 opencode，按“项目 → 任务 → agent 会话”组织工作，由常驻编排后台托管终端、门禁和记录。关闭工作台窗口后，后台与 agent 可以继续运行。

[产品页与可点击演示](https://a1024053774.github.io/Enchanted/) · [GitHub Releases 下载](https://github.com/a1024053774/Enchanted/releases)

产品页使用预设的虚构数据演示界面，不连接后台或调用模型。

项目研究怎样让协作流程不依赖模型持续记住操作手册：任务卡定义边界与完成条件；认领、交付、验收、集成与回收经过同一门禁；交付绑定 attempt、session、fence、规格版本与完整提交号。模型自述完成不能代替验收。门禁是同一用户下可信协作者的流程约束，worktree 和会话身份不构成安全沙箱。

## 当前状态

这是开发中的初版。工作台使用 Electron、React、xterm.js 和 node-pty；门禁核心位于本仓库的 `workbench/src/gates/`，命令行入口为 `workbench/src/gates/cli.ts`。前端复用了 Synara 的组件与样式，保留其 MIT 许可声明。

当前只支持 macOS arm64（Apple Silicon）。CLI 支持 Claude Code、Codex、agy 与 opencode，四种都可当主控、worker 和审查员；agy 与 opencode 没有按会话的钩子，差别见[工作台说明](workbench/README.md)。多个窗格、用户输入记录、问题面板、主控收件箱和恢复流程各有自己的验证边界；完整双主控协作、正常登录恢复与日常使用切换仍有未完成项。项目作者的日常派发目前继续使用 Herdr，切换条件以 [intent.md](intent.md) 和[项目地图](.project-map/MAP.md)为准。这是开发中的初版，不作可靠性、吞吐或成本承诺；发布代码不代表用户已确认工作台“可用”。

日常用法：点侧栏顶部的“+”打开一个目录，它就成了项目；在项目里新建或分屏出的终端直接从项目目录启动。任务卡由主控写、经门禁派发，界面里不再有新建任务的表单；经门禁派发的 agent 会话按项目出现在侧栏里，带启动时间和状态图标。在项目终端里用自己的命令启动 CLI，告诉它当主控，它会经 `a2a request` 申请角色；你在界面里批准后，它就能写任务卡、经门禁派发，身份跟着这个终端，终端关了就结束。agy 当主控请用 `agy --dangerously-skip-permissions` 启动，否则每条命令都要你确认。外观、通知和主控派发新会话时用的模型，在侧栏顶部齿轮打开的设置里调整。界面有浅色与深色两套，可以跟随系统。

详细入口与限制见 [工作台说明](workbench/README.md)。正常登录主控不会在后台重启时自动续接，worker 窗格也不会自动恢复执行；它们保留为“未恢复”，由执行主控按恢复流程处理。

## 下载与安装

到 [GitHub Releases](https://github.com/a1024053774/Enchanted/releases) 下载 macOS arm64 的 `.zip`，解压后把 `Enchanted.app` 拖入“应用程序”。使用前，先在本机安装并登录至少一种支持的 CLI（Claude Code、Codex、agy、opencode）。

应用使用 ad-hoc 签名，没有经过 Apple 公证。第一次打开时，右键点击应用并选择“打开”；也可以在终端解除隔离后再打开：

```sh
xattr -dr com.apple.quarantine /Applications/Enchanted.app
```

产品显示名为 Enchanted，bundle id 保持 `org.a2a.workbench`。后台数据目录仍为 `~/Library/Application Support/a2a-orchestrator`，默认界面数据在其 `ui/` 子目录；改名不迁移数据。

## 从源码构建

需要 Git、Python 3、Node.js `>=26.5.0 <27` 和 npm。使用对应 CLI 时，另需本机已安装并已登录该 CLI。版本与依赖以 [package.json](workbench/package.json) 和锁文件为准。

按 [AGENTS.md 构建条款](AGENTS.md#第三阶段工作台约束)，源码、工作台数据和 Electron 二进制放内置盘，构建也使用内置盘的临时目录，不再要求挂载外置盘。构建缓存、依赖和中间产物使用临时构建目录，完成后清理，只保留安装产物。标准打包命令会清理本次 `work/`，现有可复用 npm、Electron 和头文件缓存的位置及清理边界见[工作台说明](workbench/README.md#安装)。安装依赖：

```sh
cd workbench
npm ci --ignore-scripts
npm ls --depth=0
cd ..
```

### 打包 macOS 应用

从仓库根目录运行，每次使用新的槽名：

```sh
npm --prefix workbench run package:mac -- --slot mac-01
```

成功后最后一行给出 `Enchanted.app` 的绝对路径，产物位于 `os.tmpdir()/a2a-build-mac-01/Enchanted.app`，签名为 ad-hoc，未公证。要在正式版运行时另装一份试用，加 `--variant test`：产物名为 `Enchanted Test.app`，bundle id 与数据目录都和正式版分开（`org.a2a.workbench.test`、`a2a-orchestrator-test`）。安装后清理本次临时目录；失败现场先保留。

### 开发构建与运行

从仓库根目录构建；每次使用新的 `--slot` 名称，已有槽不会被覆盖：

```sh
npm --prefix workbench run build -- --slot local-01
```

输出位于 `os.tmpdir()/a2a-build-local-01/dist`，构建命令最后一行给出绝对路径。下面以 `TMPDIR=/private/tmp` 时的路径为例；请使用自己实际输出的路径。不要移动共享 checkout 的构建目录，也不要在构建输出中放指向源码或依赖的链接。

开发启动另需显式下载 Electron 二进制，步骤见[工作台说明](workbench/README.md#安装)；打包命令不需要这一步。

启动交互 agent 前，需要按[工作台说明](workbench/README.md)准备隔离状态目录、启动配置与任务卡，并通过门禁创建任务、启动会话。后台命令入口如下；`launch.json` 的字段与权限要求见该说明：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state daemon_start --launch-config /绝对路径/launch.json
node workbench/src/gates/cli.ts --state /绝对路径/state status --task 任务编号
```

窗口连接已有后台和任务。启动环境须已持有该后台对应的 `A2A_OPERATOR_CREDENTIAL`，不要将凭据写入仓库、命令记录或截图。下面命令只读取已有构建，不自动启动后台或 agent：

```sh
node workbench/app/start.mjs --build /private/tmp/a2a-build-local-01/dist --state /绝对路径/state --task 任务编号 --user-data /绝对路径/ui
```

可重复传入 `--launch 启动记录号` 选择同一任务的多个会话。验证时使用自己新建的隔离状态和 UI 目录，避免操作日常数据。a2a 不写用户的 `~/.claude` 或 `~/.codex` 全局配置；会话权限与钩子经启动参数传入。唯一的例外是 agy 作 worker 或审查员时，对每个任务目录的信任经 agy 自己的流程写入 `~/.gemini/antigravity-cli/settings.json` 的 `trustedWorkspaces`。

## 文档与证据

- [项目地图](.project-map/MAP.md)：当前决定、ticket、规格与文档索引。
- [intent.md](intent.md)：当前阶段目标、非目标和切换条件。
- [CONTEXT.md](CONTEXT.md)：统一术语。
- [AGENTS.md](AGENTS.md)：仓库协作与验收规则。
- [工作台说明](workbench/README.md)：命令、配置、恢复与已知限制。

仓库保存文本摘要、命令脚本、小输入与 `*.archive.json` 清单。原始 run/fixtures、大文件和数据库归档在 `/Volumes/WD-Elements/a2a-evidence/`，这些本机原始证据不随 Git 克隆分发；缺少外置盘时，不能据此宣称完成了原始证据重放。历史瘦身产生的旧→新提交映射在实际改写后写入 `records/`，用于查阅旧报告、提交尾注和启动记录引用；映射表不自动改写含旧哈希的命令。

## 许可

Enchanted 以 [GNU GPL 第 3 版（GPL-3.0）](LICENSE)发布。复用的 Synara 组件、样式及门禁代码保留原 MIT 版权与许可声明，完整文本见 [workbench/LICENSE.synara](workbench/LICENSE.synara)。
