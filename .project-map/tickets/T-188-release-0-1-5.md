---
id: T-188
title: 发 0.1.5（含 agy、opencode 支持），补齐产品页、GitHub 各处，替换 /Applications
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

用户 2026-10-26 逐字：“再发一个版本,完善现在没更新的产品页,GitHub 之类的所有以及我的 applications里的.”

- 按既有发布流程出 0.1.5（含 T-184～T-187 起的改动，主要是 agy、opencode 支持）：构建、签名（ad-hoc，用户 2026-10-26 选“先不管”签名问题，照实写明）、GitHub Release 标为 Latest，说明中文为主，写清首次在自己的 Codex/agy 里启动会弹信任框、换版后 macOS 会收回“文稿”授权需本人重新允许。
- 产品页：把还没更新的地方补齐——版本号与下载链接、“目前支持的 CLI”改为 0.1.5 已带四种、与当前功能不符的文案与演示截图；保留 T-182 的检查全过。
- GitHub 各处：README（中英文入口若有）、仓库 About 描述与 topics、Release 说明、CHANGELOG（若有）、docs 中的版本与 CLI 支持说法，与 0.1.5 一致。改仓库描述/topics 属对外内容，本句用户原话即授权。
- 替换 /Applications：本句用户原话授权停掉当前后台并替换为 0.1.5。替换前列出仍在运行的会话写入报告；从 Dock 启动核对版本与签名；macOS 隐私授权弹窗停下交用户，不代批。

## Acceptance

- [x] Release 0.1.5 为 Latest，附件下载回来与构建产物一致，签名核对通过。
- [x] 产品页线上 200，页面检查全过，lcu 在 Chrome 复看；无过时版本号或 CLI 说法（grep 核对 docs 与 README）。
- [x] 仓库 About/topics 与 README 更新；push 前扫描凭据、用户邮箱、agy 账号邮箱、大文件 0 命中，不 force push。
- [x] /Applications 中为 0.1.5，从 Dock 启动正常，后台已连接。

## 不做

不改写 Git 历史；不开签名票。

## Resolution

2026-10-26 PASS，证据 `evidence/2026-10-26-batch27/T-188/RESULTS.md`，agy 审查第二轮 `T-188 REVIEW PASS`。Release v0.1.5 为 Latest（目标 d68a5d50e，附件下载回来逐字节相同，ad-hoc）；产品页线上 43/43、Chrome 复看；README、工作台说明、About、topics 更新；/Applications 为 0.1.5，后台已连接。与字面不同的一处：lcu 选不到 Dock，改用干净环境经 LaunchServices 启动，并核对进程环境。
