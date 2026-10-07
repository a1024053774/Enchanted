# T-035 主控决定（2026-10-07）：审批等待与后续运行

## 根因（主控只读核对，fork `apps/server/src/codexAppServerManager.ts` 约 700–722 行）
Synara 的 runtimeMode 映射：`approval-required` → approvalPolicy `untrusted` + sandbox `read-only`；`auto` → `on-request` + `workspace-write` + auto_review；`full-access`（Synara 默认）→ `never` + `danger-full-access`。
本次派发用了 `approval-required`，因此首个只读命令也进入审批。`auto` 的 workspace-write 会遇到 T-029 已证实的 worktree Git 元数据保护，worker 无法提交。

## 处置本次受阻运行
1. 不批准这次审批请求。经 Synara 的正常入口中断或拒绝该 turn（不在 UI 上选择任何"允许"选项），确认 thread 不再运行。
2. 经门禁 reclaim 该 attempt（停止并归档 worker thread），保留 attempt、worktree、事件与全部证据。
3. 停止你自己启动的隔离 Synara 服务（4835、web 5733 等），只停你启动的进程。
4. 删除本次隔离 CODEX_HOME（含外置盘 overlay 中的 auth 副本），记录删除命令、路径与结果；确认用户 ~/.codex 原字节未变。

## 后续运行（同一 ticket 内，用新 attempt）
- 派发 worker thread 时显式使用 `runtimeMode: "full-access"`。依据：与用户本机 Codex 默认（`sandbox_mode = "danger-full-access"`）及首轮 worker 的实际权限一致，也是 Synara 的默认值；不扩大 worker 既有权限。边界仍靠任务说明、独立 worktree、隔离 CODEX_HOME 与门禁核对。
- 显式设置 Codex 的 fast：经 Synara 的模型选项 `options.fastMode = true`（见 `apps/server/src/codexServiceTier.ts`），并从 app-server 实际启动参数或会话设置中读回证据；不使用 Synara 之外的包装器。
- 模型与推理强度沿用：gpt-6.1-sol、xhigh。
- 新建隔离 CODEX_HOME，规则不变（只复制 auth.json、只信任已核对夹具根目录、只复现 git add / git commit 两条 allow 规则、不装 hook、结束后删除）。
- 再遇到任何权限或信任对话，停下报告。
- 本次受阻运行的证据保留，作为 `approval-required` 不适合无人值守运行的反例。
