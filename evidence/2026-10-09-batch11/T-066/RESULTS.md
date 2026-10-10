# T-066：BLOCKED，待批准两处上游接入

本次只完成基线红态与接入方案，未修改生产代码。ticket 保持 open；待主控批准后继续，完成后待主控关闭。

规格：T-066 `ready_rev: 1`；controller-split-user-input spec 第 5 节；任务书 `brief-T-066.md`。fork 基线为 `49cae984f22924de006e0f8358cb447eb881aaf6`，a2a 分支，受控文件未修改。开工时未跟踪的 `.grok/` 保留；a2a 主控追加日志未纳入提交。

## 阻塞点与最小方案

凭据已有冻结角色 `a2aPermissions.role`，但 ToolContext 与 MCP 上下文构造没有传递它。用户可以编辑各角色的能力，因此按能力推断角色仍会记录错误；读当前 membership 也不等于读凭据身份。

brief 明确要求其他上游文件先获批准。请求如下，完整补丁见 [upstream-proposed.patch](upstream-proposed.patch)：

| 上游文件 | 最小改动 |
| --- | --- |
| `apps/server/src/agentGateway/toolRuntime.ts:55` | 增加可选只读 callerA2ARole，类型为 contracts 的 A2ASessionPreset。 |
| `apps/server/src/agentGateway/mcpTransport.ts:366` | 从 callerSession.a2aPermissions?.role 赋值。 |

阻塞问题 `20261010T150042Z-worker:t066-issue-001` 已经 scripts/inbox 发给 triage；尚未收到批准。首次使用外部 fork 的 file 引用被 inbox 拒绝，改用仓库内请求文件引用后成功。

核心目前确实要求 caller.address 为 ideation（core.ts:1663）。批准后计划改为检查传入的 stop 能力，并只在 a2a_stop 中使用冻结角色写地址；不扩大到其他命令的地址投影。

## 红态证据

真实隔离服务端、真实 MCP、真实核心 SQLite，仅活跃会话事实受控。所有 provider 在隔离 settings 中禁用，模型 turn 为 0；未触碰正式工作台、用户配置、Herdr 或共享构建输出。

```sh
python3 evidence/2026-10-09-batch11/T-066/replay.py red02 --mode red
python3 evidence/2026-10-09-batch11/T-066/recheck-red.py
```

重放需将 label 换为未用名称，输出拒绝覆盖。进程经 fork 的 a2a/scripts/bun 启动，脱离调用者进程组；结束后只停止该进程、删除自己创建的私有 token，保留数据库和夹具。

| 检查 | 观察 |
| --- | --- |
| 授予执行主控 stop | owner HTTP 设置生效；凭据冻结角色为 executor，能力包含 operate、stop。 |
| 两分钟条件 | 新条目被 stop_too_early 拒绝；自然等待超过 121 秒后中断请求成功。 |
| 错误归属 | [原始事件](red02/executor-event.json) 的 actor 为 ideation，缺 caller_thread、caller_turn。 |
| 目标与状态 | 目标为指定 worker thread；task 状态前后相同。 |
| 请求范围 | [原生增量](red02/native-stop-delta.json) 中唯一 a2a 命令回执是 thread.turn-interrupt-requested。 |

red01 是夹具 token 观察输出缺 a2aPermissions 的 setup 失败，不算产品红态；日志和 trace 保留。red02 原始 verdict 为 FAIL：三项归属失败，加一项过严的原生事件 oracle。后者把 provider 自己追加的 activity/session 事实也当成额外操作；[重评](red02-reassessment.json) 按 a2a 命令回执核对，只中断请求条件成立，三项归属红态仍成立。原始结果未覆盖。

夹具没有真实 provider 绑定，provider 消费中断时记录失败；证据只证明中断请求与核心事件，不能证明 provider 物理中断成功。参数中附带了伪造身份字段，但基线缺字段，不能据此宣称完整反例通过。

## 失败方式与未完成检查

| 失败方式 | 计划处理／当前状态 |
| --- | --- |
| 调用者凭据失效 | 沿用网关活跃 turn、吊销检查；失效反例未运行。 |
| 两个角色先后 stop 同一目标 | 追加各自身份，目标相同；未实现或运行。 |
| stop 与 ack 交叠 | 保留条目锁；ack 先完成则拒绝 stop，stop 持锁时 ack 不能插入；并发验证未运行。 |
| 旧库缺新列 | events.details 为 JSON；计划不新增列、不改旧事件，缺调用者字段显示“未记录”；未实现或运行。 |

INCOMPLETE：修复绿态、构思主控及其他角色停止、身份伪造反例、失效凭据、ack 交叠、旧事件读取、既有套件、typecheck、lint、fmt:check、冻结候选独立审查。没有 fork 交付提交，本次只有 a2a 证据提交。
