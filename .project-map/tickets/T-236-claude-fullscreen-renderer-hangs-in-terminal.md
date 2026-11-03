---
id: T-236
title: 项目终端里启动 Claude Code 没有任何输出（与 macOS 隐私授权有关，授权后恢复；未发现 Enchanted 缺陷）
type: build
status: out-of-scope
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---
## What to build

2026-11-02 Computer Use 实测发现（`evidence/2026-11-02-batch30/cu-bugsweep/BUGS.md`、`BUGS-r2.md`，截图 `shots/r2-claude-no-output.png`）：在隔离的 Enchanted（HEAD `2b3b12dac` 打包）项目终端里运行 `claude --model claude-haiku-5-5`，3 次都是 5～7 分钟只显示命令行、没有界面也没有报错，进程还在。

主控随后在 Claude Code 桌面应用的普通终端里，用同一个插件目录启动 Claude，Claude 先打印：上次在这台机器上 fullscreen renderer 没能启动完成，这次改用 classic renderer，下次还会再试 fullscreen。所以无输出就是全屏渲染器在 Enchanted 终端（私有 hc core + xterm.js）里启动卡住。复盘那次 Claude 有界面，是因为它是紧接着失败之后的那次启动，自动退回了经典渲染器。

推测（未核实）：全屏渲染器启动时向终端发了某个查询（设备属性、尺寸、键盘协议等），hc 或 xterm.js 这一层没有回应。要查清是哪个查询、该由哪一层回应，修在根因处；不靠让用户改 Claude 的 `/tui` 设置（那会写 `~/.claude`）。

## Acceptance

- [ ] 先写下可能出错的方式。
- [ ] 修前红态：项目终端里 Claude 首次启动无输出，记下终端收到但没回应的序列。
- [ ] 修后：项目终端连续多次启动 Claude（每次都走全屏渲染器）都出界面；受管 worker、复盘窗格同样。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

2026-11-02 进展（未关闭）。原推测“全屏渲染器在 Enchanted 终端里起不来”与第 1 版结论“文稿文件夹授权”都不成立：

- 已查到的（[T-236 结果](../../evidence/2026-11-02-batch30/T-236/RESULTS.md)、[T-238 第 2 轮报告](../../evidence/2026-11-02-batch30/T-238/REPORT-02.md)）：项目终端里的 Claude 停在加载 skill 时打开 `~/Documents/SKILLS/...` 下的文件；Codex、agy 卡住时也各有线程停在 open 类系统调用（路径未取得）。
- 打开 `~/Documents/SKILLS` 下的几个 SKILL.md 会在内核 `open` 里停约 5 秒后以 `Interrupted system call` 失败；同一现象在打包应用的终端、源码后台的终端、Codex 自己的进程里都出现，**不是 Enchanted 独有**；主控工具进程里读同样的文件 0.02 秒内返回。`~/Documents` 下别处的文件（如 `~/Documents/Code/a2a/AGENTS.md`）读得出来。
- 已否定：“新包在等文稿文件夹授权”（从没启动过的新包读 `~/Documents` 0.11 秒返回，`tccd` 无该请求）；已排除：文件被占用、iCloud、Endpoint Security 扩展。`~/Documents/SKILLS` 及部分子目录带 `com.apple.macl`，与此是否有关未查；再往下需要 `sudo fs_usage` 一类的系统工具，主控没有这个权限。
- 目前没有证据表明是 Enchanted 的代码缺陷，也没有可做的代码修复；状态 **INCOMPLETE**，等用户决定是否继续查。

2026-11-02 第 3 轮（[结果](../../evidence/2026-11-02-batch30/T-236/r3/RESULTS.md)），状态 **BLOCKED**，等用户重启 macOS 后复测：

- 根因层定位到 macOS：卡住的是 TCC“文稿”文件夹访问检查。凡是需要 TCC 新做判定的进程（Enchanted 项目终端、与 Claude 桌面应用和 Enchanted 都无关的 launchd 独立任务、上午 Codex 的进程），打开 `~/Documents` 下的文件都停在内核 `open`；卡住期间 `tccd` 没收到任何“文稿”文件夹请求，所以既不弹框也不拒绝。已有授权的 Claude 桌面应用的进程，以及在 Enchanted 里用“打开目录”对话框选过的目录（`com.apple.macl` 里有同一个应用标识），不受影响。不只 SKILLS，`~/Documents` 下大多数目录都一样。
- 现象时好时坏：11:26–11:29 同一个旧包里一切正常，11:5x 起新包又卡；两个包的代码只差 T-239 的界面解码。
- 没有发现 Enchanted 代码缺陷的证据，不在终端里加超时或重试。给包加 `NSDocumentsFolderUsageDescription` 等用途说明的实验没有改变结果（检查根本没送到 `tccd`），没有提交；系统恢复后再复测要不要加。
- 用户回来后：重启 macOS；在打包应用的项目终端里 `cat ~/Documents/Code/VibeGame/README.md`，应立即读出或弹出授权框（是否允许由用户决定；每个新 ad-hoc 包是新身份，授权不沿用）。仍卡则需用户运行 `sudo fs_usage -w -f filesys <pid>`。

2026-11-03 以 out-of-scope 结束（证据强烈支持 macOS 隐私授权相关原因，未发现需要修改 Enchanted 运行时代码的证据；验收项未执行，不勾选、不补称通过；[第 3 轮结果](../../evidence/2026-11-02-batch30/T-236/r3/RESULTS.md)，[关闭审查](../../evidence/2026-11-02-batch30/T-236/reviews/)）：

- 用户：“我已执行 cat 命令然后同意了读取目录”（没有重启）。之后打包应用项目终端里与 11-02 同一组 18 个混合路径全部打开成功（其中 15 个在 `~/Documents`，此前 12 个超时；探针只核对 `open` 成功）；launchd 独立进程从超时变为立即 `Operation not permitted`。
- 授权操作后症状消失，强烈支持隐私授权（TCC）相关的原因；具体是哪个请求挂着、属于哪个应用，没有直接记录，排队机制未确认。没有发现需要修改 Enchanted 运行时代码的证据。
- 授权后 Codex `gpt-6.1-terra` Computer Use 复测（[报告](../../evidence/2026-11-02-batch30/cu-cli-r2/REPORT.md)）：项目终端里 Claude Code、Codex、agy 都回复了“测试正常。”。这只证明本轮问答可用。
- `workbench/README.md` 加一段条件式排查说明：终端里程序无输出或排队时先检查系统授权框；重新构建的 ad-hoc 包可能需要重新授权。
- `NSDocumentsFolderUsageDescription` 是可选的授权框说明文案，留作体验改进，本次不加。
- 原验收建立在已被推翻的“全屏渲染器在 Enchanted 终端里起不来”推测上：“记下终端收到但没回应的序列”“连续多次全屏启动、受管 worker、复盘窗格同样”这几条没有执行，按不适用处理，不补称通过。
