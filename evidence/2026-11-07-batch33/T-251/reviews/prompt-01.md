你是 a2a（Enchanted）仓库的独立审查员，只读：不改任何文件、不提交、不运行会写仓库的命令。工作目录是一个 git worktree，分支 `fix/t251-untrusted-turn`。用中文写结论。

审查对象：分支头（`git rev-parse HEAD`），父提交 `94abc1347`；用 `git diff 94abc1347 HEAD -- workbench .project-map` 看改动。需求见 `.project-map/tickets/T-251-claude-worker-cwd-untrusts-turn.md`（rev 2 一节写了用户原话、原因链和范围）；审查约定见 `REVIEW.md`，项目规则见 `AGENTS.md`。

改动要点：
1. `workbench/src/questions.ts`：钩子的 cwd 在本次启动的工作区或 `extra_directories` 以内（含子目录）即算本会话（原来要求严格相等）。
2. `workbench/src/panes.ts`：SessionEnd 用同一规则；已启动的 Claude 会话发来 `source: "compact"` 的 SessionStart 时按本会话记录、不改回合状态；`claudeStop` 在 worker 回合不可信（trust 为 unknown）时不再抛错卡住，而是把请求交给中继记为拒收，然后照常结束回合。
3. `workbench/src/relay.ts`：`receive` 多一个 `refusal` 参数，校验通过后不执行，记为拒收结果（写进 relay_requests/relay_results，以后同一请求只重放拒收）。
4. `workbench/src/daemon.ts` 与 `workbench/src/gates/core.ts`：拒收后调用新的 `turnRefused`，给执行主控追加一条阻塞系统问题并经收件箱送达；不取任务操作锁（注释写了理由）。
5. `workbench/src/gates/refusals.ts`、执行主控技能 `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md` 第 4 步。
6. 测试：`workbench/tests/test_t251_hook_cwd.ts`、`workbench/tests/test_t251_untrusted_turn_e2e.py`；结果在 `evidence/2026-11-07-batch33/T-251/`（red/green/mutants/regression）。

请重点找这些问题，每条给出文件:行号、具体输入或时序、会出什么错；拿不准的写“未证实”，不要当成缺陷：
- 身份核对有没有被放宽到不该放的地方：别的会话、子代理（agent_id）、工作区外目录、前缀相同的兄弟目录、符号链接、审查员的候选副本与审查 worktree（T-141 的情形：二者是兄弟目录，不应互相接受）。
- 不可信回合结束后：有没有路径让这一回合的请求被执行或被以后的 Stop 重放；窗格状态、`stopInProgress`、排队的用户输入（claudeQueuedPrompts）、被打断（interrupted）的语义有没有被破坏；回收是否可能提前杀掉仍在工作的 agent。
- `turnRefused` 不取锁是否有竞态会写错记录或让 Stop 失败；它抛错时 worker 窗格会怎样。
- compact SessionStart 的放行是否会被伪造的、非本会话的钩子利用；会话未启动时是否仍走原检查。
- 测试是否真的能区分对错：期望值是否来自需求而非实现输出；端到端测试的前提核对是否足以说明场景触到了缺陷；变异是否覆盖每条修复。
- 有没有违反 AGENTS.md / REVIEW.md 的地方（门禁唯一入口、操作锁语义、不加无证据的 fallback）。

结尾给结论：可合并 / 需修复（列出必须修的）/ 无法判断（缺什么）。
