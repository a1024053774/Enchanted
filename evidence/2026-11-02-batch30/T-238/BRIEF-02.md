# 任务书：T-238 第 2 轮调查（2026-11-02）

用户原话：“第三个要让 codex 去调查清楚”。你是调查员：只调查、记录，不改代码、ticket、地图。第 1 轮结论 INCOMPLETE（`REPORT.md`）：旧现场已没了，新项目里没复现。

## 主控刚查到的线索（先读）

- 原先“macOS 文稿文件夹权限框”的推测已被**否定**：从没启动过的新包里，项目终端读 `~/Documents` 下的文件 0.11 秒返回，同期 `tccd` 日志里没有任何文稿文件夹的权限请求（`../T-236/tcc-probe-new.json`、`../T-236/RESULTS.md` 将更新）。
- 新发现：Enchanted 项目终端里，`cat ~/Documents/SKILLS/reality-evidence-engineering/evidence-first-testing/SKILL.md` 一直停在内核 `__open`（`sample` 证据见 `../T-236/tcc-probe-skills-3.json`），两个不同的包都复现；同一文件在主控自己的终端里 0.003 秒读完；同目录别的文件此前读得出来。项目终端里的 Claude 也恰好停在加载 skill 这一步（`--debug-file` 日志停在 “skipping skills-dir entry 'synced'”，正常运行下一行是 “Loaded 32 unique skills”，`../T-236/open5-tcc2-debug.log`）。
- 为什么这次 open 会停住还不知道：没有别的进程持有该文件，没有 Endpoint Security 系统扩展；内核日志里有 `AppleSystemPolicy ... Unable to apply provenance sandbox ... herdr-core`（每个新包都有），关系未查。
- 经用户自己的 zsh 发长命令做探针不可靠：用户的 zsh 插件（语法高亮会对输入的路径做 stat）可能自己先卡住，用 glob 或长命令行时命令根本没执行。请设法绕开（例如经 `zsh -f` 子 shell、把命令写进脚本文件再执行）。

## 这一轮要查清的

1. 项目终端里的 Codex 卡住，是否也停在打开某个文件上（`~/.codex/AGENTS.md` 等引用的 `~/Documents` 路径，或别的）；agy 同样。
2. 哪些文件会卡、哪些不会；共同点是什么（路径、xattr、git 仓库、文件内容、最近被谁写过……）；卡住的 open 最终会不会返回、多久返回。
3. 是不是 Enchanted 的进程血缘（打包的 `herdr-core` → holder → zsh）造成的：同一个 `cat` 放在主控起的源码后台（`node workbench/src/gates/cli.ts daemon_start`，core 来自 `hc-cache`）的项目终端里会不会卡；在 `/Applications/Enchanted.app` 之外别的 app 的终端里会不会卡（只读观察，不要启动用户的真实 Enchanted）。
4. 找到根因后判断是不是 Enchanted 的缺陷、修在哪一层（只提建议，不改代码）。

## 程序与边界（前几轮出过误启动用户真实数据的事故，务必照做）

- 被测包：`/private/tmp/a2a-build-t238-20261102/Enchanted.app`（主控刚打的新包，只被主控的一次探针启动过）。**只准**这样启动：

  ```bash
  open -n /private/tmp/a2a-build-t238-20261102/Enchanted.app --args --state /private/tmp/a2a-t238b/state --user-data /private/tmp/a2a-t238b/ui
  ```

  每次启动后用 `ps` 核对后台参数里是 `/private/tmp/a2a-t238b/state`。可以不用界面：照 `../T-236/scripts/t236tcc.py` 的做法，经后台 socket 开项目终端、发输入、读输出（推荐，不会误开别的应用）。如果用 Computer Use，不要按应用名打开或切换到 “Enchanted”。
- 测试项目：自己在 `/private/tmp/a2a-t238b/project` 建一个小 Git 仓库。
- **macOS 系统权限框（“想访问‘文稿’文件夹”之类）不要点**，也不要改系统设置；它正是要观察的对象。CLI 自己的目录信任框（对 `/private/tmp/a2a-t238b/` 下的目录）、Codex 钩子信任框可以同意并记录。
- 停进程时只结束命令行里含 `/private/tmp/a2a-build-t238-20261102/` 或 `/private/tmp/a2a-t238b/` 的进程；不碰用户的 Herdr、别的 hc、`/Applications/Enchanted.app`。
- 不写 `~/.codex`、`~/.gemini`、`~/.claude` 的配置。只写 `evidence/2026-11-02-batch30/T-238/` 下的文件。截图不要拍到账号邮箱。

## 要做的

1. 在新包的项目终端里启动 `codex`，像旧现场那样发一句话（例如“请回复：测试正常。不要操作文件。”）。看它是否排队、不执行。卡住时，在进程还活着时记下：进程树（core → shell → codex 及其子进程）、各进程 `ps` 状态、`sample <pid> 1` 里内核调用那几行（是否停在 `open`/`openat`/`stat` 一类）、`lsof -p` 里与 `Documents` 有关的项。对照：同一个包的另一个项目终端里 `cat` 一个 `/private/tmp` 文件与一个 `~/Documents` 下的文件各需多久。
2. 同样对 `agy --dangerously-skip-permissions` 做一次（简单问答即可）。
3. 对照组：在你自己这个终端（已有“文稿”权限）里，同版本 `codex`、`agy` 对同一句话的反应时间。
4. 如果 Codex 停在打开文件上，尽量找出是哪个路径：例如逐个 `cat` 它配置里引用的 `~/Documents` 路径，看哪个卡住。不要改它的配置。

## 交付

中文报告 `evidence/2026-11-02-batch30/T-238/REPORT-02.md`：步骤、命令、观察、证据位置；写清卡住的位置与根因（或查到哪一步、还差什么），是不是 Enchanted 的缺陷、建议修在哪一层（只提建议，不改代码）；T-236（Claude）与 T-238（Codex、agy）是否同因。总结论用 PASS / INCOMPLETE / BLOCKED / NO_GO。结束时结束本包与本夹具的全部进程并用 `ps` 核对；`/private/tmp/a2a-t238b/` 保留。
