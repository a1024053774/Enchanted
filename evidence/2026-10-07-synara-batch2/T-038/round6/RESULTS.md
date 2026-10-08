# 决定 06：一轮有限复验（2026-10-08）

**INCOMPLETE，一轮结束，交接主控。** 未改代码，候选仍为 `ad13b72c5faeb5fb601c3d40b7090d746f4f2758`；旧结论、独立审查与失败现场全部保留。ticket 第 1 项仍未通过。本轮没有模型 turn、响应拦截、业务状态注入或用户 profile，也没有新增依赖或下载。

## dev Chrome 路由对照

基线 `/Users/luckye/Documents/Code/synara-t038-baseline` 为 `a9cc30c395af9ffd51476a1841d80bca66568993`，候选为上述冻结代码。分别顺序启动 full dev 服务，使用各自隔离 home 和同一端口配置。通过原生 RPC 以相同输入新建 R6 项目和一个空 thread；只是夹具元数据，不启动 turn。输入、RPC 收据、服务启动/就绪/停止记录都在本目录中。

相同步骤为根页面、UI 处理公告、悬停公共 thread、进入该 thread；候选另悬停并点击新增的任务窗口入口。Chrome 使用已有安装、独立 context、1600×1000 与 reduced-motion 偏好。命令均经 fork `a2a/scripts/bun run node chrome-route-probe.mjs <variant> <label>`。

| 运行 | 观察结果 |
| --- | --- |
| [基线](baseline-chrome.json) | 根页面和公共 thread 导航成功；没有 `_nonReactive`；有 `/api/editor-icon?id=cursor` 的 404。 |
| [候选](candidate-chrome.json) | 相同公共步骤成功，新增入口悬停和任务窗口打开成功；没有 `_nonReactive`；同一 editor-icon 404。 |

对应 [基线 thread 截图](baseline-chrome-thread.png)、[候选任务窗口截图](candidate-chrome-task.png)，[原始对照结论](route-comparison-conclusion.json)。本轮没有复现旧 Electron 的 `_nonReactive`，不能据此认定新增路由造成回归，也不能认定该错误属于上游；具体原因仍未知。只有 editor-icon 404 在未改基线也出现。没有因未复现而改代码、重新冻结或重做审查。

## Electron 直达任务窗口

在同候选、已有 Electron 43.4.1 与新的隔离 profile 中先到根页面，再通过正常页面导航直接进入 `http://localhost:7771/a2a`。实际命令与退出码见 [完整命令](../round6-desktop-command.json)，UI 操作、身份、源码版本与诊断见 [原始记录](desktop-direct-proof.json)。这是一轮中的唯一 Electron 会话，没有修改上游或注入状态。

根页面渲染后，直接导航阶段等待 `#root button` 可见 45 秒超时；尚未进入后续弹窗关闭动作（uiActions 为空）。日志有 WebSocket `Invalid frame header`，随后 ERR_CONNECTION_REFUSED，另外有 404。具体传输失败原因未确定，不扩大排查。保留 [根页面截图](desktop-direct-proof-root.png) 与 [有效失败截图](desktop-direct-proof-failure.png)，后者显示加载中的侧栏/启动画面，不满足两任务、worker/reviewer 和门禁状态的桌面图要求，不计 PASS。

结束前后 git HEAD 相同，tracked diff 为空。Electron 关闭等待超时后只终止本次启动 PID；三个本轮服务均按创建记录停止，[清理记录](cleanup.json) 核对 PID 已退出、5811/7771 无监听。基线 worktree 继续保留到主控关闭；R6 夹具目录保留在外置盘 `/Volumes/WD-Elements/dev-cache/synara/instances/t038/fixtures/round6-route-project`。源码、上游测试和原有失败证据未改。
