# Enchanted 真实用户式试用（Computer Use）

你扮演第一次用 Enchanted 的开发者：手上有几个小仓库，想让 AI agent 在 Enchanted 里帮你改代码。用 Computer Use 操作应用 **Enchanted Test**，像真实用户一样摸索、犯错、换路子。目的是找出问题，不是证明它能用：已经测过的正常路径之外，多试真实用户会做的事（误操作、取消、重复点击、关窗、换顺序、怪路径、长输出、中文输入）。

## 边界（必须遵守）

- 只操作 **Enchanted Test**（bundle id `org.a2a.workbench.test`）。不要碰用户自己的 **Enchanted**（`org.a2a.workbench`）或其他应用的窗口；不改系统设置。
- 遇到登录、密码、付款、系统隐私授权，停下，记 BLOCKED，换下一项。
- 只在 `/private/tmp/uat/` 下改文件；不 `git push`，不改 `~/.claude`、`~/.codex`、`~/.gemini` 等全局配置。CLI 弹出“信任这个文件夹”之类会写全局配置的选择框时不要选信任，截图记下，换别的 CLI 或别的路子。
- 在项目终端里启动 Claude Code 时一律用 `claude --model claude-haiku-5-5`。
- 同一时间最多一个 worker 在跑（派发前确认上一个已交付或已回收），控制费用。
- 截图和报告只写进 `/private/tmp/uat/ui-check/`，截图文件名带编号。
- 应用退出后要重新打开，用这条命令（保持同一份测试数据）：
  `open -n "/var/folders/7v/58svbpnj5k91zdnm5zggb38h0000gn/T/a2a-build-uat01/Enchanted Test.app" --args --state /private/tmp/uat/state --user-data /private/tmp/uat/ui`

## 手上的东西

- `/private/tmp/uat/repos/notes-cli`：Python 小工具（`notes.py`、`test_notes.py`），有已知毛病：`done` 给不存在的编号会崩溃，`add` 不带文字会加一条空笔记。
- `/private/tmp/uat/repos/landing-page`：一页静态 HTML。
- `/private/tmp/uat/repos/我的 项目`：中文加空格的路径，Git 仓库。
- `/private/tmp/uat/repos/not-a-repo`：普通文件夹，不是 Git 仓库。
- 说明文档：`/Users/luckye/Documents/Code/a2a/workbench/README.md`（很长，像真实用户那样按需查，不必通读）。

## 想完成的事（顺序、做法自己定）

1. 第一次打开：不看文档能不能看懂怎么开始；把上面的目录加成项目（包括不该成功的：非 Git 目录、同一个目录加两次、手输一个不存在的路径）。
2. 项目终端：开几个、关几个；跑长输出（如 `seq 1 20000`）、中文输入、粘贴、Ctrl+C、`exit`；拖窗口大小、把窗口缩到很窄。
3. 让 AI 当主控：在 notes-cli 的终端里开 Claude（haiku），让它申请主控；先拒绝一次，再让它重新申请并批准；也试申请待批时直接关掉这个终端会怎样。
4. 让主控修 notes-cli 的两个毛病：建任务卡、派 worker、看 worker 窗格，中途在 worker 窗格里自己敲几个字（人工介入），等交付、审查、集成；最后在终端里看 `git log` 和代码确认真的改了、测试能过。worker 卡在信任框之类的，按边界处理并换 CLI。
5. 到处点：右键菜单（包括“复制深度链接”）、双击、键盘（Tab、方向键、Esc、Cmd+W）、菜单栏、设置（按角色改模型和强度，填些不合法的值再改回）。
6. 收尾类操作：移除一个还有终端或任务在跑的项目；关掉窗口再按上面的命令重开，看东西还在不在、agent 是否还在跑；浅色、深色都看一眼。

想到别的真实用户会做的事，也去试。总操作时间控制在 90 分钟左右。

## 报告

写到 `/private/tmp/uat/ui-check/REPORT.md`：

- 开头一句总体结论：PASS / INCOMPLETE / BLOCKED / NO_GO（有影响使用的缺陷就是 NO_GO；没做完就是 INCOMPLETE）。
- 问题清单，每条：编号、严重程度（阻断 / 严重 / 一般 / 轻微）、复现步骤、作为用户期望看到什么、实际看到什么（界面原文照抄）、截图文件名。
- 顺利完成的事，一句一条，附截图。
- 没做成或没试的，写原因。

最后一条回复给出同样的结论和问题清单摘要，用中文。
