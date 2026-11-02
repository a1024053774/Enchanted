---
id: T-237
title: 复盘进程已退出、后台重启后，复盘列表里那一行仍显示“进行中”
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---
## What to build

2026-11-02 Computer Use 实测（`evidence/2026-11-02-batch30/cu-bugsweep/BUGS-r2.md`，截图 `shots/r2-reflect-status.png`）：第一轮 06:02 启动的手动复盘，在目录信任框里选了退出，CLI 随后结束；第一轮结束时隔离后台也被停掉。第二轮用同一状态目录 `/private/tmp/a2a-cu/state` 重新启动，Reflect 页里这一行仍是“进行中”，报告为“—”。库里只有 `retrospective_started`，没有任何结束事件。

期望：复盘的 CLI 退出、或后台重启后找不到它的终端时，这一行显示已结束（没有产出就写没有报告）或“未知”，不能一直显示“进行中”。要查清复盘的结束是怎么判定的、后台重启时为什么没有核对。

## Acceptance

- [x] 先写下可能出错的方式。
- [x] 修前红态：启动复盘、让 CLI 退出且不写报告、重启后台，列表仍显示“进行中”。
- [x] 修后：同一场景显示已结束或未知；正常写出报告的复盘照旧导入。
- [x] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

2026-11-02 关闭，**PASS**。结果记录：[r2/RESULTS.md](../../evidence/2026-11-02-batch30/T-237/r2/RESULTS.md)。

- 判定方式：每分钟的复盘检查在导入之后，看还没导入的复盘的终端。终端的关闭有记录（被关掉，或后台重启时确认 shell 进程已不在）记 `ended`（`terminal_gone`）；启动满一分钟后终端里除 shell 外没有进程记 `ended`（`cli_not_running`）；前台进程组里有 shell 以外的进程仍是进行中。拿不准时（后台恢复中、没接回且不能确认已退出、读不到进程、只剩后台程序）不判结束，复盘上记 `end_check_unknown`（带诊断，原因不变不重复），页面写明无法确认的原因。已结束的复盘之后写出报告照常导入。
- 根因之一在恢复层：core 随后台一起没了、重新启动后，`hc.find` 对找不到的终端直接抛错，恢复走不到 shell PID 退出核对，终端永远“退出未确认”。改为找不到或不再 live 都由 PID 核对确认退出。
- 失败方式写在测试文件开头（8 条）。修前 `82e747f4a` 红态失败于 `exited_cli_marked_ended`；11 个已知坏实现各自失败在对应检查上；候选三次 PASS（19 项，含真实 Electron 读 Reflect 页）。回归：T-136、T-223 三个时区、T-212 重启与 core 崩溃均 PASS。
- 审查：第 1 轮 NO_GO（5 条阻塞，[REVIEW-01](../../evidence/2026-11-02-batch30/T-237/reviews/REVIEW-01.md)），第 2 轮 PASS（[REVIEW-02](../../evidence/2026-11-02-batch30/T-237/reviews/REVIEW-02.md)）。
- Computer Use（Codex `gpt-6.1-terra`）在打包应用上复验四个场景（关终端、CLI 退出、后台连同 core 停掉再重启、CLI 留在前台的反例）全部通过：第 1 轮测审查前版本（[cu-fixcheck](../../evidence/2026-11-02-batch30/cu-fixcheck/REPORT.md)），第 2 轮测最终版本（[cu-fixcheck-r2](../../evidence/2026-11-02-batch30/cu-fixcheck-r2/REPORT.md)）。
- 未直接覆盖（审查非阻塞）：恢复超过一分钟、等待期间被另一轮导入、`background_only`、无法确认原因改变；测试清理用 `pkill -f <夹具目录>`。
- 范围外发现：T-136 测试遗留私有 core（已有 T-232）；CU 复验时重启后历史窗格出现 `TextDecoder` 解码错误，登记 [T-239](T-239-history-pane-textdecoder-error-after-restart.md)。
