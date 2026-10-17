# 单角色 controller 转交候选：失败方式

契约来源为主控 #178 与 #175 原始请求／hook／窗口动作，场景仅一个 controller、假 API、模型0。实际 Claude 新绿态尚未运行。

| 失败方式 | 对应观察与拒绝条件 |
| --- | --- |
| worker 错误扩到新 controller | 实际 bin/inbox 的 schema2 queued 文件；没有 attempt/fence/operator；parent writer 红态保留 |
| 持久启动记录或当前任务不再同一身份 | launch/preset/project/task/spec_rev/session/native session/prompt 任一变化拒绝；原生 await 后再核对 |
| 原生进程换人或 Stop 过期 | leader/shell/native session 绑定；旧 Stop 不入 relay；替换 active 不结算原提交 |
| 参数伪装构思主控为执行主控 | 两条独立 role sentinel；`list --role executor` 仍只返回实际 ideation scope |
| 工具许可 CR 替换 active | #175 原载荷与 control 记录；只有匹配 PermissionRequest 的同 prompt/active CR 保留登记，普通 CR 仍是用户提交 |
| 读请求目录就算业务执行 | queued/delivered 分开；实际 Stop 前 journal 行0；Stop 后实际执行收据，第二回合只确认反馈 |
| 文件回放再次执行或 unknown 自动重试 | request_id 去重／未知结果保留；第二 Stop 不新增 effect 或反馈根 |
| 新 schema 破坏 worker/reviewer 历史 | schema1 回归；nullable journal 迁移保存已有数据与 append-only triggers；worker `/tmp` 拼写仍接受 |
| 假 API 强造成功／空结果过关 | 假服务只能响应固定 command；实际 tool_result 必须 queued JSON；真实执行结果的独立 sentinel、关联 request_id、实际 UPS/Stop/intent/idle 均核对 |
| 第三次反馈增加工具或第四 Messages | 历史唯一固定 tool ID/command；第三次只反馈；第四请求拒绝，预算坏变异在该条件实际失败 |
| 批准被旧场景复用或控制动作未送达 | 新实例、逐屏批准、实际 permission event/原屏/一次 Yes；同 request/window 的 action→admission→intent→written 齐全，否则停 |
| 将 fixture 输入说成另一真实角色发送 | scenario 显式 incoming fixture origin；只播种独立输入，不代理本次角色业务请求 |
| 结果/清理异常被重试抹平 | 每个输出新目录；失败停、不发信号／重试；原失败根、归档与 slot 保留，cleanup 另批 |

沙箱外入口6／空框17／runtime12／input-failures11／worker-inbox14 由主控阶段执行；真实 Claude 绿态、独立 reviewer、09B/09C 和整票均 INCOMPLETE。
