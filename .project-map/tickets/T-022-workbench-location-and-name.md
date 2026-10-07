---
id: T-022
title: 工作台的代码位置与正式名称
type: decide
status: superseded
blocked_by: []
claimed_by:
supersedes:
---

## Question

工作台的代码放在哪里，正式名称叫什么？

候选位置：a2a 仓库内；以 Herdr 硬分叉为基础的独立仓库；其他。名称同时决定 T-018 要求的独立命名空间（可执行文件名、环境变量、socket 目录、集成 hook）、外置盘上的缓存路径，以及以后开源的仓库名。

## Resolution

2026-10-06，用户决定代码放在本 a2a 仓库，名称交给 agent 起（"你帮我起个名字吧，就在现在这个 a2a 文件夹下"）。

定名 **Muster**：英文里有"集结"之意，"pass muster"指经得起检验，呼应 a2a 的验收门禁。用户以后可以改名。

命名检查（2026-10-06）：
- GitHub 上的同名项目只有已归档的 `facebookarchive/muster`（Go 批处理库）；Homebrew 没有同名 formula；crates.io 有同名 crate，M1 不发布 crate。
- 未采用 `drover` 和 `bellwether`：前者已有 agent 编排项目，后者已有管理 Herdr agent 的项目。

落地方式：
- 代码放在本仓库的 `muster/` 目录。
- 命令行程序叫 `muster`，桌面应用叫 Muster.app，环境变量前缀为 `MUSTER_`，目录和 hook 文件名用 `muster`。详见 [spec](../specs/workbench-m1-2026-10-06.md)。
- GitHub 私有仓库沿用项目名 `a2a`，开源时可以再改名。

**2026-10-07：被 T-030 取代**（改为基于 Synara 的 fork，见 `.grilling/synara-fork.md`）。
