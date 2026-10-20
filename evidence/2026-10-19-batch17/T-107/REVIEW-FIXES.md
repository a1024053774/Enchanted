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


## 第二轮审查 F4：rollout 根文件归属

本轮修复与本地回归 **PASS**；新候选真实 Electron 与独立复审为 **INCOMPLETE**。
已冻结的旧候选 `f563fd5182feebfd16bee9063714e278536ddc6b` 中，同一 submission 的
启动钩子之后，精确文件名的未答根问题为 unknown，rollout 前缀的同一问题却为 running。
新增的实际 daemon/socket sentinel 在修改产品前按业务断言取得此红态，清理完成；
原始现场 `/private/tmp/t107-daemon-read-gxcOlV` 保留。

归属校验统一放在现有 paneRecovery 模块，恢复定位、原生采集和侧栏读取共用。
文件名接受既有的 session 后缀合同，同时核对 metadata 的 ID、CLI 来源和工作目录。
归属结果区分根、已核实的辅助会话和未知；不能核实的问题保持未知，文件名不匹配
不再被当作辅助会话证据。侧栏仍只读保存的事件，不扫描原生日志、不写库或 trace。
采集器的 ambiguous_native_session 拒绝保留，并有冲突会话反例核对。

最终红／绿重放在 `/tmp/t107-f4-regressions-03.json`，现场
`/private/tmp/t107-review-fixes-obzcig2f`，12 项全部得到预期结果：F1／F2 旧候选失败、
新候选通过；F4 仅变换文件名时旧候选 rollout 失败，两种名称在修复后都为 unknown；
F3 写库变异仍被新投影和实际 daemon 的持久化业务断言拒绝，旧 oracle 仍放过该变异。
F4 两种名称均包含同一 submission 的启动钩子，并要求提问前为 running、提问后为 unknown；
读取前后的所有表、schema、trace 和游标相同。恢复定位器也须接受这两种名称。

原有三项投影变异、main/preload IPC 合同与 T-096 恢复合同均 PASS。新增投影反例覆盖
文件名、metadata ID、来源、辅助父会话和工作目录未核实的问题；明确绑定的辅助问题
不会改变根会话状态。摘要见 `f4-fixes-summary.json`。

首次投影运行因共享归属模块引入既有 effect 依赖、而稀疏 checkout 未安装依赖，尚未进入
断言；该运行不计红态。重放脚本和变异脚本使用独立临时源码与内置盘既有依赖，修正后
完成全部断言。既有原件和审查者的报告／脚本均保留，未修改。

真实 Electron 待主控执行：

```sh
bash evidence/2026-10-19-batch17/T-107/RUN-OUTSIDE-01-ELECTRON.sh electron-06
```

脚本已串入 F4 两种文件名的实际 daemon sentinel；原 Electron 已知坏基线、侧栏 IPC
零写入、五条准确恢复拒绝、焦点、层级、Git 和只读断言保留。此运行不调用模型，
不要求原生对话框操作，不截图。整票原有状态信号、worker 父绑定和真实通知缺口不变。

本轮地图复查为既有 8 个稀疏检出缺文件问题、0 stale，详见 project-map-f4-status.txt。
