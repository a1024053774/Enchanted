# T-104 / a1 独立审查 01 修复

状态：**INCOMPLETE**。旧候选 `d54826223194b56ca057b8ab3213729c9e53a29a` 的独立审查为 NO_GO；两项修复与验收加强已写，修复后的真实重跑、提交和独立复审未完成。旧 ui-01 的 PASS 不证明本次修复。

## 合同与红态

主控 #24 更正审查任务书：“只有创建和关闭事件”超出了 ticket 原文。此次按主控的明确裁定，普通 shell 的逐次输入、composition、observation 不记接收事件或通用请求日志，避免次数与时间泄露；凭据、序号、防重放检查保留在内存。布局、窗口创建／关闭与进程诊断继续保留，agent 的用户输入、人工介入和门禁事实不削弱。没有擅自把所有其他事件都删除。

按 evidence-first-testing，改产品前先用 `PROBE-REVIEW-RED.py` 只读真实归档：`review-red-24.json` 记录 R1 有 4 条 shell 的 window_request_admitted；R2 审查变异在第一次 daemon_stopped 后实际创建了两个新 shell（seq 82、84），但旧后台验收仍退出 0。探针退出 1，两个反例都被要求导出的断言拒绝；不是环境失败。原始审查报告和 review-outside-01 现场均保留。

**Tracer bullet**：真实窗口输入 → 后台身份与序号检查 → 内存分流 → PTY，再经完整后台与真实 Electron 重跑核对。**Deep modules**：修在 daemon 的事件采集层；复用已有窗口创建事件核对历史身份，不增加存储表、权限 API、门禁或输入记录器。**Ubiquitous language**：角色 shell、launch、窗口凭据、逐次输入事件与布局／进程诊断分开表述。

## 产品修复

`daemon.ts` 只对已绑定 shell 窗口的逐次请求停止持久化。当前窗口的角色保存在服务端内存；对已关闭或后台重启前的窗口，从既有 window_opened 与不可变 launch 记录核对角色，覆盖错误凭据、过期窗口的拒绝路径。角色不接受调用者自报。

序号、request_id 消费、重复请求检查和所有凭据验证原样保留；shell 的 window_release 本就不支持，也不记录这种逐次请求元数据。window_opened、window_closed、pane_layout_*、pane_stop_intent、shell_created／closed／exit_confirmed 等继续记录。agent 分支仍追加 window_request_admitted 及原通用日志；其 recordInput、appendUserInput、panes.userInput 和人工介入／门禁路径未改。新增的历史窗口查询只读既有数据，不改变认证结果。

## 验收加强

- 后台场景增加 composition 成功、重复序号拒绝、重复 request_id 拒绝。逐次请求的 envelope ID 由测试发送端保存，既检查 shell launch 没有逐次事件，也检查成功、错误编码、错误凭据、关闭和重启后的请求没有通用日志。允许的生命周期与诊断不被一刀切禁掉。
- 重启前明确要求只有两次主动创建得到的 shell launch／shell_created；重启后比较全体记录与创建事件，必须完全相同，并核对完整项目打开集。检查不再只取打开集首项或只观察旧 launch。
- 真实 UI 旅程同样比较全部 shell 清单、全部创建事件与重开后全部 shell 窗格；该夹具没有向 agent 输入，因此也拒绝其事件流中的所有逐次输入通用日志。保留原 nonce、进程、只读 agent、跨项目、旧 key 与退出检查。
- 后台套件包括 6 场真实入口对照及 4 项原回归：缺功能的 cc18、R1 已知坏候选 d548、好候选、正文日志变异、逐次输入事件变异、自动重启变异。后两个变异必须在相应业务断言失败且清理完成；套件还独立读归档库，确认坏事件或新 shell 确实发生。环境错误或未生效变异不能算通过。
- 自动重启变异逐字沿用审查补充的 `this.startShell(record.project, record.worktree)`；逐次事件变异只去掉 shell 的接收事件写入守卫。正文变异在分流处恢复原载荷日志。测试输入和预期来自 ticket 与主控裁定，不从产品常量生成。

## 重跑与提交命令

主控在沙箱外运行，使用新编号保留旧结果：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-08-REVIEW-FIX.sh review-fix-01
```

08 调用加强后的后台套件，再执行基线／候选的两处合同与完整真实 Electron 红／绿旅程，最后显式要求两个变异都生效并被拒。继续共用保留的 T-103 内置盘 Electron 43.4.1，红／绿同一二进制；构建输出、缓存、原始日志、截图与夹具写外置盘，缺盘停止。没有模型调用。

核对重跑原件和截图后，主控按已授权 Herdr 交付方式提交：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-09-COMMIT-REVIEW-FIX.sh review-fix-01
```

09 要求新复核摘要与 UI 均 PASS、两个变异有实际效果、源码和测试与通过快照逐字节相同；只暂存本票列明路径，`git add --sparse`，由原 hook 加真实 worker 尾注，不 push。当前仍在 d548，修复提交号尚未知，不预先记为已提交。

## 证据限制

本次实现会话不是独立 reviewer。真实重跑尚未运行，不把源码分流或语法检查当成修复 PASS。完整 checkout 地图检查和真实可输入 worker 的 user_input → human_intervention 复验仍不在已有证据中；只读历史 worker 不能证明后者。agent 路径的静态保持与原回归结果要分别报告。当前稀疏 worktree 的 8 个缺失项也不能记成 0。

## 主控 #26：review-fix-01 的归档查询失败

此次完整命令退出 1，不能记作整套通过。已完成的缺功能红态、metadata-known-bad、好候选和正文变异符合预期；input-events-mutant 也在 privacy 阶段以“shell 逐次输入事件进入事件流”退出 1，且 cleanup_complete 为 true。随后 RUN-SUITE 对它的归档库作独立效果核对时失败，自动重启变异与真实 UI 尚未开始。review-fix-01 原件保留，不补写为通过。

`archive-read-red-26.json` 使用 RUN-SUITE 中实际的查询块复现错误：文件存在、204,800 字节，主库头的读写版本均为 2（WAL），旁边无 -wal／-shm。不是库路径错误或被清理。普通 mode=ro 连接在该环境中仍需 WAL 协调文件，因此执行 SELECT 时失败；[SQLite 官方说明](https://www.sqlite.org/wal.html#read_only_databases)允许已知不可变的 WAL 库使用 immutable 方式只读打开。

仅修 RUN-SUITE 的归档读取：要求清理完成、归档路径正好属于该 case、主库存在且没有非空 WAL／journal，再用 mode=ro&immutable=1；不将它用于运行中的库，不加重试，不更改文件权限或原件。相同查询块在 `archive-read-green-26.json` 退出 0，独立读出 8 条变异写回的逐次事件。产品和测试断言未因本次脚本故障修改。

使用新编号完整重跑：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-08-REVIEW-FIX.sh review-fix-02
```

通过并核对原件后，提交脚本的参数相应改为 `review-fix-02`。本次仍为 INCOMPLETE，不能以查询探针通过代替剩余后台反例和真实 UI。
