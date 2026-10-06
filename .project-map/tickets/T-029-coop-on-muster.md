---
id: T-029
title: coop.py 改接 Muster 控制接口
type: build
status: open
blocked_by: [T-027]
claimed_by:
supersedes:
---

## What to build

主控用 `coop.py` 管理受管任务时，worker 由 Muster 分派到 muster pane 中，不再经过 Herdr。门禁语义保持不变：认领、显式交付、独立验收、CAS 集成和回收都与首轮一致。三套验收和一次真实 `run` 在 Muster 运行时上通过。

只替换可执行文件，不保留 Herdr 与 Muster 两条并行路径；Herdr 版本留在 git 历史中。对应关系见 [spec](../specs/workbench-m1-2026-10-06.md) 的"控制接口与名词"。

## Acceptance

- [ ] `coop.py` 只调用 `muster`，不再调用 `herdr`；版本检查和启动参数规则保留。
- [ ] 交付 8 项、恢复 9 项、编排 18 项在 Muster 运行时上通过；编排负例的替身改为模拟 muster 边界，并标明是隔离证据。
- [ ] 完成一次真实 `run`：Codex worker 在 muster pane 中完成分页夹具、显式 submit，经独立 oracle 验收、CAS 集成后回收 pane；运行记录以追加方式保存。
- [ ] 反事实检查：去掉 attempt 绑定或 fence 校验的错误实现，会被 Muster 运行时上的验收抓住。

## Resolution

未执行。
