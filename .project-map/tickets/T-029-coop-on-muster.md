---
id: T-029
title: coop.py 改接 Muster 控制接口
type: build
status: open
blocked_by: [T-027]
claimed_by: Codex worker wF:pT
supersedes:
---

## What to build

主控用 `coop.py` 管理受管任务时，worker 由 Muster 分派到 muster pane 中，不再经过 Herdr。门禁语义保持不变：认领、显式交付、独立验收、CAS 集成和回收都与首轮一致。三套验收和一次真实 `run` 在 Muster 运行时上通过。

只替换可执行文件，不保留 Herdr 与 Muster 两条并行路径；Herdr 版本留在 git 历史中。对应关系见 [spec](../specs/workbench-m1-2026-10-06.md) 的"控制接口与名词"。

## Acceptance

- [x] `coop.py` 只调用 `muster`，不再调用 `herdr`；版本检查和启动参数规则保留。
- [x] 交付 8 项、恢复 9 项、编排 18 项在 Muster 运行时上通过；编排负例的替身改为模拟 muster 边界，并标明是隔离证据。
- [ ] 完成一次真实 `run`：Codex worker 在 muster pane 中完成分页夹具、显式 submit，经独立 oracle 验收、CAS 集成后回收 pane；运行记录以追加方式保存。
- [x] 反事实检查：去掉 attempt 绑定或 fence 校验的错误实现，会被 Muster 运行时上的验收抓住。

## Resolution

**BLOCKED（2026-10-07）**。当前冻结候选 `09a576b37f0e3f303cdb70f389a3da76cfedb1fd` 的构建、8/9/18、fence mutant 通过。原 b102c2a0ec3b447f8a022c1c042d2b13 的 Git 请求仅按一次 Esc 拒绝，确认 idle 后 CLI reclaim，dirty worktree 与历史保留。

修复前真实 index.lock 拒绝及实际 argv 红态均保留。dispatch 现在只追加 task.repo 的 Git common dir 写目录，参数回归绿态，实际 Codex 进程 argv 已核对相同；但新 attempt `a4107e835c8a4b17aec0fea46f1a87f2`、fence=3 在相同 Git 暂存请求上再次 blocked。因此目录声明合同通过，无人值守 Git 提交的真实绿态尚未成立，不能称该缺陷已完整修复。未回答当前 UI，未再增加目录、规则、hook 或改变沙箱。

按已生效 AGENTS 66fa604 的 idle 规则，自动回收旧实现的提前关闭被业务红态抓住，加入有界只读等待后绿态；业务门禁不变。当前真实 run=paused、task=claimed，未 commit/submit/verify/integrate/reclaim，独立审查仍未执行，ticket 保持 open。

server、blocked pane、dirty worktree 与证据保留。auth/config/hook 副本删除且未重建；后台曾重建临时缓存目录，已再次清理，最终结束客户端后须再核对。当前请求见 [APPROVAL-REQUEST-03](../../evidence/2026-10-07-m1-batch3/T-029/APPROVAL-REQUEST-03.md)，全部证据与旧失败见 [RESULTS](../../evidence/2026-10-07-m1-batch3/T-029/RESULTS.md)。根文档 stale 项交主控处理，worker 未改根文档。
