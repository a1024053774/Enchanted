# T-105 / a1 交付

状态：**INCOMPLETE**。候选已实现；真实 Electron 红绿与独立审查尚未取得当前版本的结果。起点为 `37c8a9e77c7c0a0e7426accbec077f0e33946bf4`，交付候选已暂存，但提交被沙箱拒绝（共享Git元数据的`index.lock: Operation not permitted`）；须主控运行下述提交脚本。提交后以`exec/t105`包含本报告的版本为准。无模型调用、无 push、无全局 CLI 配置修改。

## 实现与验收

| 条件 | 当前证据 |
| --- | --- |
| 空库新建终端，默认家目录，可选目录 | 实际 main IPC 合同红→绿；真实 Electron 待运行 |
| 右/下分屏、放大/还原、改名、关闭、中文菜单及键盘操作 | 已实现；真实 Electron 交互与几何断言待运行 |
| 布局与名字重开恢复，普通终端不重跑 | main IPC 的右分屏/改名/重开合同通过；真实后台/应用重启待运行 |
| 右键转发 | 使用真实鼠标事件与 xterm 协议；PTY 接收程序的开/关反例待运行 |
| 普通终端输入不进 agent 记录，也不记逐次输入元数据；关闭结束子进程 | 原路径保留；真实 PTY 隐私与进程断言待运行 |
| 受管窗格菜单、worker 关闭与人工介入语义 | 主控/worker 原关闭入口与输入路径保留；reviewer只读菜单合同通过；真实活跃worker的人工介入未复验 |
| 门禁、操作锁 | 门禁核心未改；`gates/cli.ts` 只把普通终端的项目参数改为可选；IPC原有拒绝检查保留 |
| project-map | 本稀疏 checkout 有起始即存在的8项缺文件错误，stale living docs为0；未改地图/其他ticket |

Tracer bullet：先完成空库→家目录终端→右分屏→重开，再扩展其余操作。Deep modules：进程仍归Panes管理，布局仍在既有事件流中投影。Ubiquitous language：沿用窗格、普通终端、人工介入等现有术语。

关界面仍只断开视图：重开时连接后台中仍在运行的原终端；后台也重启时，旧普通终端显示“已结束”，不拉起新zsh。agent沿用T-096。受管agent关闭仍经`pane_layout_close`移除视图，不杀进程或回收attempt。

## 已运行

- `node --experimental-vm-modules workbench/tests/test_t105_panes.mjs`：PASS。实现前同一入口报“请先选择任务”，见`red-ipc.txt`；绿态见`green-ipc-final-01.txt`。这是main IPC证据，不是GUI证据。
- `node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /tmp/t105-ipc-final-01.json`：PASS。14个显式handler、15个桥接名称，跨窗口pane key、iframe、未知sender、历史worker、独立序号/凭据、关闭/恢复反例保持；已知坏版本和既有变异仍被拒。见`ipc-contract-final-01.json`。
- reviewer首次并存检查拒绝“Pane is not a current running session”，保留`reviewer-red-01.json`；随后只读reviewer并存/改名通过上面的当前合同检查。
- 临时源码与依赖副本中运行`node tests/test_pane_dispatch_state.ts /private/tmp/t105-dispatch-results-01`：PASS（无真实PTY/模型，已有状态回归）。见`dispatch-regression-01.json`。首次调用误用了仓库cwd，报`MODULE_NOT_FOUND .../tests/test_pane_dispatch_state.ts`；改在副本根目录运行后通过，不把该设置错误当作红态。
- 同一临时副本运行`node app/build.mjs --slot t105-check-final-01`：PASS。Node 26.5.0；依赖复制自本机现有workbench/node_modules；没有修改原依赖。Vite仍提示renderer chunk大于500kB。本轮未打包`.app`。
- Python脚本编译、driver的`node --check`、shell脚本语法、`git diff --check`：PASS。

## 主控运行

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t105
bash evidence/2026-10-19-batch17/T-105/RUN-OUTSIDE-02-COMMIT.sh
bash evidence/2026-10-19-batch17/T-105/RUN-OUTSIDE-01-ELECTRON.sh 01
```

两条命令须在沙箱外运行，worker不申请升级。提交脚本核对分支/起点/暂存范围，使用保存的本worker非秘密身份字段，仍让现有钩子生成尾注；不手写尾注、不更改全局Git配置。Electron脚本的说明如下。脚本在`/private/tmp`复制当前候选及固定基线、`npm ci --ignore-scripts`，只在测试副本修正spawn-helper执行位。默认使用主checkout的内置盘Electron 43.4.1；可用`T105_ELECTRON_DIST`指向另一份同版本内置盘dist。不会安装应用、调用模型、碰用户的HOME或运行中的Herdr。

脚本覆盖普通终端的真实Electron红绿、分屏几何、菜单键盘、放大/还原、中文名字、缩窗、SGR右键字节、关闭进程、界面与后台分别重开、隐私断言；另用明确标注的历史agent夹具验证恢复失败只读及关闭worker不改变task/attempt。历史夹具不是活跃真实agent证据。摘要写入`electron-01.json`，已有编号不覆盖，不保存截图或大现场。进程退出确认后清理临时构建与夹具；退出不明时保留位置并报INCOMPLETE。

本worker没有进行独立审查。[behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md)要求“Review one frozen candidate snapshot in a fresh, read-only context.”，应由执行主控另开干净只读会话；本报告的自检不替代该证据。
