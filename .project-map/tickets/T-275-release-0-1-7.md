---
id: T-275
title: 发 0.1.7（Git 图与改动面板、T-249～T-273），更新 Release 与产品页
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

用户 2026-11-09 逐字：“做完记得更新GitHub 以及产品页,要把新的 Git树以及 diff 这些也展示出来”；随后：“这些都修复完再做发布的流程”。

- 按 T-248 的发布流程出 0.1.7：从已提交版本构建，ad-hoc 签名照实写明。
- GitHub Release v0.1.7 标为 Latest，中文说明（`evidence/2026-11-09-batch35/T-275/release-notes.md`）。
- 产品页加第 7 站“Git 图和改动就在旁边”（4 步：Git 图、提交详情与 diff、改动、受管 worktree 只读），更新一节改为 0.1.7。
- 同一个安装包替换 /Applications（之前装的是 T-273 的 0.1.6 构建）。

## Acceptance

- [ ] 安装包版本号为 0.1.7，codesign 严格核对通过；替换 /Applications 后应用与后台正常起来。
- [ ] Release v0.1.7 为 Latest，附件下载回来与构建产物逐字节相同；旧版本 Release 保留。
- [ ] 产品页线上 200；第 7 站四步能切换，面板跟随聚焦窗格、受管 worktree 只读。
- [ ] push 前扫描凭据、用户邮箱、agy 账号邮箱、大于 1 MB 的文件 0 命中；不 force push。

## 不做

不改写 Git 历史；不开签名票。
