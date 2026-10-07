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

**BLOCKED（2026-10-07）**。冻结候选为 `0bea0e6728548fd894addbcb54ccccbfff6ff2a2`。`coop.py` 已改为只调用显式 `MUSTER_BIN`，无 Herdr 回退；交付/恢复/编排在独立 Muster pane 中分别 8/9/18 项通过。去掉 fence 校验的 mutant 在同一真实运行时中被业务断言抓住。

真实 `run` 启动 Codex 后遇到目录信任对话；task 为 paused，prompt_sent=false，没有 submit、verify、integrate 或回收，不能关闭 ticket 或声明切换通过。用户正常 `~/.codex` 配置原始字节未变；暂停时隔离 server/pane 保留；交接前只读复核发现 server 已退出、原因未知。会话目录、原始 UI、状态与归档仍保留，等待主控核对外部状态和批准目录信任，不能依赖旧 pane ID。独立审查尚未执行，恢复后完成真实 run，再冻结并进行一次 fresh-context 只读审查。

逐项结果、版本、命令与原始记录见 [T-029 RESULTS](../../evidence/2026-10-07-m1-batch3/T-029/RESULTS.md)，具体权限请求和恢复边界见 [APPROVAL-REQUEST](../../evidence/2026-10-07-m1-batch3/T-029/APPROVAL-REQUEST.md)。README/CONTEXT 的 stale 项由主控按任务书权限处理，worker 未修改根文档。
