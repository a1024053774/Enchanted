---
from: "executor"
to: "user"
kind: "disposition"
reply_to: "20261010T073006Z-worker:t064-issue-001"
refs: []
created_at: "2026-10-10T08:31:05.714116Z"
schema: 1
title: "T-064 真实 provider 证据缺口：已按决定 02 补证，留给用户关闭"
action: "forward"
reason: "涉及验收证据边界，不由执行主控关闭"
basis: "file:evidence/2026-10-09-batch11/T-064/controller-decision-02.md"
id: "20261010T083105Z-executor-disposition-001"
---

执行主控已决定补证：Codex 用隔离 CODEX_HOME 跑最多 4 个真实 turn；Claude 用真实 CLI + 本机受控模型 API（不碰用户凭据）。补证结果出来前该问题保持开放。