# T-077：relay 夹具字段修复与静态核对

2026-10-11，回应主控 #72。**INCOMPLETE**：上次 preimage 是夹具错误，未取得后台业务红态，候选阶段未运行。旧 `outside-relay-check-01/` 原样保留。本轮不改产品代码或业务预期，不启动真实 Codex。

## 修正

失败的 `status` 原始 stdout 已有 `task.current_attempt.runtime_identity.launch`，顶层没有 `launch`。现在直接读取该持久化身份字段；同时从归档中的 PTY 环境核对，它与 `A2A_LAUNCH` 及 attempt/session/fence 一致。没有按预期结果、文件名猜测或生成 launch。

全用例静态检查另发现三个 `pane_*` 调用继承了自动加 `--task` 的任务门禁 helper；CLI 的 `noTask`/allowed 参数规则会拒绝它。改用本测试的 `pane_cli` 发无 `--task` 的调用，继续检查 exit 0、ok=true。涉及 `pane_release`、`pane_status`、`pane_process_info`。公用测试 helper、产品参数规则不变。

可审查补丁：`relay-field-audit-01/fixture.patch`。AST 对照确认原有所有 assert 调用不变，仅将 pane 调用指向修正的 helper；新增 helper 保留原有的成功返回检查。

## preimage 与候选的字段核对

静态证据为 `relay-field-audit-01/audit.json`。该文件列出整个用例的字符串字段读取清单，以及两套源码中的生产位置与行号。与失败归档逐字节核对，两个产品版本仍只在 relay 修复处不同；本轮产品没有新增变化。

| 读取内容 | 核对来源及结论 |
| --- | --- |
| `dispatch.attempt`，attempt 的 thread_id / attempt_id / session_id / fence / spec_rev / workspace / base_commit | `gates/core.ts` 的 claim 构造及返回；失败运行 dispatch/status 原文也包含这些字段 |
| `status.task.current_attempt.runtime_identity.launch/native_session` | `gates/core.ts` 的 status 返回整个持久化 task；Panes 的 readThread 产生 runtime_identity；launch 取值已与归档环境实值核对 |
| `status.task.state/candidate_commit/current_attempt` | 同一 status 返回；submit 保存相应 task，字段不存在时仍会报错，没有兜底取值 |
| 新 attempt 的 `conflict_source` | claim 在提供 conflict 时写入 verification_id；writeConflict 的已结束会话分支将原冲突传给新 claim |
| `pane_status.state`；pane_release / pane_process_info 的 `ok` | daemon 返回顶层 ok 与 Panes 数据；三条命令均不接受 `--task`，已修正调用 |
| worker 请求的 `queued/delivered`；signal 成功回执 `{}` | `relayFiles.ts` 的请求写入返回；`gates/cli.ts` 的 signal 成功输出；不把 queued 当成交付通过 |
| `events[].type` | core 的 events 查询/返回；检查的仍是实际 submitted 事件数 |
| relay_requests 的 launch / request_id；relay_results 行数 | 两个 relay 版本都有这些列，schema 未改 |
| runtime 文件的 native / file / turn；环境的 A2A_REQUEST_DIR / A2A_LAUNCH | 原 host 的 runtime 对象、原 Panes 的 spawn 环境；两者源码未改，归档中对应数据可读 |
| completion_conditions[0].argv、contract.pass、runner 返回字段 | 本测试及父测试构造；完成条件中的 Python 字符串解析为带真实换行的 `worker+host`，与原独立业务预期一致，未改 oracle |

这只是静态字段和已存数据核对 **PASS**，不是后台行为 PASS；未走到的流程仍须本次沙箱外运行。

## 交主控执行

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh relay-check-02
```

新产物为 `outside-relay-check-02/`。仍按原顺序先跑 preimage，再跑候选，任一步不符即停；同名目录已存在则拒绝覆盖。预期红态仍是 a2 的合法 `delivery` 应被接受，候选仍须完成原来的身份、重放、重验、集成与保留引用断言。

静态审计重现命令（在本 worker worktree 执行，新输出不得已存在）：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/check-relay-fixture-fields.py --output /tmp/t077-relay-field-audit-replay
```

本次 socket/自建进程仍按任务卡交执行主控运行。真实回合保持 **4/4**，本轮新增 **0**；实际后台复验结果待回传。
