# T-066 独立审查输入

用户要求只做 T-066，依据 ready_rev 1。fork 基线为 49cae984f22924de006e0f8358cb447eb881aaf6；候选 fork 为 ddb765956cae4a4d0b87b875970601068567ed93。a2a 冻结证据提交另在审查请求中给出。

重建验收条件时只读 ticket 的 What to build、Acceptance、说明（在 `## Resolution` 前截断）；以及 brief 的范围、模型调用限制、独立审查要求，controller-decision-01 的批准边界。核心条件：能力授权，凭据冻结角色/thread/turn 记录，参数伪造无效；两分钟/ack/只中断不变；旧事件不改写，读取缺字段显示未记录。

禁止读取 RESULTS*.md、ticket Resolution、inbox 条目正文、旧审查、acceptance-plan.md、upstream-scope-request.md、实现者的对话与推理。不得读取整个 a2a 提交 diff（会包含禁止的报告）；可以读 fork diff，a2a 中只读本文件、重放驱动和原始机械输出。

主控追加的 controller-poll.log、dispatch.jsonl、panes.txt 不属于候选。只审查一次、只读，不启动第二位审查者，不修改文件、分支或提交。需要独立核对时，用只读 SQLite 连接和原始输入/输出重建 oracle；不运行会向仓库写新证据的 replay.py。

可读的原始证据：red02/executor-event.json、red02/trace.json、red02/state.sqlite3、red02/native-stop-delta.json、red02-reassessment.json；最新完整 green 目录（审查请求指定）；old-db-reopen.json 与两份 SQLite；*-final.log/json、web01.log/json、*-red03.log/json。

精确重放入口（label 必须取未使用值，以免覆盖；审查者只检查命令）：

```sh
python3 evidence/2026-10-09-batch11/T-066/replay.py <新label> --mode green --legacy evidence/2026-10-09-batch11/T-066/red02/executor-event.json --ui
T066_MUTANT=parent-tools python3 evidence/2026-10-09-batch11/T-066/check.py <新label> run --cwd apps/server test src/a2a/cap-composition.test.ts --config /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-066/counterfactual.config.mts
T066_MUTANT=ack-without-lock python3 evidence/2026-10-09-batch11/T-066/check.py <新label> run --cwd packages/a2a-gates test src/inbox.test.ts --testNamePattern 'serializes stop and ack' --config /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-066/counterfactual.config.mts
T066_MUTANT=missing-capability python3 evidence/2026-10-09-batch11/T-066/check.py <新label> run --cwd packages/a2a-gates test src/inbox.test.ts --testNamePattern 'requires a stop grant' --config /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-066/counterfactual.config.mts
```

实际模型 turn 为 0；活跃会话事实受控。真实服务端/MCP/SQLite 与真实任务窗口用于证明中断请求和记录；不以此宣称真实 provider 物理中断已证明。初轮 setup/夹具/配置失败保留，不能当产品红态或绿态。
