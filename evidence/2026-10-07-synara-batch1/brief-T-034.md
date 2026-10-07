# Worker 任务书：T-034 Synara fork 能构建运行（task）

你是 a2a 的 worker（Codex）。主控是 Claude Code（Herdr pane wF:pM）。只做 T-034，不扩大范围。
先读：a2a 仓库的 AGENTS.md、intent.md、.project-map/specs/synara-m1-2026-10-07.md（"fork 与上游""构建与缓存""隔离运行"）、
.project-map/tickets/T-034-synara-fork-builds.md（完成条件以它为准）、README 的"Rust 构建：外置盘入口"（缺盘门禁的已有做法）、
以及 fork 仓库 `~/Documents/Code/synara` 的 AGENTS.md、CLAUDE.md、CONTRIBUTING.md、README.md。

## 两个仓库
- fork：`/Users/luckye/Documents/Code/synara`，分支 `a2a`（v1.0.1-beta.2，`f176e89`），remote `origin`=我们的 fork，`upstream`=原作者。
  你在这里新增文件和提交；不 push 任何分支（主控负责推送）。
- a2a：`/Users/luckye/Documents/Code/a2a`。只写 T-034 ticket 和证据目录 `evidence/2026-10-07-synara-batch1/T-034/`；不改 MAP.md、AGENTS.md、README.md、CONTEXT.md。

## 要求
1. 构建入口：在 fork 中新增一个我们自己的入口脚本（放在专属路径，例如 `a2a/scripts/`，不改上游已有脚本），在 `bun install`、构建、运行前：
   - 检查 `/Volumes/WD-Elements` 是真实挂载点（可复用 a2a 仓库 `scripts/build` 的判断方式），缺盘即报错退出，不回退；
   - 把 Bun 全局缓存、Electron 及其二进制下载缓存指向 `/Volumes/WD-Elements/dev-cache/synara/`（具体环境变量以 Bun、Electron、electron-builder 当前文档为准，写明来源）；
   - Node：Synara 要求 Node 24.13.1（`.mise.toml`、`engines`），本机全局是 v26.5.0 且没有 mise。从 nodejs.org 官方发布下载 24.13.1 的 macOS arm64 包，核对官方 SHASUMS256，解压到 `/Volumes/WD-Elements/dev-cache/synara/toolchains/`，只在入口脚本里加进 PATH；不改全局 Node、不装 mise、不改 ~/.zshrc。
2. 安装、构建、运行：经入口执行 `bun install`、构建、dev server、桌面版（脚本名见 fork 的 package.json）。Synara 使用隔离的数据目录与身份（先读其 desktop identity 与数据目录机制），不读写用户可能已安装的 Synara 数据。能启动的服务和窗口，确认后由你关闭（只关你启动的进程）。
3. 实测并记录：`node_modules` 与内置盘其他新增占用（前后 `df` 与 `du`）、外置盘缓存占用、安装耗时、dev server 与桌面版启动耗时、桌面版截图。
4. 缺盘反例：用一个不存在的挂载点模拟缺盘（不要真的卸载外置盘），证明入口报错且没有在内置盘生成缓存。
5. 上游合并演练：在临时分支（如 `a2a-merge-drill`）上把 `upstream/main` merge 进 `a2a` 的副本，记录冲突、解决方式与类型检查或测试结果；演练结束后不把演练结果合进 `a2a`，不推送临时分支，保留该分支供主控查看。
6. 安全：本机 Codex 默认 `danger-full-access`，没有沙箱兜底，你要自己守边界：不改用户级配置、不碰用户正在用的 Herdr、不删除任何不是你创建的文件；需要用户级改动或权限时停下说明。

## 完成
- 在 T-034 ticket 的 Resolution 写结论（PASS/INCOMPLETE/BLOCKED、命令、结果、证据路径、fork 的提交号），全部满足才改为 closed。
- a2a 仓库：运行 project_map.py status；本地 commit 只含 T-034 ticket 与你的证据（英文信息，末尾 `Co-Authored-By: Codex <noreply@openai.com>`）。fork：在 `a2a` 分支提交入口脚本等，不 push。
- 最后终端回复一行：`T-034 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit> <fork commit>`。
