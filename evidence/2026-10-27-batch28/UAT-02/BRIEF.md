# Enchanted 真实用户式试用 第 2 轮（Computer Use）

接着第 1 轮（报告在 `/private/tmp/uat/ui-check/REPORT.md`，看一眼避免重复）。用户已经允许 Enchanted Test 访问“文稿”文件夹，终端里的 Claude 现在应当能启动。这一轮专攻第 1 轮没走成的主路径，并且像真实用户那样在路上犯错、换路子；不要只走顺的路。

## 边界（必须遵守）

- 只操作 **Enchanted Test**（bundle id `org.a2a.workbench.test`），不碰用户自己的 **Enchanted** 或其他应用；不改系统设置；遇到登录、密码、付款、系统隐私授权就停下记 BLOCKED。
- 只在 `/private/tmp/uat/` 下改文件；不 `git push`。
- 信任框：**Claude Code** 对 `/private/tmp/uat/repos/` 下的夹具仓库问“是否信任这个文件夹”时，可以选信任（只限这些夹具目录）。Codex 的 “Trust this folder?” 不要选信任；agy 的信任由应用后台处理，你不要替它选。遇到不能选的信任框，截图记下，换别的 CLI 或别的路子。
- 项目终端里启动 Claude Code 一律用 `claude --model claude-haiku-5-5`。
- 同一时间最多一个 worker 在跑。
- 截图和报告只写进 `/private/tmp/uat/ui-check2/`，截图文件名带编号。
- 应用退出后重开用：
  `open -n "/var/folders/7v/58svbpnj5k91zdnm5zggb38h0000gn/T/a2a-build-uat01/Enchanted Test.app" --args --state /private/tmp/uat/state --user-data /private/tmp/uat/ui`

## 想完成的事

1. 在 notes-cli 的终端里开 Claude（haiku），让它申请当主控（用自然语言说，比如“你来当这个项目的主控”，看它自己会不会找到办法）。界面上出现申请时，**先拒绝一次**；再让它重新申请，**批准**。另开一个终端再开一个 Claude 申请，待批时直接关掉那个终端，看申请怎么处理。
2. 让主控修 notes-cli 的两个毛病：`done` 给不存在的编号会崩溃；`add` 不带文字会加一条空笔记。让它建任务卡、派 worker。看任务页和 worker 窗格；中途在 worker 窗格里自己敲一句话（人工介入），看界面怎么记。
3. 等交付、审查、集成。worker 卡在信任框、登录或报错时：截图，按边界处理，让主控回收后换一个 CLI 重新派（例如 Claude Code 或 agy）。记下你作为用户看到了什么提示、能不能自己弄明白下一步。
4. 集成后在普通终端里 `git log --oneline`、`python3 -m unittest -v`、`python3 notes.py done 99`、`python3 notes.py add` 确认真的修好了。
5. 顺路再试：右键受管会话行的“复制深度链接”，把剪贴板内容记下；“流程”“问题”“记录”“指标”几个页签各点开看一眼是否看得懂、有没有报错；任务进行中关掉窗口再按上面命令重开，看 worker 是否还在跑、界面是否接得上。

想到别的真实用户会做的事，也去试。总操作时间控制在 90 分钟左右；worker 长时间没有进展（15 分钟以上）就记下并换路子。

## 报告

写到 `/private/tmp/uat/ui-check2/REPORT.md`：

- 开头一句总体结论：PASS / INCOMPLETE / BLOCKED / NO_GO。
- 问题清单，每条：编号、严重程度（阻断 / 严重 / 一般 / 轻微）、复现步骤、作为用户期望看到什么、实际看到什么（界面原文照抄）、截图文件名。
- 顺利完成的事，一句一条，附截图。
- 没做成或没试的，写原因。

最后一条回复给出同样的结论和问题清单摘要，用中文。
