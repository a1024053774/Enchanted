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

**BLOCKED（2026-10-07）**。当前冻结候选 `328922f94cb24ed05a4cb5d448427d87be3fb445` 的构建、交付/恢复/编排 8/9/18 和 fence mutant 检查通过，生产门禁与上一候选一致。

主控许可后，最小复现证实同组 server 随启动工具结束而消失，独立进程组则持续运行；已修夹具生命周期，不改引擎。原 attempt 经真实同命名空间权威清单与原 attempt CLI reclaim，历史/worktree/布局保留。新的隔离 CODEX_HOME 只复制 auth.json 与已批准夹具的信任配置，不安装 hook，已整目录删除，用户配置字节未变。

同一注册 task 的新 attempt `b102c2a0ec3b447f8a022c1c042d2b13`、fence=2 已投递并修改 pager.py，但 Git 的 index.lock 写入触发 `git add -- pager.py` 权限对话。主控许可不包括其他权限；worker 没有答复，run=paused、task=claimed，当前脱离进程组的 server 与 blocked pane 仍保留。尚未 commit/submit/verify/integrate/reclaim 当前 attempt，不能关闭 ticket 或声明切换通过。fresh-context 独立审查仍待完整真实 run 后执行。

当前权限请求见 [APPROVAL-REQUEST-02](../../evidence/2026-10-07-m1-batch3/T-029/APPROVAL-REQUEST-02.md)，逐项证据及前次失败见 [RESULTS](../../evidence/2026-10-07-m1-batch3/T-029/RESULTS.md)。当前 README stale 项交主控处理，worker 未改根文档。
