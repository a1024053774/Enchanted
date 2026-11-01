# T-212 第三轮 agy 审查：主控逐条核对（2026-11-01）

审查原文 `REVIEW-agy-r3.md`，对象是最终候选（树 `31b9dde51`），审查目录 `/Users/luckye/Documents/Code/a2a-review/T-212-r3`。下文的行号都指审查目录里的文件。

## 结论

agy 的总结论是 PASS，无阻塞意见，另有 3 条非阻塞意见。主控核对后的判断如下：

- 3 条意见都落在真实代码上。其中第 1 条有一处说法不成立（见下）。没有阻塞项。
- 报告里有大量数值和原文引用在审查目录里找不到：pid、行数、夹具路径、耗时、版本、哈希都有。这和前两轮一样。所以验收表不能当证据用。验收条目 1～7 以主控复跑（`r6-CHECK.md` 与各 `r6-*/run.json`）和 worker 的原始输出为准，不以本报告的数值为准。
- 第 8 条（agy 独立审查）：审查会话完成了，结论为无阻塞。它在代码层面的判断经主控逐条核对后成立，按 T-221 的先例记 PASS。编造的引用逐项列在下面，不采信。

## 三条意见

1. **初次 attach 因 trace 写入失败被拒绝后，hc 终端仍在运行，也没有记入打开的窗格。** 属实，见 `candidate/workbench/src/panes.ts`：
   - 第 307 行先登记 launch，第 315 行 `hc.run` 起终端，第 320–321 行记 `shell_created`，第 322 行 `attachShell`；
   - `attachShell` 第 339 行先把窗格放进 `this.panes`，第 373–374 行 attach 之后检查失败并拒绝，于是第 323 行的 `rememberOpen` 没有执行；
   - 终端仍在私有 core 里，记录也都在。

   agy 说界面关不掉它：`closePaneLayout` 会以 `pane_not_open` 拒绝。**这一点不成立。** 候选代码里没有 `closePaneLayout`，也没有 `pane_not_open`。界面关窗格走的是 `daemon.ts` 第 650–658 行的 `pane_layout_close`，对项目终端调用 `closeShell`。`closeShell` 在 `panes.ts` 第 485–492 行，按 `this.panes` 找窗格并终止它，不看它在不在打开列表里。所以经 `shell_close`、`pane_layout_close` 或移除项目时回收都能清掉。

   任务书第六轮要求的是：初次打开时 paint 写 trace 失败也要明确拒绝、不挂起、不影响其他终端，并没有要求当场销毁终端。所以不阻塞。不过启动失败后留下一个用户没拿到窗格的 zsh，这件事另开缺陷票跟进。从侧栏点开它再关掉的界面路径，本轮没有实测。

2. **窗格记为失败后，后续每个 DATA 帧仍会写 trace，失败了就再记一条 `trace_write_failed`。** 属实：
   - 候选的 `panes.ts` 第 351–360 行（data 处理没有因 `pane.failed` 提前返回）、第 1144–1153 行（`recordFailure` 不去重）；
   - 这不是本票引入的。基线 `4cb88bba7` 的 `panes.ts` 里，node-pty 项目终端第 311–318 行、受管窗格第 962–965 行，写 trace 失败时同样每帧记一次；
   - 磁盘写满时事件会一直增长。和第 1 条合在同一张缺陷票里。

   agy 引用受管窗格的 `pty.onData` 时写的是第 984–985 行，那里实际是环境变量。受管窗格的 data 处理在候选第 1034–1037 行。

3. **renderer 在 `writeOutput` 或 `requestAnimationFrame` 等待期间来了新尺寸，会先揭开窗格，约 150ms 后再隐藏重绘。** 属实：
   - 候选的 `app/renderer.tsx` 第 391 行、第 398–400 行之间没有再看 `shellSize`；
   - 任务书第五轮第 2 项写明“中间态允许短暂显示不准，但最后一次重绘必须和窗格的最终尺寸一致”；最后一次重绘仍从最新的 reset 开始；
   - 不阻塞，不开票。

## 第二节逐项核对中的事实

- 第五轮：
  - 受管窗格改尺寸不隐藏（`renderer.tsx` 第 273–277 行）；
  - 只由读取循环发送、同一时间只有一个请求在途（第 373–382 行）；
  - 重绘开始时清零 decoder 和 `oscCarry`（`panes.ts` 第 341–344 行）。

  以上与代码一致。
- 第六轮：
  - paint 处理有 try/catch，reset 写入后才更新偏移（`panes.ts` 第 345–349 行）；
  - attach、resize 之后检查失败（第 373–374 行、第 383–384 行）；
  - `hc.ts` 第 46–55 行的 `reply()` 先从 pending 删除，accept 抛错时先 reject 再抛；
  - 抛出的异常经第 27–30 行 destroy socket，再进第 34–41 行的 `fail()`。

  以上与代码一致。agy 贴出的 `reply()` 片段里写的是 `if (!call) return;`，实际第 45 行是 `throw new Error('unexpected hc RPC reply')`。结论不受影响。
- 红态、绿态与变异：
  - 真实入口的红态在第五轮候选上取得：`evidence/round6-trace-resize-red-02/run.json` 第 2 行 INCOMPLETE、第 23–24 行 `timed_out`、第 110 行 SIGKILL known-bad；
  - 最终候选上主控复跑两种情况都 PASS；
  - 两个变异都在目标断言上失败；
  - 连续改尺寸的红态（`evidence/round5-burst-red-01/run.json` 第 280 行 AssertionError）在第四轮实现上失败。

  这些定性结论与原始输出一致。

## 找不到出处的引用（不采信）

| agy 写的 | 实际 |
| --- | --- |
| 主控 `r6-mismatched-01`：pid 96934、shell_pid 96928、before 413、after 438、493 行 | `controller/r6-mismatched-01/run.json` 第 106–109 行：pid 18808、shell_pid 18805、before 412、after 432；第 134–135 行：460 行 |
| 主控 `r6-screen-01`：pid 98945、492 行 | 同文件第 101 行 pid 19008，第 129–130 行 466 行 |
| 主控 `r6-burst-01`：515 行 | 第 279–280 行 488 行 |
| `r6-trace-initial-01`：shell_pid 19428、夹具 `t212-trace-oet2k6c3` | 审查目录里没有这两个值 |
| 红态夹具 `t212-trace-q87b23_x`，耗时 3.005232875、3.001781167 | `round6-trace-resize-red-02` 的夹具是 `t212-trace-mlp0i9g3`，耗时 3.001306125；`round6-trace-initial-red-03` 的夹具是 `t212-trace-83cm6qpn` |
| `round5-burst-red-01`：`added_resets: 23` | 第 263 行是 24 |
| `round6-evidence-boundary.json`：`checked_files: 84` | 第 16 行是 651 |
| 打包：`candidate_commit 77bb8b92…`、版本 `v0.16.0-pre`、SHA-256 `d357b42b…`、包内路径 `Contents/Resources/bin/herdr-core` | `round6-package-01.json` 第 49 行版本 0.1.15，包内路径是 `Contents/Resources/app/hc/herdr-core`（第 33 行）；所列提交与哈希在审查目录里都不存在 |
| 打包态 core_pid 16217 | `round6-packaged-runtime-01/run.json` 第 74 行 pid 10600 |
| `r6-CHECK.md` 第 15 行写了 `private_hc_state_files=0` 等 | 第 15 行讲的是变异现场的保存位置，没有这些字段 |
| `closePaneLayout`、`pane_not_open` | 代码里没有 |
| 第 5 节验收表的八条条目（如“启动一个持续输出并记录自身 pid 的前台程序……”“连续产生超过 256 KiB 输出”） | 与 `ticket.md` 第 26–33 行的八条验收条目对不上，是审查员自拟的；本票各条状态以主控按票面写的 RESULTS.md 为准 |
| `windowResize` 在 `panes.ts` 第 1685–1705 行 | 那里是交付状态查询；`window_resize` 的处理在 `daemon.ts` 第 693 行起 |
| `hc-asset.ts`（含 `cleanHcEnv`），改动涉及 `package.json`、`prepare-hc.mjs`、`verify-packaged-app.mjs` | 候选里没有这些文件改动；hc 分发在新文件 `workbench/src/hcDistribution.mjs`，打包改的是 `workbench/app/package.mjs` |

`hc-asset.ts`、`HcSupervisor` 的边界说法（第 4、6 节）不涉及第五、六轮改动。前两轮主控核对过的不再重复；本轮没有逐行复核的，不当作新的证据。
