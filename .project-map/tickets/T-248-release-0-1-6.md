---
id: T-248
title: 发 0.1.6（hc 终端运行时与 T-189～T-247 的修复），更新 Release 与产品页
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

用户 2026-11-04 逐字：“构建并打包发布新版本,更新 release,也更新产品页 a1024053774.github.io/enchanted”。

- 按 T-188 的发布流程出 0.1.6：从已提交版本的干净 checkout 构建，ad-hoc 签名照实写明（2026-10-26 用户选“先不管”签名）。
- GitHub Release v0.1.6 标为 Latest，中文说明，写清升级提醒（换版后 macOS 收回“文稿”授权）和已知限制（T-235 等待复现）。
- 产品页 `docs/index.html` 的版本号、更新一节与发行说明链接改为 0.1.6；T-182 页面检查本地与线上全过。
- 这次没有要求替换 /Applications，不替换。

## Acceptance

- [x] 安装包版本号为 0.1.6，codesign 严格核对通过，内带固定版本的 hc；以隔离的状态目录启动安装包，项目终端经内带 hc 打开并能执行命令。
- [x] Release v0.1.6 为 Latest，附件下载回来与构建产物逐字节相同；旧版本 Release 保留。
- [x] 产品页线上 200，页面检查全过；docs 与 README 无过时版本号。
- [x] push 前扫描凭据、用户邮箱、agy 账号邮箱、大于 1 MB 的文件 0 命中；不 force push。

## 不做

不改写 Git 历史；不开签名票；不替换 /Applications。

## Resolution

2026-11-04 关闭，PASS。证据见 [RESULTS.md](../../evidence/2026-11-04-batch32/T-248/RESULTS.md)。
- Release v0.1.6 为 Latest，目标 `4ec534bed`。附件下载回来逐字节相同，签名为 ad-hoc。
- 安装包冒烟：项目终端经内带 hc 打开，并执行了命令。
- 产品页线上 200，本地与线上页面检查都是 43/43。
- 用户写的小写网址 `/enchanted/` 返回 404（Pages 路径区分大小写），正确的网址是 `/Enchanted/`。
