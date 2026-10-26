# T-187 事实核对：agy 1.4.7 与 opencode v2.1.4

2026-10-25，执行主控实测。探针 `ptyprobe.py`：在 pty（140×40）里启动真实 CLI，按 `STEPS` 输入，保存原始输出。遇到 CLI 自己的信任或权限弹窗（OSC 7501 `blocked:kind=permission`）时立刻停下，不发送任何按键。这条规则是 probe-01 出事后加的，见文末。原始输出在外置盘，见 `probe-raw.archive.json`。

## 状态信号：两者都支持 OSC 7501

| 信号 | agy | opencode |
| --- | --- | --- |
| 是否输出 | 要在环境里设 `AGY_CLI_OSC7501=on`。它会先探测终端是否支持，Enchanted 的 pty 不回应这个探测 | 默认就输出，不需要设置 |
| 运行中 | `state=working:app=antigravity` | `state=working[:id=<会话>]:app=opencode:title=<base64>` |
| 回合结束 | 先 `state=done:...:msg=<base64 最后一条回复>`，再 `state=idle` | 先 `state=clear:id=<会话>`，再 `state=idle:app=opencode` |
| 等用户回答提问 | `state=blocked:kind=question:...:msg=<base64 问题原文>`（agy-03） | `state=blocked[:id=..]:kind=question:...:msg=<base64 "Input needs response">`（oc-01） |
| 等权限确认 | `state=blocked:kind=permission:...:msg=<base64 "Approve RunCommand: …" / "Trust this folder?">`（agy-04、agy-05、agy-02） | 未观察到 |
| 登录 | 启动时出现 `state=blocked:kind=auth`（"Sign in required"），随后变成 idle | 未观察到 |

因此后台可以从 pty 输出里直接解析 OSC 7501，得到运行中、空闲、等回答三种状态，不需要钩子，也不写这两个 CLI 的配置。

## 按会话注入（不写全局配置）

- opencode：环境变量 `OPENCODE_CONFIG_CONTENT` 能按会话传配置。直接运行 `opencode` 会连到已经在运行的后台服务，这个服务不读本会话的环境变量，所以 instructions 没生效（oc-01）。加 `--standalone` 后生效：回复带上了 instructions 要求的暗号（oc-02）。按会话传的插件在两种情况下都没有产生事件，原因未查；状态已经可以从 OSC 7501 拿到，所以没有继续追。
- agy：`--help` 里没有按会话的指令参数或插件目录参数。插件通过 `agy plugin install` 装进用户的全局配置，Enchanted 不能用。`-i` 会把文字当作一次提问发出去，不能当开局说明用。结论：agy 没有按会话注入开局说明的办法。

## 识别是哪个 CLI 发起的 `a2a request`

- opencode 执行命令时会给子进程设 `OPENCODE=1` 和 `OPENCODE_SESSION_ID`（env-oc.txt）。
- agy 的环境变量没取到：`--mode auto` 下它执行命令前仍要确认（agy-05），探针按规则停下了。
- 探针的子进程继承了外层 Claude Code 的 `CLAUDECODE=1`。只按 `CLAUDECODE` 判断，会把嵌套在里面的 opencode 认成 Claude。改为沿父进程链往上找，取第一个在 `terminalClis.ts` 里登记过的程序名，这样认出的是最内层的 CLI。

## 接入判断读得到什么

- `processArgs.py` 经 KERN_PROCARGS2 读进程的启动参数和启动环境。macOS 不给出系统自带程序（如 /bin/sh）的启动环境：对 `sh` 只读到 argv，读不到其中的 `A2A_SHIM`。第三方程序读得到：`A2A_SHIM=agy node …` 读出 `"shim": "agy"`。agy、opencode 都是第三方程序。

## 真实 agy 走不通的地方

- 隔离 HOME（`HOME=/private/tmp/t187-agy-home`）下 agy 没有登录，要求选择登录方式（Google OAuth / Google Cloud 项目）（agy-06）。登录不能代办，也不复制用户的 agy 凭据。
- 在用户自己的 `~/.gemini` 下运行时，每个新的夹具项目目录都会弹“Trust this folder?”，确认就写进用户配置。所以真实 agy 的端到端运行要用户本人点一次信任，或者由用户指定一个已经信任过的固定目录。

## worker 权限（需要用户决定）

- Codex worker：`-a never --sandbox workspace-write` 加 writable_roots，由操作系统沙箱保护 worktree 的 Git 元数据。Claude worker：shell 沙箱加 `--permission-mode dontAsk`。门禁逐项核对这些启动参数。
- agy：`--mode auto` 下执行命令仍逐条确认（agy-04、agy-05）。不想有人逐条点，就只能用 `--dangerously-skip-permissions`。`--sandbox` 的说明是 "terminal restrictions"，具体限制什么还没实测。每个新目录第一次打开都会弹“Trust this folder?”，确认后把该目录写进用户的 `~/.gemini/antigravity-cli/settings.json` 的 `trustedWorkspaces`；信任按具体目录记录，不从父目录继承（agy-02：家目录本身已在列表中，家目录下的新目录仍会弹框）。每个 attempt 都是新 worktree，所以每次派发都会弹一次，每次确认都写一次用户配置。
- opencode：没有操作系统沙箱。`--auto` 会自动批准所有没有明确拒绝的权限；可以经 `OPENCODE_CONFIG_CONTENT` 写按命令模式匹配的 permission 配置。没有新目录信任弹窗。

## probe-01 事故

第一次运行 agy 探针时，夹具放在 `/private/tmp/t187-probe/repo`。探针在固定的等待时间后盲发了提示文字和回车。回车落在 agy 的“Do you trust the contents of this project?”弹窗上，确认了默认项“Yes, I trust this folder”，于是 `/private/tmp/t187-probe/repo` 被写进了用户的 `~/.gemini/antigravity-cli/settings.json` 的 `trustedWorkspaces`（第 7 项）。这违反了“不把 Enter 当默认批准”和“不写全局配置”。之后的探针改成：先等到 idle 再输入，看到 `blocked:kind=permission` 立刻停下。那一项没有回退：回退本身又是一次写入，留给用户决定。
