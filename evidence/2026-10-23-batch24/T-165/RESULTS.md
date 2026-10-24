# T-165-1 / a1 进度记录

状态：INCOMPLETE。检查点 PLAN；01 两次均因夹具观察错误超时，不能算红态；02 已准备待执行主控运行。产品实现未开始，没有宣称 RED 或 DELIVERED。

任务身份：worker `b24-t165`，task `T-165-1`，attempt `a1`，session `24606d10-cfde-4e53-8158-f544130fa48c`，launch `launch-c034197297074885aeb04bff28b7f8b7`。未取得 fence，不补造。规格为 T-165 ready_rev 1 与本目录任务卡。基线为当前 main `f2756ea2030d8ce0bddf9980d3f36d1825201d3a`；开始时 worktree 干净。

## 现场与目标

只读检查 `/private/tmp/t157-stop-input-63d2qaht/state/state.sqlite3`：seq 114 原 submit 通过；seq 116 等待原生排队输入；seq 120 新 prompt 的 Stop 到达，121 `stop_not_matched`；123～125 才登记该 prompt 的原生 turn。当前 `panes.ts` 未匹配分支返回后，没有保存该 Stop 供后来的转录登记消费。现场属于既有失败证据，不能代替本候选确定时序红态。

目标：转录核验完成后，先到的 Stop 仍能完成同一轮；无关 Stop 仍不匹配。非目标：renderer、门禁核对、自动重试或超时兜底。Tracer bullet 沿真实 CLI、hook、后台与窗格状态；Deep modules 在现有 Panes 处理原生 turn 的拥有层修复；Ubiquitous language 沿用原生 turn、attempt、submit。

## 确定时序探针

新增 `workbench/tests/test_t165_queued_stop_e2e.py`，复用 T-157 原有真实 Electron、daemon、PTY、Claude CLI 与全部断言，不修改 T-157 文件。仅在临时源码副本的 Claude scan 入口加读取屏障：收到 queued UPS 后暂不读取转录，观察到真实新 prompt 的 Stop 请求返回、确认该 turn 尚未登记及原生排队记录完整落盘，再开放读取并经 `pane_process_info` 显式触发一次真实采集，用 `pane_status` 观察。夹具不写 pane 或数据库，也不伪造原生 prompt。此探针控制转录的可见性，不能证明物理落盘先后；最终仍须不带屏障的 T-157 连续回归。供应商模型回合 0，本地脚本化 Messages。

运行命令：`zsh evidence/2026-10-23-batch24/T-165/RUN-OUTSIDE-01.sh`。两次计划内独立红态运行均固定 `--revision f2756ea2030d8ce0bddf9980d3f36d1825201d3a`，每次保存新目录、新 summary 与截图。只有原 submit 通过、新 Stop 明确先于 native-transcript 登记、`stop_not_matched` 且最终 busy、无运行错误时，才记 `red_reproduced=true`。底层 T-157 仍因空闲断言失败返回 INCOMPLETE；脚本总 PASS 只表示两次红态复现成立。

已运行静态检查：Python AST 与 `--help`、`zsh -n`、`git diff --check` 均通过。未在沙箱内启动 Electron 或本机服务，未申请这类提权；按任务卡交主控沙箱外执行。开始及准备脚本后的 project-map status 均为 Problems 0 / Stale living docs 0。

## 01 失败调查与 02 修正

主控 #77 回传 `/private/tmp/t165-outside-01.rkwCi3/RESULT.json`：两场均 INCOMPLETE、`red_reproduced=false`，错误为“超时：真实新 Stop 已返回，转录尚未登记”。01 的原始 summary、日志与 fixture 原样保留；没有把它们改成 PASS。

只读检查两个已停止 fixture 的 SQLite（immutable 方式，不打开 WAL/SHM 写权限），并与保存的 `final_timeline` 核对：`umpsk_4v` 与 `vzji5c0h` 都是 seq 110 queued UPS、114 原 submit 通过、116 等待原生排队、119 新 Stop 收到、120 turn_end_signal、121 stop_not_matched、122 signal 返回成功。此时无转录登记，最终 active=null、busy。屏障生效，但没有释放，尚缺原现场 123～125 那段后登记的证据。小文本摘录见 [DIAGNOSIS-01.json](DIAGNOSIS-01.json)。

夹具错误有两处：第一，观察器带 task 查询事件，但 request_received/request_result 的 task/launch 列为空，导致它看不到真实 Stop 请求的返回。第二，`pane_status` 是纯状态读取，不能保证释放屏障后会采集转录。02 只修夹具：查询全局事件，按 queued hook 的 launch、signal 输入的 launch 和 request id 严格关联成功回执；等待 CLI 完整排队记录后释放，再调用一次 `pane_process_info` 核对真实 leader 并采集。不改产品、不放宽 T-157 的空闲或交付断言。

运行命令：`zsh evidence/2026-10-23-batch24/T-165/RUN-OUTSIDE-02.sh`。仍在同一固定 main 基线执行两场，保存新目录与新摘要。01 的失败状态保持 INCOMPLETE，02 运行结果尚未取得。

已对 01 两份全局事件调用新的 `find_early_stop` 作只读回放：均找到 request seq 118、成功 result seq 122；把同一输入改为旧 task 过滤后均找不到，确认检查能拒绝已知坏观察方式。结果见 [OBSERVER-REPLAY-02.json](OBSERVER-REPLAY-02.json)，该 PASS 仅限夹具关联。02 脚本的 `zsh -n`、探针的 `--help` 与 `git diff --check` 通过；未把这些局部检查算成真实红态。

## 待完成

- 收到 02 的真实结果后核对两次确定红态，再实现最小修复。
- 同时覆盖无关 Stop；在坏实现上拒绝丢失早到 Stop 的行为。
- 同时序绿态、不带屏障的 T-157 多次运行、T-157 基线与坏实现、T-159/T-160/T-133 回归。
- 最终候选的独立只读审查与门禁验收由执行主控安排；当前无产品通过结论。
