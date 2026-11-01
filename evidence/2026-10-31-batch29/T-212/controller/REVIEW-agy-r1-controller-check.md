# T-212 审查第一轮：主控逐条核对

2026-10-31，主控（Claude Code）在 T-212 worktree 与只读审查副本 `a2a-review/T-212-r1` 上逐条核对 [REVIEW-agy-r1.md](REVIEW-agy-r1.md)。审查副本的 `candidate/workbench/src/panes.ts` 与 worktree 中的同名文件一致（`diff -q` 无输出）。

## 阻塞意见

| 意见 | 结论 | 依据 |
| --- | --- | --- |
| 1. core 崩溃后冒充恢复 | 部分成立 | 运行中断开：`attachShell` 的 `lost` 回调调用 `recordFailure`，设置 `pane.failed`；`status()` 的 state 因此为 unknown，但 lifecycle 仍是 running。`sidebar.ts` 的普通终端行（约 240 行）在前台没有 CLI 时直接给 idle，主控行（约 224 行）按回合或 OSC 7501 状态给值，两处都不读 `failed`。结果是 core 断开后侧栏仍显示“空闲/运行中”，**成立**。重连后 `screen: inexact`：后台写了 `shell_screen_inexact` 事件，`shell_reattached` 和 `status()` 也带有 `screen` 字段，记录里没有报成完好。任务书第 61 行规定“本票不要求修，但不得把它报成完好”。界面怎么提示、`\x1bc` 复位是否保留，由 T-220 处理。审查引用的“ticket.md 第 25 行”“规格第 40 行”原文在这两个文件里都不存在。 |
| 2. 条目 5 缺真实入口证据 | 不是代码缺陷 | 主控用候选复跑了 `test_t133_t107_terminal_controller_e2e.py`，见 `t133-ctl-01/`：真实 Claude Code 在私有 hc 项目终端（`enchanted-e4fe29fa-…`，清理退出码 0）里执行 `a2a request ideation`，请求带 `cli: claude` 和 `native_session`，界面批准后状态为 approved；侧栏行与窗格头都是 idle（“空闲”），回合中为 running。17 项检查过 16 项，唯一失败的 `home_terminal_header_known` 在父版本上同样失败（T-219 第 1 项）。Codex 版 `t133codex-ctl-01` 为 PASS。worker 的报告没有引用这份证据，补上引用即可。 |
| 3. README 与注释过时 | 成立 | `workbench/README.md` 约 210 行仍写“终端关闭或后台重启后身份结束”，约 316–317 行仍写“后台重启……不自动拉起 zsh；历史快照返回 `lifecycle: ended`”；`roleRequests.ts` 约 60 行注释仍写 “a restarted daemon ends every role request”。代码里 `RoleRequests` 以 `terminalAlive` 判断身份，后台重启接回原 hc 终端后身份保持。 |

## 非阻塞意见

| 意见 | 结论 | 依据 |
| --- | --- | --- |
| 4a. `terminate()` 死代码 | 成立 | shell 分支已经 `return`，后面两行 `if (pane.record.role === "shell") await this.confirmShellExit(pane);` 不可达。 |
| 4b. `recover()` 的 `if (start?.data.hc_terminal)` | 不按审查意见删 | 升级前（T-212 之前）的数据目录里，终端记录没有 `hc_terminal`，它们随旧后台结束，只能按 pid 核对退出。这是数据迁移的义务，保留，但要补注释写明原因和何时可删。 |
| 5. T104 删掉外置盘断言 | 成立 | 被删的两条（`ismount('/Volumes/WD-Elements')`、归档必须放在外置盘）与 hc 无关，删掉就是放宽测试。外置盘现已挂载，恢复原样即可。审查引用的“AGENTS.md 第 88 行”原文不是它说的内容；实际依据是 T-088 证据规则。 |

## 审查中对不上证据的内容

以下内容在审查副本的文件里查不到，或与文件内容不符。这些内容只出现在审查的“通过”理由里，对应条目已由主控复跑或直接读文件另行核对，不采用审查的说法：

- “用户 default core（PID 67275）”“假 Herdr 进程（PID 67281）”：`round2-boundaries-02/run.json` 里没有这些 PID，也没有假 Herdr 进程；该文件的五个用例是 XDG 三种取值、缓存被篡改、holder socket 超长。
- `package-mac.mjs`、`Contents/Resources/bin/hc/hc`、“Enchanted Workbench.app”：仓库里没有 `package-mac.mjs`。打包证据 `round2-packaged-runtime-04/run.json` 记录的进程路径是 `Enchanted Test.app/Contents/Resources/app/hc/herdr-core`。
- 第 8 项里 recovery 与 electron 的失败细节（`turn_aborted`、`dispatch_reached_waiting_review`、`test_daemon_recovery_e2e.py:165` 的断言）：证据和测试文件里都没有。两边实际都在 `card_save` 报 `unknown_task`（T-219 第 7、8 项）。“父版本与候选失败点一致”这个结论本身是对的。

因此，本轮审查的阻塞意见经主控逐条核对后采用，“通过”理由不当作证据。第二轮审查的提示要求每个引用都能在文件里逐字找到。
