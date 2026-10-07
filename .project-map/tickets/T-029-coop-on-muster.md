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
- [x] 完成一次真实 `run`：Codex worker 在 muster pane 中完成分页夹具、显式 submit，经独立 oracle 验收、CAS 集成后回收 pane；运行记录以追加方式保存。
- [x] 反事实检查：去掉 attempt 绑定或 fence 校验的错误实现，会被 Muster 运行时上的验收抓住。

## Resolution

**INCOMPLETE：四项验收均 PASS，待独立只读审查（2026-10-07）**。生产候选 `66565453cf3f188c7b368fc91a512222b6cab0bc` 已在 Muster 运行时上通过 8/9/18、fence mutant 和真实 run。当前 task=accepted，attempt=`afa79f067af44952b5d03d70c76051fa`，fence=4，独立 oracle 12 项通过，CAS 写入 `47976b1538721d9d58fa6787c23f48a2c2e72b37`，agent idle 后 pane 回收。旧三次失败与全部历史保留。

按主控第三份决定，已回退无效的 Git common dir 声明；隔离 home 只复制 auth、仅信任已核对夹具，并逐字加入用户的 git add / git commit 两条 allow 规则，无其他规则/config/hooks。此次未出现权限对话，用户 config/hooks/rules 字节未变，整个隔离 home 和 owned server 已清理。无人值守 run 依赖 worker Codex 允许 git add / git commit，生产配置前提由主控写入 README；worker 不安装生产规则、不改根文档。

当前四项证据见 [RESULTS](../../evidence/2026-10-07-m1-batch3/T-029/RESULTS.md)，完整实际 argv、身份、Git/Oracle 与 idle 关闭核对见 final-runtime-04/delivery-checks.json。独立审查完成前保持 open，不能复用 T-027 审查或宣布 M1 完成。README/CONTEXT stale 项交主控处理。
