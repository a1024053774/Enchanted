# T-204 关闭终端后窗格报 a2a:resize 内部错误（2026-10-27）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，见 `review-1.md`。

## 根因

关闭普通终端时，后台要等终端里的前台程序退出（`confirmShellExit`，最多 5 秒）。试用里前台是 Claude Code，收到挂断后要过一会儿才退出。这几秒里 shell 已退出，待批申请随之结束，界面顶部的申请横幅消失，所有窗格变高。正在关闭的窗格这时照常向主进程发 resize，并继续轮询快照。主进程对正在关闭的窗格拒绝这两种请求（`Window is not available for input`、`Task view changed`），界面把前者当“输入尚未确认”显示，把后者当连接错误显示。

空闲的 zsh 收到挂断立即退出，复现不出来（`red-1.json` 在旧场景下通过）。

## 修复

`workbench/app/renderer.tsx`：用户点“关闭窗格”后，该窗格不再发 resize，也暂停轮询快照。关闭失败时恢复，并补发一次当前尺寸。主进程对关闭中窗格的拒绝保持不变。

## 测试

`workbench/tests/test_t204_close_pane_e2e.py`：真实后台、真实 Electron 窗口（CDP 驱动）、真实 zsh，零模型调用。场景：

1. 第二个普通终端发出构思主控申请，申请待批；终端前台跑一个收到挂断后 3 秒才退出的程序。
2. 在界面打开这个终端，从窗格菜单“向右分屏”开一个新终端。
3. 点击待批终端的关闭按钮。

检查：

- 关闭全过程中，MutationObserver 记下的所有 alert 都不含内部错误。
- 申请已结束；关闭后再批准，仍被拒绝（`request_not_pending`）。
- 剩下的终端仍可输入，PTY 跟着变宽（77 → 159 列）。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | 修前，空闲 zsh、无分屏 | 通过（场景不足以复现，保留为记录） |
| `red-2.json` | 修前，加慢退出前台程序 | 失败：`a2a:snapshot … Task view changed`、`输入尚未确认 … a2a:resize … Window is not available for input` |
| `red-3.json` | `--revision a3ae46cf2`，最终场景 | 失败，同上两条 |
| `green-1.json` | 修后，无分屏 | 通过 |
| `green-2-run1..4.json` | 修后，最终场景 | 通过（本应是 red-3 与两个变异体；shell 循环没把参数传进去，四次实际都跑的是修后代码，按实际内容改名保留） |
| `green-3.json`、`green-4.json` | 修后，最终场景（green-4 含“关闭后再批准被拒”） | 通过，6 项检查 |
| `mutant-resize-while-closing.json` | 去掉 resize 守护 | 失败：`a2a:resize` 错误 |
| `mutant-poll-while-closing.json` | 去掉轮询守护 | 失败：`a2a:snapshot` 错误 |
| `mutant-no-resize.json` | 停掉所有 resize | 失败：剩下的终端没有变宽 |
| `green-final.json` | 最终代码（含 T-200、T-202 对 renderer 的改动） | 通过 |

截图在外置盘，清单见 `screenshots.archive.json`。

复现命令（在 `workbench/tests` 下）：

```
python3 test_t204_close_pane_e2e.py --summary <新路径> [--revision a3ae46cf2 | --mutant resize-while-closing|poll-while-closing|no-resize]
```

## 没做

- 审查 P3：关闭过渡的几秒内，用户自己点回终端再打字，仍会看到“输入尚未确认”。这是用户主动输入，提示内容也属实，本次不改。
- 票里“可以说一句申请已随终端关闭而作废”是可选项，本次没加提示。
- 主进程 `a2a:close-pane` 的已有问题：`window_close` 失败时 `pane.closing` 不复位，窗格会一直拒绝输入。这次没有触发，也不在本票范围内，只在这里记下。
