---
id: T-040
title: 切换到工作台并删除旧运行路径
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
---

## What to build

M1 第 1～5 项通过且用户认可界面后，主控与 worker 的日常分派改到 Synara；删除 a2a 仓库中 Muster 引擎与 `coop.py` 的运行路径，参考实现留在 git 历史与证据中。更新 AGENTS.md、README、CONTEXT.md 与地图。

## Acceptance

- [x] 用户确认界面外观与切换时机。
- [ ] 删除后仓库内无 Muster/coop.py 运行入口；门禁 8/9/18 项经原生入口仍通过。
- [ ] 一次日常分派经 Synara 完成并留证据。

## 用户决定（2026-10-08）

- 外观："还可以，外观先这样"（T-043）。
- Q1 = A：日常用 fork 构建的桌面版，专用数据目录（`~/Library/Application Support/a2a-workbench`），与可能已装的官方 Synara 分开；Codex 用用户自己的登录。
- Q2 = A：主控仍是终端中的 Claude Code，派发、查状态、回收改为调用门禁 CLI/MCP；worker 由 Synara 原生创建为 Codex 会话，用户在任务窗口看进度。以后再考虑把主控搬进 Synara。
- Q3：先推送（a2a `be59634`、fork `d3b5bcc` 已推送），再开始删除。

分两部分并行：A 删除旧运行路径（a2a 仓库，经 Herdr worker）；B 工作台启动器与专用数据目录（fork）。两者完成后，主控经 Synara 完成第一次日常派发。

## Resolution

### A 部分交付（2026-10-08）

**INCOMPLETE，需要主控决定；ticket 保持 open，删除后验收复选框未勾选。** 代码候选 `1279adb73c06308fc71eebf35002628730f320d5` 已删除 2,966 个退役受控文件，提升原生验收与边界替身，并更新 README；未 push、未修改 fork。删除前原生 8/9/18 通过；删除后交付 8/8、编排 18/18、恢复第二轮 9/9，指向已删除入口的反例明确失败。

恢复首轮 1 项失败：并发 verify/integrate 未在原有 2 秒时限内退出，两轮现场均保留。唯一一次 fresh-context 只读独立审查为 FAIL，恢复时限验收 NO_GO；同源重跑不能排除首轮业务红态。主控须定位失败边界并决定必要修正及真实入口复验，不放宽断言；AGENTS.md、CONTEXT.md、地图治理更新仍归主控，末次 status 报 CONTEXT.md stale。详见 [A 部分记录](../../evidence/2026-10-08-batch4/T-040-A/RESULTS.md) 与 [独立审查](../../evidence/2026-10-08-batch4/T-040-A/独立审查.md)。

### B 部分：启动器与主控入口（2026-10-08）

INCOMPLETE：最终真实隔离的启动、重复启动、HTTP gate status、0600/错误 token 反例、停止无监听、重启 token 轮换和数据保留均已 PASS；审查发现的就绪/构建判断问题已修正并取得旧提交红态、新提交绿态及限定复审 PASS。全仓测试有 5 项失败，未在父修订证明基线情况。fork `a2a` 分支最终提交 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`，新增 `a2a/scripts/workbench`、`gate` 与中文使用说明。默认专用目录前后未创建，未登录、未调用 Synara provider、未 push。

完整结果、失败记录、隔离输入、原始命令和收尾归档见 [T-040-B RESULTS](../../evidence/2026-10-08-batch4/T-040-B/RESULTS.md)。T-040 继续 open；最终地图 0 problems / 0 stale。全仓失败的基线核对、专用目录首次启动和日常真实分派交回主控。
