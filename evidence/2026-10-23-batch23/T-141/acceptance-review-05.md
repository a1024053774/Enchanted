STATUS: FAIL
TARGET: 29e4e69b6234cfbbe2107fdee9f5fdc22b845c6f
EVIDENCE:
- 最终 HEAD 仍为冻结候选。
- 与 base 比较，T-127 仅改变获准的四个判据及四处旧变异定位；其余检查和等待期限保留。
- 本地 oracle 检查退出 0：14 组判据输入、13 个唯一变异目标及语法检查通过；只证明 L1 判据逻辑和变异定位。
- `zsh -n RUN-OUTSIDE-05.sh` 通过；runner 包含要求的 T-141、T-127、T-140、T-131、T-132 和变异场景。
- 原始 outside04/t127.json 在旧 restricted 启动判据失败；记录的实际启动为 `["turn_submitted"]`。

FINDINGS:
- [P2] evidence/2026-10-23-batch23/T-141/RUN-OUTSIDE-05.sh:85 — 两个 reviewer trust 变异仅凭非零退出和泛化的 `review_launch_boundary` 错误判为反例通过。该门禁也因 sandbox、目录、身份等无关条件拒绝，故 unrelated reviewer setup failure 可被误计。应保留拒绝详情，核对实际 trust 变异及其他边界条件，而非只匹配错误码。

COUNTEREXAMPLE:
- 对 runner 原判据输入 `exit=1`、`verify.error="review_launch_boundary"`，并明确标记原因为无关 reviewer sandbox mismatch，结果仍为 `accepted_as_known_bad_rejected=true`。生产门禁确实将这些不同失败归入同一错误码（workbench/src/gates/core.ts:2394–2398）。
- 独立 oracle 输入正确拒绝了 worker trust override、home 改写和 reviewer project hook 标记。

LIMITATIONS:
- RUN05 尚未执行；真实 Codex 启动、reviewer 隔离、hook/exec policy 行为仍为 INCOMPLETE。
- 未启动原生 agent 或 daemon；语法检查不能证明变异已产生目标行为。
- 按任务限制未读取 RESULTS.md，不能核对其比较内容。
- 能力范围涉及 orchestration、async、identity/scope、CLI、文件和本地副作用；retrieval N/A。本次没有真实边界通过证据。

RULE:
- 在 runner 分类器的本地检查中加入“相同错误码、无关边界原因”的反例，要求归为 INCOMPLETE；在真实变异运行中核对具体被破坏的条件。
