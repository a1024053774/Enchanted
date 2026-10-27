# 真实用户式试用 第 1 轮（2026-10-27）

用户原话：“然后最后也要让 gpt6.1terra 用 computer use 测试一下软件，像真实用户一样使用，不要只测试我们验证没问题的路径。”

状态：BLOCKED。主控 → 派发 → 交付 → 审查 → 集成这条主路径没走成：Enchanted Test 终端里的 CLI 读用户的 `~/Documents` 时，macOS 弹出“文稿”文件夹访问授权，CLI 停在那里。系统隐私授权不在代批范围内，要用户本人点。其余发现见下。

## 做法

- 被测：`main` `37b17192b`（含 T-194、T-195），`node app/package.mjs --slot uat01 --variant test` 打包的 Enchanted Test；状态目录 `/private/tmp/uat/state`，界面数据 `/private/tmp/uat/ui`，都是新建的隔离目录。
- 夹具：`/private/tmp/uat/repos/` 下 notes-cli（带两个已知小毛病）、landing-page、`我的 项目`（中文加空格）、not-a-repo（非 Git）。
- 试用者：Codex `gpt-6.1-terra` high，Computer Use，按 `BRIEF.md` 自己摸索；工作目录 `/private/tmp/uat`，信任经启动参数 `-c projects."/private/tmp/uat".trust_level="trusted"` 给，不写全局配置。报告原文 `REPORT-round1.md`；截图在外置盘，见 `ui-check-round1.archive.json`。
- 本轮没有代批任何 Computer Use 或系统授权。

## 发现

| # | 现象 | 判断 | 去向 |
| --- | --- | --- | --- |
| 1 | 终端里的 Claude（haiku）启动后几分钟零输出 | 环境：见下“Claude 无输出的归因”；应用自己的提示说对了原因 | 主路径 BLOCKED，等用户授权 |
| 2 | 中文目录“我的 项目”在侧栏和标题里显示为 `project` | 缺陷：项目号只能用 ASCII，界面直接拿项目号当名字；第二个中文目录会显示 `project-2` | T-200 |
| 3 | 非 Git 目录能加成项目，侧栏显示原始的 `git status` 报错（被截断） | 缺陷：能加是设计（可以在任意目录开终端），但状态应当说“不是 Git 仓库”，不露原始命令错误 | T-201 |
| 4 | `sleep 300` 这类本来就安静的命令也提示“可能在等 macOS 的权限弹窗” | 缺陷（文案）：提示只看“没有输出”，对本来就不输出的命令说得太肯定 | T-202 |
| 5 | 设置里 worker 的思考强度填 `banana` 也显示“已保存” | 按 T-112 设计不按固定值拒绝；是否加提示留给用户定，不开票 | — |
| 6 | Codex、agy 在新目录弹信任框，opencode 要求连接集成 | 设计行为（T-141；agy 信任由后台核对画面后处理，见 T-187）；试用者按边界没选 | — |

顺利的：首屏提示能看懂；加项目、同目录不重复；`seq 1 20000` 长输出、中文粘贴、Ctrl+C、`exit` 后转为只读历史；分屏两个终端；普通终端的“复制深度链接”置灰并说明原因；有运行中终端时移除项目被拦下并提示；Cmd+W 关窗后用同一命令重开，项目和终端还在；浅色、深色。

没测到：主控申请（拒绝、批准、待批时关终端）、建卡、派发、人工介入、审查、集成；受管会话的深度链接；窄窗口。

## Claude 无输出的归因

- 同一 Claude 2.1.311、同一夹具目录，在本机 pty 里（无论带不带 Enchanted 终端的环境变量与插件）都在几秒内画出信任框。
- 应用内两次启动、`pty.raw` 里 Claude 没写出任何字节；Claude 下次启动时说“全屏渲染上次没启动完”。
- 用户的 `~/.claude/skills`（以及 Codex、agy 的技能目录）有链接指向 `~/Documents/SKILLS`。探针轮（`BRIEF-probe.md`、`REPORT-probe.md`）在应用里再启动一次 Claude，同时录 tccd 日志：Claude 的二进制以 Enchanted Test（`org.a2a.workbench.test`）为责任进程请求 `kTCCServiceSystemPolicyDocumentsFolder`，tccd 记 `AUTHREQ_PROMPTING`（摘录 `tccd-documents-prompt.log`，完整日志在外置盘 `UAT-01/tccd-stream.log`）。
- 每次新打包的 Enchanted Test 是 ad-hoc 签名的新身份，“文稿”授权不继承；用户日常用的 Enchanted 已有授权，所以不影响日常使用。试用者的 Computer Use 只截应用窗口，看不到这个系统弹窗。

## 继续的条件

用户在系统弹窗（或“系统设置 → 隐私与安全性 → 文件与文件夹”）里允许 Enchanted Test 访问“文稿”后，用同一个打包（uat01）跑第 2 轮，覆盖上面“没测到”的部分。
