# T-184 结果：实测那轮主控终端没有钩子、没有 a2a 插件的原因

## 状态：PASS

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

## 独立审查

agy（只读）审查候选 cb8f002a8：`T-184 REVIEW PASS`。两项 P3：正常入口下钩子送达没有在本票用真实模型复验（上面已写明，挪到 T-186）；包装机制完全依赖 PATH（即上面的可选加固，交构思主控）。全文 `review-agy-01.md`。

## ready_rev 2：绕过包装脚本时界面提示

构思主控在 ready_rev 2 写入用户 2026-10-25 的选择：“不加固，绕过时界面提示 (Recommended)”。要求：后台发现项目终端里前台的 claude/codex 进程没有带 Enchanted 的接入参数时，在窗格里提示，该会话状态显示未知，不显示假状态；只依据进程 argv。上面“可选的加固”因此不做。

### 改动

- `src/processArgs.py`（新）：用 sysctl `KERN_PROCARGS2` 读一个进程的 argv。只对用户自己的进程有效；输出只给后台做一次判断，不入库。实测那轮仍在运行的进程读出来正是 `/Users/luckye/.local/bin/claude --model claude-haiku-5-5`。
- `src/terminalClis.ts`（新）：包装脚本所包的 CLI，以及各自“经过包装脚本”的判据，集中在一处（T-187 加新 CLI 也加在这里）。Claude 的判据是 `--plugin-dir` 后面跟 `…/plugin/enchanted-a2a`；Codex 的判据是某个参数里含 `$A2A_TERMINAL_BIN/a2a`（钩子命令里未展开的写法）。
- `src/panes.ts`：项目终端里每提交一行，约 1.5 秒后读前台进程组长的 argv，按 argv[0] 的文件名查判据。是被包的 CLI 却缺接入参数，就记为“未接入”，每 5 秒复查一次，CLI 退出后撤下。读进程失败时不显示提示，并记 `cli_wiring_check_failed`。`pane_status` 加 `unwired_cli`。
- `src/sidebar.ts`：未接入的会话，主控行和普通终端行的状态都显示“未知”。修前，主控行在有会话号时会默认“运行中”。
- `app/renderer.tsx`：窗格提示“这个会话没接入 Enchanted，状态和主控命令不可用。退出后直接敲 claude 重启（不要用绝对路径或别名启动）。”。
- `README.md` 同步。

### 验收（真实 Electron、后台、项目终端与包装脚本；真实 Claude Code 2.1.310 用本地脚本化接口、不发提示词；真实 Codex 0.164 用空的隔离 home，停在启动画面）

`workbench/tests/test_t184_unwired_cli_e2e.py`，场景：

1. 终端 B 用真实 claude 的绝对路径启动（与 lcu 实测原样），再以这个终端的身份完成执行主控的角色申请。申请方式与 Claude 里运行 `a2a request executor` 相同：上报 cli=claude 和会话号，后台批准并确认。
2. 终端 N 直接敲 `claude`。
3. 终端 C 用真实 codex 的绝对路径启动，终端 D 直接敲 `codex`。
4. B 里 `/exit` 回到 shell。

| 运行 | 结果 |
| --- | --- |
| 修前 main（`red-main-01`） | 4 项失败：B 没有提示，主控行“运行中”（即 lcu L03 的假状态）；C 没有提示、“运行中”。截图 `shots/red-main-01-bypassed-claude.jpg` |
| 修后 `green-04`、`green-05` | PASS 8/8：B 有提示（claude），状态“未知”；N 无提示，“运行中”；C 有提示（codex），“未知”；D 无提示；B 退出后提示撤下。截图 `shots/green-05-bypassed-claude.jpg` |
| 合并 main（含 T-185 的 Codex SessionStart 参数）后 `green-06-after-main-merge` | PASS 8/8 |
| 变异 `name-only`（只看进程名，不看接入参数） | 被拒：N、D 误报 |
| 变异 `never-clears`（CLI 退出后不撤） | 被拒：`warning_clears_after_exit` |

`setup-error-01/` 按原样保留测试过程中的问题：

- 前两轮是测试自身的问题（侧栏行还没出现就点了；隐藏窗格只在可见时才刷新状态）。
- `green-02` 实际查出了被测代码的一个缺陷：Codex 判据最初要求 `"$A2A_TERMINAL_BIN/a2a"` 两边紧跟引号，而真实 argv 里写的是 `\"$A2A_TERMINAL_BIN/a2a\"`，结果经包装脚本启动的 codex 也被误报。已改为只认 `$A2A_TERMINAL_BIN/a2a`。

### 回归

`test_t174_silent_cli_hint_e2e.py`（与本票共用每秒一次的定时器）：PASS 6 项（`regression-t174-01`）。

### 没做 / 未验证

- 只认 argv[0] 文件名为 `claude`、`codex` 的进程。以 `node …/cli.js` 方式启动的 CLI 不会被认出来，也就不提示（不会误报）。
- 用户从 Dock 启动的真实应用里复看，放在 T-186 装好 0.1.4 之后做。

## 独立审查第二轮（ready_rev 2，`review-agy-02.md`，候选 85ddd951f）：`T-184 REVIEW PASS`

- F01（P3）：通过项是 8 项，不是 9 项。终端 D 只断言了没有提示，状态只记录、没有断言。已把上表改为 8/8。
- F02（P3）：说变异和 setup-error 的 summary 没有落盘。这一条与事实不符：`mutant-name-only-01`、`mutant-never-clears-01`、`setup-error-01/green-02-codex-marker-false-positive` 等的 summary.json 都已提交。不改。
- F03（P3，观察）：Claude 的判据假定 `--plugin-dir <目录>` 分成两个参数，与包装脚本一致；以后包装脚本改写法时要同步改判据，判据集中在 `terminalClis.ts` 一处。
