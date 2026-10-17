# A-15 冻结预算与阶段顺序

来源为原 `09b-materials-01/protocol.json`，本包 protocol.json 与其逐字相同；表中许可屏数是 Bash 一次性批准的预期次数，额外屏幕或请求即停止。

| 顺序 | 阶段 | 输入与真实 Stop 效果 | roots | Messages | 工具许可屏 |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | I1 | 批准的模拟用户停止请求；异步 send，Stop 后条目 pending、发送方可见、零反馈 | 1 | 2 | 1 |
| 2 | executor B1/onboarding | I1 读回后串行启动；unknown 时仅排队，不放行业务输入 | 0 | 0 | 0 |
| 3 | I2 | 初始 release 实际 delivered 后的原 send 反馈；确认 | 1 | 1 | 0 |
| 4 | E1 | 同一 stop 的 inbox wake；wrong-target 真实拒绝 | 1 | 2 | 1 |
| 5 | E2 | 原 E1 拒绝反馈；对实际 target 只 Esc 一次 | 1 | 2 | 1 |
| 6 | E3 | 原 E2 成功反馈；真实 executor ack | 1 | 2 | 1 |
| 7 | E4 | 原 E3 ack 反馈；重复 ack 幂等 | 1 | 2 | 1 |
| 8 | I3 | 实际 ack wake；越权 ack 拒绝 | 1 | 2 | 1 |
| 9 | I4 | 原 I3 拒绝反馈；确认并 idle | 1 | 1 | 0 |
| 10 | E5 | 原 E4 反馈；已 ack stop 再停止被拒 | 1 | 2 | 1 |
| 11 | E6 | 原 E5 拒绝反馈；确认并 idle | 1 | 1 | 0 |
| 合计 ideation | I1–I4 | turn_limit=4 | 4 | 6 | 2 |
| 合计 executor | E1–E6 | turn_limit=6 | 6 | 11 | 5 |

供应商模型 0；总 Messages 17。首启每角色六次单键，不计业务 roots/Messages。两个角色从不同 HOME/config/tmp/shell/requests/hooks/user-data 启动；同一时间只做一个角色的启动步骤。

I2 与 E1 的 HTTP 到达顺序可能相反；以实际 dispatch/request/entry ID 和全局 seq 关联，不能按到达先后重编号。E3 之后 I3 与 E4、E4 之后 E5 可能提前到达。未批准的阶段 HTTP 响应在夹具中等待，不能注入替代提示。
