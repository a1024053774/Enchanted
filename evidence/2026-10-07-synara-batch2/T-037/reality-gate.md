# T-037 接缝核实（2026-10-07）

REALITY GATE: PASS（仅指已核实的接入方向）

目标：移植 run 编排、attempt 所有权保护和人工介入记录。非目标：真实模型调用、M1 切换、T-038 界面与用户实例。验收以 T-037 五项为准。

- observed：fork `a9cc30c395af9ffd51476a1841d80bca66568993` 已有 GateRuntime、服务端原生 thread 创建、MCP a2a_submit、受锁 verify/integrate/reclaim；无 run 命令。参考来源为 core.ts、service.ts、tools.ts。
- observed：decider.ts 的 thread.turn.start 生成 thread.message-sent，显式 dispatchOrigin 为 user/agent/automation；客户端 command schema 剥除 dispatchOrigin，agentGateway 与现有 a2a 分派使用 agent。
- observed：ProjectionSnapshotQuery 的 shell 提供 id、worktreePath、latestTurn、session、hasPendingApprovals、hasPendingUserInput；engine 提供有序持久 event replay 和先注册的订阅。
- observed：主控决定 01 赋予 contracts/a2aGates.ts 与 service.ts 最小接入写入权，不涉及其他共享文件。
- inferred：thread/turn/worktree 是旧 terminal/前台领导者/cwd 的原生协议身份对应；同 turn 的辅助工具活动不应视为更换所有者。
- unknown：真实 Codex app-server 的完整生命周期尚未调用；本 ticket 不据替身宣称通过真实闭环。

最小探针：先把原18项的运行时边界移植为受控 thread 服务；真实 CLI、Git、SQLite 和独立分页 oracle 保留。缺失 run 必须返回契约红态，然后同入口转绿，并捕获 done 无 submit 与忽略 expected attempt 两个 mutant。人工输入通过真实 decider 的消息事件和核心记录接口核对；agent/automation/assistant 与非受管输入不得记录。探针失败保留原始记录；不启动用户服务，不运行模型。责任人 s2-t037，证据保存在本目录。

采用 Tracer bullet：CLI → 同一 Deep modules 门禁核心 → thread 服务边界 → oracle/Git → 收尾回读。Ubiquitous language 沿用 task、attempt、session_id、fence、spec_rev、run、人工介入。
