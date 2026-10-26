---
id: T-186
title: 发新 Release（含 T-174～T-185）并更新产品页
type: build
status: closed
blocked_by: [T-184, T-185]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

用户 2026-10-25 逐字：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”

在 T-184、T-185 完成后，按既有发布流程出 0.1.4：签名、公证状态照实记录、Release 说明写本批用户可见改动（中文为主）；产品页下载链接、版本号与改动说明更新；替换 /Applications 前先停后台并经用户同意（同上次流程）。

通用：先留真实入口的红态再修根因；真实 Claude 用 claude-haiku-5-5、尽量少；不写 ~/.claude、~/.codex 等全局配置，钩子只经每会话启动参数；agy 独立审查。

## Acceptance

- [x] GitHub Release 0.1.4 可下载，签名核对通过；产品页显示新版本与链接，Pages 200，lcu 在 Chrome 复看。
- [x] push 前凭据与私有数据扫描 0 命中；不 force push。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-25 21:22 关闭：Release、Pages、Chrome 复看、替换 /Applications、真实应用复看全部完成，PASS。途中 claude 卡在 macOS“文稿”授权，由用户本人允许。见 evidence/2026-10-25-batch26/T-186/RESULTS.md。
