---
id: T-101
title: 瘦身 Git 历史并发布初版到 GitHub（origin main）
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

落实 [T-097](T-097-slim-git-history-before-release.md) 的决定（用户 2026-10-19 作答，逐字见该票）。

1. 按 T-097 第 1～4 条瘦身：备份 → 在副本里 `git filter-repo` → 核对 → 替换；映射表入仓库。
2. 发布前补齐开源必需件：根目录 `LICENSE`（GPL-3.0，AGENTS.md 已定）、保留 `workbench/LICENSE.synara`、一份中文 `README.md`（项目是什么、怎么构建运行、当前状态与已知限制）。写 README 走 `document-writing`。
3. 发布前扫描：全仓（含所有保留的历史）凭据扫描，命中则停下上报，不 push。含 auth.json、token、`~/.claude` / `~/.codex` 副本、会话正文。
4. push：`origin`（`git@github.com:a1024053774/a2a.git`）的 main，一次。SSH 在桌面会话失败过，用 gh 的一次性 HTTPS 凭据形式（见记忆 github-push-over-https）。只推 main，不推 backup/* 等分支，不 force 到别人的仓库以外的地方；远端若已有内容，先看再说，需要 force 才能推时停下问用户。

## Acceptance

- [ ] 红态：瘦身前 `.git` 体积与 evidence 跟踪文件数；绿态：瘦身后体积、保留的摘要和被引用输入都在、现有相关测试与 `project_map.py status` 通过。
- [ ] 反例：外置盘未挂载时报错且不改写；备份对象数不一致时不替换。
- [ ] 凭据扫描 0 命中，扫描命令与输出摘要入证据。
- [ ] 映射表可用：随机抽 5 个旧哈希能查到新哈希。
- [ ] push 前后 `git ls-remote` 对比；报告远端 URL 与提交。
- [ ] 不泄露凭据；不动用户 `~/.claude`、`~/.codex`。

## 说明

- push 已由 T-097 的用户决定授权，范围仅限上面一次。
- 与 T-102（打包）并行；本票不碰 `workbench/` 源码，只可能碰仓库根的 LICENSE、README。
