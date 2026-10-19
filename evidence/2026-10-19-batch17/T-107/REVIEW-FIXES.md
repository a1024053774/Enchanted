# T-107：审查 F1／F2／F3 修复交接

本地针对三项审查问题的回归为 **PASS**；修复候选的真实 Electron 和独立复审仍为
**INCOMPLETE**。基线固定为 `3c3f2e9e189ddf37eeec4091266c8701a2dde33f`。
提交继续由执行主控处理。本轮未调用模型工具、未启动 CLI／模型回合、未操作 Herdr。

| 问题 | 旧候选红态 | 修复与绿态 |
| --- | --- | --- |
| F1：辅助原生会话清除根问题 | 实际 daemon/socket → sidebar → Panes，显式采集根问题及辅助 start 后变为 running，被“辅助会话不能释放根问题”断言拒绝。 | 原生文件须有与已绑定根会话 ID、CLI 来源、文件名匹配的元数据；根回合须匹配。未答或无法归属的问题保持未知，不以新回合代替答案。相同入口保持 unknown；来源不明的 start 也不能清除问题。 |
| F2：读取执行 scan | 未消费原生日志时，实际侧栏查询追加 native_record 和 native.jsonl，被持久化原值断言拒绝。 | status() 统一为纯快照，scan 移至已有 worker 终端输出采集回调；原 hook、进程观察和退出采集保留。相同入口的全部表、schema、trace 与读取游标不变。没有另开读取路径或开关。 |
| F3：完成条件放过写库 | 旧产品加一行 store.event('sidebar_read')，冻结的旧完成条件仍 PASS，复现验收缺口。 | 新投影完成条件、实际 daemon/socket 入口均在业务断言上拒绝同一单行变异。另在真实 Electron 驱动加入直接侧栏 IPC 读取，比较读取前后的所有持久化原值，待主控执行。 |

`t107_persistence.py` 独立枚举夹具下每份 SQLite 的 schema、每张表的全部行及 trace
文件原始字节，不使用哈希。实际 daemon 夹具包括 state.sqlite3、membership.sqlite3、
locks/t.sqlite3，并放入尚未消费的根原生日志。测试通过真实 Unix socket；只给 Panes
注入受控的 PTY 身份和日志，不启动进程，也不宣称证明了真实模型行为。

可重放本轮完整红／绿／变异：

```sh
python3 -B workbench/tests/test_t107_review_regressions.py --source . --summary /tmp/t107-review-fixes-replay.json
```

本轮最终结果为 `/tmp/t107-review-fixes-03.json`，完整现场保留在
`/private/tmp/t107-review-fixes-yxdy7x7k`；摘要见 `review-fixes-summary.json`。
首轮脚本把“新产品”误配给“旧 oracle”，因新增根身份要求失败；现场
`/private/tmp/t107-review-fixes-56vwheji` 保留，未把该错误当作 F3 反例。
修正后使用旧产品加写库变异配旧 oracle，后两次完整重放均得到预期结果。
其他探索、红态和变异原件均保留在摘要列出的 /private/tmp 路径，未删除，归档待主控处理。

原有投影变异和 main/preload IPC 合同回归 PASS；没有删除或放宽原焦点、只读、
层级、Git、角色、attempt 与 IPC 拒绝断言。运行中的正例补齐了独立根元数据／回合事实，
同时新增缺少这些事实时必须未知的反例。Python 3.9 语法、Node 语法和 diff 检查 PASS。

真实 Electron 新编号命令：

```sh
bash evidence/2026-10-19-batch17/T-107/RUN-OUTSIDE-01-ELECTRON.sh electron-04
```

此入口已串入 F1／F2 的实际 daemon 验证和 Electron 侧栏 IPC 的持久化原值检查，
原来已通过的旅程保留。旧现场和 electron-01／02／03 摘要不覆盖。整票的七状态、
完整 worker 父层级和真实系统通知缺口仍为 INCOMPLETE。

审查方的 `REVIEW-OUTSIDE-01.sh` 未修改：它仍固定旧候选并预期写库变异通过。
主控冻结新提交后，需由审查方更新其候选与拒绝预期，再用于新候选复审。
地图检查仍为既有 8 个稀疏检出问题、0 stale，未改地图或治理文件。

## electron-04 后的夹具断言修正

主控运行 electron-04 后，新增的真实 daemon 隔离／只读检查和 Electron 侧栏 IPC
持久化检查已通过；历史窗格检查被“全页无 alert”的旧断言拒绝。核对 F2 前保留的
electron-02 与 electron-04 库，五个 launch 的恢复拒绝原因完全一致：两个
restore_record_unrecognized，三个 restore_managed_attempt_requires_reclaim；恢复方法
原文也未变化。这是旧断言与刻意不可恢复夹具矛盾，早先曾在窗格尚未加载时通过，
不属于 F2 改变恢复语义。

本次仅修测试：等待全部五个已绑定 launch 的窗格加载；逐窗格要求确切的一条恢复拒绝
提示、输入只读，并要求全页 alert 恰好为这五条，拒绝额外连接错误。每次聚焦后重复
核对，原焦点、状态、层级、Git 与持久化断言保留。缺窗格、错提示、缺提示、可写历史、
额外连接错误和缺全页提示六个反例均被业务断言拒绝，见 restoration-oracle-summary.json。
旧现场保留；真实重跑命令的标签改为 electron-05，审查者脚本未修改。
