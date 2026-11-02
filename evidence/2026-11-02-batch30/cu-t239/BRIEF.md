# 任务书：Computer Use 复验 T-239 修复，并实测项目终端里的三家 CLI（2026-11-02）

用户原话：“继续查然后执行修复任务, codex做 computer use 的 reviewer,我要离开,所以授权你都自己点”。你是 Computer Use 复验员，只测试和记录，不改代码、ticket、地图。

## 程序与边界（前几轮出过误启动用户真实数据的事故，务必照做）

- 被测包（含 T-239 修复，未提交的工作区代码打包）：`/private/tmp/a2a-build-t239-20261102/Enchanted.app`。**只准**这样启动：

  ```bash
  open -n /private/tmp/a2a-build-t239-20261102/Enchanted.app --args --state /private/tmp/a2a-t239cu/state --user-data /private/tmp/a2a-t239cu/ui
  ```

  每次启动后用 `ps` 核对后台参数里是 `/private/tmp/a2a-t239cu/state`。
- **Computer Use 不要按应用名打开或切换到 “Enchanted”**（会拉起用户真实的 `/Applications/Enchanted.app`）。先用上面的命令启动，再对已经在运行的窗口操作。项目列表里出现不是 `/private/tmp/a2a-t239cu/` 下的项目，说明开错了，立即退出并写进报告。
- 测试项目：自己在 `/private/tmp/a2a-t239cu/project` 建一个小 Git 仓库，在界面里打开它。
- 停后台、core 时只结束命令行里含 `/private/tmp/a2a-build-t239-20261102/` 或 `/private/tmp/a2a-t239cu/` 的进程，不碰别的 hc、用户的 Herdr、`/Applications/Enchanted.app`。
- 只写 `evidence/2026-11-02-batch30/cu-t239/` 下的文件；截图放 `shots/`，不要拍到账号邮箱（agy 界面会显示邮箱，截图前确认不在画面里，或只截终端的相关行）。
- 授权：CLI 对 `/private/tmp/a2a-t239cu/` 下目录的信任框、Codex 钩子信任框、Enchanted 里的角色申请批准，直接同意并记录。CLI 的更新提示选“跳过/以后”，**不要选 Update now**。**macOS 系统权限框（隐私、“文稿”文件夹等）不要点**，截图记下，继续做不依赖它的部分。不写 `~/.codex`、`~/.claude`、`~/.gemini` 的配置文件（CLI 自己因信任框写入的除外，记下）。

## A. T-239：历史窗格不再报解码错误

背景：项目终端输出停在半个 UTF-8 字符上时后台重启，修前历史窗格报 `TypeError: Failed to execute 'decode' on 'TextDecoder' ...` 并显示“窗格未连接”。修后应照常显示历史。

1. 新建一个项目终端，输入：`printf 'CU-A1\n\344\270'; sleep 3600`（回车）。看到 `CU-A1` 后，从菜单退出 Enchanted，结束本包的后台进程（命令行含 `daemon.ts` 与 `/private/tmp/a2a-t239cu/state` 的那个），**core 先不结束**；用同一条命令重新启动。打开这个终端，按 Ctrl-C，输入 `print CU-A2`。
2. 再从菜单退出 Enchanted，这次结束本包的后台**和** core（以及 core 下的 zsh），再启动。打开这个已结束的终端（历史窗格）：期望无错误提示、顶部不显示“窗格未连接”，能看到 `CU-A1`、`CU-A2`。
3. 新建一个项目终端，输入 `printf 'CU-B1 \377 CU-B2\n'; print CU-B3`：期望三段都显示（中间是一个替换字符），无错误提示，之后还能继续输入命令。
4. 每步截图，记录看到的文字。

## B. 项目终端里的三家 CLI（T-236、T-238 的用户视角复测）

背景：上午项目终端里 `claude` 没有任何输出、`codex` 输入一直排队、`agy` 一直 working；当时系统里打开 `~/Documents/SKILLS` 下的 skill 文件会卡 5 秒后失败（不只在 Enchanted 里）。主控 16:26（本地 11:26）复测时该现象已消失，打包应用里 Claude 能加载全部 skill 并画出信任框。请从用户视角确认：

1. 在项目终端运行 `claude --model claude-haiku-5-5`，信任框同意后，发“请回复：测试正常。不要操作文件。”，记录多久出现回复、回复内容。退出（`/exit` 或 Ctrl-C 两次）。
2. 同一终端运行 `codex -c check_for_update_on_startup=false`，同样发这句话，记录是否回复、多久。退出。
3. 运行 `agy --dangerously-skip-permissions`，同样发这句话，记录是否回复、多久。退出。
4. 任何一家没有回复时：在它还活着时用 `ps`、`sample <pid> 1` 记下它停在哪里（是否停在 open/openat），并在你自己的终端里 `time cat ~/Documents/SKILLS/reality-evidence-engineering/evidence-first-testing/SKILL.md` 对照一次，写进报告；不要反复重试超过两次。

## 交付

中文报告 `evidence/2026-11-02-batch30/cu-t239/REPORT.md`：每个场景的步骤、期望、实际、截图、结论（通过 / 失败 / 未测并写原因）；最后总结论用 PASS / INCOMPLETE / BLOCKED / NO_GO。测完从菜单退出 Enchanted，结束本包的后台、core、CLI 进程并用 `ps` 核对；`/private/tmp/a2a-t239cu/` 保留。
