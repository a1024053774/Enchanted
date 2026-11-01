# T-230 执行报告（2026-11-01）

状态：**PASS**，代码提交 `d4c9f9dc1`。写代码的是 Claude Code 主控，在会话里写；基线为 `121c43f21`。

## 改动

- `workbench/src/panes.ts` `startShell`：项目终端启动时，经 `/usr/bin/env -u` 去掉 `HC_SOCKET`、`HC_SESSION`、`HC_TERMINAL_ID`、`HC_TERMINAL_SOCKET`，与去掉 XDG 变量的做法相同。编排后台与私有 core 仍用原来的受控环境。`A2A_TERMINAL`、`A2A_TERMINAL_SOCKET` 保留，a2a 命令照常可用。
- `workbench/app/renderer.tsx`：窗格类型加 `screen`；`screen === 'inexact'` 时，标题栏显示“历史不完整”，悬停说明“终端服务重启过，之前的输出只接回了最后一段”。后台的复位与接回逻辑没有改动。
- `workbench/README.md`：第 10 行补充终端不带私有 core 的地址；第 33 行补充界面提示。
- `workbench/tests/test_t212_hc_boundaries_e2e.py`：原来断言终端里 `HC_SESSION`、`HC_SOCKET` 等于私有身份，现在改为断言四个变量都不存在。leak-xdg 变异随之改写。hc 缓存路径改为优先取 `ENCHANTED_HC_CACHE_DIR`，见下文“偏差”第 4 条。
- 新增 `workbench/tests/test_t230_terminal_hc_isolation_e2e.py`，开头列出失败方式 1–9（第 9 条是审查后补的）。

## 红态（基线代码，真实入口）

| run | 结果 |
| --- | --- |
| `red-boundaries` | 终端里四个 `HC_*` 变量都存在，修改后的边界断言失败 |
| `red-race` | 终端里有四个变量。core 被杀后，终端里的 `hc ls` 抢先拉起外来 core：pid 43626，父进程为 1，没有持有私有 `core.lock`，夹具 HOME 下出现该会话的状态目录。原终端的 shell 没了，探针退出码 129。后台重启时，T-228 的身份核对拒绝了这个外来 core，后台没起来。这就是 T-220 run-01 的情形 |
| `red-ui-02` | 后台检查全过；界面上 inexact 窗格没有“历史不完整”（`ui_inexact_pane_says_history_incomplete: false`），exact 窗格没有提示 |
| `red-ui-01-electron-unreachable` | 无效：Electron 的 CDP 端口没就绪，测试就去连了（ECONNREFUSED），没走到界面断言 |

## 绿态（候选代码）

- `green-ui-07`、`green-boundaries-03`：在恰好等于提交 `d4c9f9dc1` 内容的工作区上重跑，都是 PASS（11 项、5 个场景）。`green-ui-06` 跑的时候，工作区里还有 T-229 改了一半的代码（`panes.ts`、`daemon.ts`、`inputDraft.ts`）。主控先把这三个文件备份，恢复成只有 T-230 的状态，跑完这两项，再把 T-229 的改动原样放回。`committed.patch` 是提交时暂存区的 diff。
- `green-ui-06`：加了新断言后的第一次运行，PASS，11 项检查全为 true。比 `green-ui-05` 多一项 `terminal_hc_answered_without_enchanted_terminals`：终端里的 `hc --json ls` 退出码为 0，回答是 `{"hidden_finished":0,"terminals":[]}`，即它连到的是夹具 HOME 下用户自己的 core，看不到 Enchanted 的终端。基线的 `red-race` 里这次调用退出码为 129，新断言在基线上同样会失败。
- `green-ui-05`：加这项断言之前的运行，PASS，10 项检查全为 true。
  - 终端里没有四个变量，a2a 身份还在。
  - core 被杀，同时触发终端里的 `hc ls`：私有 core 由 holder 在受控环境下重新拉起（父进程不是 1，lsof 核对持有私有锁），夹具 HOME 下没有外来会话目录，原 shell 还在。
  - 后台重启后接回同一个 shell 进程，标 `inexact`。
  - 界面上 inexact 窗格显示“历史不完整”，新开的 exact 窗格不显示。截图为 `green-ui-05/inexact-pane.png` 与 `green-ui-05/exact-pane.png`。
- `green-boundaries-02`：PASS，五个场景（xdg-unset、xdg-values、xdg-empty、corrupt-cache、long-holder-socket）全过，四个变量都断言为不存在。
- `mutant-leak-xdg-02`：按预期失败。变异后终端读到泄漏的 XDG 值，断言识别了出来。

## 验收第 4 条：经 a2a 命令跨终端发字

这一条没有另写新测试，由 T-216 的既有 e2e 在候选代码上重跑覆盖。

- `t216-provenance-claude`、`t216-provenance-codex`：受管 worker 经门禁命令行（身份是 `A2A_CAPABILITY`）上报问题，后台把它推进主控所在的项目终端。主控终端的这次提交认领为系统输入，不进用户输入记录（`system_not_user`、`same_body_claim_once`）。
- `t216-issue-push`（GUI）覆盖同一条推送路径。
- 同一批运行里，主控 CLI 在项目终端里执行 `a2a request executor` 申请角色并获批。项目终端里已经没有 `HC_*` 变量，这条 a2a 命令仍然送达后台，说明它只依赖 a2a 自己的终端令牌（`A2A_TERMINAL`、`A2A_TERMINAL_SOCKET`）。

第一轮审查指出：上一版报告把 worker 的上报写成“在项目终端里执行 `a2a issue`”，这不对。worker 走的是门禁命令行，上面已按实际路径改写。跨终端投递与来源判定的覆盖仍然成立。

## 回归（候选代码，`run-regression.sh`，结果在 `regression-runs.log`）

| run | 结果 |
| --- | --- |
| t212-core-crash、t212-electron（mismatched-screen） | PASS |
| t228-holder、t228-foreign | PASS |
| t216-provenance-claude/codex、t216-history-codex、t216-issue-push、t216-r2-online、t216-codex-local、t216-recover、t216-unknown-gui | 都是 PASS，没有失败的检查 |
| green-boundaries（第一次） | 五个场景里前三个 PASS，到 corrupt-cache 时找不到 hc 缓存而中止，原因见“偏差”第 4 条。改名保留为 `green-boundaries-01-cache-path`，修正后的重跑是 `green-boundaries-02` |
| mutant-leak-xdg | 按预期失败 |

主控逐个读了每个 run 的 `run.json` 或 summary，没有失败的检查项。用户自己的 core 与状态目录前后不变：T-230 测试与 T-212 测试都做了核对。

## 偏差

1. 第一版 UI 测试在 CDP 端口就绪前就去取诊断，现场保留为 `green-ui-01-diagnostic-too-early`。
2. 侧边栏选择器写成了 `data-terminal-launch`，实际是 `data-agent-launch`，现场保留为 `green-ui-02-wrong-sidebar-selector`。T-212 的 Electron 测试用的是同一个旧选择器，只因为界面上只有一个窗格才碰巧通过。这不在本票范围，没有改。
3. `green-ui-03`、`green-ui-04` 是 PASS，但测试每轮轮询都点一次侧边栏，窗格反复恢复，`green-ui-04` 的截图里留着恢复遮罩。改为只点一次、等窗格稳定后再截图，即 `green-ui-05`。
4. 边界测试的 corrupt-cache 场景原来固定从 `ROOT.parent/hc-cache` 读 hc 包，只在 worktree 布局下才找得到；从主 checkout 运行时找不到。现在改为优先取 `ENCHANTED_HC_CACHE_DIR`，与后台使用同一个缓存目录。
5. `Electron.until` 报出的错误是它最后捕获的那次异常，可能已经过时，排查 UI 超时时被它误导过一次。

## 审查

- REVIEW-01：PASS，附两条 P2 意见，主控都核实属实：
  1. `agent_call.exit` 只记录、不参与判定。已补断言（失败方式第 9 条），重跑为 `green-ui-06`。
  2. REPORT 把 T-216 worker 的上报路径写错了。已按实际路径改写，见“验收第 4 条”。
- 第一轮审查之后，候选只改了测试里的这一条断言和本报告，产品代码没有变。改后没有再开第二轮审查。

## 没覆盖的

- “终端里敲 `hc` 用的是用户自己的设置”，测试只在夹具 HOME 下核对（不碰私有 socket，不在私有会话下起 core）；没有在用户真实 HOME 里跑，这是有意不碰用户自己的 core。
- 类型检查没有单独跑；renderer 的改动经 Electron 构建并在真实界面上显示出来。
