# 09B 阶段 A runner 拒绝路径 spy

`test_t078_09b_runner_spies.py` 通过真实 `run-09b.py` entry 与纯函数变异，所有检查都在 runner spawn 前完成；没有启动 daemon、fake API、target、CLI 或模型，也没有新增 `/private/tmp/t078-2-09b-run-*` root。

| 检查 | 修复后绿态 | 去掉对应检查的变异红态 |
| --- | --- | --- |
| approval 字段 | 实际 runner 对 `approved_by/stage/approval_ref/allow_role_cli_spawn` 不符退出1，result `spawned=false` | mutant 接受仅 approval 字段错误的 payload |
| source_revision | 实际 runner 对材料 revision 不符退出1，未新增 root | mutant 接受错 revision |
| dispatch 回执 | `validate_attempt` 拒绝缺 attempt/session/fence/thread/workspace 或空值 | mutant 接受空 workspace 回执 |

逐项 JSON 在 `09b-run-spies-06/`，总读回 `results.json` 为 PASS、5/5。每个实际 entry 拒绝结果保存错误和 `roots_added=[]`；变异只执行纯 validator，不调用 runner spawn。

阶段 A 正式运行仍需要主控填写 [stage-a-approval-template.json](stage-a-approval-template.json)，再按 [09B-RUN-PLAN.md](09B-RUN-PLAN.md) 执行 runner。spy 结果不替 readiness、真实 claim 或进程身份验收。
