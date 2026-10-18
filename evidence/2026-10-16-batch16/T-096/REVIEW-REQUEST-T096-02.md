# T-096-02 独立审查请求

状态：**候选重新冻结，审查待派发；整票 INCOMPLETE**。主控 #112／#17 要求另开 reviewer，本 worker 不代审、不启动子会话。本文件不是独立审查结论。

仓库 `/Users/luckye/Documents/Code/a2a-wt-t096`，task T-096、attempt a1、writer s16-t096。由执行主控另开干净、只读的 gpt-6.1-sol／xhigh reviewer；不复用实现会话，不 claim／submit／集成或改文件。唯一候选以主控传入的 `T-096 FROZEN <完整 SHA>` 为准，并与本文件首次提交核对：

```sh
git log -1 --format=%H -- evidence/2026-10-16-batch16/T-096/REVIEW-REQUEST-T096-02.md
```

比较起点仍为 `3c9016d02`。第一轮冻结候选 `11b32303bebf276d20026a6e718719d15f5d4068` 经独立审查 01 为 NO_GO；修复与新实跑的产品版本为 `d61876fe29916ccf577da7b9b912cf305d9fdd9d`。本次重新冻结在 d61876fe2 上只加入新实跑摘要、归档清单、worker 只读核对和文档，workbench/src／app／tests 与该实跑版本应无差异；请自行核对。候选在审查期间变化则返回 INCOMPLETE，不追逐新版本。

先从最新 main 的 T-096 ticket（含用户裁定 B）、任务卡 T-096-1 和当前用户任务重建完成条件，再检查候选及证据。主控窗格按原启动参数续接；worker 保留“未恢复”，不启动、不重绑定、不改 attempt；恢复不产生模型回合。不改 gates／Herdr／全局配置，不用裸 resume 或默认参数补位。RESULTS 是实现者的证据索引和适用性说明，不是审查 oracle。

使用 behavioral-acceptance-review 核对行为与反事实，涉及结构边界时核对 design-integrity-review 的关注项。重点如下：

1. **审查 01 的空集缺陷。** 只有从未保存布局才默认选择当前窗格；明确关闭最后一格后，后端保存空集，退出／重开仍无 pane key／DOM／新 worker 凭据。检查 store 的任务范围、daemon.saved、main 默认选择和 preload 空数组，以及现有 renderer 空状态；不要把“总是返回空”当修复。
2. **四个产品文件的最小修复。** `git diff 11b32303b d61876fe2 -- workbench/src workbench/app` 应仅列 store.ts、daemon.ts、main.ts、preload.ts。确认原恢复／配置、门禁、worker attempt 与关闭写入路径没有隐藏变更；新增 saved 只是同一事件流的事实，不是另一份布局状态。显式指定 launch 与首次未保存仍能打开。
3. **新实跑的真实边界。** `empty-reopen-b-01.run.json` 报告 d61876fe2、31 项 PASS、模型／POST 0、cleanup true；主控报告 rc 0、两主控逐屏批准。独立读取外置盘原件：两主控实际续接 argv／历史 nonce、gate-before／after 完整 task、worker 只读未恢复，以及清空后第三个 Electron 的空 DOM、pane_keys、保存集与事件。不要只信摘要绿色或 worker readback。
4. **旧七场证据的适用性。** RESULTS 最新表逐个说明 red、tracer、three、缺 argv、版本不符、缺 session、失败隔离。旧状态仍绑定原 revision。新的三格正例与空集路径已重跑；三个拒绝和“一个主控失败”没有在新产品版重新注入。请以实际调用链和原件独立判断未改行为的证据能否复用、是否还需补跑；不要把代码无差异直接当整票通过，也不要把新正例当作故障复跑。
5. **局部反事实。** `empty-layout-red-02.json` 和 `empty-layout-green-02.json` 是实际 main/preload、替代 Electron／transport 的红绿；同一断言拒绝 11b32303b。`spawn-argv-green-02.json` 直接核对交给 PTY 的完整命令并拒绝“事件正确、实际参数丢失”的 M1。可检查已有 T-091 key／发送者／序列号回归与 worker 不启动／attempt 不变断言；新增测试不自成独立 oracle。
6. **进程与证据边界。** 检查新 runner 的第三个串行 Electron、退出未确认时不重复请求／不停止后台／不归档，以及无模型输入。原 process-tree／version 清理证据及限制仍保留；新正常退出不补称重现旧 version-b-01 的瞬态竞态。旧失败及私密排除范围不能被新清理抹掉。

原始证据根目录 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/`。仓库只交文本摘要和归档清单，不复制整个 fixture／sqlite／日志进 Git。

| 范围 | 仓库入口 | 原件重点 |
| --- | --- | --- |
| 本轮新实跑 | `empty-reopen-b-01.run.json`、`empty-reopen-b-01.archive.json` | empty-reopen-b-01/ 下的 before／after-view、两份 resumed-argv／resumed-view、synthetic-history、gate-before／after、fake-api-requests、startup-screens 与逐屏批准回执 |
| 关闭全部后重开 | 同一新实跑；`empty-reopen-b-01.readback.json` 仅供定位 | empty-layout-before-reopen、empty-layout-after-reopen、empty-reopened-view、window-2／3 阶段／正常退出回执；SQLite 关闭集与 cutoff 后无新增打开／授权／恢复事件 |
| 第一轮审查与反例 | `independent-review-01.md`、`REVIEW-OUTSIDE-01.sh`，原文未改 | 01 仅审 11b32303b；其脚本固定旧 SHA，预期 NO_GO／退出 1，不用于给新候选判绿 |
| 旧七场原件 | red-b-05、tracer-b-05、three-b-01、no-argv-b-02、version-b-02、no-session-b-01、isolation-b-01 的 run／archive | 实际 argv、历史 nonce、拒绝事件、只读未恢复、完整 task／attempt、无成功事件；范围见 RESULTS 逐场表 |
| 本轮局部合同 | empty-layout-red-02／green-02、spawn-argv-green-02、empty-layout-transport-01、empty-reopen-cleanup-03、empty-reopen-startup-01 | 区分真实 SQLite 与替代 IO／GUI；核对已知坏版本或变异确实被业务断言拒绝 |
| 旧进程与故障清理 | process-tree-red-02／green-01、cleanup-version-b-01、version-cleanup-contract-03 及对应清单 | 自然退出不发信号、身份变化拒绝、退出回执、私密排除与旧未知保留；不是所有竞态已验证 |

本轮归档清单记录 1,237 文件／568,773,593 字节、comparison=true；这是主控 runner 的比较结果，worker 只核对了清单与部分原件。请按需要独立核对。原始 SQLite 若需查询，先连 WAL／SHM 复制到新临时目录或使用确认不会写原件的方式，不打开原件的可写连接。

审查只做只读源码／证据核对及沙箱内纯合同检查；不要自行启动 Electron、daemon、PTY、供应商 CLI，或在沙箱外执行 ps／截图，不申请升级。缺原件或真实边界时返回精确 INCOMPLETE 与待主控运行的命令，不能猜成 PASS。返回 PASS／FAIL／INCOMPLETE，绑定唯一完整 SHA，给出发现、业务反例、文件行号和限制；由主控协调后续，reviewer 不修改本 attempt。
