# T-174 结果：CLI 启动后无输出时的窗格提示

## 状态：INCOMPLETE（待 agy 审查）

## 根因与改动

L01：CLI 卡在 macOS 隐私弹窗（弹窗被其他窗口压住）时一个字节都不输出，窗格空白，界面没有任何提示。

- 只用一个机械事实：项目终端的前台程序在终端最后一次输出**之后**才启动，并且已经 6 秒没有输出。不猜原因，不替用户按键，不改系统设置。
- `workbench/src/processSnapshot.py`：进程行加 `started`（libproc 的启动时间，原来就读到了，只是没输出）。
- `workbench/src/panes.ts`：项目终端记录最后输出时间；输入后（新前台程序只会由输入启动）在安静满 6 秒时读一次进程树，找前台进程组长，满足条件就在 `pane_status` 里给出 `silent_foreground`（程序名、启动时间）；任何输出立刻清除。读进程树失败不出提示，记 `silent_foreground_check_failed` 事件，下次输入再查。
- `workbench/app/renderer.tsx`：窗格顶部显示提示：“claude 启动后还没有任何输出。它可能在等 macOS 的权限弹窗……有输出后这条提示自动消失。”
- 应用自身的隐私授权状态没有可靠读法，没有加指向系统设置的说明。

## 验收

测试：`workbench/tests/test_t174_silent_cli_hint_e2e.py`，真实 Electron、后台、node-pty、zsh；CLI 是 `t174_cli.c` 编译成的 `claude` 替身（silent：建标志文件前不输出；normal：立即输出后空闲），零模型调用。

| 运行 | 结果 |
| --- | --- |
| `--revision 8f36d6495`（修前 main） | 红：`idle_prompt_no_hint` 过，之后“超时：后台标出无输出的前台程序” |
| 修后（6edcf6f05 + 选择器修正 68c9fcf80） | PASS 6/6：6.8 秒出提示；有输出后后台与窗格都撤掉；正常启动 12 秒内无提示；空闲提示符无提示 |
| `--mutant no-start-check`（去掉“最后输出之后才启动”） | 被拒：正常启动的 CLI 也出提示 |

`setup-error-01/`：第一次三轮都停在测试自己的选择器（终端行已不在 `.project-terminals` 下），没有到达断言，保留原样。

截图：`shots/silent-hint.jpg`（提示出现）、`shots/after-output.jpg`（有输出后消失）。

复跑：

```sh
cd workbench/tests
python3 test_t174_silent_cli_hint_e2e.py --summary <新路径> [--revision <rev> | --mutant no-start-check]
```

## 没做

- 没用真实 Claude 复现隐私弹窗（需要撤销用户的系统授权，属于系统设置，不做）；替身只证明“无输出”这一机制。
