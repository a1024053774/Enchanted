---
id: T-265
title: 完整审查材料内联导致原生 Codex 拒绝超长输入
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

2026-11-09 T-249 候选 d8f55c9 通过三项机械验收后，审查启动被 Codex 0.167.0 拒绝：输入 1318486 字符超过 1048576 上限，native turn 未开始。现场在 evidence/2026-11-09-batch35/T-265/controller/。GateCore.requestReview 将任务卡、完整 diff、verification 内联为 prompt，PaneManager.createReview 再整体写进 CLI 输入框。

保留完整材料，存为每次审查独立、绑定原身份的文件；原生交互终端只接收简短入口和文件路径。优先用已有 request_dir，与 review-template/result 同属该 launch。不新增公开 API、schema 或依赖，不按大小保留两条路径，不截断材料，不改变正常 Stop、只读候选和 review_submit 门禁。

授权来自本轮用户“修复现在 enchanted故障并继续”“主线是完成主要的两个面板的任务以及 bug 修复”。本票修复原面板审查的阻点；T-264 的额度错误状态恢复单独处理。

## Acceptance

- [ ] 保留真实旧版本拒绝；新检查在父版对超长内联输入失败，原因对应本缺陷。
- [ ] 完整材料原字节可读，含任务卡、diff、机械结果、先前问题和提交方式；原生消息简短且指向本 review/launch，不截断、不串会话、不覆盖旧材料。
- [ ] 文件写失败不发送缺失或半写材料；原候选身份可追溯，只读与提交门禁保持。
- [ ] 长短材料、Unicode、两个审查隔离及 2-5 个已知坏实现有明确结果；隔离真实 Codex 能开始回合并读到完整长材料。
- [ ] 独立审查、标准打包安装后接回 T-249 大候选；保留历史拒绝，不 push，不手改数据库。

## 当前状态

INCOMPLETE。原 T-249 attempt 已升级结束，候选保留，已交付 worker 正常回收；后台经 daemon_stop 重启，旧两个审查 CLI 已结束。没有接受旧草稿或重放请求。
