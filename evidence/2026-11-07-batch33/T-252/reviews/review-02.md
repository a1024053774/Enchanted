STATUS: **PASS**

SUMMARY: 未确认 T-252 新增的缺陷。审查 01 的两项阻塞原因——候选变化、绿态未绑定版本——在本轮已消除。T-253 的已有缺陷仍存在，未被写成通过。

TARGET: `1e424ccc43aae8842310cbcb09b4554b60063416`，比较基线 `b4fb97815`。本轮所有源码和证据判断均取自该固定候选；结束时 HEAD 仍为该 SHA，工作区干净。

EVIDENCE:

- **审查 01 的代码结论仍适用。** `git diff 6159e7697 1e424ccc4 -- workbench` 为空；`98e5e6111` 只新增 T-253 票据，`1e424ccc4` 只新增 T-252 证据目录。抽查 [panes.ts:2269](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/panes.ts:2269) 和 [panes.ts:2309](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/panes.ts:2309)：只有匹配当前回合、可信度为 `unknown` 的 worker 才携带 refusal 完成收尾；其他角色、permission 状态和不匹配 Stop 未获得该例外。`daemon.ts:994` 优先取 `prompt_id`、其次取 `turn_id`，`core.ts:823` 将其写入问题。README 与这一区别一致。本轮未重跑审查 01 的 216 项组合检查。

- **版本绑定有效。** 四份 `green/*-6159e7697.json` 的 `revision` 和 `argv --revision` 均为 `6159e7697`，可唯一解析为 `6159e76975cfae402c1603427622738cd1427216`。测试将该参数传入 Fixture；[scripted_claude.py:101](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/tests/scripted_claude.py:101) 确实通过 `git ls-tree`／`git show` 取源码，后台和门禁入口使用该源码目录。

- **四份重跑记录与 RESULTS 一致。** 前提 `outside_hook_judged_foreign` 均成立，具体检查结果如下：

  | 记录 | 核对结果 |
  | --- | --- |
  | `green/e2e-codex-run-6159e7697.json` | PASS，7 项通过；claimed、idle、拒收问题与回合号匹配，回收和再派成功；原 run 以 `run_superseded` 结束 |
  | `green/e2e-agy-6159e7697.json` | PASS，7 项通过 |
  | `green/e2e-opencode-6159e7697.json` | PASS，7 项通过 |
  | `green/e2e-codex-dispatch-6159e7697.json` | FAIL，前 5 项通过；回收报 `identity_conflict`，再派报 `already_claimed` |

  最后一项与审查 01 已确认的 T-253 一致：attempt 的 `leader_pid` 已绑定、`native_session` 为空，而 `core.ts:4502` 要求两者均已绑定。候选没有修改该规则，RESULTS 也明确保留了失败。

- **摘要未把局部证明扩大成完整证明。** [RESULTS.md:14](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/evidence/2026-11-07-batch33/T-252/RESULTS.md:14) 明确写出本轮收件箱回执为 `pending / role_session_missing`；在线主控实际收到问题引用的是 T-251 的 `untrusted-online` 场景。我核对了该历史记录，其版本为 `7f01355c9`，包含通过的 `issue_reached_executor_cli`。这支持共享送达路径的历史证据，不能视为本候选重新跑过在线主控场景。RESULTS 同时明确限定了 Codex 完整回收链路只在 `run` 路径通过。

FINDINGS:

- **本轮无新增已证实问题，无本票必须修复项。** 审查 01 对修复范围和 T-253 归属的结论仍成立；其 INCOMPLETE 所依据的候选冻结与绿态版本绑定问题已解决。

COUNTEREXAMPLE:

- 四份红态均绑定 `b4fb97815`，只有 `untrusted_delivery_not_executed` 通过，其余六项失败。Codex `run` 为 busy／`worker_working`；Codex `dispatch` 为 busy／`identity_conflict`；agy、opencode 为 unknown／`run_external_unknown`。与 RESULTS 表格一致。
- 五份变异的失败集合逐一一致：两份取消 refusal 的变异触发“交付未执行”和三项问题检查失败；两份保持 busy 的变异触发空闲、回收、再派失败；`issue-no-turn` 仅触发 `issue_names_the_turn` 失败。不是仅因启动失败或前提未满足而判红。

LIMITATIONS:

- **`reportedEnding` 交错仍为“未证实”。** [panes.ts:2352](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/panes.ts:2352) 同时检查 `stopInProgress` 和 `reportedEnding`，在调用异步收尾前设置后者，并在 promise 完成后清除；`daemon.ts:1132` 在此期间可能启动反馈回合。需要验证的时序是“旧收尾未完成 → 反馈回合启动 → 新 working、idle 报告到达”。本轮没有取得这一交错的运行证据，也未从代码推出确定的重复结束、漏结束或提前回收，因此不列为缺陷。
- 本轮只读核对源码和已保存证据，没有启动会写文件的端到端测试。变异及回归摘要未绑定提交号，证据强度低于四份新绿态；没有把它们称为固定候选上的独立重跑。全量测试未运行，RESULTS 已说明。
- 不据此宣称 Codex `dispatch` 的完整回收链路可用，也不外推至真实厂商模型、Electron 界面或所有 OSC 时序。项目地图检查为 Problems 0、Stale 0。

**结论：可合并。本轮无必须修复项；T-253 保持已有缺陷记录，OSC 交错保持“未证实”。**