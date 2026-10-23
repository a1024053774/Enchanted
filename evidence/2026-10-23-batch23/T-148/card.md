# 任务卡 T-148-1（T-141 后过时的测试夹具）

先读 `evidence/2026-10-23-batch23/COMMON.md`、`.project-map/tickets/T-148-stale-fixtures-after-t141.md`、`evidence/2026-10-23-batch23/merge-1/run-20261023T170406Z/NOTE.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-148-1 |
| 来源 | T-148 ready_rev 1（ready_by executor） |
| 目标 | `test_t146_reviewer_hooks.mjs` 的审查员 argv 与 `t145_mouse_receiver.c` 的模拟启动屏改到 T-141 后的契约，使两项在 main 上绿；清点其他旧契约夹具。 |
| 非目标 | 产品代码；任何断言、检查名、超时；T-141 的契约本身。 |
| 修改边界 | 允许：`workbench/tests/test_t146_reviewer_hooks.mjs` 的 argv 夹具、`workbench/tests/t145_mouse_receiver.c`、`workbench/tests/test_t145_mouse_reports_e2e.py` 的夹具部分、清点中确认过时的其他测试夹具与注释、`evidence/2026-10-23-batch23/T-148/**`。禁止：`workbench/src/**`、`workbench/app/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`。 |
| 验收文件（oracle_paths） | 上述测试文件中的断言与检查（只许改夹具输入） |
| 红态命令 | 起点上 `node workbench/tests/test_t146_reviewer_hooks.mjs <out> .` 报 `review_launch_boundary`；`python3 workbench/tests/test_t145_mouse_reports_e2e.py --summary <out>` 超时“受管 receiver 就绪并收到派发”。 |
| 任务类型 | 测试 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main（产品代码同 edd8a7cad） |
| 唯一写入者 | Herdr agent `b23-t148`，worktree `/Users/luckye/Documents/Code/a2a-wt-t148`，分支 `exec/t148` |

## 完成条件与交付

1. 夹具改动逐项在 RESULTS 里写前后对照，并说明对应 T-141 契约的哪一条。
2. 审查员 argv 夹具最好由与门禁相同的真实来源生成（如构造 launch 的函数），而不是再手抄一份；做不到就说明。原有的坏实现变异（changed_cli_flag 等）必须仍被拒。
3. T-145：receiver 模拟已信任的 Codex 正常启动；T-145 的红态（还原其修复）与变异仍失败在原检查上。
4. RUN-OUTSIDE-01.sh：两项绿、两项红/变异、T-127 与 T-141 绿态回归；`git add --sparse` 提交，交付时说 DELIVERED <提交号>。
