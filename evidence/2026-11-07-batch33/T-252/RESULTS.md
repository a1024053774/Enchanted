# T-252 证据摘要（2026-11-07）

分支 `claude/dreamy-ptolemy-d0f2f0`，父提交 `b4fb97815`（T-251 收尾，产品源码 `8e546df51`）。修复提交 `6159e7697`（`panes.ts`、`daemon.ts`、`gates/core.ts`、README、端到端测试）。票据提交 `0ac219264`（T-252）、`98e5e6111`（T-253）。

测试环境：真实编排后台与门禁，不起 Electron。Codex 是真实安装的 Codex CLI 0.164.0，模型换成本地脚本化 Responses 接口（照 T-140、T-229，零次厂商模型调用，Codex 在夹具的隔离 home 里）；agy、opencode 用 T-187 的本地替身 CLI（`t187_fake_cli.c` 受管模式，回合状态用 OSC 7501 报给终端，不连模型）。hc 缓存用 `ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache`。

测试 `workbench/tests/test_t252_untrusted_turn_other_cli_e2e.py`：worker 回合中途，经同一个钩子入口（gate CLI 的 `signal`，带本 worker 的启动身份）进来一条来源核对不上的钩子，之后 worker 照常提交、submit、结束回合。Codex 的那条是照它真实发出的 PostToolUse 复制、只改 cwd（`/private/tmp`）与工具调用号，在 Codex 自己的 shell 工具里发出；agy、opencode 没有按会话的钩子，替身 worker 在回合里发一条 PostToolUse。检查（期望来自票据验收条目，不取实现输出）：

- 前提 `outside_hook_judged_foreign`：那条钩子确实被判为来源不符（`native_question_unverified`），否则判 INCOMPLETE。
- `untrusted_delivery_not_executed`：任务仍是 claimed，没有候选提交。
- `turn_ended_not_running`：窗格回到 idle。
- `controller_status_shows_reason`：执行主控的 `status` 里有一条阻塞系统问题，正文含 `current_turn_untrusted` 与被拒的 `submit`。
- `issue_names_the_turn`：问题的 `turn_id` 等于那条伪造钩子被判时所在的回合。
- `issue_sent_through_inbox`：问题发给派发它的执行主控，收件箱有回执（夹具的主控终端前台没有 CLI，回执是 `pending / role_session_missing`，与 T-251 相同；送进在线主控 CLI 由 T-251 的 `untrusted-online` 场景证明，与 worker 用哪个 CLI 无关）。
- `old_attempt_reclaimed`、`new_worker_dispatched`：回收旧 attempt，同一任务再派出新 worker。

`--launch`：Codex 的验收用 `run`（T-251 之后执行主控技能的默认做法），agy、opencode 用 `dispatch`。原因见下文“另一个根因”。

## 修前红态（`--revision b4fb97815`）

四次运行前提都满足，都只有 `untrusted_delivery_not_executed` 通过，其余六项失败：

| 运行 | 窗格 | 回收 | 再派 | `status` 里的问题 |
| --- | --- | --- | --- | --- |
| `red/e2e-codex-run.json`（Codex，run） | busy，Stop 被拒 `current_turn_untrusted` | `worker_working` | `already_claimed` | 无；run 一直在等 |
| `red/e2e-codex.json`（Codex，dispatch） | busy，同上 | `identity_conflict`（另一个根因） | `already_claimed` | 无 |
| `red/e2e-opencode.json`（dispatch） | unknown：Stop 抛错被记为 `stop_transfer_failed`，窗格标失败 | `run_external_unknown`（blocked） | `already_claimed` | 无 |
| `red/e2e-agy.json`（dispatch） | 同 opencode | `run_external_unknown` | `already_claimed` | 无 |

`red/e2e-codex.json`、`red/e2e-opencode.json` 用的是加 `--launch` 之前的测试版本，那一版只有 dispatch，流程与现在的 `--launch dispatch` 相同，摘要里没有 `launch` 字段。票据原文写的“回收被拒 `worker_working`”只对 Codex 的 run 成立；agy、opencode 修前的窗格被记为失败，回收被拒的是 `run_external_unknown`，后果相同：回收不了、派不出新 worker。

## 修后绿态

| 运行 | 结果 |
| --- | --- |
| `green/e2e-codex-run.json` | PASS，7 项全过。请求记拒收（`relay_rejected`），下一次 Stop 只重放拒收（`relay_replayed`）；问题的 `turn_id` 是 Codex 的回合号；回收后 run 以 `run_superseded` 结束；再派成功 |
| `green/e2e-opencode.json` | PASS，7 项全过，问题的 `turn_id` 为 `osc7501:<submission>` |
| `green/e2e-agy.json` | PASS，7 项全过 |
| `green/e2e-codex-dispatch.json` | FAIL，只有 `old_attempt_reclaimed`（`identity_conflict`）与随之的 `new_worker_dispatched`（`already_claimed`）失败；Stop 一段的五项都过。见下一节 |

上表是在工作区源码上跑的（摘要里 `revision` 为空），跑完后提交为 `6159e7697`，中间没有改过产品源码。审查 01 指出这批证据没有绑定提交号，于是用 `--revision 6159e7697` 从 Git 取源码重跑了同样四次，结果相同：

| 运行 | 结果 |
| --- | --- |
| `green/e2e-codex-run-6159e7697.json` | PASS，7 项全过 |
| `green/e2e-opencode-6159e7697.json` | PASS，7 项全过 |
| `green/e2e-agy-6159e7697.json` | PASS，7 项全过 |
| `green/e2e-codex-dispatch-6159e7697.json` | FAIL，同样只有回收（`identity_conflict`，attempt 的 `leader_pid` 已绑、`native_session` 为空）与再派失败 |

`6159e7697` 之后的提交没有改产品源码与测试（只加票据、证据与地图）。

## 另一个根因：经 dispatch 派出的 Codex worker 回收不了

`dispatch` 在 Codex 开始回合前读一次窗格并绑定 attempt 的身份，这时 Codex 的原生会话号还不知道（`green/e2e-codex-dispatch.json` 里 `leader_pid` 已绑、`native_session` 为空；`red/e2e-codex.json` 里两项都空）。之后只有 `run` 每轮的观察、一次被受理的 submit 或审查提交会补绑，而 `reclaim` 要求两项都已绑定。所以 Codex worker 经 dispatch 派出、没有一次被受理的交付时，回收一直被拒 `identity_conflict`。与回合可信度无关，改的是门禁回收的身份规则，超出本票的两段 Stop，已记为 [T-253](../../../.project-map/tickets/T-253-codex-dispatch-reclaim-identity-unbound.md)（`ready: no`，等决定）。Claude worker 的会话号在启动参数里，agy、opencode 用后台自造的会话号，派发时都已知，不受影响。

## 变异

每个变异在源码副本上只改一处（测试核对恰好匹配一次）：

| 变异 | 改了什么 | 结果 |
| --- | --- | --- |
| `codex-untrusted-executes` | Codex Stop 不把 refusal 交给中继 | `mutants/e2e-codex-untrusted-executes.json` FAIL：`untrusted_delivery_not_executed`（交付被执行，run 接着走验证，任务停在 paused）及三项问题检查 |
| `codex-turn-stays-busy` | Codex 拒收后窗格仍记 busy | `mutants/e2e-codex-turn-stays-busy.json` FAIL：`turn_ended_not_running`、`old_attempt_reclaimed`（`worker_working`）、`new_worker_dispatched` |
| `reported-untrusted-executes` | `reportedStop` 不把 refusal 交给中继（agy） | `mutants/e2e-agy-reported-untrusted-executes.json` FAIL：`untrusted_delivery_not_executed`（被执行成 submitted）及三项问题检查 |
| `reported-turn-stays-busy` | `reportedStop` 拒收后窗格仍记 busy（opencode） | `mutants/e2e-opencode-reported-turn-stays-busy.json` FAIL：`turn_ended_not_running`、`old_attempt_reclaimed`、`new_worker_dispatched` |
| `issue-no-turn` | 问题的回合号只取 `prompt_id`（opencode） | `mutants/e2e-opencode-issue-no-turn.json` FAIL：只有 `issue_names_the_turn`（`turn_id` 为空） |

## 回归

修后源码上运行，摘要在 `regression/`：

- 单元：`t207_interrupted_turn_hooks.json` PASS（被打断回合的钩子）；`t157_turn_identity.txt`、`t165_queued_stop.txt`、`t166_queued_input.txt` PASS；`t251_hook_cwd.json`、`t251_queued_subdir.json` PASS；`relay_role.json` PASS；`relay_core.json` 无失败；`native_final_read.json` 9 个场景无失败。
- 端到端：`t251_untrusted_claude.json` PASS（T-251 的 Claude 不可信回合，经改名后的 `turnRefused` 字段）；`t187_deliver_agy.json`、`t187_deliver_opencode.json` PASS（可信回合正常交付、审查、集成）；`t127_codex_home.json` PASS（Codex worker 可信回合正常交付、reviewer、集成）。
- 没跑：全量测试（改动集中在两段 Stop 与一个字段名，上面这些覆盖这些路径）；`relay_scope`（T-251 记录它在父提交上已有 4 项失败，本票没改中继）。
- 一次误报：第一次跑 `test_t251_queued_subdir.ts` 时我给了相对输出目录，`subdirectory`、`worktree_root` 两项失败（摘要原文 `{"status":"FAIL",...,"failed":["subdirectory","worktree_root"]}`，那个输出目录已被我删掉）。改用绝对路径后修前、修后都 PASS；修前源码（`/Users/luckye/Documents/Code/a2a-wt/t251`）用相对路径同样失败这两项，所以是调用方式的问题，与本票改动无关。

## 审查

Codex 0.164.0，`gpt-6.1-sol` high，`codex exec -s read-only`，新开干净会话；提示与结论在 `reviews/`。

- 审查 01（`reviews/review-01.md`）：INCOMPLETE。没有确认本票新增的缺陷：用真实 `Panes.signal`、`reportedStop` 做了 216 个组合检查（三家 CLI、四种角色、verified/unknown/permission，正常、failed、stopInProgress、被打断、回合号不对、过期），只有与当前回合匹配的不可信 worker 回合拒收后结束，被打断时仍 busy，其他角色与 permission 没有放宽；用内存 SQLite 调真实 `RequestRelay.receive` 核对已拒收的请求以后重放三次，执行次数为 0。确认 T-253 属实、是已有问题、与本票无关，Codex 用 `run` 验收的理由成立（但只证明 run 路径）。判 INCOMPLETE 的原因有两条：审查期间我提交了 T-253 票，HEAD 从 `6159e7697` 变成 `98e5e6111`；绿态证据没有绑定提交号。`reportedEnding` 与快速连续 OSC 7501 报告的交错没有独立运行证据，审查员写明“未证实”存在重复结束或漏结束，不算缺陷。
- 处理：`98e5e6111` 只加了 T-253 票据，没有改产品源码；按提交号重跑了绿态（见上文）；把证据提交为 `1e424ccc4`，在这个固定提交上做复审 02，复审期间没有提交。
- 复审 02（`reviews/review-02.md`）：PASS，可合并，没有必须修的。核对了 `git diff 6159e7697 1e424ccc4 -- workbench` 为空，四份按提交号重跑的绿态确实从 Git 取 `6159e7697` 的源码，红态、变异与本摘要的表一致；本摘要没有把局部证明说成完整证明。审查员同时写明的限制：变异与回归是在工作区源码上跑的（当时源码与 `6159e7697` 相同），没有绑定提交号，证据强度低于按提交号重跑的绿态；`reportedEnding` 与反馈回合、快速连续 OSC 7501 报告的交错仍“未证实”（需要“旧收尾未完成，反馈回合已启动，新的 working、idle 报告到达”这一时序的运行证据，代码里读不出确定的重复结束或漏结束）；Codex 只证明了 `run` 路径，送进在线主控 CLI 引用的是 T-251 的场景（`7f01355c9`），本票没有重跑。没有开第三轮。

## 设计自查（design-integrity，实现者自查）

- 没有新增 fallback、重试、兼容分支或平行接口：复用 T-251 的 `refusal` 参数、中继拒收记账与 `gates.turnRefused`。
- 不放宽身份核对：只有 worker、回合可信度为 unknown、Stop 与当前回合匹配三者同时成立才走拒收；reviewer、monitor、controller、permission 等待、不匹配的 Stop 仍按旧行为抛 `current_turn_untrusted`。Codex 一段在 transfer 之后仍复查可信度（拒收时跳过），与 `claudeStop` 一致；`reportedStop` 原本就没有这次复查，没有加。
- `turnRefused` 的字段 `prompt_id` 改名 `turn_id`：问题记录的字段本来就叫 `turn_id`，Codex、agy、opencode 没有 prompt_id。它只由后台在不可信回合的 Stop 里调用；`turn_refused_not_current` 事件的数据字段随之改名，这个事件是 T-251 新加、还没发布过。

## 重跑命令

在 `workbench/tests` 下：

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 test_t252_untrusted_turn_other_cli_e2e.py --cli codex --launch run --summary /tmp/t252-codex.json
```

`--cli` 取 `codex`、`agy`、`opencode`；`--launch` 取 `dispatch`（默认）、`run`；`--revision <commit>` 从 Git 取那一版源码；`--mutant <名字>` 在当前源码副本上打变异。

## 夹具状态

`fixtures-status.json` 记了每次运行的夹具目录、是否保留、字节数、文件数与结果。通过的运行由测试自己删除夹具；失败的 11 个运行与 t127 留下的夹具共 12 个（10 MB 到 115 MB，带 `--revision` 或 Codex 的夹具较大，共约 0.48 GB），在记下状态后已删除；我这次单元测试留下的 9 个 `/private/tmp/a4-final-native-*` 与 1 个 `/tmp/a2a-relay-core-*` 也已删除。另有 9 个 `a4-final-native-*` 和 1 个 `a2a-relay-core-*`（20:15，T-251 那次留下的）没动。仓库里只留本目录的文本摘要。
