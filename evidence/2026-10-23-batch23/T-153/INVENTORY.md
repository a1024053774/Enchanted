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

## 主控 #14 后的 oracle 补强

02 的真实 reviewer 证明旧的五组用例不足：缺失 minutes 默认填 0、成功输出多行 JSON 的变异能同时通过外部 oracle 和 acceptance.py。原五组输入与原有函数结果、异常消息、退出码、错误 JSON 比较全部保留。

按夹具卡“每项含 name 与非负整数 minutes（bool 不算整数）”补上缺失 minutes，False、浮点 0.5/1.0、字符串数字/空串、null、数组与对象 minutes；按“name 是字符串、去空白后不得为空”补上缺失 name、空串、全角空白及 null/bool/数字/数组/对象 name。所有非法输入同时检查 normalize 的 ValueError 消息和实际 report.py 的退出码 2、错误 JSON。成功及错误 stdout 都必须恰为一行；JSON 内容比较仍保留。两份 oracle 均从同一个 ORACLE 字符串生成，新增用例合计后为 24 组。

没有扩展到合同未说明的非法顶层容器或无法解析的 stdin，也没有改 reviewer 提示词、mutation_checks 或交付断言。零模型反事实命令与结果见 RESULTS 的 oracle 补强一节。

## 主控 #15 后的系统检查

03 reviewer 发现“只校验第一行”的变异仍通过 24 项。第四轮按 [MUTATION-PLAN-04.md](MUTATION-PLAN-04.md) 一次列出合同类别：minutes 的 19 类非法输入、name 的 14 类非法输入，分别在三行输入的首/中/末，共 99 个矩阵检查点。原五组输入保留；正常路径补上内部空白、非相邻合并、大小写排序、制表/换行去空白，以及 0/59/60/61/119/120/125/6001 分钟的手写预期，合计 116 组。

normalize 的异常类型与消息、CLI 的退出码、stdout 的 UTF-8/单行/单个 JSON/精确结构与数值类型都显式检查；stderr 只作诊断，不作结果，也不要求为空。函数和 CLI 各接收从同一原始 wire input 独立生成的参数，避免函数修改参数影响 CLI 的输入。

全类别变异、实际补丁、逐格非法输入、完整命令及两份 oracle 的杀死结果见 [MUTATION-SWEEP-04.json](MUTATION-SWEEP-04.json)。原始输出保留在 MUTATION-SWEEP-04-raw.json；最终 JSON 只额外附上从实际被测副本读取的 diff，所有检查结果保持不变。机械验证的边界见 RESULTS，不能把有限变异全过写成所有错误实现都已排除。
