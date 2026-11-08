STATUS: INCOMPLETE

SUMMARY: 未确认最初候选新增的缺陷，但审查期间 HEAD 发生变化，本次不能给出“可合并”结论。

TARGET: 最初冻结的候选为 `6159e76975cfae402c1603427622738cd1427216`，比较基线为 `b4fb97815`。结束核对时 HEAD 已变为 `98e5e611117a9ca10b66e48344a8ea968c74bcde`；以下证据只覆盖最初候选。

EVIDENCE:

- **Stop 的放宽范围正确。** [panes.ts:2266](workbench/src/panes.ts:2266) 和 [panes.ts:2307](workbench/src/panes.ts:2307) 都要求 `matched && trust === 'unknown' && role === 'worker'` 才生成拒收原因。用真实 `Panes.signal`／`reportedStop`、内存事件和受控运行时边界，执行了 **216 个组合检查**：覆盖三家 CLI、四种角色、verified／unknown／permission，以及正常、failed、stopInProgress、中断、错误回合号和过期时间。均符合预期：只有匹配的不可信 worker 回合允许拒收后结束；中断后保持 busy；其他角色与 permission 未获放宽。

- **已拒收请求不会在以后 Stop 重放成执行。** [relay.ts:152](workbench/src/relay.ts:152) 在执行命令前处理 `refusal`；[relay.ts:89](workbench/src/relay.ts:89) 对已有请求返回持久化结果。我用内存 SQLite 调用真实 `RequestRelay.receive`，先拒收一条独立 sentinel 请求，再分别以不匹配及匹配 Stop 重放三次：均返回原拒收，执行次数为 **0**。

- **Claude 的 `claudeStop` 没有被本票修改。** 共享回调的字段从 `prompt_id` 改为 `turn_id` 后，[daemon.ts:994](workbench/src/daemon.ts:994) 仍优先取 Claude 的 `stop.prompt_id`；Codex 取原生 Stop 的 `turn_id`，agy／opencode 取 [panes.ts:2354](workbench/src/panes.ts:2354) 从当前 `active.nativeTurn` 构造的 `turn_id`。已读绿态记录中的问题回合号与被判不可信的回合一致。

- **测试具有有效的反事实证据。** 新测试通过真实 `signal` 入口注入钩子；Codex 基于真实 PostToolUse 改 cwd，agy／opencode 使用明确标注的替身 CLI。父提交记录显示前提成立后卡在回合收尾；绿态和变异记录能区分“请求被执行”“窗格仍 busy”“问题缺回合号”。期望的 claimed、无候选、拒收原因、可回收及可重派来自票据需求，没有导入产品实现作为答案。相关断言见 [测试:283](workbench/tests/test_t252_untrusted_turn_other_cli_e2e.py:283)。

FINDINGS:

- **未确认本候选新增的缺陷。**
- **[P2 | pre-existing] Codex `dispatch` 后的身份绑定缺口属实。** [core.ts:4502](workbench/src/gates/core.ts:4502) 要求回收前 attempt 已绑定 `leader_pid` 与 `native_session`。已有红态 `red/e2e-codex.json` 在父提交上就报 `identity_conflict`；修后 `green/e2e-codex-dispatch.json` 已显示窗格 idle、请求拒收、问题生成，但仍因 attempt 的 `native_session === null` 无法回收。`leader_pid` 是否也为空取决于派发时是否已观察到进程，并非每次两项都空。
  
  本票没有修改该绑定逻辑。[core.ts:3036](workbench/src/gates/core.ts:3036) 的 `run` 观察会补绑定，因此 Codex 使用 `run` 验收有理由，且没有绕过回收门禁；它只能证明 **run 路径下**本票修复成立，不能证明 `dispatch` 的完整回收链路已经恢复。该问题应另票处理，不应计成本票新增回归。

COUNTEREXAMPLE:

- 父提交能拒绝新测试的核心收尾要求。
- 已读变异记录分别触发了交付未执行、窗格空闲／回收、问题回合号等断言失败。
- 本次独立内存检查确认：已拒收请求的后续重放没有产生执行副作用。

LIMITATIONS:

- **候选未保持冻结。** 我没有继续追查新 HEAD，不能把旧候选的检查结果移用于它。
- 本次未启动会写文件的端到端测试；真实 CLI／后台结果来自已有记录。绿态记录的 `revision` 为 `null`，未直接记录完整被测提交号，且证据目录在审查时仍未跟踪；完整版本绑定尚不足。
- `reportedEnding` 与快速连续 OSC 7501 报告、反馈回合启动之间的实际交错，尚未取得本次独立运行证据。**未证实**存在重复结束、漏结束或提前回收，不能列为缺陷。
- 最初差异未修改冻结的 `acceptance/**`，未见新增门禁旁路、操作锁放宽或无证据 fallback；project-map 检查为 Problems 0、Stale 0。这些结论同样不覆盖新 HEAD。

停止依据是 [behavioral-acceptance-review 的 SKILL.md](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md)：“If the branch, candidate, or diff changes, return `INCOMPLETE`; do not chase a moving target.”

**结论：无法判断是否可合并。需要固定最终完整 SHA、绑定该版本的运行证据，再对固定候选完成审查；目前没有已证实的本票新增必修项。**