# T-145-2 / a2 交付报告

状态：**INCOMPLETE**。已定位并修正测试等待条件；真实 Electron 绿态、修前版本、两个变异和回归待执行主控在沙箱外运行。未修改产品代码，未沿用 a1 的通过结论。

绑定：worker `b23-t145b`，task `T-145-2`，attempt `a2`，分支 `exec/t145-a2`，起点 `bf932d49940104ec099023aa957d06fe95116e92`；完整交付版本以本报告所在提交为准。任务卡来自主 checkout 的 `evidence/2026-10-23-batch23/T-145-a2/card.md`（本 worktree 初始没有该文件）。

## 根因与失败证据

执行主控提供的两次红态均停在“超时：鼠标模式输出已显示”，此前通过 `receiver_native_identity_bound`：

- `../merge-1/run-20261023T125644Z/t145-green.json`：夹具 `/private/tmp/t145-hpfq5kx2`。
- `../merge-1/run-20261023T125644Z/t145-green-rerun-alone-01.json`：夹具 `/private/tmp/t145-90d34e1n`。

已只读核对两份夹具：`receiver-home/mouse-ready` 都存在，尺寸均为 154 列、42 行；对应 `state/traces/<launch>/pty.raw` 都包含 `ESC[?1003;1006;1004hT145_MOUSE_READY\r\n`。这证明接收程序已输出鼠标模式和标记，不能单凭超时认定产品吞掉输出。原始文件未更改。

测试原先只在 `.xterm-accessibility-tree [role=listitem]` 中查找 `T145_MOUSE_READY`。a1 起点 `f8aa84625` 的 renderer 固定 `screenReaderMode: true`；合并后的 renderer 第 482 行默认 `screenReader=false`，T-139/T-143 自身的独立验收也明确检查 `screen_reader_default_off`。依赖 `@xterm/xterm` 6.0.0 的 `CoreBrowserTerminal.ts` 只在此选项开启时创建辅助树。因此，原等待条件依赖被 T-143 合法改变的读屏默认值，与 T-145 的协议转发/记录契约无关。

## 最小改动

只修改 `workbench/tests/test_t145_mouse_reports_e2e.py` 的两处等待条件及文件头失败方式说明：

1. 打开 worker 后，等指定 launch 的窗格可输入、可见且 `data-restoring=false`，避免将 T-139 保留在 DOM 中的隐藏窗格误认为已打开。
2. 仍等待相同的 `T145_MOUSE_READY`，但查询 `.xterm-rows > div` 的实际渲染行，并要求该行有布局且 `visibility=visible`。`@xterm/xterm` 的 `DomRenderer.ts` 第 451 行从终端缓冲区渲染这些行；此观察方式在读屏开关两种状态下都成立。

所有检查名、断言、期望字节与等待期限保持不变；没有启用读屏模式、添加输出副本、跳过检查或改动生产路径。`panes.ts`、侧栏、视图刷新及受保护的验收文件均未修改。

Tracer bullet 仍是原来的 Electron/CDP → 后台 → 受管 worker PTY/门禁 → 记录页。本次只修正该链路的显示观察方式。Deep modules 与 Ubiquitous language 均沿用已有接口和术语，没有增加生产抽象。

## 验证与复跑

沙箱内静态检查及交付前地图状态见本目录 `local-checks-01.txt`。这些结果只证明语法与范围，不证明真实界面通过。

执行主控在沙箱外运行：

```sh
zsh evidence/2026-10-23-batch23/T-145-a2/RUN-OUTSIDE-01.sh
```

脚本为每次运行建立 `outside01-XXXXXX`，逐项保留完整命令、stdout、stderr、退出码与摘要，运行：

- T-145 当前候选：应完整通过。
- T-145 `--revision f8aa84625`：应在 `mouse_focus_do_not_create_records` 失败，而非显示等待失败。
- `--mutant record-reports`：应在同一记录断言失败。
- `--mutant drop-reports`：应在“三次移动均到 PTY”失败。
- T-139/T-143 当前候选：视图、只读输入边界和读屏默认设置回归。
- T-133/T-134：记录页与指标回归。

这些真实运行目前均为 **INCOMPLETE / 未运行**。两份原始合并失败摘要是本次修复前证据；脚本中的历史红态与变异用于确认观察器更改没有削弱 T-145 的业务验收。原始运行夹具由执行主控按 T-088 归档。独立 behavioral-acceptance-review 由执行主控另开干净只读会话完成，本报告不构成独立审查。
