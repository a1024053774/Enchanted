# 人工输入订阅状态（2026-10-08）

`status`、`events` 和门禁 GET 在既有返回中新增 `human_input_observer`。真实服务配置了记录器时，该对象含 `state`（starting / healthy / failed / stopped）、`updated_at`；失败时含 `failure`：`event_id`、`source_sequence`、`thread_id`、`message_id`、`reason`。源流本身异常结束而没有具体消息时，仅提供原因。未安装原生记录器的独立 CLI / 隔离替身不声称健康，字段省略。

订阅异常、defect 或非预期结束由核心记为 failed。正常 scope 取消记为 stopped。failed 在该实例内保持，不能靠再调用安装函数重置。状态保存在服务实例内，因为存储故障可能阻止写入失败状态本身；只读查询仍读取原记录并返回失败信息。存储恢复后，新的服务实例先回放 Synara 源日志，再进入 healthy；无自动重试、跳过失败消息或额外运行路径。

| 命令 | 失败后的行为与理由 |
| --- | --- |
| status | 继续读取 task，并显示 failed 与源事件、原因 |
| events | 继续读取已落盘的历史，并显示 failed 与源事件、原因 |
| GET /api/a2a?thread=… | 继续读取绑定 task，并显示同一状态；返回 200/ok=true 是可读取，不是订阅健康 |
| create | 拒绝：注册任务、快照、初始化引用与项目会改变状态 |
| claim | 拒绝：分配 attempt/fence 与 worktree |
| revoke | 拒绝：撤销当前所有权 |
| revise | 拒绝：改变规格与所有权 |
| dispatch | 拒绝：分配所有权、创建并投递 thread |
| run | 拒绝：编排上述状态和外部效果 |
| submit | 拒绝：冻结候选与交付状态 |
| verify | 拒绝：创建验证记录、worktree 并运行 oracle |
| integrate | 拒绝：写集成意图、CAS 引用与 accepted 状态 |
| reclaim | 拒绝：它要写回收意图/结果，可能撤销当前所有权，并停止、归档 thread；故障时不能把未完整记录的回收当作安全完成 |

专用错误码为 `human_input_observer_failed`。异步操作的后续写入与外部动作也核对状态；已发生的外部效果不伪装回滚。记录故障可能阻止最终 run 收据落盘，此时保留旧持久阶段，回复非完成结果及可查询的失败；修复后的核对继续走原恢复入口。

实际故障探针：真实 engine 接收有效人类消息，隔离 SQLite 写锁使记录失败；查询仍可用，全部 10 个变更命令拒绝且 task/attempt/事件前缀不变，真实 GET 返回 failed。另一条后续消息留在源日志；新记录器回放两条遗漏消息各一次。界面显示由 T-038 验证，不把本次 GET 证据当作界面截图。
