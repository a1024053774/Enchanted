# T-110 重连后的作答回执

INCOMPLETE。本轮起点 `4a6d6bb9ecefc2bb16196b326ff032726d4d16fb`。已定位并修复产品的窗口命令序号缺口；本地修前红态、修后合同、IPC、T-108 和构建通过。当前候选的完整原生闭环、e1c7b5c27 同场景对照及独立复审仍待主控运行。

## 判断依据

第六轮原件 `/private/tmp/t110-outside-06.json` 的 green 已通过同一问题恢复及去重，随后报 `First window_answer final receipt timed out`；renderer_console 为空。daemon 已确认退出后，仅复制该夹具的 DB／WAL，再把副本整理为可独立读取的数据库，未写入原库。精简证据在 `outside-06-summary.json`。

- 原库事件中没有 `window_answer` 请求，所以这不是旧 receipt 监听漏读。驱动每次作答都会重新打开同一 state 下的数据库，在点击前读取当前最大 seq，再寻找首条答复的最终回执；这套监听没有更改。
- 最后一次接纳的窗口命令为 seq 14；恢复后的首条 resize 是 seq 17，被拒为 `invalid_window_sequence`。随后 resize／focus observation 连续被同一检查拒绝，共 10 条。序号 15、16 没有到达 daemon。
- main 原来在调用 transport 前增加 pane.sequence。连接缺失时，命令没有发送，但序号已经消耗；renderer 后续的 resize／observation 失败触发 failInput，输入锁住。问题仍能显示，不代表它能作答。
- `git diff e1c7b5c275eaca7e342da44cb2582cf81f56ca17 4a6d6bb9ecefc2bb16196b326ff032726d4d16fb -- workbench/app/main.ts workbench/src/transport.ts` 输出为空。这段序号缺陷在两版共有，不能归因为 4a6d6bb9e 修改了答复的 launch／attempt 绑定；两版在同一真实场景下是否均失败，仍由下面的对照实跑确认。原 T-108 常规闭环通过不覆盖断连命令未发送的情况。

## 最小修复与验证

main 不提前增加序号，而把分配回调传给现有 request；transport 在 socket 的 connect 回调内、序列化发送前调用一次。连接前失败不占序号；已发送但结果未知、或 daemon 返回业务拒绝时仍占序号。没有回退序号、重发命令、自动重连、放宽 daemon 的连续序号／request_id 检查，或更换窗口身份。没有改 panes.ts、提问信任判定、作答按键、attempt 绑定、receipt helper 或界面状态逻辑。

本轮 main 的改动仅在 sendWindowCommand（123–143 行）；transport 改 request 签名及 connect 时的发送（19–34 行）。renderer、sidebar 和设置页本轮没有改动。这个修复位于原命令队列／传输边界，无需新增产品模块或另一条发送路径。

`receipt-sequence-contract-01.json` 执行实际 main 队列与实际 transport，只有 socket 边界由测试提供。修前 4a6d6bb9e 在“未连接命令不能消耗序号”失败，实际 2、期望 0；修后 PASS。它还核对原窗口／同一问题、已发送未知结果不重放、业务拒绝继续传出、放行请求未完成时仍允许新输入使声明过期、重复放行拒绝、request_id 唯一和无自动重连。该合同不冒充真实 Electron 证据。

`receipt-ipc-01.json` PASS，原有 handler／bridge、越权、历史、只读、关闭、空布局、通知及断连拒绝检查均保留。`receipt-questions-01.json` PASS（429 个 hook 异常案例、14 个作答生命周期案例）。`receipt-local-checks.json` 记录语法、构建及系统通知 API 检索；临时构建已清理。`receipt-snapshot-01.json` 与 `receipt-harness-checks.json` 核对快照 JSON 契约、Python 3.9 语法、脚本入口和 UTF-8 编码。地图检查仍为稀疏检出的 8 个既知缺失、0 stale，见 `receipt-project-map-status.json`。

真实入口增加一次断连中的实际 preload/main resize 调用，须原样报 ENOENT，使未连接命令的序号问题稳定出现，不依赖 ResizeObserver 的偶然时序。失败时保存窗口快照和相关窗口事件，方便区分输入禁用、请求未接纳及最终回执失败。原作答入口与最终回执成功断言未改。

## 主控执行

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT-05.sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-RECEIPT-COMPARE.sh /private/tmp/t110-receipt-compare-01.json
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t110-outside-07.json
```

对照脚本只跑 e1c7b5c27 与当前候选。两者都走相同的断连、断连中刷新／重载、恢复，然后再点击一次可见“刷新列表”，使 e1 已知的选择恢复问题不阻止到达作答入口。e1 的窗格可能此时才挂载，因此两版都使用一次界面重载恢复读取，取代完整场景中的手动窗格重连按钮。额外操作只用于这个对照，两版动作一致；同一问题、原 paneKey／项目／daemon 身份、去重、作答最终回执及原 PTY 后续输入的断言均保留。e1 通过时如实记 PASS；失败须已到作答入口且有 invalid_window_sequence 的真实拒绝与界面错误，否则整个对照 INCOMPLETE。当前候选必须完成全部原生作答合同才算绿态。

完整入口仍不增加这次恢复刷新；继续验证界面自行保留项目。共六个运行：隐藏通知、断连角标、恢复视图三个旧红态，新增 4a6d6bb9e 的重连作答红态，当前正常闭环和禁用通知。新增红态必须有真实序号拒绝及作答失败，不能把导入、清理或其他故障计成红态。

第六轮另有 native PID 34879 的清理身份变化，已上报 `20261020T141307Z-worker:s18-t110-issue-001`，正文见 `ISSUE-OUTSIDE06-CLEANUP.md`。未向不确定身份发信号，也未修改清理检查；旧夹具保留。
