# red-01 只读诊断与后续脚本

日期：2026-10-17。状态：**INCOMPLETE**。red-01 不是有效产品红态；当前仅完成诊断、脚本修正及局部检查。未操作 PID 6599，未运行 Electron／daemon／PTY／系统进程查询／AppKit／截图，未改产品代码。

执行主控 #30 报告：“没有发生任何按键或模型回合”。原 `run.json` 同时记录 keys 为空、supplier_model_turns 为 0；本次诊断和新收尾脚本均不增加按键或模型回合。red-01 的 `red_observed: false`、`cleanup_complete: false` 和全部原件不改写，后续收尾成功也不把 red-01 上调为产品 PASS。

## 零输出的原因与证据边界

| 结论 | 证据与性质 |
| --- | --- |
| 构建产物没有缺失 | 实际只读检查 `red-01/build.json` 指向的 main、preload、renderer：均为普通文件，分别 9874、654、567 字节；main 导出 `run`，并在第 96 行等待 `app.whenReady()` |
| 现场支持已经进入 `run()` | 原夹具 `ui/` 中恰有 `session`、`logs`、`crashes` 三个空目录。父脚本只预建 ui 父目录，这三目录由已构建 `run()` 在 `app.whenReady()` 之前创建。这是执行到该段的副作用证据，强于仅看 PID 活着 |
| 最可能卡在入口模块与 ready 的相互等待 | 旧 `red_window.mjs` 在入口模块顶层 `await run()`；`run()` 又等待 Electron ready。仓库已有 `workbench/tests/bisect_electron_ready.py` 和现有 `electron_driver.mjs` 针对该模式改为不等待 run 完成便释放入口模块。此处重引入了已知问题。red-01 缺逐阶段日志，不能声称已采到具体 await 栈或 ready 事件时间线；本结论是代码与目录现场共同支持的高置信度诊断 |
| 零输出不能证明管道接错 | 旧 observer 的首次日志和 stdout ready 都在 `await run()` 之后，stdin 监听器也在之后。run 不返回就不会写这三份输出；零 stderr 也符合没有抛异常的等待。父脚本确实以 stdin/stdout PIPE 启动，但没有独立 OS 管道观测，不能把“接管道正确”写成已实测结论 |
| 收尾顺序确有错误 | 旧 `Observer.close()` 调用尚未安装监听器的 close RPC，再等一次 response 超时。外层 finally 捕获错误后仍无条件执行 `if started: daemon_stop`，所以后台与 CLI 已退出，而 Electron 6599 留下；与主控现场一致 |

三份 snapshot、process、first-screen 已保存，证明本次三个后台窗格的启动与身份读回已走到；它们不证明 Electron 同时显示三个窗格。原始输出根为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-01/`；主控日志为用户给出的 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t091-red-01.log`。

## (a) 只处理原 Electron 6599 的收尾

先审阅 `close_red01.py` 与 `owned_electron.py`。前者不接受 PID／夹具覆盖参数，锁定：

- PID `6599`，启动时间 `Sat Oct 17 06:30:34 2026`（按主控提供的本地时间固定）；完整命令须逐字匹配原 `electron-command.json` 的四项 argv。
- 原夹具 `/private/tmp/t078-2-t091-red-05cht89k`、原 state／user-data、原 window-plan 和输出根须一致。
- 原 daemon 5171 与六个 shell／CLI PID 只读检查，任何一个仍存在则停下；脚本不能停止它们。

通过检查后，仅对该 PID 的 `NSRunningApplication` 调一次 `terminate()` 请求正常退出；不按标题或 bundle id 批量退出，不发送 SIGTERM／SIGKILL，不用 forceTerminate，不发送窗口按键。SDK `NSRunningApplication.h` 将该方法定义为“正常退出请求”，且明确要求另行确认退出；脚本因此最多等 15 秒并读回 PID 消失。拒绝、超时、PID 被复用或命令不符都以 **BLOCKED / rc 2** 停下，不归档运行中现场。

```sh
python3 -B evidence/2026-10-16-batch16/T-091/close_red01.py \
  --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-01-close-01 \
  --label red-01-close-01 \
  --approval-ref '主控对仅 6599 正常退出及原夹具复制的本次批准位置'
```

只有确认所有原写入者已退出、后台端点消失，才复制原夹具到新外置输出的 `fixture/` 并比较文件数与总字节数。原夹具保留，不删原件，不改 `red-01/`。新清单 `red-01-close-01.archive.json` 含 original、archive、files、bytes、replay，不带校验值；新 `run.json` 的 **PASS / rc 0** 仅指收尾与复制完成。若 6599 在脚本运行前已自行退出，记录 already_absent，不向其他进程发送退出请求，再按同样规则检查与归档。

## (b) 修正脚本，用 red-02 新标签

修正保留原预算：两个固定 Claude CLI、一个受控 receiver、一个 Electron；供应商模型回合 0、假 Messages POST 0、按键／粘贴／放行 0，不复制 auth.json、不碰真登录。本次批准单独填写，不能沿用 red-01 或 T-078 的批准。

`red_window.mjs` 现在不在入口模块顶层等待启动；stdin 监听器先安装，`main()` 及 `run()` 都异步继续。它从 `module_loaded` 起写独立阶段日志，覆盖 main import、product run、Electron ready、窗口创建、页面加载、stdin 收到请求及 stdout 写入回调。由此可区分启动未进入、ready 未发生、loadFile 失败和实际协议错误。

`run_red.py` 在等待 ready 前保存 `electron-owner.json`；收尾经同一个 PID 正常退出方法，脱离 ready／stdin 协议。只有确认 Electron 退出，才停后台、核对其原子进程并归档。退出未确认时报告 `backend_cleanup_deferred`，不再把“后台停了”当作界面已关。父脚本自己的拒绝式假 API 会随脚本结束停止，此时不宣称整套运行仍可用。

确认 (a) 已完成后，审阅新清单并运行：

```sh
python3 -B evidence/2026-10-16-batch16/T-091/run_red.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t091 \
  --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-02 \
  --label red-02 \
  --approval-ref '主控对 red-02 CLI、hook、零按键与零模型预算的本次批准位置'
```

正常取得预期红态仍退出 **1**。须逐项核对 `red_observed: true`、expected 3／observed 1、`electron_exit_confirmed: true`、`cleanup_complete: true`、最终假 Messages POST 0，且无 error、archive_error 或收尾错误。原图仍仅用核对过归属的 `screencapture -l` 捕获单个隔离窗口；缺权限时停下报告，不改用其他截图范围。

## 已跑检查与未跑项

已执行以下纯检查，未调用 Electron、AppKit、ps 或任何原生 CLI：

```sh
python3 -B evidence/2026-10-16-batch16/T-091/test_red_cleanup.py --output evidence/2026-10-16-batch16/T-091/red-02-script-checks.json
node --check evidence/2026-10-16-batch16/T-091/red_window.mjs
```

纯 Python 两项检查为 **PASS**：启动未完成时收尾不等待未安装的 close RPC；Electron 退出未确认时不调用 daemon_stop。两项均执行原提交 `034257dc5d22810a2b40e7acac7a3a46551f052e` 的实际脚本类／finally 片段，分别因 RPC 等待和错误停后台行为被断言拒绝；当前片段通过。模拟边界仅覆盖 Python 编排，不证明 macOS 正常退出能力或 Electron ready 已修好。Python AST 语法检查、Node 语法检查通过；产品及原有测试相对起点 diff 仍为空。

仍未运行：对 6599 的任何退出操作、原夹具归档、red-02、截图、Tracer bullet 实现、三格绿态、反例与产品回归。当前交付到此，等主控实跑结果再推进。
