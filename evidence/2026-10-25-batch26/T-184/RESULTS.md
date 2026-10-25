# T-184 结果：实测那轮主控终端没有钩子、没有 a2a 插件的原因

## 状态：PASS（根因已定位并取证；产品无需修改）

## 依据

ticket T-184（ready_rev 1）。用户 2026-10-25 原话：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”。对应 T-176 遗留：lcu 实测（真实 0.1.3、用户真实 Claude 2.1.310）中，主控终端一条钩子事件都没送到后台，技能里也没有 a2a。

## 根因

那一轮的主控 Claude 是用**绝对路径** `/Users/luckye/.local/bin/claude` 启动的，没有经过 Enchanted 的 `claude` 包装脚本，所以没有带上 `--plugin-dir`。插件没加载，于是钩子（UserPromptSubmit、Stop、PreToolUse）和 a2a skill 都不存在。

经过：前两次在项目终端里敲 `claude --model claude-haiku-5-5` 都没有任何输出（这是 L01：macOS 的“文稿”权限弹窗被压在其他窗口后面，CLI 卡在 openat），操作者按 Ctrl-C 结束；中间 `claude --version` 正常；第三次改用真实 CLI 的绝对路径启动，界面出现，之后整轮实测都在这个进程里。

这是实测时的操作偏差（为绕开 L01 而手工绕过了包装脚本），不是包装脚本、ZDOTDIR 启动链、PATH 顺序或 Claude 对 `--plugin-dir` 的处理出了问题。

## 证据

实测那轮的 0.1.3 后台（pid 61281，2026-10-24 23:25 启动）和主控终端至今仍在运行，以下均为只读采集：

| 文件 | 内容 |
| --- | --- |
| `process-argv-env.txt` | 主控终端 zsh（pid 62132，`/bin/zsh -l -i`）下的 Claude 进程（pid 66577）argv 为 `/Users/luckye/.local/bin/claude --model claude-haiku-5-5`，没有 `--plugin-dir`。它的环境里 PATH 第一项就是 `/Applications/Enchanted.app/Contents/Resources/app/terminal/bin`，`A2A_TERMINAL_BIN` 也在，说明 ZDOTDIR 启动链已正常生效；zsh 记下的 `_` 为 `/Users/luckye/.local/bin/claude`。令牌只记变量名。 |
| `pty-commands.txt` | 该终端 pty.raw 中依次提交的 4 条命令与时间：两次 `claude --model …` 无输出被中断，`claude --version` 正常，23:31:02 用绝对路径启动。 |
| `zprobe.py`、`zprobe-installed-0.1.3.txt` | 复现命令：用已安装 0.1.3 的 ZDOTDIR 启动链，在 pty 里起一个真正的交互登录 zsh（读用户自己的启动文件，不改动它们），在提示符下查 `claude` 的解析结果。第一项是包装脚本，`$commands[claude]` 也指向它，没有别名或函数。运行：`python3 zprobe.py /Applications/Enchanted.app/Contents/Resources/app/terminal`。 |
| `shim-argv.txt` | 已安装 0.1.3 的包装脚本把真实 CLI 换成只打印 argv 的替身后，敲 `claude --model claude-haiku-5-5`，实际执行的命令带 `--plugin-dir …/plugin/enchanted-a2a`。 |

## 已排除的假设

- 应用从 Herdr 用 `open` 启动、继承了 `HERDR_*`/`CLAUDECODE` 等变量：启动链照常生效（PATH 与 `A2A_TERMINAL_BIN` 正确）；T-176 用这些变量也复现不出缺失。
- 用户 zsh 启动脚本让 `claude` 解析到包装脚本以外：用户 `.zprofile`、`.zshrc` 往 PATH 前面加了 `~/.local/bin` 等目录，但启动链最后把包装目录挪回第一位；交互提示符下的解析结果为包装脚本，没有别名、函数或 precmd 改 PATH。
- 替换应用期间插件目录失效：包装脚本、插件目录都在，可执行权限正确（`-rwxr-xr-x`）。
- Claude 2.1.310 对 `--plugin-dir` 的行为：T-176 已用真实登录确认带 `--plugin-dir` 时插件能加载；T-181 的真实 haiku 复跑里插件钩子正常送达。

## 没做 / 未验证

- 没有修改产品代码：根因是绕过包装脚本，正常敲 `claude` 时包装脚本生效。
- ticket 第二条（“若可修：修前在真实应用复现钩子缺失，修后送达”）不适用：正常入口下无法复现缺失。为省用户额度，这里没有另起真实 Claude 复验；从 Dock 启动、敲 `claude` 后钩子送达，放到 T-186 装好 0.1.4 后的 lcu 复看里一并做。
- 一个可选的加固（未做，交构思主控决定）：如果希望用户用绝对路径或自己的别名启动 Claude 时插件也生效，需要改成不依赖 PATH 的加载方式（例如经终端环境变量指定插件目录）。这会改 T-120 定下的包装脚本做法，属于设计取舍。
