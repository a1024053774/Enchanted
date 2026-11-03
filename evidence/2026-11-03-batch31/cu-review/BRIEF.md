# 任务书：T-231、T-232、T-233、T-235 审查（GPT，含 Computer Use，2026-11-03）

用户原话：“修复 4 张票,你负责修复,让 GPT 6.1 terra 用 computer use审查”。你是审查员：只读代码、运行测试、用 Computer Use 观察界面、写报告。**不改** `workbench/`、ticket、地图里的任何文件；不提交、不 push。

审查规则（用户全局规则）：审查发现是缺陷主张，先复现再报告；不能复现的写明“未复现”和你做了什么。每条发现给出反例（输入、步骤、观察到的结果）。只有一轮审查加至多一轮复审，所以请一次查全。

## 改动（未提交的工作区，`git -C /Users/luckye/Documents/Code/a2a diff -- workbench`）

| 票 | 改了什么 | 主控的证据 |
| --- | --- | --- |
| T-233 | `test_t212_shell_hc_e2e.py`：侧栏行选择器 `data-terminal-launch` → `data-agent-launch`；Electron 场景在打开窗口前多开一个终端窗格 | `evidence/2026-11-03-batch31/T-233/`：`red-old-selector/run.json`（两个窗格 + 旧选择器 → 超时）、`green/`、`green-mismatched/` |
| T-232 | `scripted_claude.py`：`stop_private_core` 从 T-212 测试移来；`Fixture.stop` 停私有 core 并核对夹具进程（argv 或环境里含夹具路径）没有残留；`Fixture.env` 传入 `ENCHANTED_HC_CACHE_DIR`（复制的源码旁没有 hc-cache，会每次下载 hc，超过 10 s 启动期限）；其他 4 个测试改为从 `scripted_claude` 引用 | `evidence/2026-11-03-batch31/T-232/`：`red-residue.txt`、`forced_failure.py`、`green-*`、`green-user-core.json`、`attempt-1/`、`attempt-2/`（启动超时的两次尝试） |
| T-231 | `test_native_final_read.ts`：会话文件放进 `sessions/YYYY/MM/DD`（T-221 后扫描只读这里）、真实路径、钩子带全字段、模拟终端输出触发扫描、接上空的 `recordUserSubmission` | `evidence/2026-11-03-batch31/T-231/`：`bisect.txt`（`f3a4a54162` 起失败，其父提交通过）、`red-head-results.json`、`green-results.json`、`mutant-no-final-read.sh` 与结果 |
| T-235 | 没有改代码：HEAD 与基线 `59815ea30` 上都没有复现 | `evidence/2026-11-03-batch31/T-235/`：`head-*`（9 次真实测试）、`base-t157-*`（3 次）、`*-probe-*`（界面状态时间序列） |

主控对 T-231 的判断（请专门挑战）：测试过时，不是产品缺陷。`f3a4a54162`（T-108）把 `signal()` 里的扫描移到会话核对之后；产品里 Codex worker 的会话靠终端输出触发的扫描绑定，钩子一般在那之后到达。主控没有找到真实 Codex 运行里出现 `hook_native_session_mismatch` 的证据，也没有证明它不会出现。

## 要做的

运行测试前 `export ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache`。所有输出写到 `evidence/2026-11-03-batch31/cu-review/` 下（用新的子目录名，不要覆盖主控的证据）。

1. 读 diff 与四张票（`.project-map/tickets/T-231-*.md`、`T-232-*`、`T-233-*`、`T-235-*`），逐条对照验收项，找反例。
2. 自己重跑：
   - T-233：`python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output <新目录>`，以及加 `--mismatched-screen` 的一次。
   - T-232：`python3 evidence/2026-11-03-batch31/T-232/forced_failure.py <新目录>/ff.json`，之后用 `evidence/2026-11-03-batch31/T-232/residue.sh /private/tmp/t216-` 核对没有残留。
   - T-231：`node workbench/tests/test_native_final_read.ts <新目录>` 和 `evidence/2026-11-03-batch31/T-231/mutant-no-final-read.sh <新目录>`。
   - T-235：`python3 workbench/tests/test_t165_queued_stop_e2e.py --scenario unrelated-stop --summary <新目录>/x.json` 至少 2 次。
3. Computer Use（界面实测，只操作下面这个隔离包）：
   - **只准**这样启动：`open -n /private/tmp/a2a-build-t239-20261102/Enchanted.app --args --state /private/tmp/a2a-cur/state --user-data /private/tmp/a2a-cur/ui`。启动后用 `ps` 核对后台参数里是 `/private/tmp/a2a-cur/state`。不要按应用名打开或切换到 “Enchanted”（会拉起用户真实的 `/Applications/Enchanted.app`）；项目列表出现 `/private/tmp/a2a-cur/` 以外的项目就是开错了，立即退出并写进报告。
   - 在 `/private/tmp/a2a-cur/project` 建一个小 Git 仓库，在界面里打开。
   - T-233 对应的界面行为：新建两个项目终端，分别点侧栏里的两行，核对每次显示的是被点的那个窗格（例如各自 `echo` 不同的字）。截图。
   - T-235 对应的界面行为：在一个项目终端里运行 `claude --model claude-haiku-5-5`，信任框同意，发“请回复：测试正常。不要操作文件。”，观察回复结束后窗格标题栏的状态与侧栏这一行的状态：是否一致、各用了几秒变为空闲。截图。退出 Claude。
   - 从菜单退出应用；结束命令行里含 `/private/tmp/a2a-build-t239-20261102/` 或 `/private/tmp/a2a-cur/` 的进程并用 `ps` 核对。
4. 授权：CLI 对 `/private/tmp/a2a-cur/` 下目录的信任框直接同意并记录。CLI 更新提示选“跳过/以后”，不要选 Update now。**macOS 系统权限框不要点**，截图记下。不写 `~/.codex`、`~/.claude`、`~/.gemini` 的配置文件（CLI 因信任框自己写入的除外，记下）。不碰用户的 Herdr、其他 hc core、`/Applications/Enchanted.app`。

## 交付

中文报告 `evidence/2026-11-03-batch31/cu-review/REPORT.md`：

- 每张票一节：验收项逐条“满足 / 不满足 / 无法判断”，附命令与结果文件。
- 发现列表：阻塞 / 非阻塞，每条附复现步骤；未复现的写明。
- Computer Use 两项：步骤、期望、实际、截图路径。
- 最后一行写 `结论：PASS` 或 `结论：NO_GO`。
