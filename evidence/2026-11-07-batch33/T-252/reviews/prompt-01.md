你是 a2a（Enchanted）仓库的独立审查员，只读：不改任何文件、不提交、不运行会写仓库的命令。工作目录是一个 git worktree，分支 `claude/dreamy-ptolemy-d0f2f0`。用中文写结论。

审查对象：分支头（`git rev-parse HEAD`），父提交 `b4fb97815`（T-251 收尾，产品源码 `8e546df51`）；用 `git diff b4fb97815 HEAD -- workbench .project-map` 看改动。需求见 `.project-map/tickets/T-252-other-cli-untrusted-turn-stop.md`（写了用户原话、原因链与范围）；前一张票 `.project-map/tickets/T-251-claude-worker-cwd-untrusts-turn.md` 是本票照做的做法；审查约定见 `REVIEW.md`，项目规则见 `AGENTS.md`。

改动要点：
1. `workbench/src/panes.ts`，`signal` 里 Codex 共用的 Stop 段：worker 的回合可信度为 unknown、Stop 与当前回合匹配时，不再在把窗格记为空闲之前抛 `current_turn_untrusted`，而是把 `refusal='current_turn_untrusted'` 交给 transfer，然后照常结束回合；其他情况（reviewer、monitor、controller，不匹配的 Stop，permission）保持旧行为。
2. 同文件 `reportedStop`（agy、opencode 由 OSC 7501 得出的回合结束）：同样的改法。
3. `workbench/src/daemon.ts`：调 `gates.turnRefused` 时回合号取 `stop.prompt_id ?? stop.turn_id`；`workbench/src/gates/core.ts` 里 `turnRefused` 的字段 `prompt_id` 改名 `turn_id`。
4. `workbench/README.md` 两处说明。
5. 测试：`workbench/tests/test_t252_untrusted_turn_other_cli_e2e.py`；结果在 `evidence/2026-11-07-batch33/T-252/`（red/green/mutants/regression），`RESULTS.md` 若已写好也可以看。

请重点找这些问题，每条给出文件:行号、具体输入或时序、会出什么错；拿不准的写“未证实”，不要当成缺陷：
- 有没有路径让不可信回合的请求被执行，或被以后的 Stop 重放成执行；`matched` 为假、`pane.failed`、`stopInProgress`、被打断（interrupted）、permission 时的语义是否和改前一致。
- 回合结束后窗格状态是否正确；`reportedEnding` 与 OSC 7501 报告的时序会不会让同一回合被结束两次或漏结束；回收是否可能提前杀掉仍在工作的 agent。
- reviewer、monitor、controller 的不可信回合是否仍被拒；改动有没有影响 Claude 的 `claudeStop`。
- `turnRefused` 的回合号：Codex、agy、opencode 的 Stop 各带什么字段，取到的值是否就是这一回合的。
- 测试是否真的能区分对错：期望值是否来自需求而非实现输出；伪造钩子是否经真实入口进来、前提核对是否足以说明场景触到了缺陷；变异是否覆盖每条修复；Codex 用 `run` 而不用 `dispatch` 作验收的理由（见测试文件头注释）是否成立。
- 另一个根因：Codex 经 `dispatch` 派出、交付被拒时，回收被拒 `identity_conflict`（attempt 的 `leader_pid`、`native_session` 没绑定）。本票没改它。请判断这个判断是否属实、是否与本票改动有关。
- 有没有违反 AGENTS.md / REVIEW.md 的地方（门禁唯一入口、操作锁语义、不加无证据的 fallback）。

结尾给结论：可合并 / 需修复（列出必须修的）/ 无法判断（缺什么）。
