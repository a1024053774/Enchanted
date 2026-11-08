STATUS: INCOMPLETE
SUMMARY: 未发现已复现的候选缺陷；缺候选真实入口绿态、门禁 verify 与独立审查，不能宣布业务通过。
TARGET: a2d6dbcbbf4c4a43240f89273f1bafb05fc1234c，worker 自查。
EVIDENCE:
- 独立期望来自 T-257 Acceptance：同一真实 Stop 续跑场景结束后 idle、队列继续、reclaim 成功；真正工作中仍拒绝 reclaim。测试不以实现输出生成期望值。
- L3 修前：主控 red-controller-diagnostic-02.json 在 5c7df3a93019cea1a690194773d967bebb69a4ef 上经真实后台、门禁和交互 Codex 取得 10 项前提、5 项业务失败、两次真正工作中的回收拒绝。worker 阅读该证据，没有将其改写为自己的执行结果。
- L1/L2 当前模块：相同 TS 检查修前 104 场景中 30 个失败，修后 104 场景全过。71 个有界排列覆盖 0～2 次扫描和旧 Stop，24 个固定种子覆盖 Stop transfer 等待期间的重复 Stop/task_complete，9 个反例覆盖来源、时间、中断与完成信号。逐场序列、失败与种子保存在 module-red-02-schedules.json / module-green-01-schedules.json。
- Python 真实入口使用唯一随机 marker 作为后续消息，核对实际 turn_submitted、CLI 本地 Responses 收到 marker、原生 task_complete、最终窗格与门禁 reclaim，不只检查模型文字或请求返回 ok。四条真实请求按 key 核对只执行一次。测试仅在隔离源码副本包装 hook 命令的返回时间屏障，不修改 hook 输入、生产状态或 rollout。
- 第二 Stop 的识别依赖相同 session/turn 和晚于第二 UPS 的后台 seq，stop_hook_active 只记录；跨进程时间改用 UTC。已从主控旧红态选到 seq 174 / false 的真实 Stop，静态回读见 static-v2-baseline.json。
- L0：Python AST/compile、Node 语法、diff 格式检查通过；现有 T-207 中断身份检查 7 项通过。没有执行全套或当前候选的真实 CLI 测试。
FINDINGS:
- 无已复现的候选缺陷。
COUNTEREXAMPLE:
- 无绑定的已知坏父实现：UPS → Stop → duplicate-Stop 得到 nativeTurn=null，模块测试拒绝；等待 transfer 的 24 个种子也因 Stop 未匹配而拒绝。加回唯一绑定后同一测试通过。
- 原生 task_complete 单独到达不能释放 active；旧时间戳、其他 session/turn、子 agent、错误 cwd/transcript、缺 turn 的信号不能获得该提交；中断后的 Stop 仍保持 busy。以上为模块层，不宣称已证明真实门禁身份/attempt/fence/CAS。
- 原生产版本被 L3 真实入口按业务断言判红；初次测试 Stop 标志过度限制和模块 hc 初始化权限错误均另存为测试/环境缺口，不计作产品反例。
LIMITATIONS:
- 本文是任务卡指定的自查，没有新开审查会话，不替代主控安排的独立审查。
- 当前候选 L3 仍须主控在沙箱外以 ENCHANTED_HC_CACHE_DIR=/private/tmp/t257-hc-cache-20261108 执行 Python 真实入口，并执行门禁 verify。缓存未写入或清理。更换 --summary 文件名保留每次结果。
- 编排/状态、异步事件、身份/范围、CLI 交互和门禁副作用适用本票。编排与异步只有模块层候选绿态；真实身份绑定、操作锁、attempt/fence、中断回收与实际队列投递须候选 L3/回归核对。启动或恢复产品不是本票范围。
- 检索/记忆、媒体生成、供应商模型理解为 N/A：本票无相关能力变化，模型固定为本地 Responses 服务。不能从 scripted 模型推断真实供应商理解能力。
- workbench/README.md 的 stale 标记已排队 issue 交主控处理；未改越界文档或地图。敏感变更集成前的用户证据批准仍由主控执行。
RULE:
- 不以模块绿态、模型自报、queued 回执或重启恢复替代真实入口候选验收。
