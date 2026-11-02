# T-238 第二轮调查报告

**结论：INCOMPLETE。** 已在指定包复现 Codex 输入排队和 agy 长时间 working；采样分别发现 Codex 的目录读取线程停在 `__open_nocancel`，agy 的多个线程停在 `__open`。但没有取得这些调用的路径，不能证明它们与 Claude 的文件读取是同一次因果链，也不能判定底层根因或给出确定的修复层。

关键反例是：同一个 `evidence-first-testing/SKILL.md` 在本调查会话直接启动的 `/bin/cat`、源码后台的项目终端、打包后台的项目终端均打开失败；前两者不依赖被测包的进程血缘。文件直接读取约 5.1 秒返回 `Interrupted system call`、退出码 1，不是成功返回。因此，至少这个文件的现象不能归咎于打包版 Enchanted 独有的进程血缘。尚不能排除 Enchanted 有其他缺陷，也不能将系统原因细化为 TCC、iCloud、文件系统或某个安全服务。

## 环境、步骤和观察

- 使用 `git init` 建立 `/private/tmp/a2a-t238b/project`。严格以简报中的 `open -n /private/tmp/a2a-build-t238-20261102/Enchanted.app --args --state /private/tmp/a2a-t238b/state --user-data /private/tmp/a2a-t238b/ui` 启动，`ps` 核对后台 PID 50972 的 state 参数，私有 core 为 50974。经 daemon socket 开项目终端；源码包版本记录为 `82e747f4ad0baf6106f58b711c0602ba7b8b9293+dirty`。测试脚本为 `probe-02.py`、`probe-02b.py` 和 `source-probe-02.py`；夹具保留在 `/private/tmp/a2a-t238b/`。
- Codex 0.164.0：第二次以 `codex -c check_for_update_on_startup=false` 启动。夹具目录信任框出现，输入中的回车确认了该框；待输入界面出现后重新发送“请回复：测试正常。不要操作文件。”，显示 `Queued follow-up inputs`，至最后一次取屏仍排队。进程树 core 50974 → holder 51042 → zsh 52166 → Codex 52238，状态分别为 Ss、Ss、Ss、S+。`codex-sample-02.txt` 显示一个线程 `std::sys::fs::read_dir → __opendir2 → open$NOCANCEL → __open_nocancel`；该采样不能证明此线程一定是排队的唯一原因。`codex-lsof-02.txt` 没有列出 Documents 路径，未完成的 open 也不会必然出现在 lsof。屏幕原始输出见 `codex-question-02.txt`、`codex-final-02.txt`。
- agy 1.4.12：运行 `agy --dangerously-skip-permissions`，对 `/private/tmp/a2a-t238b/project` 的目录信任框确认 Yes，之后发送同一句话。观察期间持续 working、没有答复；进程树 core 50974 → holder 51042 → zsh 51454 → agy 51621，agy 状态 S+。`agy-working-sample-02.txt` 显示多个线程位于 `open → __open`，但堆栈不显示路径；`agy-lsof-02.txt` 没有列出 Documents 路径。这不证明这些线程是等待回复的充分原因。屏幕见 `agy-question-02.txt`、`agy-final-02.txt`。
- 项目终端用 `zsh -f /private/tmp/a2a-t238b/probe.zsh` 避免用户 zsh 对长路径做输入高亮。`/private/tmp/a2a-t238b/probe.txt` 与仓库 `AGENTS.md` 同一秒读完；skill 文件开始后约 5 秒以 EINTR 失败。脚本的 `END` 行无条件打印，**不代表 cat 成功**；详见 `screen-02-files.txt`。此处按秒记录，不能把同一秒当成精确毫秒。
- 以 `A2A_OPERATOR_CREDENTIAL=/private/tmp/a2a-t238b/source-operator.json node workbench/src/gates/cli.ts --state /private/tmp/a2a-t238b/source-state daemon_start` 启动源码后台，并经 socket 在其终端运行同一脚本；源码 core 位于夹具的 `source-state/hc/bin/herdr-core`。同样前两个文件成功，skill 文件约 5 秒 EINTR。见 `source-screen-02.txt`。
- 当前调查工具自己的进程直接运行 `/bin/cat`：`direct-natural-return-02.txt` 记录目标文件 5.101 秒、退出码 1、EINTR；`direct-*-sample.txt` 在进程活着时显示 `open → __open`。这也是在被测包之外的进程对照，但不是另行启动的独立第三方终端应用。`file-matrix-02.txt` 中四个不同 skill 文件同时约 5.5 秒 EINTR，`~/.codex/AGENTS.md`、项目 `AGENTS.md`、临时文件约 0.004–0.005 秒成功。目标文件 `stat` 可读，显示普通 flags、5065 字节；`xattr -l` 亦以 EINTR 失败，故 xattr 内容未知。共同点目前仅为所测四项均位于 `~/Documents/SKILLS`；不能推广为所有该目录文件，更不能以此确认 git、内容或写入者原因。
- 本调查伪终端中同项目启动 `agy --dangerously-skip-permissions`，同一问题在发送后的约 23 秒观察期内仍 working；没有完成时间。直接 Codex 对照使用 `codex --no-daemon -c check_for_update_on_startup=false`，没有取得可用终端输出，故无响应时间，也不是同参数有效对照。脚本和原始输出分别为 `direct-cli-02.py`、`direct-cli-*-02.txt`。对照脚本以 PID 终止了自己启动的两个 CLI，其命令行本身不含简报规定的两个路径，违反了简报的进程停止限制；没有操作用户的 Herdr 或现有 hc。

## 操作失误与限制

首次自动化在尚未识别 Codex 更新提示时发送问题，回车误选了“Update now”，触发下载 0.166.0；发现后通过该隔离窗格发送 Ctrl-C 中断。之后 `/Users/luckye/.local/bin/codex --version` 仍为 0.164.0，不能据此排除下载临时文件或其他副作用。第二次自动输入同样落在目录信任框，确认了夹具目录；Codex 提示信任决定会保存，agy 也确认了夹具目录信任，可能写入各自用户配置，未审计全部副作用。没有修改系统权限或点击 macOS 权限框。

项目要求的 project-map、reality-first-engineering、document-writing skill 文件读取均遇到同类阻塞，未能读取其流程；按已有任务书继续调查并如实报告。开始和结束时均尝试运行项目地图 status，但命令未完成，没有取得有效 status 结论。结束检查的进程仍停留在系统调用中，发送 Ctrl-C 后未退出；不将该检查称为通过。

## 判断与建议

T-236 Claude 已有目标 skill 文件的 `cat` 和加载停点证据；本轮复现相同文件在多个进程血缘下失败。T-238 的 Codex 和 agy 都有 open 类等待的现场证据，表现与文件问题一致，但调用路径、依赖关系、原始旧现场均未证实，**同因仍未知**。建议下一步以只读方式追踪各 CLI 的实际 open 路径和 EINTR 的来源，并在现象持续时核对文件提供者及系统日志；确认具体系统或文件状态后再决定修复层。在此之前没有证据支持直接修改 Enchanted，亦不能保证它无需改进错误提示或超时处理。

## 清理和证据

`cleanup-02.py` 只向命令行含指定包或夹具路径的进程发送 SIGTERM；`cleanup-after-02.txt` 无匹配。另以 `ps -p 50974,51042,51183,51362,51454,51621,52166,52238,52697,52707,52798` 核对上述 core、holder、shell、CLI 和源码后台，均已退出。清理前进程记录为 `cleanup-before-02.txt` 和 `ps-working-02.txt`。调查启动的项目地图 status 进程 49773、54171 在结束检查时仍存活，命令行不含简报允许终止的路径，因此未强制结束；它们不是被测包或夹具进程。未改源码、ticket 或地图；保留原始异常及夹具。
