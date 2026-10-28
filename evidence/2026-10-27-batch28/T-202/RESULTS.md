# T-202 安静的命令也被说成可能在等权限弹窗（2026-10-27）

状态：INCOMPLETE。改动与替身复现已过 agy（`gemini-3.8-flash-high`）独立审查，结论“可合并”（`review-1.md`，一条 P3：测试要用 `/usr/bin/clang` 编译替身）；票的第 2 条验收（真实系统授权弹窗）未做，见文末。

## 做法

触发条件不变：前台程序启动满 6 秒、启动后终端没有任何输出（T-174 的机械事实）。只改 `workbench/app/renderer.tsx` 的文案：“如果它本该有输出（例如 claude、codex 启动后会画出界面），可能在等 macOS 的权限弹窗……；sleep 这类本来就不输出的命令不用管。”

没选“只对已知 CLI 提示”：系统授权框也会挡住别的程序；触发条件只认机械事实，判断交给读提示的人。

## 测试

`workbench/tests/test_t202_silent_hint_e2e.py`：真实后台、zsh 与 Electron 窗口，零模型调用。项目终端里先跑 `sleep 300`，再跑一个编译出来、名为 `claude`、读到一行输入前不输出的替身（模拟被“文稿”授权框挡住的 Claude Code）。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | `--revision a3ae46cf2`，替身是 shell 脚本 | sleep 两项失败；替身显示为 `sh`，CLI 那步超时（测试问题，已改为编译程序） |
| `red-2.json` | `--revision a3ae46cf2` | sleep 两项失败（断言“它可能在等”）；CLI 提示出现、有输出后消失 |
| `green-1.json` | 修后 | 4 项通过 |

T-174 的旧测试（断言提示里有 claude、权限弹窗、可能）在最终代码上重跑通过（`t174-regression.json`）。

复现：`python3 test_t202_silent_hint_e2e.py --summary <新路径> [--revision a3ae46cf2]`

## 没做（INCOMPLETE）

票的第 2 条验收要求“CLI 真被系统授权弹窗挡住时（可用新打包的 Enchanted Test 复现）提示仍出现”。本次用替身复现同一触发条件，没有重新打包触发真实系统弹窗：那会在用户屏幕上弹出系统授权框，需要用户本人处理。
