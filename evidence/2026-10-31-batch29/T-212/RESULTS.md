# T-212 结果：私有 hc core 与项目终端走 hc

状态：**PASS**（2026-11-01，主控核对）。

- 代码：worktree 提交 `4884f769e`（树 `31b9dde51`，基线 `4cb88bba7`），合入 main 为 `8006f37ea`；合入时无冲突。
- 写代码的是 Codex worker，共六轮；审查员是 agy，只读，共三轮；主控按票面逐条核对。
- 原始证据已归档到外置盘，清单见 `archive/`。

## 票面验收

| 条目 | 状态 | 依据 |
| --- | --- | --- |
| 修前经真实入口留下红态 | PASS | 基线上 worker 的 `red-02`（夹具 `/private/tmp/t212-sp4e0ova`，已归档）：`AssertionError: 程序随后台重启结束：编号停止增长，原进程已退出`。`red-01` 因 `/bin/ps` 权限失败，不计为红态 |
| 修后后台重启，程序仍在，窗格接回后屏幕与历史完整 | PASS | 最终候选上主控复跑 `controller/r6-mismatched-01.run.json`：强制 hc 193×120 后再由 Electron 拟合；pid 18808 存活，460 行与 hc 逐行一致。`r6-screen-01` 466 行一致，`r6-burst-01` 488 行一致。合入后 main 上的 `m-mismatched-01` 726 行一致，`m-burst-01` 712 行一致 |
| 私有 core 由打包的固定版本 hc 启动，用户 Herdr 不变 | PASS | worker 的 `round6-packaged-runtime-01/run.json`：私有 core pid 10600，版本 0.1.15，进程路径在包内 `Contents/Resources/app/hc/herdr-core`。各次运行前后，用户 core（pid 87319、87320、87407）与状态目录都不变（每份 run.json 的 `user_core` 字段）。边界测试见 `round6-boundaries-01` |
| 打字、粘贴、中文、Esc、Ctrl-C 与输入记录 | PASS | 尺寸错配场景里，程序从真实 PTY 读到的原始字节与预期一致，终端查询只收到一份应答，项目终端键入不写 `user_inputs`（`r6-mismatched-01` 的 checks）。T104 回归见 `archive/t104-round6.archive.json` |
| Claude Code 经 `a2a request` 申请主控，界面批准后生效，侧栏不出现新的“未知” | PASS（限定） | 主控在第三轮候选上跑的 t133（`T-212-controller/t133-ctl-01`，已归档）：真实 Claude 在 hc 项目终端里申请构思主控，结果 `state: approved`，批准后侧栏行与窗格头都是“空闲”。这次 t133 整套记 INCOMPLETE，原因是既有的窗格头检查，这里只引用它证明的这段流程。worker 第六轮的 T107、T121 回归通过，崩溃后侧栏显示 unknown 的检查也通过 |
| 打包产物含 hc 二进制与 Apache-2.0 许可 | PASS | `round6-package-01.json` 第 52–53 行：包内有 `hc/LICENSE` 和 `hc/THIRD-PARTY-NOTICES`。该 LICENSE 来自同一固定版本归档，是 Apache License 2.0。核对完后包已删除 |
| 项目终端不再经 node-pty 启动 | PASS | 合入后 `workbench/src/panes.ts` 里 node-pty 只剩三处调用：第 526 行启动受管主控，第 770 行恢复受管窗格，第 1018 行启动受管窗格。项目终端只经 `startShell` → `hc.run`（第 316 行）。旧的 node-pty shell 记录在恢复时只核对进程是否退出（第 660–666 行），不再起新进程 |
| 独立审查（agy 只读）无未处理的阻塞意见 | PASS | 共三轮。第三轮原文 `controller/REVIEW-agy-r3.md`，结论无阻塞。主控逐条核对见 `controller/REVIEW-agy-r3-controller-check.md`：3 条非阻塞意见落在真实代码上；报告里的大量数值和验收表条目找不到出处，不采信。前两轮的阻塞意见已在第三到第六轮处理，见 `REVIEW-agy-r1/r2-controller-check.md` |

## 主控复跑与变异

- 最终候选（`controller/run-ctl-r6.sh`，汇总 `r6-runs.log`、`r6-CHECK.md`）：
  - 尺寸错配、原画面、连续改尺寸、trace 写入失败（resize 与初次 attach 两种情况）共 5 个入口，全部 PASS；
  - 两个变异都在目标断言上失败：
    - `no-catch`：paint 不捕获写入错误，另一个终端也被拖垮；
    - `no-check`：resize 后不检查失败，返回带旧偏移的成功。
- 第四轮（`run-ctl-r4.sh`）：把 resize 改回只发 RESIZE、不重新 attach，尺寸错配场景失败。
- 第一轮（`run-ctl.sh`）：`no-reset`、`forget-token`、`leak-xdg` 三个变异都失败。
- 合入后的 main（`controller/run-ctl-merged.sh`，汇总 `m-runs.log`，HEAD `8006f37ea`，含 T-221 对 `panes.ts` 的改动）：
  - T-221 按日扫描 196 项通过；
  - 尺寸错配、连续改尺寸（24 种尺寸只新增 1 次 reset）、trace 失败两种情况，都 PASS。

## 留给后续

- 缺陷 [T-227](../../../.project-map/tickets/T-227-trace-failure-aftermath.md)，来自审查意见 1、2：
  - 初次 attach 失败后 hc 终端仍在运行；
  - 窗格失败后每个 DATA 帧重复记 `trace_write_failed`。后者在基线的 node-pty 路径上也一样。
- core 崩溃后谁重启、历史不完整时界面怎么提示，交给 T-220 与 T-226 的 Q3。

## 归档

外置盘目录 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-212/`：

- `worker-evidence/`：worker 的完整证据；
- `controller/`：主控复跑的完整目录；
- `fixtures/`：失败运行的夹具现场与回归夹具；
- `t104-round3`～`t104-round6`。

清单在 `archive/`。通过运行的夹具和构建槽不归档，核对后删除。
