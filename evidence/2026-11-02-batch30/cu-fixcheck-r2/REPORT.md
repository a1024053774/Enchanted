# T-237 最终修复：Computer Use 第 2 轮复验

总结果：**PASS**，限于任务书指定的四个界面场景。四行均在等待至少 70 秒后呈现预期状态；本轮没有重跑修前版本或报告正常导入的验收，不能据此单独证明完整回归覆盖。修前现象见 [T-237](../../../.project-map/tickets/T-237-stale-retrospective-shows-running.md)，本轮没有修改代码、ticket 或地图。

时间为 2026-11-02 美国东部时间（EST）。测试项目为新建 Git 仓库 `/private/tmp/a2a-fix2/project`。两次均仅用以下命令启动指定包；每次启动后 `ps` 均确认后台 `daemon.ts` 参数包含 `/private/tmp/a2a-fix2/state`，窗口项目路径也在该隔离目录下。四次复盘均选 Claude Code、`claude-haiku-5-5`、`low`。

```bash
open -n /private/tmp/a2a-build-t236-tcc2/Enchanted.app --args --state /private/tmp/a2a-fix2/state --user-data /private/tmp/a2a-fix2/ui
```

## 场景一：关闭复盘终端

- 步骤：10:04 启动复盘；终端显示隔离项目的 Claude 信任框后，关闭该终端。等待超过 70 秒后打开 Reflect。
- 期望：显示“已结束，没有报告（终端已不在）”。
- 实际：约 10:06 显示该文字，报告为“—”。
- 截图：[终端](shots/a1-terminal.png)、[结束状态](shots/a1-ended.png)。
- 结论：**通过**。

## 场景二：CLI 退出，终端保留

- 步骤：10:06 启动第二次复盘；在信任框按 Ctrl-C，CLI 提示再次按 Ctrl-C，随后退出，10:06:28 终端回到 zsh 提示符。等待超过 70 秒后查看 Reflect。
- 期望：显示“已结束，没有报告（CLI 已退出或没有启动）”。
- 实际：约 10:08 显示该文字，报告为“—”。
- 截图：[shell 提示符](shots/a2-prompt.png)、[结束状态](shots/a2-ended.png)。
- 结论：**通过**。

## 场景三：停止后台和 core 后重启

- 步骤：10:08 启动第三次复盘，确认终端和信任框出现；从菜单退出应用，按命令行路径核对并结束指定包的后台、core、holder 和该次测试 CLI；使用同一命令重启，确认后台参数，打开 Reflect 并等待超过 70 秒。
- 期望：显示“已结束，没有报告（终端已不在）”。
- 实际：重启后初看为“进行中”，约 10:10 显示预期的结束文字，报告为“—”。
- 截图：[重启前终端](shots/a3-before.png)、[重启后状态](shots/a3-ended.png)。
- 结论：**通过**。
- 另一个观察：重启后原历史窗格曾显示 `TypeError: Failed to execute 'decode' on 'TextDecoder': The encoded data was not valid.` 和“窗格未连接”；切到新复盘终端后显示“后台已连接”。这是本轮观察到的独立现象，未调查原因，也没有单独截图。

## 场景四：CLI 保持前台的反例

- 步骤：10:10 启动第四次复盘，在 `/private/tmp/a2a-fix2/project` 的 Claude 信任框选择“Yes, I trust this folder”（按任务书授权）；保持 CLI 前台运行，等待超过 70 秒，再查看终端和 Reflect。
- 期望：复盘记录仍显示“进行中”。
- 实际：终端画面显示 Claude 仍在工作，计时 1 分 34 秒；约 10:12 Reflect 对应行显示“进行中”，报告为“—”。
- 截图：[前台启动](shots/a4-cli.png)、[等待后前台](shots/a4-cli-after.png)、[Reflect 状态](shots/a4-status.png)。
- 结论：**通过**。

## 与第 1 轮比较

[第 1 轮报告](../cu-fixcheck/REPORT.md)中 T-237 四个场景也都通过；本轮在任务书指定的最终修复包上重新执行，四项可见状态与第 1 轮一致，未出现“无法确认”的状态。本轮不测试第 1 轮另列的 T-236 项目终端现象。两轮是不同构建的观察，各自证据不能互相替代。

## 清理与范围

约 10:12 从应用菜单退出；结束命令行包含指定构建路径或 `/private/tmp/a2a-fix2/` 的后台、core、holder 和测试 CLI。10:13 运行 `ps -axo pid,ppid,command | rg 'a2a-build-t236-tcc2|a2a-fix2' | rg -v 'rg '`，无匹配输出。隔离目录保留；未操作 macOS 系统权限框，也未见需要处理的系统权限框。截图未包含账号邮箱。

会话开始与结束运行项目地图 status，均报告 Problems 0、Stale living docs 0。截图和报告之外未改写本仓库文件。
