# T-145-1 / a1 交付报告

总体状态：**INCOMPLETE**。执行主控已运行 RUN-OUTSIDE-01：真实 Electron 红态按预期失败，候选的鼠标、焦点和设备回复检查通过，随后卡在键入注入。根因为测试使用了 xterm 在 screenReaderMode 下忽略的 `Input.insertText`，此次未观察到生产过滤吞字。已修正测试驱动，真实 Electron 完整绿态、变异及 T-133/T-134 回归仍待 RUN-OUTSIDE-02 复验。未宣称已验收。

绑定：worker `b23-t145`，task `T-145-1`，attempt `a1`，分支 `exec/t145`，任务卡 ready_rev 1，起点 `f8aa846252ddd97008a5e506469ce30024aaacab`。完整候选版本以本报告所在交付提交为准，提交尾注由现有钩子生成；不把派发时的模型、强度或服务档位当作供应商实际运行证明。

## 改动

根因位于 `Panes.userInput`：所有窗格输入包都会调用用户输入记录器，并占用草稿。xterm 的鼠标上报也经过同一个入口，因而被门禁派生为人工介入。

生产改动仅限 `workbench/src/panes.ts` 的输入转发部分。完整的 SGR / X10 鼠标、焦点与设备回复等协议包跳过用户输入记录与草稿代次变更；仍经同一身份检查、串行写入队列和 PTY 写入，保留原字节。真实文字、中文、方向键、Esc、回车、修改键 F3 和带协议文字的 bracketed paste 保留原路径。

没有修改 renderer、daemon、门禁验收逻辑、记录读取或记录页，也没有删除或重分类历史记录。这里按终端协议格式识别完整包，不判断文字含义。未识别的包、混合普通文字的包、拆成多次调用的半个序列仍走既有记录路径；当前 xterm 的鼠标和设备上报按完整序列发出。

这是一处输入通道修复，未增加跨层抽象；保留同一生产入口，符合 Deep modules 的小接口原则。验收沿用 Ubiquitous language 中的“用户输入记录”和“人工介入”。真实 Electron → 后台 → 门禁 / PTY → 记录页是本次 Tracer bullet 的待运行验证路径。

## 已取得的证据

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| 修复前红态 | PASS（证明缺陷） | `protocol-red-01.json`：修复前发送 `ESC [ <35;9;3M`，记录回调被调用，断言失败。不是环境错误。 |
| 修复后方法检查 | PASS | `run-htufoE/protocol-green.json`：完整上报不记录、不占草稿；字节原样送 PTY；真实键入保留；过期身份拒绝；共享写入顺序保留。 |
| 起点反事实 | PASS（拒绝已知坏版本） | `run-htufoE/protocol-red.json`：通过 `git show` 提取起点生产源码，同一断言失败。 |
| 继续记录上报的变异 | PASS（拒绝变异） | `run-htufoE/protocol-mutant-record-reports.json`：失败原因是上报被记为输入。 |
| 吞掉上报的变异 | PASS（拒绝变异） | `run-htufoE/protocol-mutant-drop-reports.json`：失败原因是 CLI 的原字节缺失。 |
| T-091 回归对照 | PASS（符合“不更差”条件；测试本身仍失败） | `run-htufoE/t091-baseline.json` 与 `t091-candidate.json`：均以同一 IPC handler 名称契约断言退出 1，错误与 checks 一致。使用 `--experimental-vm-modules`。 |
| 新脚本静态检查 | PASS | Python 编译、Node 语法检查、zsh 语法检查、C 夹具以 `clang -Wall -Wextra -Werror -std=c11` 编译成功。 |
| 沙箱外起点红态 | PASS（证明缺陷） | `run-JzoEtp/electron-red.json`：真实鼠标移动造成新增用户输入，失败在 `mouse_focus_do_not_create_records`。 |
| 沙箱外候选鼠标 / 焦点 / 设备回复 | PASS（仅这些断言） | `run-JzoEtp/electron-green.json` 的前八项通过，包含原字节对照、记录和门禁事件数不变。 |
| 沙箱外完整候选 | INCOMPLETE | 同一摘要在真实键入到 PTY 处超时；输入驱动修正待新运行。Electron 变异和 T-133/T-134 因前项失败而未运行。 |

可重现上述方法级红 / 绿 / 变异及 T-091 对照：

```sh
evidence/2026-10-23-batch23/T-145/RUN-OUTSIDE-01.sh --bounded
```

`run-htufoE/MANIFEST.json` 保存逐条命令、退出码、摘要路径、起点和当时未提交的生产 diff。初次 `run-e7JqMf` 漏传 T-091 所需的 VM 参数，所得环境失败保留为探索记录，不能用来证明 T-091 业务回归；有效对照以 `run-htufoE` 为准。初次 RUN-OUTSIDE 脚本根目录多取一层导致 mktemp 失败，已修正为四级父目录，未覆盖旧证据。

## RUN-OUTSIDE-01 的键入失败诊断

失败夹具保留在 `/private/tmp/t145-v3ud74xx`。只读核对 SQLite 与 `receiver-home/received.bin` 后，窗格写入记录只有六个鼠标包和四个焦点 / 设备回复；输入表只有独立种入的历史记录，没有真实文字，也没有对应的 PTY 写入意图。接收文件末尾与这些上报一致。诊断摘要见 `typing-driver-diagnosis-01.json`。

`workbench/app/renderer.tsx` 启用了 `screenReaderMode: true`。依赖 `@xterm/xterm` 6.0.0 的 `CoreBrowserTerminal.ts` 第 1196 行仅在该模式关闭时转发 `input(insertText)`；第 1175 行的原生 keypress 路径则转发字符。旧测试使用 CDP `Input.insertText`，没有产生 keypress，因而没有进入后台。该证据支持测试注入失败；不能把它当作“生产过滤收到文字后吞掉”的证据。

现在测试使用 CDP `Input.dispatchKeyEvent` 的 `char` 事件，输入一个随机大写字母，严格对应“真正打字一次、新增一条”。测试先断言 xterm textarea 收到了可信 keypress 和正确 charCode，再核对 PTY 精确收到一次字符、输入表与人工介入各增加一条。新增浏览器事件、字符、接收字节和键入后输入记录诊断；等待期限仍为 10 秒。生产 `Panes.userInput` 没有再修改。

另修正了同一测试夹具的会话文件布局：旧 C 接收程序把元数据放在 `sessions/` 根目录，后台只扫描 `sessions/YYYY/MM/DD`，导致清理时出现 `native_bound_log_unavailable`。这是夹具身份绑定缺口，发生在键入超时后的清理阶段，与键入根因分开。文件现在放入本地日期目录，e2e 额外核对真实前台 PID、原生会话和 failed 状态；没有修改生产扫描器。C 编译通过。一次沙箱内直接 openpty 的接收器探针未观察到启动输出，结果保留为 `receiver-smoke-02.json`（INCOMPLETE），不能当成运行通过；完整运行仍交给沙箱外。

## 沙箱外复验

执行主控运行：

```sh
evidence/2026-10-23-batch23/T-145/RUN-OUTSIDE-02.sh
```

02 脚本每次建立新的 `run02-XXXXXX` 目录，保留 stdout、stderr、JSON 摘要和命令清单，不覆盖 01 或已有输出。大块临时源码、运行夹具与原始接收字节留在 `/private/tmp`，由执行主控按 T-088 归档；构建槽由既有 Electron 夹具在关闭时清理。

真实 e2e 为 `workbench/tests/test_t145_mouse_reports_e2e.py`，使用本任务新建的原生 C 接收程序 `t145_mouse_receiver.c`，**不是真实 Claude 或 Codex，不运行模型**。使用真实后台、受管 worker 门禁身份、node-pty、Electron 和 CDP。程序在隔离 CODEX_HOME 中生成最小会话元数据，走现有的 Open restricted 启动流程；不改全局配置、不改生产就绪判断。任务卡明确允许这类开启鼠标 / 焦点模式的夹具程序。

待运行的检查包括：

- CDP 只移动、滚动和切焦点，用户输入记录与 `human_intervention` 事件数不增加；根据窗口尺寸和 CDP 坐标独立计算三次移动的原字节，并与接收文件逐字节比较。
- 当前 renderer 仍沿用既有 1004 焦点上报拦截；另经真实窗口凭据入口发送焦点 / 设备回复，核对原字节到达 CLI 且不记录。
- CDP 一次原生按键输入随机大写字母，恰好新增一条输入和一个人工介入事件；记录页显示该输入并保留独立种入的历史误记录。
- `--revision f8aa846252ddd97008a5e506469ce30024aaacab` 必须因鼠标新增记录而失败；`--mutant record-reports` 必须同因失败；`--mutant drop-reports` 必须因接收端缺字节而失败。其他设置错误不能当成红态。
- `test_t133_t134_records_metrics_e2e.py` 必须通过，仍用既有脚本化接口和真实 Claude Code `claude-haiku-5-5`；T-091 同时重跑起点与候选，要求失败与起点一致。

02 版测试的上述真实界面与回归为 **INCOMPLETE / 未运行**，没有沿用 01 的部分通过结论替新测试背书，也没有用方法检查代替。独立 behavioral-acceptance-review 由执行主控另开干净只读会话完成；本报告不是独立审查。

## 范围外事项

`project_map.py status` 检出 `workbench/README.md` 因覆盖的生产文件变化而 stale。任务卡未授权 worker 修改 README 或地图，已用 `scripts/inbox send` 非阻塞上报：`20261023T122904Z-worker:b23-t145-issue-001`，正文见 `README-SYNC-ISSUE.md`。执行主控集成时须同步文档并复验；worker 未擅改禁区。
