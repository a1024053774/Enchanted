# T-228 结果记录（2026-11-01）

状态：**PASS**。

- 代码提交：`10e4fcbfd`（基线 `03ba1cf54`）。
- 改动的文件：`workbench/src/hc.ts`、`workbench/src/daemon.ts`、`workbench/README.md`、`workbench/tests/test_t212_shell_hc_e2e.py`，以及新增的 `workbench/tests/test_t228_core_identity_e2e.py`。
- 写代码的是 Claude Code 主控，在会话里写。审查由 Codex `gpt-6.1-sol` high 做，每轮新开干净的只读会话，共三轮。

## 认 core 的判据

后台连上 socket 后，在同一条连接上调 `server.status`，取得对方 core 的 pid。认这个 core 须同时满足两条：

1. 它不在后台的进程组里；
2. 它打开着本会话私有状态目录里的 `herdr-core/<session>/core.lock`。

第 2 条用 `lsof -a -p <pid> -Fp -- <lock>` 核对，由 lsof 按文件身份匹配。lsof 退出非 0、超时，或输出里没有 `p<pid>`，都不认。

启动失败时，后台记 `hc_start_failed` 事件，带上原因，然后退出。事件写入也失败时，抛出同时含两个错误的 `AggregateError`。

## 验收对照

| 验收项 | 证据 | 结论 |
| --- | --- | --- |
| 先写下出错方式 | 新测试开头列出失败方式 1–9 | 满足 |
| 修前红态 | `red-holder-01`：holder 重拉的 core 被误拒（`private hc core did not detach`）。`red-foreign-01`：外来 core 被接受 | 满足 |
| 修后两种场景 | `r3-green-holder`：接受，shell 进程号不变，`screen: inexact`。`r3-green-foreign`：拒绝，事件带锁路径。两者加 `--non-ascii`（`LC_ALL=C`，目录名含 `测试 目录`）也都 PASS | 满足 |
| 测试能区分好坏实现 | 变异“任意 core.lock 都算”，以及三轮各自的“忽略 lsof 结果”，都在 foreign 场景失败 | 满足 |
| T-212 回归 | `r3-t212-core-crash`、`r3-t212-electron`（mismatched-screen）PASS；用户自己的 core 与状态目录前后不变 | 满足 |
| 独立审查 | REVIEW-01：FAIL（lsof 转义；事件写入盖掉原错误）。REVIEW-02：FAIL（核对与连接不是同一个 core）。REVIEW-03：PASS | 满足，无未处理的阻塞意见 |

## 主控核对

- 主控逐个读了上表各 run 的 `run.json.checks`。三个 FAIL 记录不过的项，正好是红态或变异应当不过的业务断言；其余 run 的检查全为 true。
- 三轮审查的意见都已核实属实，并已修正。
- REVIEW-03 第 4 条限制说 REPORT 第 7 行仍写着旧描述。现在的 REPORT 第 7 行已写明“第三轮起经同一连接的 `server.status` 取 pid”，与代码一致。
- 已入库的补丁与冻结的 `candidate.patch` 逐字一致。

## 没覆盖的

以下几条路径只做了静态核对，没有端到端证据：核对期间换 core、lsof 故障或超时、同进程组、事件写入失败。

- 主控删掉了两处失败现场：`t212-crash-itqemlik` 和非 ASCII 红态现场。删之前读过的值写在 REPORT 的“偏差”一节，run.json 与日志都还在。
- 类型检查没跑成。

## 文件

- 本目录：REPORT.md、三轮审查及各自的提示词、变异 diff、`r3-runs.log`。
- REPORT 里链接的 run 目录和日志、各轮补丁、审查会话日志都已归档到 WD，清单见 [archive/evidence.archive.json](archive/evidence.archive.json)。测试现场的清单见 [archive/fixtures.archive.json](archive/fixtures.archive.json)。
