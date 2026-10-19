---
id: T-101
title: 瘦身 Git 历史并发布初版到 GitHub（origin main）
type: build
status: closed
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

- [x] （用户裁定 B 不瘦身，本条作废）红态：瘦身前 `.git` 体积与 evidence 跟踪文件数；绿态：瘦身后体积、保留的摘要和被引用输入都在、现有相关测试与 `project_map.py status` 通过。
- [x] （用户裁定 B 不瘦身，本条作废）反例：外置盘未挂载时报错且不改写；备份对象数不一致时不替换。
- [x] （按用户批准的精确豁免：484 命中全部豁免、未豁免 0）凭据扫描 0 命中，扫描命令与输出摘要入证据。
- [x] （历史未改写，无需映射，本条作废）映射表可用：随机抽 5 个旧哈希能查到新哈希。
- [x] （以 gh api 核对远端 a96a040d3 → e6b87da61）push 前后 `git ls-remote` 对比；报告远端 URL 与提交。
- [x] 不泄露凭据；不动用户 `~/.claude`、`~/.codex`。

## 说明

- push 已由 T-097 的用户决定授权，范围仅限上面一次。
- 与 T-102（打包）并行；本票不碰 `workbench/` 源码，只可能碰仓库根的 LICENSE、README。

## 裁定（2026-10-19，force push）

执行主控 needs-decision：远端 origin main 已有旧历史 a96a040d3（private，2026-10-11 推送），改写后 push 需 force。用户选项逐字："A force 覆盖远端 (Recommended)"，选项原文："用 --force-with-lease 把瘦身后的历史覆盖到 origin main。远端旧历史不再可见(GitHub 上仍可能短期缓存)。仓库是你自己的 private 仓库,最直接,仓库地址不变。"

据此：允许对 `origin` 的 main 用 `--force-with-lease=main:a96a040d3`（锁定远端当前值，远端若已变则停下上报）。仍只推 main 一次；其余停下条件不变。

## 裁定（2026-10-19，凭据扫描）

执行主控 needs-decision（收件箱 `20261019T082941Z-executor-needs-decision-001`）：413 处命中，379 测试假值、5 文档占位、28 标识符误报，未确认真实密钥；H005 在一份 Codex 原生会话记录的加密字段里，无法判断；仓库跟踪 23 份 rollout-*.jsonl（含对话正文）。用户选项逐字："B 豁免包括 H005,保留会话记录"，选项原文："同样豁免,H005 也豁免,23 份会话记录留在公开历史里。对话正文会被公开,且 H005 是不明内容。"

据此：假值、占位、误报、H005 都按对象哈希加 offset 精确豁免，23 份会话记录保留在历史里；豁免清单与 H005 的位置存证据。其余停下条件不变。用户知情选择公开这些对话正文，Resolution 里要写明。

## Resolution

2026-10-19，执行主控。PASS（按用户裁定 B：不瘦身，直接发布）。

- 用户逐字："T101 选 B,推完把已有 GitHub 备份的不需要的大文件清理掉"。T-097 的瘦身方案按这次裁定不执行，历史没有改写。
- 发布：origin main 从 a96a040d3 快进到 e6b87da61，没有 force，只推了 main；推前推后都用 gh api 核对过远端。仓库仍为 private，可见性没有改。
- 开源必需件：根目录中文 README.md、GPL-3.0 LICENSE；workbench/LICENSE.synara 保留。
- 凭据扫描：对完整历史共 89,545 个对象做固定模式扫描，484 处命中，全部在用户批准的精确 object+offset 豁免内（credential-exemptions-01.json），未豁免 0 处。
  - 413 处来自 triage-01，用户选 B，包括 H005；
  - 71 处来自 triage-02，全部是公开测试假值，用户回复“加”。
  - 合并后新增的对象另行核对，3 处命中都在豁免内。
  - 局限：固定模式扫描不能证明不存在加密或编码过的秘密。
- 按用户裁定 B，公开历史里包含 23 份 Codex 原生会话记录（rollout-*.jsonl）的正文。
- 瘦身试跑（trial-20261019-01）的备份和候选在外置盘上，已不再需要，清理范围待用户确认。
