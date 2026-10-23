# T-153 修改前清单

起点：`b058e3a75`。行号对应该版本的 `workbench/tests/run_worker_delivery.py`。
完整 assert 原文见 `pre-edit-inventory.json`；以下同时列出显式异常检查和夹具检查。

| 原行号 / 检查 | 判定与迁移 |
| --- | --- |
| 25–43，独立 ORACLE 的 5 组输入、函数结果、ValueError、进程退出值、stdout JSON | 有效，全保留。期望来自本文件任务卡的姓名合并、排序、分钟格式和非法输入要求，不取产品输出。 |
| 74、80，命令 exit、JSON ok | 有效；环境、用法、启动失败单独报 INCOMPLETE，不当作红态。 |
| 87，外置盘必须已挂载 | 构建约束已由 AGENTS.md 的 2026-10-19 裁定替换；运行原始证据留 /tmp，归档交主控，不在测试中要求挂载或删除原始现场。 |
| 98，stub 必须先被独立 oracle 拒绝 | 有效，保留；这只是夹具红态，不替代产品变异红态。 |
| 100–112，隔离 home、两条 Git allow、旧角色卡和授权引用 | 隔离 home 与两条 allow 保留（AGENTS.md 真实 Codex 验收规则，T-127 明确保留）；使用当前 workbench 角色卡，运行授权显式传入，删去早期已不存在的决定05路径。 |
| 118–119，后台 pid=pgid=sid，且与调用者不同 | 有效，全保留（现行 spec §2 和 AGENTS.md）。 |
| 143–178，领导进程确认、累计 turn-budget、pane_release | 领导进程确认保留；旧批次累计预算改为本次显式授权、worker 最多两回合、reviewer 最多两回合。T-127 删除手动放行：等待原生 ready 后自动派发；不改共享基类。 |
| 182–191，submitted、idle、writing、queue、两个完成回合及超时 | 有效，保留两个完成回合；queue 单独断言，避免重复通知变异只表现为超时。 |
| 193、203，独立 oracle 不变 | 有效，两处保留。 |
| 195–196，candidate=worker HEAD，main 仍为 G | 有效，全保留。 |
| 197–198，verify 后直接 integrate | 过时。spec §3.5–7、T-070/T-072：verify 开独立 reviewer，等报告与 review_reclaimed，传 score-file 再 integrate。 |
| 200–202，verification G/M、两父 merge、host 文件未丢 | 有效，全保留；继续在 worker claim 后制造独立主分支提交 G。 |
| 212–217，交付 turn_context 存在，模型/强度非 unknown，delivery 与原生记录相同 | 有效，全保留，来源 spec §8、T-072。 |
| 218–221，九个 A2A 尾注逐字核对 | 固定 Tool=codex-cli 0.162.1 过时（T-118）；Tool 改为独立执行安装的 CLI --version，其余逐项保留。 |
| 225–228，恰好一个 integrated、intent G/M、readback、恰好一个 submitted | 有效，全保留。 |
| 229–234，独立 git diff numstat 与 submission_metrics | 有效，全保留。 |
| 235–236，错误 fence、不完整请求被拒 | 有效，全保留；注入字段绑定 create 返回的完整 task id（T-123）。 |
| 237，重复 delivery 的 relay_replayed | 有效；全局 id:delivery 改为 launch 所属的 id:<launch>:delivery（relay.ts:93–98、T-123 的身份隔离）。仍核对重复请求成功回放，非只检查任意 replay。 |
| 238，delivery 恰好处理一次 | 有效，保留。 |
| 239–242，status/issue 转交，status 回执的 attempt | 有效，全保留。 |
| 246，恰好两个主会话回合 | 有效，保留，不把 reviewer 回合算入 worker。 |
| 248–249，model、never、network_access=false | model 和 never 保留；网络改 true，来源 T-141 用户原话“网络全开”，不是抄当前 turn_context。 |
| 250–256，一批 Stop 一个 gate notice，原生 user 消息只出现一次且与登记文本相等 | 有效，全保留。 |
| 257–261，收据回合无 function_call/custom_tool_call | 有效，保留并按 task_started/task_complete 的记录区间检查，避免缺 turn_id 导致空匹配。 |
| 262–263，无 permission_wait、最终 queue 为空 | 有效，全保留。 |
| 269–291，关闭前记录进程/事件、退出确认、删除隔离凭据、归档 | 保留关闭和退出确认；原始现场与数据库只保存在 /tmp，删除隔离 home 须先确认自有进程全部退出。主控按 T-088 归档，测试不在仓库生成 tar/sqlite。 |

## 已删或改名命令全集（本文件的调用范围）

`pane_release`：已删除，T-127（`282906b9e`），无同名替代命令；原生 ready 后后台自动放行。
其余 `card_save`、`create`、`daemon_start`、`daemon_stop`、`dispatch`、`events`、`integrate`、`launch_show`、`orchestration_events`、`pane_process_info`、`pane_status`、`status`、`verify` 仍在现行 CLI 命令表。
没有其他删掉或改名的命令；`integrate` 的参数与前置流程已变化，见上表。

## 失败方式与反事实

保留检查可能失败于：重复请求再次获得反馈；一批 Stop 发多条通知；通知未送入原生会话或重复送入；收据回合调用工具；交付模型/强度或尾注与真实 turn_context 不符；主分支 CAS 或合并父提交不符。
变异只改 /tmp 源码副本：让 replay 再次获得回执，必须命中“一批 Stop 一次通知”或“最终 queue 为空”的保留检查。运行/启动/预算故障不能算变异被抓住。
本次不新增共享辅助文件，不改共享基类。运行前清单属于静态诊断，真实绿态和变异红态由主控沙箱外运行取得。
