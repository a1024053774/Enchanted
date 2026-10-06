# Worker 任务书：T-026 把构建缓存与工具链放到外置盘

你是 a2a 项目的 worker（Codex）。主控是 Claude Code（pane wF:pM）。只做本 ticket，不扩大范围。

先读：AGENTS.md、.project-map/MAP.md、.project-map/tickets/T-026-external-build-cache.md、T-020、
.project-map/specs/workbench-m1-2026-10-06.md 的"构建与工具链"一节、CONTEXT.md。

## 目标
让本仓库（a2a）之后的 Rust 构建（Muster 引擎、Muster.app、T-025 探针）默认把输出和缓存放在
`/Volumes/WD-Elements`，外置盘未挂载时构建直接报错，不回退到内置盘。

## 范围与限制
- 只改本仓库内的文件（例如仓库内的 cargo 配置、一个构建入口脚本或 justfile/Makefile、文档）。
  不改 ~/.zshrc、~/.cargo/config.toml、全局 git 配置等用户级持久配置；需要时写成建议交给主控。
- Enchanted 已冻结：不改 Enchanted 仓库，只在结论里写出它以后应如何套用同一方案。
- 外置盘上的目录建议：/Volumes/WD-Elements/dev-cache/a2a/（target、cargo-home 或 registry、zig-cache）。
  是否迁 CARGO_HOME 自行判断并说明理由（registry 体积、离线与断盘行为）。
- Zig 0.16（Herdr 引擎需要，见 .upstream/herdr/flake.nix 与 crates/ghostty-vt/build.rs）：
  可用 Homebrew 或 ziglang.org 官方发布包安装；安装前先确认能拿到 0.16，拿不到就停下报告，不要换版本。
  Zig 全局缓存也要指向外置盘。
- 不重启、不修改用户正在用的 Herdr server。

## 必须实测并留证据（写到 evidence/2026-10-06-m1-batch1/T-026/）
1. 缺盘报错：用一个不存在的挂载点模拟（不要真的卸载外置盘），证明构建入口报错退出、没有在内置盘生成 target。
2. 机械盘耗时：用 .upstream/herdr（只读副本，复制到外置盘的临时目录里编译，不要改 .upstream）
   做一次冷编译和一次改动一个文件后的增量编译，记录耗时、峰值与结束占用、内置盘可用空间前后对比。
3. 并发：两个编译同时用同一 target 目录时的表现（是否互相阻塞），给出多 worker 时的建议（共享还是按 worktree 分目录）。
每项记录精确命令、环境变量、输出摘要与结论。

## 完成方式
- 在 T-026 ticket 的 Resolution 写结论（PASS/INCOMPLETE/BLOCKED，命令、结果、证据路径），全部满足才把 status 改为 closed。
- 运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`，处理 stale doc。
- 提交一个本地 git commit（英文提交信息，末尾加 `Co-Authored-By: Codex <noreply@openai.com>`），不要 push。
- 最后在终端回复一行：`T-026 DONE <PASS|INCOMPLETE|BLOCKED> <commit>`。
遇到权限请求、需要用户决定的事或无法核对的状态，停下并在终端说明，不要猜。
