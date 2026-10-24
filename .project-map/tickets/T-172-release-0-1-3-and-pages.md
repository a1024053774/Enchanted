---
id: T-172
title: 发新 Release 并更新 Pages 页面（本批修复）
type: build
status: open
blocked_by: [T-171]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-24 逐字选择：“发新 Release 并更新页面”（选项：把本批修复写进页面和发行说明，按 T-114 流程发新版本）。
目标：按 T-114 的流程，在 T-171 合并后打新版本（版本号接 0.1.2 之后，由你按现有规则定），构建安装产物（内置盘临时目录、构建完清理），发 GitHub Release；把本批对用户有意义的变化（输入法定位、视图分屏、额外目录与放宽限制、终端流畅度、流程页与记录页修正、批准入输入记录、审查员格式恢复、回收失败 attempt 等）写入 docs 页面与发行说明，中文为主，文案过 frontend-less-ai-tone，不夸大（不写未验证的收益）。
推送与发布前核对：diff 无凭据/auth.json/用户私有数据/用户邮箱，无大文件，不 force push；Release 附件只含安装产物。用户 2026-10-24 已授权 push 与 Pages 更新（“做完继续更新 github 以及 pages”）与上述发新 Release；失败如实报告。

## Acceptance

- [ ] GitHub Release 已发布，附件可下载并核对大小；Pages 返回 200 且含新版本说明。
- [ ] 发行说明与页面只写已验证的变化，并标明 T-163 的 M02 残余等已知限制。
- [ ] 安装产物在内置盘临时构建、构建缓存已清理。

## 不做

范围外的问题经问题上报，不顺手改。
