# T-138-1 / a1：输入法中间插入修复候选

状态：**INCOMPLETE**。真实 Electron 红态已确认；生产修复、变异测试和沙箱外复跑脚本已准备。候选绿态、变异和两组 Electron 回归仍待主控运行，不能据静态检查宣称修复通过。

## 身份与范围

- worker：b23-t138；task：T-138-1；attempt：a1；分支：exec/t138；任务卡 ready_rev 1。
- 起点：`b99f4869bbe087946017716a5a8479c0cb47e6c8`。
- 生产变更仅在 `workbench/app/renderer.tsx` 的终端输入/composition 部分；其余变更为本次新增的 e2e 和本 ticket 证据。未改 xterm、后台、既有验收文件、地图或 ticket；读屏模式继续保留。

## 红态与原因

主控在沙箱外运行 `RUN-OUTSIDE-01.sh`，回传 `outside-01-20261023-131559-9292/red.json`。真实 Electron → renderer → 编排后台 → node-pty；PTY 运行 raw 字节接收器，不调用模型。输入只经 CDP 注入，DOM 用于导航、聚焦和观察，没有修改 textarea.value 或调用 a2a.input 注入测试内容。

- 读屏关闭：三次中间插入及回车后中间插入均收到“打出”。隐藏输入框的选区始终在末尾。
- 读屏开启：输入“前面怪了”并左移两次后，隐藏输入框选区为 `start=end=2`。四次“打出”均错误收到“怪了”：预期 `e68993e587ba`，实际 `e680aae4ba86`。
- 因为 xterm CompositionHelper 以 textarea 长度记提交起点，读屏模式允许方向键移动 textarea 选区后，它从旧长度处取到了末尾两字。主控已明确要求两种模式都正确，不能关闭读屏模式规避。
- 初版测试的额外可信性检查失败：compositionstart/update/input 的 isTrusted=true，但 compositionend=false。原始结果和标志保留，未重写成通过。新版要求可信开始/更新/输入及实际结束事件，完整记录结束事件的原始 isTrusted；不补发结束事件、不修改其可信标志。曾向主控询问是否有额外手工事件注入，尚未收到答复；当前按回传命令和仓库驱动没有额外注入处理。若确有手工注入，须先还原实际过程再解释复跑结果。

沙箱内首次运行 `sandbox-red-01.json` 为环境失败：Electron CDP `ECONNREFUSED`，没有输入场景，不能当红态。现场 `/private/tmp/t138-4bsq6y0a` 保留，未提交或归档。

## 修复

xterm 发出 onData 后，下一事件轮次清空隐藏输入框，让下一次 composition 的起点和选区回到 0。延后清空是为了让 xterm 先读出提交内容，并等浏览器完成原生 textarea 更新。composition 进行中不清空；开始新 composition 时取消尚未执行的清空。窗格卸载时取消定时器并移除新增监听器。

保持原有 admitInput、IPC 和 PTY 路径，没有从 compositionend.data 另建发送路径，也没有改 xterm 的取词算法。

## 验证

- PASS：隔离生产构建，命令和结果见 `build-02.json`；临时构建目录已清理。
- PASS：Python 语法、RUN-OUTSIDE 脚本 zsh 语法、git diff 空白检查。
- PASS（仅比较相同失败）：`t091-comparison-03.json`；加 `--experimental-vm-modules` 的基线/候选都在同一 IPC 名单断言失败，错误、检查和三组旧反例结果相同。不能称作 t091 通过。
- 保留失败现场：`t091-*-02.json/log` 是遗漏 VM 参数导致的配置失败；`t091-*-03.json/log` 才是有效比较。
- 尚未运行：候选真实 Electron 绿态、`--mutant retain-input`、新版脚本在起点上的红态复跑、T-139/T-143 联合 e2e、T-145 e2e。
- 地图检查 INCOMPLETE：`project-map-status-02.txt` 报 `workbench/README.md` stale（renderer 的 covered 变更）。README 和地图在 worker 写入范围外，已向 triage 上报 `20261023T172307Z-worker:b23-t138-issue-001`，请主控集成时核对并处理，worker 未越界修改。

## 沙箱外复跑

```sh
zsh evidence/2026-10-23-batch23/T-138/RUN-OUTSIDE-02.sh
```

每次建立新目录，不覆盖证据；依次运行起点红态、提交版本绿态、移除清空动作的变异、T-139/T-143、T-145、t091 基线/候选。汇总到 `run-summary.json`，只有全部条件满足才报 PASS。变异/红态要求确实抓到读屏模式把“打出”变成“怪了”，不接受启动或配置失败作为有效反例。

新版 e2e 两种模式各覆盖连续三次中间插入、回车后插入，以及普通英文键入后插入随机新词；检查读屏可访问性容器实际建立/移除，防止模式切换失效却通过。每个提交记录输入框内容和选区、事件、预期/实际 UTF-8 字节。

截图留在证据目录，不提交；临时夹具保留，归档由主控处理。真实 macOS 输入法/读屏软件交互未实测；CDP 输入验证不能代替该结论。完整交付后的独立审查和验收由执行主控安排。
