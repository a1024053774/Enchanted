# T-230 结果记录（2026-11-01）

状态：**PASS**。

- 代码提交：`d4c9f9dc1`（基线 `121c43f21`）。
- 改动的文件：`workbench/src/panes.ts`、`workbench/app/renderer.tsx`、`workbench/README.md`、`workbench/tests/test_t212_hc_boundaries_e2e.py`，以及新增的 `workbench/tests/test_t230_terminal_hc_isolation_e2e.py`。
- 写代码的是 Claude Code 主控，在会话里写。审查由 Codex `gpt-6.1-sol` high 做，新开干净的只读会话，一轮。

## 做了什么

- 项目终端启动时，经 `/usr/bin/env -u` 去掉 `HC_SOCKET`、`HC_SESSION`、`HC_TERMINAL_ID`、`HC_TERMINAL_SOCKET`。这是项目终端唯一的启动入口，worker、主控、普通终端都从这里起。a2a 自己的终端身份 `A2A_TERMINAL`、`A2A_TERMINAL_SOCKET` 保留。
- 界面上，`screen` 为 `inexact` 的窗格在标题栏显示“历史不完整”；`exact`、缺失或其他值都不显示。后台的复位与接回逻辑没有改。

## 验收对照

| 验收项 | 证据 | 结论 |
| --- | --- | --- |
| 先写下出错方式 | 新测试开头列出失败方式 1–9 | 满足 |
| 修前红态 | `red-boundaries`：终端里四个变量都在。`red-race`：core 被杀后，终端里的 `hc` 拉起外来 core（父进程为 1，没有持有私有锁，夹具 HOME 下出现会话目录），原 shell 没了，后台重启时拒绝这个外来 core。`red-ui-02`：界面没有提示 | 满足 |
| 修后：变量不存在，终端 hc 碰不到私有 core，私有 core 按受控环境接回，原终端还在 | `green-ui-07`（11 项全过），`green-boundaries-03`（5 个场景全过）。两项都在恰好等于提交内容的工作区上跑 | 满足 |
| 经 a2a 命令跨终端发字有记录，目标提交不记为用户输入 | T-216 既有 e2e 在候选上重跑：`t216-provenance-claude/codex` 的 `system_not_user`、`same_body_claim_once`，以及 `t216-issue-push`；同一批运行里，项目终端里的 `a2a request executor` 照常送达 | 满足，覆盖方式见下文“没覆盖的” |
| inexact 窗格显示“历史不完整”（截图），复位与接回不变 | `green-ui-05`、`green-ui-06`、`green-ui-07` 的 `inexact-pane.png` 与 `exact-pane.png` | 满足 |
| T-212、T-216 既有 e2e 仍通过 | `regression-runs.log`：t212 两项、t228 两项、t216 八项都是 PASS | 满足 |
| 独立审查 | REVIEW-01：PASS，两条 P2 意见都已核实并处理 | 满足，无未处理的阻塞意见 |

测试能区分好坏实现的依据：

- leak-xdg 变异被识别出来（`mutant-leak-xdg-02`）。
- 基线上的红态，就是新断言应当识别出来的情形。

## 主控核对

- 回归集每个 run 的 `run.json` 或 summary，主控都逐个读过，没有失败的检查项。
- 用户自己的 core（pid 87319、87320、87407）与状态目录前后不变。
- 第一轮回归里的 green-boundaries 没跑完：测试固定从 `ROOT.parent/hc-cache` 读 hc 包，从主 checkout 运行时找不到。现在改为优先取 `ENCHANTED_HC_CACHE_DIR`，重跑后通过。失败现场已归档。
- `green-ui-06` 跑的时候，工作区里还有 T-229 改了一半的代码。主控先把这几个文件备份，恢复成只有 T-230 的状态，重跑出 `green-ui-07` 与 `green-boundaries-03`，再把 T-229 的改动原样放回。
- REVIEW-01 之后，候选只改了测试里的一条断言（失败方式第 9 条）和报告，产品代码没有变；改后没有开第二轮审查。

## 没覆盖的

- 验收第 4 条没有新写测试。T-216 的用例里，发送方是受管 worker，经门禁命令行（`A2A_CAPABILITY`）上报，不是“从一个项目终端发 a2a 命令到另一个项目终端”。项目终端里的 a2a 命令能用，靠的是同一批运行里的 `a2a request executor` 送达，这是间接证据。
- “终端里敲 `hc` 用的是用户自己的设置”只在夹具 HOME 下核对过，没有在用户真实 HOME 里跑，这是有意不碰用户自己的 core。
- 类型检查没有单独跑。
- 范围外发现：
  - `t216-issue-push`、`t216-r2-online` 跑完后，没收掉它们夹具里的私有 core 和一个 Claude 进程。主控在归档前结束了这些进程，已开缺陷票 [T-232](../../../.project-map/tickets/T-232-t216-tests-leave-fixture-cores.md)。
  - T-212 Electron 测试点侧栏行用的 `data-terminal-launch` 已经过时，什么也点不到，只因为界面上只有一个窗格才碰巧通过。已开缺陷票 [T-233](../../../.project-map/tickets/T-233-t212-electron-stale-selector.md)。

## 文件

- 本目录：REPORT.md、REVIEW-01.md 和审查提示词、`run-regression.sh`、`regression-runs.log`、`candidate.files`。
- 各 run 目录、日志、截图、补丁、审查会话日志都已归档到 WD，清单见 [archive/evidence.archive.json](archive/evidence.archive.json)。测试现场的清单见 [archive/fixtures.archive.json](archive/fixtures.archive.json)。
