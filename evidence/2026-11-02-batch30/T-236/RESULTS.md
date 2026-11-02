# T-236 调查结果（2026-11-02，第 2 版）

结论：**INCOMPLETE**，根因未查清。第 1 版的结论“不是代码缺陷，是 macOS 在等‘文稿’文件夹授权”已被直接探针**否定**，撤回（第 1 版见本文件的 git 历史）。

## 已经确定的

1. **项目终端里的 Claude 停在加载 skill 这一步。** `--debug-file` 日志（`open5-tcc2-debug.log`）停在 `skipping skills-dir entry 'synced'`；同一命令在主控自己建的伪终端里，下一行 20 毫秒后就是 `Loaded 32 unique skills`（对照日志 `own-pty-claude-debug.log`）。此时 Claude 的一个线程停在 `openat$NOCANCEL`。
2. **停住的是一次普通的打开文件。** 在 Enchanted 项目终端里逐个 `cat` 用户 `~/.claude/skills` 能连到的 SKILL.md，前 7 个都读完，读到 `~/Documents/SKILLS/reality-evidence-engineering/evidence-first-testing/SKILL.md` 时停住；`sample` 显示 `cat` 停在内核 `__open`（`tcc-probe-skills-3.json`）。连续三次都停在同一个文件（`tcc-probe-skills-1/2/3.json`）；换成上午能画出 Claude 界面的旧包 `a2a-build-cu-test-20261102` 也一样（`tcc-probe-skills-cutest.json`）。同一文件在主控自己的终端里 0.003 秒读完。
3. **不是“文稿”文件夹授权。** 从没启动过的新包 `a2a-build-t236-tcc2` 里，项目终端读 `~/Documents/Code/a2a/AGENTS.md` 0.11 秒返回（`tcc-probe-new.json`）；探针期间实时抓取的 `tccd` 日志里没有任何文稿文件夹（`kTCCServiceSystemPolicyDocumentsFolder`）请求。
4. 已排除：没有别的进程持有该文件（`lsof`）；文件是普通文件，没有特殊标志，只有 `com.apple.provenance` 扩展属性（`~/Documents/SKILLS` 下能读完的那几个 SKILL.md 也有）；`~/Documents` 不在 iCloud；本机没有 Endpoint Security 系统扩展（只有 OBS 虚拟摄像头与 Radio Silence 网络扩展）。

## 还不知道的

- 为什么这次 open 会停住（起初以为只在 Enchanted 终端里，第 2 轮补充见下：不经 Enchanted 的进程也会）。内核日志里每个新包都有 `AppleSystemPolicy ... Unable to apply provenance sandbox ... herdr-core`，与此是否有关未查。
- 停住的 open 最终会不会返回。
- 第 1 版所说的“新包卡住、用过的包能画出界面”不成立：同一个旧包现在也卡。上午那次 2.5 秒画出界面，与现在卡住之间差在哪里，未知。

## 探针的局限

Enchanted 是经 `open` 启动的，项目终端跑的是用户自己的 zsh 和配置；用户的 zsh 插件（如语法高亮会对输入的路径做 stat）可能自己先卡住。用 glob 或很长的命令行时命令根本没执行（`tcc-probe-parallel.json` 全部 False 是探针失效，不是读取结果）。

## T-238 第 2 轮补充（Codex，`../T-238/REPORT-02.md`）

同一个文件在 Codex 自己的进程（不经 Enchanted）、源码后台的项目终端、打包后台的项目终端里都打不开：`open` 停约 5 秒后以 `Interrupted system call` 失败；`~/Documents/SKILLS` 下另外三个 SKILL.md 同样，`~/.codex/AGENTS.md`、仓库 `AGENTS.md` 0.005 秒读完。所以这**不是 Enchanted 独有**的现象；主控自己的工具进程读同样文件 0.02 秒内返回，差别在“由哪个进程打开”。`~/Documents/SKILLS` 及部分子目录带 `com.apple.macl`，关系未查；再往下需要 `sudo fs_usage` 一类工具。

## 下一步（原计划，已由上面的补充执行）

T-238（项目终端里的 Codex、agy 不执行）很可能同因，第 2 轮调查交给 Codex（`../T-238/BRIEF-02.md`），一并查清这次 open 停住的原因、是否与 Enchanted 的进程血缘有关，再决定 T-236 修在哪一层。

## 对用户环境的影响（第 1 版已记，仍然成立）

- Claude Code 的全屏渲染器启动失败计数满 2 次后已在本机关掉（今天 Enchanted 里被卡住后结束的 Claude 与主控的短探针都计入）。运行 `/tui fullscreen` 或 Claude 更新后恢复；主控没有替用户改设置。
- 第 1 版推测可能留下未回答的“文稿”权限框；按现在的证据，这类框大概率没有出现。

脚本在 `scripts/`：`t236tcc.py`（读文件探针，`SKILLS=1` 逐个读 skill，`PARALLEL=` 并行读，后者失效）、`t236open5.py`（带调试日志启动 Claude）及第 1 版的探针。
