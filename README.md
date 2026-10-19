# a2a

a2a 是面向 macOS 的多 agent 协作工作台。它在交互终端里运行 Claude Code 和 Codex，按“项目 → 任务 → agent 会话”组织工作，由常驻编排后台托管终端、门禁和记录。关闭工作台窗口后，后台与 agent 可以继续运行。

项目研究怎样让协作流程不依赖模型持续记住操作手册：任务卡定义边界与完成条件；认领、交付、验收、集成与回收经过同一门禁；交付绑定 attempt、session、fence、规格版本与完整提交号。模型自述完成不能代替验收。门禁是同一用户下可信协作者的流程约束，worktree 和会话身份不构成安全沙箱。

## 当前状态

这是开发中的初版。工作台使用 Electron、React、xterm.js 和 node-pty；门禁核心位于本仓库的 `workbench/src/gates/`，命令行入口为 `workbench/src/gates/cli.ts`。前端复用了 Synara 的组件与样式，保留其 MIT 许可声明。

当前只面向 macOS，首批 CLI 为 Claude Code 与 Codex。多个窗格、用户输入记录、问题面板、主控收件箱和恢复流程各有自己的验证边界；完整双主控协作、正常登录恢复与日常使用切换仍有未完成项。日常派发目前继续使用 Herdr，切换条件以 [intent.md](intent.md) 和[项目地图](.project-map/MAP.md)为准。已发布代码不代表用户已确认工作台“可用”，也不代表已证明长期可靠性、吞吐或成本收益。

详细入口与限制见 [工作台说明](workbench/README.md)。正常登录主控不会在后台重启时自动续接，worker 窗格也不会自动恢复执行；它们保留为“未恢复”，由执行主控按恢复流程处理。

## 环境与安装依赖

需要 Git、Python 3、Node.js `>=26.5.0 <27` 和 npm。使用对应 CLI 时，另需本机已安装并可登录的官方 Claude Code 或 Codex。版本与依赖以 [package.json](workbench/package.json) 和锁文件为准。

依赖缓存、Electron 下载、构建缓存和产物放在真实挂载的 `/Volumes/WD-Elements`。未挂载时安装与构建报错，不回退到内置盘。源码和工作台数据目录放内置盘。安装依赖：

```sh
cd workbench
python3 -c 'import os; assert os.path.ismount("/Volumes/WD-Elements"), "外置盘未挂载"'
electron_config_cache=/Volumes/WD-Elements/a2a-electron-cache npm ci --cache /Volumes/WD-Elements/a2a-t075-npm-cache
npm ls --depth=0
cd ..
```

## 构建与运行

从仓库根目录构建；每次使用新的 `--slot` 名称，已有槽不会被覆盖：

```sh
npm --prefix workbench run build -- --slot local-01
```

输出位于 `/Volumes/WD-Elements/a2a-workbench/local-01/dist`。不要移动共享 checkout 的构建目录，也不要在构建输出中放指向源码或依赖的链接。

启动交互 agent 前，需要按[工作台说明](workbench/README.md)准备隔离状态目录、启动配置与任务卡，并通过门禁创建任务、启动会话。后台命令入口如下；`launch.json` 的字段与权限要求见该说明：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state daemon_start --launch-config /绝对路径/launch.json
node workbench/src/gates/cli.ts --state /绝对路径/state status --task 任务编号
```

窗口连接已有后台和任务。启动环境须已持有该后台对应的 `A2A_OPERATOR_CREDENTIAL`，不要将凭据写入仓库、命令记录或截图。下面命令只读取已有构建，不自动启动后台或 agent：

```sh
node workbench/app/start.mjs --build /Volumes/WD-Elements/a2a-workbench/local-01/dist --state /绝对路径/state --task 任务编号 --user-data /绝对路径/ui
```

可重复传入 `--launch 启动记录号` 选择同一任务的多个会话。验证时使用自己新建的隔离状态和 UI 目录，避免操作日常数据。a2a 不写用户的 `~/.claude` 或 `~/.codex` 全局配置；会话权限与钩子经启动参数传入。

## 文档与证据

- [项目地图](.project-map/MAP.md)：当前决定、ticket、规格与文档索引。
- [intent.md](intent.md)：当前阶段目标、非目标和切换条件。
- [CONTEXT.md](CONTEXT.md)：统一术语。
- [AGENTS.md](AGENTS.md)：仓库协作与验收规则。
- [工作台说明](workbench/README.md)：命令、配置、恢复与已知限制。

仓库保存文本摘要、命令脚本、小输入与 `*.archive.json` 清单。原始 run/fixtures、大文件和数据库归档在 `/Volumes/WD-Elements/a2a-evidence/`，这些本机原始证据不随 Git 克隆分发；缺少外置盘时，不能据此宣称完成了原始证据重放。历史瘦身产生的旧→新提交映射在实际改写后写入 `records/`，用于查阅旧报告、提交尾注和启动记录引用；映射表不自动改写含旧哈希的命令。

## 许可

项目以 [GNU GPL 第 3 版](LICENSE)发布。Synara 复用部分保留 [MIT 版权与许可声明](workbench/LICENSE.synara)。
