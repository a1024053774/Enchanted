STATUS: FAIL
TARGET: f41503eabd50c4c30f963ae6b5b8d8d45055838a

EVIDENCE:
- 从 T-140 ticket 与任务卡独立重建标准：真实 Electron、Claude/Codex worker 的 X/Y 写边界、移除后新 worker 撤权、追加事件、启动 argv、项目终端不变。
- 既有 SQLite 红/绿日志证明目录列表投影与追加事件；构建日志仅证明可构建。
- 原生记录 `native-sandbox-01.json` 在创建 `/Users/Shared` 夹具时失败，模型请求为 0。
- 对固定候选中的 `plan()` 做无写入 AST 提取并传入真实 reviewer 目录结构，复现 `AssertionError: unknown working directory`。
- 审查结束时 HEAD 仍为固定候选；project-map status 为 0 Problems、0 Stale living docs。

FINDINGS:
- [P1] `workbench/tests/test_t140_extra_dirs_e2e.py:70` — reviewer 分支之前先断言任务必须能从 cwd 的 `/T-*-a1` 推导。真实 reviewer cwd 是 `state/review-copies/<UUID>`（`workbench/src/gates/core.ts:2271`、`workbench/src/panes.ts:709`），因此首个 reviewer 请求必然失败，完整绿态、monitor 和移除验证无法抵达。应先识别 reviewer，并从审查请求绑定的 task 字段取得任务名，再对 worker 使用 cwd 匹配。

COUNTEREXAMPLE:
- 实际 reviewer 目录结构已被错误拒绝；这是测试设置失败，不能算权限反例成功。
- 忽略设置事件的旧实现被存储测试业务断言拒绝，已有红态日志。
- 两个原生权限变异尚未运行；不能认定已被业务断言拒绝。

LIMITATIONS:
- 核心权限行为仍为 INCOMPLETE；未取得真实 CLI 写入、撤权或真实 Electron 完整旅程证据。
- 添加目录绕过了原生选择器；即使后续 e2e 通过，也不能覆盖选择器交互。
- `/tmp`、`$TMPDIR` 的既有默认授权已单独上报，移除登记能否满足这些路径的撤权要求尚未证明。
- 能力覆盖：编排、异步、身份/范围、交互、文件及写副作用适用；检索 N/A；部署与恢复未在本次证明。
- 未发现经本次证据确认的生产权限违约；上述 FAIL 来自可复现的验收测试故障。

RULE:
- 无：本次未确认重复失败类别。
