# 任务书：用 Computer Use 复验 T-237 最终修复（2026-11-02，第 2 轮）

用户原话：“前两个缺陷你来修复,让 codex 6.1terra 去 computer use 测试”。你是测试员，只测试和记录，不改代码、ticket、地图。

## 程序与边界（上两轮出过两次误启动用户真实数据的事故，务必照做）

- 被测包（含 T-237 第 2 轮审查通过的最终修复，未提交的工作区代码打包）：`/private/tmp/a2a-build-t236-tcc2/Enchanted.app`。**只准**这样启动：

  ```bash
  open -n /private/tmp/a2a-build-t236-tcc2/Enchanted.app --args --state /private/tmp/a2a-fix2/state --user-data /private/tmp/a2a-fix2/ui
  ```

  每次启动后用 `ps` 核对后台参数里是 `/private/tmp/a2a-fix2/state`。
- **Computer Use 不要按应用名打开或切换到 “Enchanted”**：上一轮这样做拉起了 `/Applications/Enchanted.app`（用户的真实数据）。先用上面的命令启动，再对已经在运行的那个窗口操作；如果工具要按名字启动应用，停下，改用命令行启动。看到窗口标题或项目列表里出现不是 `/private/tmp/a2a-fix2/` 下的项目，说明开错了，立即退出并写进报告。
- 测试项目：自己在 `/private/tmp/a2a-fix2/project` 建一个小 Git 仓库。
- 停后台、core 时只结束命令行里含 `/private/tmp/a2a-build-t236-tcc2/` 或 `/private/tmp/a2a-fix2/` 的进程，不碰别的 hc、Herdr、`/Applications/Enchanted.app`。
- 不改 a2a 仓库源码；只写 `evidence/2026-11-02-batch30/cu-fixcheck-r2/` 下的文件。截图放 `shots/`，不要拍到账号邮箱。
- 授权：CLI 对 `/private/tmp/a2a-fix2/` 下目录的信任框、Codex 钩子信任框、Enchanted 里的角色申请批准，直接同意并记录（用户原话：“他要是让授权,你帮我点同意就行”）。**macOS 系统权限框（例如“Enchanted 想访问‘文稿’文件夹中的文件”）不要点**，截图记下，继续做不依赖它的部分。

## A. T-237：复盘不再一直“进行中”

规格：`workbench/README.md` 复盘一节新增的三句（T-237）。Reflect 页状态应为“已结束，没有报告（终端已不在）”或“已结束，没有报告（CLI 已退出或没有启动）”；后台每分钟检查一次，所以每次操作后至少等 70 秒再看。

1. 终端被关掉：Reflect 页“立即复盘”（Claude Code、`claude-haiku-5-5`、low）。复盘终端出现后（不管 Claude 是否画出界面），把这个终端关掉。等 70 秒以上，看这一行。
2. CLI 退出：再启动一次复盘；在它的终端里按 Ctrl-C（必要时两次）让 CLI 退出，终端回到提示符。等 70 秒以上，看这一行。
3. 后台连同 core 一起停掉再重启（第二轮实测遇到的情形）：再启动一次复盘，等它的终端出现；从菜单退出 Enchanted，再结束本包的后台与 core 进程（见上面的边界），然后用同一条命令重新启动，打开 Reflect，等 70 秒以上看这一行。
4. 反例：再启动一次复盘，让它的 CLI 一直留在前台（不关、不退出），等 70 秒以上，这一行应仍是“进行中”。
5. 每个场景截图，记录看到的文字和时间。

## 和第 1 轮的不同

第 1 轮（`../cu-fixcheck/REPORT.md`）测的是审查前的版本，四个场景都通过。最终版本改了判断方式：只有终端的关闭有记录才算“终端已不在”（场景 3 现在靠后台重启时确认终端里的 shell 进程已不在）；看不清时不判结束，而是显示“进行中（无法确认 CLI 是否还在：……）”。所以四个场景要在新包上重做一遍；如果某一行显示“无法确认”，照实记下原文。项目终端里直接运行 `claude` 可能没有输出（T-236/T-238，正在另查），本轮不测它。

## 交付

中文报告 `evidence/2026-11-02-batch30/cu-fixcheck-r2/REPORT.md`：每个场景的步骤、期望、实际、截图、结论（通过 / 失败 / 未测并写原因），与第 1 轮结果的差异；最后总结论用 PASS / INCOMPLETE / BLOCKED / NO_GO。测完从菜单退出 Enchanted，结束本包的后台、core、CLI 进程并用 `ps` 核对；`/private/tmp/a2a-fix2/` 保留。
