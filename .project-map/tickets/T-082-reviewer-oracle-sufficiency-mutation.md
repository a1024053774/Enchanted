---
id: T-082
title: 门禁加固 D3：reviewer 必查完成条件是否够格，并在一次性副本里做变异检查
type: build
status: open
blocked_by: [T-077]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

依据 [决定记录](../proposals/gate-hardening-2026-10-14.md) D3。完成条件由执行主控写，能不能拒绝错误实现是判断题，交给 reviewer；变异检查在 reviewer 里做，不建平台。

1. **审查请求加必查项**：门禁发给 reviewer 的审查请求里写明：判断完成条件（含验收文件，见 [T-080](T-080-protected-acceptance-files.md)）是否足以拒绝明显错误的实现；针对候选的关键逻辑构造少量错误实现（建议 2～5 个），确认完成条件或候选的新测试会失败；结果写进审查报告的单独一节（每个变异：改了什么、跑了什么命令、结果）。完成条件不够格时结论为“需修复”，问题清单写明缺什么。
2. **一次性副本可写（用户 2026-10-14 已选）**：门禁为每次审查另建一份候选副本（不是 `verification/review-*` 审查目录本身，也不是 worker 的 worktree），reviewer 以这份副本为工作目录、`workspace-write` 沙箱、断网启动；候选提交、审查目录、worker worktree、共享仓库仍不可写。
   - 门禁的审查启动核对（现在要求 `read-only`）改为核对新边界：工作目录是本次审查的副本、沙箱为 `workspace-write`、网络关闭、`/tmp` 与 `$TMPDIR` 不额外可写（`sandbox_workspace_write.exclude_slash_tmp`、`exclude_tmpdir_env_var`，以实际 CLI 版本的参数为准并在 RESULTS 写明）。
   - 审查结束后门禁核对：候选提交号不变、审查目录与 worker worktree 干净、共享仓库引用未变；然后删除副本。任何一项不符，审查结论作废并上报。
   - 副本里的改动不提交、不进集成路径；结论仍绑定原候选提交号。
3. reviewer 角色卡的措辞由构思主控已同步修改（见下方说明）。

## Acceptance

- [ ] 红态在先：当前 `main` 上审查请求不含完成条件审查与变异要求，reviewer 在审查目录写文件被拒（沿用 T-076 的只读证明，保存读回）。
- [ ] 受控入口：审查启动 argv 与新边界一致；门禁对旧的只读 argv、工作目录不是副本、网络开启、`/tmp` 可写这几种启动参数都拒绝（每种先见红）。
- [ ] 边界证明（真实 Codex reviewer 会话，隔离 home）：在副本里写文件和跑测试成功；向审查目录、worker worktree、共享仓库 `.git` 写入失败（哨兵文件不变、实际 EPERM 原文留证）；`git update-ref` 共享仓库失败；网络请求失败。
- [ ] 结束核对：人为在副本外留下改动的变体使审查结论作废并上报；正常结束副本被删除。
- [ ] 一次真实交付审查：选一张完成条件明显偏弱的夹具任务卡，reviewer 报告里有完成条件审查一节和至少 2 个变异的命令与结果；reviewer 判断是否正确如实记录，不作为门禁通过条件（模型行为不由本票保证）。
- [ ] 真实回合合计不超过 4 个（边界证明加交付审查）；完整 argv 留证；隔离 home 用后删除。
- [ ] 回归 T-076 质量串（审查绑定、不续接会话、写入会话不能审查）与 T-077 套件通过；`project_map.py status` 0 problems。

## 说明

- 改动在 `workbench/src/panes.ts`（审查启动参数）、`workbench/src/gates/core.ts`（审查请求、启动核对、副本建立与清理）；与 T-077 刚接入的审查目录命名与清理重叠，所以 `blocked_by: [T-077]`；与 T-080 重叠的文件由执行主控安排串行。
- T-076 的“只读 reviewer”证明随本票换成新边界的证明，旧结论不替新边界背书。
- 授权来源：用户 2026-10-14 在旁路会话"A2A 多Agent协作的确定性架构"说（逐字）："……第一个 P1 做……然后变异测试可以做，就比如在 reviewer 里做，平台倒是没必要单独做……"，"第一个 P1"= D3；权限做法由用户 2026-10-14 在会话"a2a-构思主控"以选择题作答（逐字）："给一次性副本可写 (Recommended)"，选项原文："门禁为每次审查另建一份候选副本，reviewer 只在这份副本里可写、断网；候选提交和审查目录仍不可改，门禁事后核对它们没变并删副本。最贴近你说的‘在 reviewer 里做’。代价：reviewer 不再是纯只读，T-076 的只读证明要按新边界重做。"`ready_by: ideation`，`ready_rev: 1`。
