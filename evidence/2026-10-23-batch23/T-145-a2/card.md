# 任务卡 T-145-2（合并回归）

先读 `evidence/2026-10-23-batch23/COMMON.md` 与 `.project-map/tickets/T-145-records-mouse-false-intervention.md`、`.project-map/tickets/T-139-view-model-split-screen.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-145-2（T-145 第二个 attempt） |
| 来源 | T-145 ready_rev 1；起因：T-145（候选 32d4f0f40，从 f8aa84625 起步）合入已含 T-139/T-143、T-140、T-146-1 的 main 后，`test_t145_mouse_reports_e2e.py` 绿态失败。 |
| 目标 | 在 main 上 T-145 e2e 绿态重新通过，T-145 的行为（协议上报原样到 PTY、不记用户输入、真实键入照记）不变；T-139 视图规则不回退。 |
| 非目标 | 改 T-145 的验收语义；视图模型本身。 |
| 修改边界 | 允许：`workbench/tests/test_t145_mouse_reports_e2e.py`、`workbench/tests/t145_*`（只限测试如何打开/定位 worker 窗格、等待条件跟随 T-139 的新视图；断言、期望字节、检查名不变）、`evidence/2026-10-23-batch23/T-145-a2/**`。若根因在产品代码（例如 T-139 视图下 worker 窗格的输出或鼠标模式没有到达界面），先上报并写明证据，产品修改限 `workbench/src/panes.ts` 输入转发部分或 `workbench/app/renderer.tsx` 终端视图部分，经我回复后再改。禁止：`workbench/src/gates/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、其他验收文件。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t139_t143_views_perf_e2e.py`、`workbench/tests/test_t133_t134_records_metrics_e2e.py`、`workbench/tests/test_t145_protocol_input.mjs` |
| 红态命令 | `python3 workbench/tests/test_t145_mouse_reports_e2e.py --summary <新路径>` 在起点 bf932d49940104ec099023aa957d06fe95116e92 失败于“超时：鼠标模式输出已显示”（执行主控沙箱外复现两次）。 |
| 任务类型 | 缺陷修复（合并回归） |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | bf932d49940104ec099023aa957d06fe95116e92（main） |
| 唯一写入者 | Herdr agent `b23-t145b`，worktree `/Users/luckye/Documents/Code/a2a-wt-t145-a2`，分支 `exec/t145-a2` |

## 完成条件与交付

1. 失败证据：`/Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch23/merge-1/run-20261023T125644Z/` 下 t145-green.json/log（并行回归中）与 t145-green-rerun-alone-01.json/log（单独），fixture 路径在 json 里。先查根因：是测试按旧视图找窗格/等输出，还是产品在新视图下没把 worker 输出显示出来。
2. 按根因修，不加长超时、不放宽断言。若改测试，说明为什么测试原先依赖的是旧视图行为而不是 T-145 的验收内容。
3. RUN-OUTSIDE-01.sh：T-145 e2e 绿态、红态（`--revision f8aa84625`）、两个 Electron 变异，T-139/T-143 candidate、T-133/T-134 回归。提交证据用 `git add --sparse`。交付时说 DELIVERED <提交号>。
