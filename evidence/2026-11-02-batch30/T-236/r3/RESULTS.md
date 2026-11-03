# T-236 / T-238 第 3 轮（2026-11-02 本地 11:25–12:10）

> **2026-11-03 更正与结果（见文末“用户回答授权框之后”）**：用户运行 `cat` 后同意了 macOS 的“文稿”文件夹授权框（在哪个应用里运行未说明）；之后同一个包里同一组 18 个混合路径全部打开成功（15 个在 `~/Documents`；探针只核对 `open`），独立进程也改为立即得到 `Operation not permitted`，不再卡住。下面写于 11-02 的“检查没有送到 `tccd`”只是当时日志里的观察。授权操作后症状消失，强烈支持隐私授权（TCC）相关的原因；具体排队机制（是哪个请求挂着、属于哪个应用）未确认。

结论（11-02 写）：**BLOCKED（根因在 macOS，不在 Enchanted）**。卡住的是 macOS 对 `~/Documents` 的隐私访问检查（TCC“文稿”文件夹）：凡是需要 TCC 新做一次判定的进程，打开 `~/Documents` 下的文件都会停在内核 `open` 里，而这次检查没有送到 `tccd`（`tccd` 日志里没有对应请求），所以既不弹授权框、也不拒绝，一直等到信号打断。Enchanted 终端只是受影响的入口之一。恢复要靠系统层面（建议重启 macOS 后复测），没有可做的 Enchanted 代码修复。

## 关键证据（时间为本地时间，命令都在仓库根目录运行）

| 时间 | 入口 | 结果 | 证据 |
| --- | --- | --- | --- |
| 11:26 | 主控工具进程（负责进程是已有“文稿”授权的 Claude 桌面应用）打开 11 个路径 | 0.03 秒内都返回：10 个 ok，1 个是目录（`IsADirectoryError`），没有等待 | `probe-mytool.json` |
| 11:26 | Claude 桌面应用的侧边终端 | 同上：10 个 ok、1 个 `IsADirectoryError`，没有等待 | `probe-termtab.json` |
| 11:27–11:29 | 打包应用 `a2a-build-t238-20261102` 的项目终端：读 21 个 SKILL.md；启动 Claude | 都正常，Claude 画出信任框 | `pkg-skills-a.json`、`pkg-claude-b.txt` |
| 11:5x | Codex Computer Use 复验（`../../cu-t239/REPORT.md` 场景 B）：项目终端里 Claude 无画面、Codex 输入排队、agy 一直 Working | 三家都不回复 | 该报告与采样 |
| 11:53 | 打包应用 `a2a-build-t239-20261102` 的项目终端里启动 Claude | 调试日志停在 `Loaded 3 installed plugins`，无画面 | `pkg-claude-c.txt` |
| 11:55 | 同一包，逐个 `cat` skill 文件 | 第 3 个（`~/Documents/SKILLS/architecture-flow-map-skill/…/SKILL.md`）停在 `__open` 超过 27 秒 | `pkg-skills-d.json` |
| 11:58 | 同一包，38 个 SKILLS 下的文件，其中一半先由主控进程读过一次 | 38 个全部 3 秒超时；先读过的也一样（“读过一次就不卡”的猜想不成立） | `cache-probe-1.json` |
| 12:00 | 同一包，混合路径 | `/private/tmp`、`~/.agents` 下的文件成功；`~/Documents` 下只有 `Code/a2a`、`Code/a1024053774.github.io` 里的文件成功，其他（`Code/VibeGame`、`Code/x-algorithm`、`GeoShift`、`Synara`、`SKILLS`）全部超时 | `cache-probe-2.json` |
| 12:01 | 同一包，3 个会卡的文件，同时抓 TCC/Sandbox 日志 | 3 个都超时；期间 `kTCCServiceSystemPolicyDocumentsFolder` 请求 0 条 | `cache-probe-3.json`、`tcc-stream-1.summary.txt` |
| 12:03 | 包加上 `NSDocumentsFolderUsageDescription` 等三项用途说明、重新 ad-hoc 签名 | 照样超时，没有变化 | `cache-probe-4-plist.json` |
| 12:05 | 与 Claude 桌面应用、Enchanted 都无关的 launchd 独立任务（`launchctl submit`，perl 打开文件，4 秒超时） | `Code/VibeGame/README.md` 与 `Code/a2a/AGENTS.md` 都超时，`/private/tmp` 文件成功；同一时刻主控进程读 `VibeGame/README.md` 0.004 秒；`tccd` 日志里没有这个任务的任何请求 | `lprobe.sh`、`lprobe.out` |

## 怎么解释这些现象

- **按负责进程区分**：主控工具进程的负责进程是 Claude 桌面应用（它声明了 `NSDocumentsFolderUsageDescription`，已有“文稿”授权），所以从不卡；Enchanted 的项目终端（负责进程是 `org.a2a.workbench`，ad-hoc 签名）、launchd 独立任务、上午 Codex 的进程都需要 TCC 判定，所以卡。
- **按目录区分（推断）**：`Code/a2a` 与 `Code/a1024053774.github.io` 的 `com.apple.macl` 里都有同一个标识 `8AEB14CC-3865-4086-9BBE-3D4E0E339958`，这两个目录都在 Enchanted 里用“打开目录”对话框选过；这符合“用户主动选择留下授权”的解释，但没有直接证明该标识代表 Enchanted。launchd 任务连 `Code/a2a` 也卡。
- **为什么是“卡住”而不是弹框或拒绝**：卡住期间抓到的 `tccd` 日志里没有“文稿”文件夹请求（系统 tccd 和用户 tccd 都没有）；内核那一侧在等什么，没有直接记录。上午 Codex 看到的“5 秒后 `Interrupted system call`”与这里的“一直等到 alarm”是同一种等待被不同方式打断。
- **为什么 11:26–11:29 正常**：未查清。那段时间同一个旧包里读 SKILLS、启动 Claude 都正常，几十分钟后新包又卡。两个包的代码只差 T-239 的界面解码，但签名身份不同（每个 ad-hoc 包是新身份），所以不能据此判断是“通路时好时坏”还是身份差异。

## 没有做、以及为什么

- 没有改 Enchanted 运行时代码：没有发现需要修改它的证据；在终端里加超时、重试只会掩盖。`NSDocumentsFolderUsageDescription` 是可选、推荐的授权框说明文案，缺少它本身不构成缺陷；加上它的实验在当时没有改善现象，但这不证明它没有价值，留作体验改进，本次不提交。目前没有可靠识别“在等授权”的办法，不加自动检测或重试。
- 没有重启 `tccd`、`sandboxd`，也没有重启系统：这是用户的系统层操作。
- 没有点击任何 macOS 权限框（本轮也没有出现）。

## 用户回来后可以做的

1. 重启 macOS，然后在打包应用的项目终端里运行 `cat ~/Documents/Code/VibeGame/README.md`：应当立即读出，或者弹出“想访问‘文稿’文件夹”的授权框。
2. 如果弹框，由用户决定是否允许。注意：每个新打的 ad-hoc 包是一个新身份，授权不会沿用；`/Applications/Enchanted.app` 的授权在下次替换前有效。
3. 若重启后仍卡，需要用户运行一条需要密码的命令采集内核等待点：`sudo fs_usage -w -f filesys <卡住的进程 pid>`。

## 用户回答授权框之后（2026-11-03 本地 03:34）

用户：“我已执行 cat 命令然后同意了读取目录”。没有重启（uptime 8 天 14 小时）。

| 入口 | 结果 | 证据 |
| --- | --- | --- |
| 打包应用 `a2a-build-t239-20261102` 的项目终端，与 12:00 同一组 18 个路径 | 全部打开成功（其中 15 个在 `~/Documents`，之前 12 个超时；只核对 `open`） | `cache-probe-5-after-grant.json` |
| launchd 独立任务（与 12:05 同一脚本） | `~/Documents` 下两个文件 0–1 秒内 `Operation not permitted`，`/private/tmp` 文件成功：TCC 照常判定并拒绝，不再卡住 | `lprobe-after-grant.out`、`lprobe-after-grant.err` |

判断：用户做了授权操作后症状消失，同一组路径恢复打开成功，独立进程从超时变为立即被拒绝。这强烈支持隐私授权（TCC）相关的原因；具体是哪个请求挂着、属于哪个应用，没有直接记录，排队机制未确认。没有发现需要修改 Enchanted 运行时代码的证据。README 里加一段条件式的排查说明：遇到终端里程序无输出或排队，先检查有没有 macOS 授权框；重新构建的 ad-hoc 包可能需要重新授权。授权后的 Computer Use 复测（`../../cu-cli-r2/REPORT.md`）中三家 CLI 都回复了，这只证明本轮问答可用，不涵盖 `a2a request`、受管窗格或完整交付闭环。
