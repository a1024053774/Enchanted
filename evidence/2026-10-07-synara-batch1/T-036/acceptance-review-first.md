# 首次独立冻结审查

STATUS: FAIL

TARGET:
- fork `5cae1072db94ccd1af20ef161481163484aecfe5`，基线 `7cb0ac0a3d5232e90ab2db1fb7eb9ee696d1af73`；a2a `1a8065c2ff30ef40381d01a295bceac5028f33f6`。
- fresh context 审查者：`gpt-6.1-sol / xhigh`，实际供应商 service tier 未验证。未读取实现者聊天、推理或隐藏规划；没有修改冻结文件或启动模型/服务。

EVIDENCE:
- 原交付套件由审查者重跑，8/8 PASS，exit 0；[命令](review-first-command.json)、[原始 trace](review-first-trace.json) 保存其结果。
- 独立预期来自三份冻结规格、synara-m1 与原 acceptance/oracle，未随候选修改。真实 CLI、SQLite、Git、detached worktree 与冻结 oracle 的输出证明交付范围。
- 状态写入集中于 core，CLI/HTTP/MCP 汇入同一核心。独立 SQLite 写事务持操作锁；集成先持久 intent 再 CAS/读回；未发现新增第二套业务状态或失败后伪造成功的 fallback。
- 审查结束时 fork 已跟踪文件干净；T-036 文件、规格、验收源与冻结提交相同。主控的三份批次日志在审查开始已 dirty，只按冻结提交读取。地图为 0 problems、0 stale。

FINDINGS:
- [P1] fork `packages/a2a-gates/src/core.ts:479`：历史 attempt 的首次回收被拒绝。可达序列为 create → dispatch A → A 停止工作 → revoke A → claim B → `reclaim --attempt A`。dispatch 创建 `reclaimed=false`；revoke 保留旧记录并清空 current_attempt；历史回收要求旧 A 已为 `reclaimed=true`，直接返回 `stale_attempt`，不能核对、停止或归档 A。违反 `supervised-run-2026-10-06.md:37`，外部预期见 `test_run_e2e.py:698`。最小修正是受锁选择指定历史 attempt，只回收其核对过的绑定；业务 task 仅在 current_attempt 匹配时改变，已回收历史继续幂等。审查的该项结论来自确定的可达路径，未声称真实原生 thread 复现。

COUNTEREXAMPLE:
- fence mutant 只删除 fence 校验，错 fence 被接受为 submitted，于原套件 `test_coop_e2e.py:135` 的 `0 != 1` 业务断言失败，有效。
- readback mutant 只有所列两处绕过，原恢复套件是 7 个 fixture-error，signals 全空；未被恢复业务断言捕获。
- 历史首次回收不在交付 8 项的覆盖范围内。

LIMITATIONS:
- 恢复记录早于冻结，2/9 PASS；7 项在 Python 入口路径核对处停止，没有 SIGKILL。没有应用提议差异；冻结恢复与 readback 反例证据缺失。
- 本地 CLI/存储证据不能证明服务认证、MCP 原生身份、模型闭环、run 编排或 M1 切换。本审查未跑全仓检查。
- 本次涉及状态、身份、CLI、文件及 Git 副作用；流式输出及检索为 N/A。

RULE:
- 移植原生门禁时保留 `test_run_e2e.py:693` 的历史首次回收、重放、当前与外来绑定不变检查；交付套件不能替代它。
