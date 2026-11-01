# T-227 结果记录（2026-11-01）

状态：**PASS**。

- 代码提交：`ce8fcfa29`（基线 `03ba1cf54`）。改动的文件：`workbench/src/panes.ts`、`workbench/tests/test_pane_trace_failure.ts`、`workbench/tests/test_t212_trace_failure_e2e.py`、`workbench/README.md`。
- 写代码的是 Claude Code 主控，在会话里写。审查由 Codex `gpt-6.1-sol` high 做，每轮新开干净的只读会话，共四轮。

## 选定的规则

执行主控按缺陷级在 T-004 的范围内决定，写进代码注释：

1. **初次打开失败算没建成。** 初次打开项目终端时 trace 就写失败，后台当场关掉刚起的 hc 终端：杀进程、核对退出、记 `shell_closed`，然后把原错误返回给调用者。关闭也失败时，抛出同时含两个错误的 `AggregateError`，消息里两个原因都写。
2. **窗格停写 trace。** 窗格的任何 trace（`pty.raw`、`native.jsonl`、主控登录会话的脱敏 trace）写失败后，这个窗格记为失败，之后不再写它的 trace。后续输出照常读：原生日志扫描、OSC 7501 报告。失败窗格的写入，包括终端协议应答，一律拒绝，这一点与基线相同。
3. **失败是终局。** 第一个失败原因保留；同一种失败每个窗格只记一次；事件库写不进的告警也只报一次。

## 验收对照

| 验收项 | 证据 | 结论 |
| --- | --- | --- |
| 先写下出错方式 | e2e 测试开头的失败方式 6–10；隔离测试开头的失败方式 | 满足 |
| 修前红态 | 隔离测试：受管窗格 5 帧记了 5 条。resize：失败后记了 43 条。initial：失败的终端仍 live、shell 仍在、没有 `shell_closed` | 满足 |
| 修后第 1 项 | `r4-green-initial`：私有 core 的终端列表里没有它，shell 已退出，记了 `shell_closed`，调用者收到 `pane_unavailable` | 满足 |
| 修后第 2 项 | `r4-green-resize`：只记 1 条；trace 恢复可写后，输出计数从 1 走到 40，trace 字节不变 | 满足 |
| 另一个终端照常可用 | resize 与 initial 的 `other_still_usable`、`socket_survives` | 满足 |
| 受管窗格只记 1 条 | 隔离测试三个场景（trace、trace 加事件库只读、native trace）全部通过 | 满足 |
| T104、T107 回归 | 各轮都是 PASS，最后一轮为 `r4-t104.json`、`r4-t107.json` | 满足 |
| 独立审查 | REVIEW-01、02、03 为 FAIL，意见都已核实并修正；REVIEW-04 为 PASS | 满足，无未处理的阻塞意见 |

用来证明测试能区分好坏实现的变异：

- 失败后仍重写 trace；
- 初次失败不关终端；
- 只记一次但照写。

三个变异都被对应的业务断言识别出来。

## 主控核对

- 四轮审查的每条意见，主控都对照代码或实测核实过，属实的已修正，报告里逐轮记录。
- 已提交的补丁与冻结的第四轮 `candidate.patch` 内容逐字一致，只有 `index` 行里哈希缩写的长度不同。
- 第四轮审查第一次启动时 Codex 额度用完，没开始审，日志保留为 `review-04-usage-limit.session.log`。用户换了 Codex 账号后重跑，就是 REVIEW-04。

## 没覆盖的

以下几条路径没有专门的运行证据：关闭也失败、主控登录会话的 trace 写失败、agy/opencode 停写之后的 OSC 7501 报告（测试检查的是排在它前面的原生日志扫描）。

- 单元测试对照只算弱证据：50 个与窗格状态有关的单元测试，在 HEAD 与新代码上退出码逐个相同，但其中 32 个在两边都失败，多数是调用方式不对或测试本身过时。
- 运行记录里 `revision` 为 null；各轮运行与候选的对应关系，靠“先跑完、再冻结”这个顺序保证。
- 范围外发现：`workbench/tests/test_native_final_read.ts` 在 HEAD 上就失败，8 个场景报 `hook_native_session_mismatch`。已另开缺陷票 [T-231](../../../.project-map/tickets/T-231-native-final-read-test-stale.md)。

## 文件

- 本目录：REPORT.md、四轮审查和各自的提示词、变异 diff、单元测试对照脚本。
- REPORT 里链接的运行目录与日志、各轮补丁、审查会话日志都已归档到 WD，清单见 [archive/evidence.archive.json](archive/evidence.archive.json)。测试现场的清单见 [archive/fixtures.archive.json](archive/fixtures.archive.json)。
