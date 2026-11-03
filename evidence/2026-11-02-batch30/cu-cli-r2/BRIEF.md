# 任务书：Computer Use 复测项目终端里的三家 CLI（2026-11-03，第 2 轮）

用户原话：“继续查然后执行修复任务, codex做 computer use 的 reviewer,我要离开,所以授权你都自己点”；随后用户：“我已执行 cat 命令然后同意了读取目录”。你是 Computer Use 复验员，只测试和记录，不改代码、ticket、地图。

背景：上一轮（`../cu-t239/REPORT.md` 场景 B）三家都不回复，原因是 macOS 的“文稿”文件夹授权框没人回答，需要 TCC 判定的打开都卡住。用户已回答该授权框；主控复测打包应用项目终端里读 `~/Documents` 下 18 个路径全部成功。本轮确认三家 CLI 现在能正常回复。

## 程序与边界（前几轮出过误启动用户真实数据的事故，务必照做）

- 被测包（含 T-239 修复，未提交的工作区代码打包）：`/private/tmp/a2a-build-t239-20261102/Enchanted.app`。**只准**这样启动：

  ```bash
  open -n /private/tmp/a2a-build-t239-20261102/Enchanted.app --args --state /private/tmp/a2a-cli2/state --user-data /private/tmp/a2a-cli2/ui
  ```

  每次启动后用 `ps` 核对后台参数里是 `/private/tmp/a2a-cli2/state`。
- **Computer Use 不要按应用名打开或切换到 “Enchanted”**（会拉起用户真实的 `/Applications/Enchanted.app`）。先用上面的命令启动，再对已经在运行的窗口操作。项目列表里出现不是 `/private/tmp/a2a-cli2/` 下的项目，说明开错了，立即退出并写进报告。
- 测试项目：自己在 `/private/tmp/a2a-cli2/project` 建一个小 Git 仓库，在界面里打开它。
- 停后台、core 时只结束命令行里含 `/private/tmp/a2a-build-t239-20261102/` 或 `/private/tmp/a2a-cli2/` 的进程，不碰别的 hc、用户的 Herdr、`/Applications/Enchanted.app`。
- 只写 `evidence/2026-11-02-batch30/cu-cli-r2/` 下的文件；截图放 `shots/`，不要拍到账号邮箱（agy 界面会显示邮箱，截图前确认不在画面里，或只截终端的相关行）。
- 授权：CLI 对 `/private/tmp/a2a-cli2/` 下目录的信任框、Codex 钩子信任框、Enchanted 里的角色申请批准，直接同意并记录。CLI 的更新提示选“跳过/以后”，**不要选 Update now**。**macOS 系统权限框（隐私、“文稿”文件夹等）不要点**，截图记下，继续做不依赖它的部分。不写 `~/.codex`、`~/.claude`、`~/.gemini` 的配置文件（CLI 自己因信任框写入的除外，记下）。

## 要做的

1. 在界面里打开 `/private/tmp/a2a-cli2/project`（自己建的小 Git 仓库），新建项目终端。
2. 运行 `claude --model claude-haiku-5-5`，信任框同意，发“请回复：测试正常。不要操作文件。”，记录从提交到出现回复的大致秒数和回复内容。退出。
3. 新建项目终端，运行 `codex -c check_for_update_on_startup=false`，同样发这句话并记录。退出（Ctrl-C 两次；不退时按隔离进程清理并记下）。
4. 新建项目终端，运行 `agy --dangerously-skip-permissions`，同样发这句话并记录。退出。截图不要拍到账号邮箱。
5. 任何一家不回复时：进程活着时 `sample <pid> 1` 记下停在哪里，并在你自己的终端里 `time cat ~/Documents/Code/VibeGame/README.md` 对照一次；同一家最多重试一次。

## 交付

中文报告 `evidence/2026-11-02-batch30/cu-cli-r2/REPORT.md`：每家的步骤、期望、实际、截图、结论；总结论用 PASS / INCOMPLETE / BLOCKED / NO_GO。测完从菜单退出应用，结束本包的后台、core、CLI 进程并用 `ps` 核对；`/private/tmp/a2a-cli2/` 保留。
