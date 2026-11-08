# T-251 证据摘要（2026-11-07）

分支 `fix/t251-untrusted-turn`，父提交 `94abc1347`。修复提交 `b013c477a`（源码、测试、技能）；`ab912013b` 只改测试读 `status` 的字段和票据；`8e546df51` 按审查 01 改排队绑定与问题文案、补 README；之后的提交只改测试与证据。产品源码的最终版本是 `8e546df51`。

测试环境：真实编排后台、门禁与 Claude Code，Messages API 由脚本应答，零次厂商模型调用，不起 Electron（`workbench/tests/scripted_claude.py`）。hc 缓存用 `ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache`。

## 三个场景

| 场景 | 做法 | 修前（`--revision 94abc1347`） | 修后（`--revision b013c477a`） |
| --- | --- | --- | --- |
| cd | worker 在 Bash 里 `cd` 进工作区子目录后写文件、submit | `red/e2e-cd-r2.json` FAIL：`delivered_at_turn_end`、`no_hook_judged_foreign` | `green/e2e-cd.json` PASS |
| compact | 回合中途送一条与真实记录同形的 `source: "compact"` SessionStart，再 submit | `red/e2e-compact.json` FAIL：同上两项 | `green/e2e-compact.json` PASS |
| untrusted | 回合中途送一条 cwd 在工作区以外的钩子（真不可信），再 submit | `red/e2e-untrusted-r2.json` FAIL：窗格停在 busy，Stop 被拒 `current_turn_untrusted`，回收被拒 `worker_working`，再派被拒 `already_claimed`，`status` 里没有问题 | `green/e2e-untrusted-r2.json` PASS |

审查 01 之后的修复在 `8e546df51` 上重跑：`green/e2e-cd-r3.json` PASS，`green/e2e-compact-r3.json` PASS；untrusted 场景见“审查 01 与处理”最后一条（`r3` 因检查期望写错而失败，改检查后在 `cce9e9635` 上重跑为 `green/e2e-untrusted-r4.json`，PASS：问题的 `controller_launch` 等于派发它的终端，回执 pending/role_session_missing）。

untrusted 场景的检查：前提 `outside_hook_judged_foreign`（那条钩子确实被判为来源不符）；`untrusted_delivery_not_executed`（任务仍是 claimed）；`turn_ended_not_running`（窗格回到 idle）；`controller_status_shows_reason`（执行主控的 `status` 里有一条阻塞系统问题，正文含 `current_turn_untrusted` 和被拒的 `submit`）；`old_attempt_reclaimed`；`new_worker_dispatched`。期望值来自票据的验收条目，不取实现输出。

`red/e2e-untrusted.json` 与 `green/e2e-untrusted.json` 是第一轮：测试按错误字段读 `status` 的问题视图（`A2AIssueView` 的记录在 `issue` 下），绿态因此误判 `controller_status_shows_reason` 失败。保留原文件；`ab912013b` 修正读取后重跑为 `-r2`。

## 变异

每个变异在源码副本上只改一处（测试核对恰好匹配一次），然后跑对应场景：

| 变异 | 改了什么 | 结果 |
| --- | --- | --- |
| `cwd-exact` | cwd 回到严格相等 | `mutants/e2e-cwd-exact.json` FAIL：`delivered_at_turn_end`、`no_hook_judged_foreign` |
| `compact-refused` | 去掉 compact 放行 | `mutants/e2e-compact-refused.json` FAIL：同上 |
| `untrusted-executes` | Stop 不把 refusal 交给中继 | `mutants/e2e-untrusted-executes-r2.json` FAIL：`untrusted_delivery_not_executed`（交付被执行成 submitted）、`controller_status_shows_reason` |
| `no-issue` | 不调用 `turnRefused` | `mutants/e2e-no-issue-r2.json` FAIL：只有 `controller_status_shows_reason` |
| `no-delivery` | 问题只记录、不交收件箱 | `mutants/e2e-no-delivery-r2.json` FAIL：只有 `issue_sent_through_inbox`（没有任何送达回执）；`mutants/e2e-no-delivery.json` 是旧检查下的运行 |
| `turn-stays-busy` | 拒收后窗格仍记为 busy | `mutants/e2e-turn-stays-busy-r2.json` FAIL：`turn_ended_not_running`、`old_attempt_reclaimed`、`new_worker_dispatched` |

单元测试 `workbench/tests/test_t251_hook_cwd.ts`：`red/hook_cwd.json`（父提交）拒了子目录、`..` 回到工作区内、extra 目录及其子目录、Codex 子目录；`green/hook_cwd.json` 全过，反例（工作区外、前缀相同的兄弟目录、`..` 逃出、相对路径、缺 cwd、未授予的 extra 目录）都拒。三个单元变异：`mutants/unit-prefix.json`（字符串前缀比较）、`unit-nonormalize.json`（不规范化 `..`）、`unit-exact.json`（严格相等）各判失败。

## 回归

- `green/t207_interrupted_turn_hooks.json` PASS（被打断回合的钩子语义）。
- `regression/t157_turn_identity.txt` PASS；`relay_role.txt` PASS；`relay_core.txt` 无失败；`native_final_read.txt` 无失败。
- `regression/relay_scope.txt` INCOMPLETE，4 项失败；在父提交 `94abc1347` 上同样 4 项失败（`relay_scope-parent-94abc1347.txt`），是已有问题，不是本票回归。
- 改了排队绑定后（`8e546df51` 的源码）重跑：`regression/t157_turn_identity-r2.json`、`regression/t165_queued_stop-r2.txt`、`regression/t166_queued_input-r2.txt`、`green/t207_interrupted_turn_hooks-r2.json`、`green/hook_cwd-r2.json` 全部 PASS（T-157 里 cwd 为 `/elsewhere` 的排队记录仍不绑定）。
- 没跑全量测试：本票改动集中在 Claude worker 的钩子与 Stop 路径和一个新的门禁方法，上面这些测试覆盖这些路径。

## 审查 01 与处理

Codex（gpt-6.1-sol high，只读，干净会话）审 `ab912013b`，结论“需修复”，3 条 P2，另列未证实项。结论原文见 `reviews/review-01.md`。逐条先复现再处理：

1. 符号链接：cwd 只按字面判断，工作区里指向外面的链接路径会被接受。用真实 Claude Code 2.1.319 探针核对（`review-probes/symlink-cd.json`，脚本 `review-probes/probe_symlink.py`）：worker 建 `outlink -> /usr/share` 后 `cd outlink`，Claude Code 按真实路径判断已出界，输出 “Shell cwd was reset to <工作区>”，之后所有钩子报的都是工作区根目录，链接路径从没出现在钩子里。钩子里的 cwd 是会话自己报的字段，伪造的钩子可以直接写工作区根目录，按真实路径解析不增加身份保证，反而会让 cwd 已被删除时误判。真实入口复现不了，不改。
2. 系统问题写“worker 已回到空闲，可以回收”，但有排队的用户输入或被打断时窗格仍忙。属实（文案过度断言，状态保护本身没错）。改为“这一回合本身照常结束；窗格之后是否空闲看 status”，下一步写“等 worker 空闲后回收，还忙时回收会被拒（worker_working）”（`8e546df51`）。README 同一处同改。
3. README 有一句“异常 Stop 不完成回合”与新行为矛盾，地图报 README、REVIEW 两项核对过期。README 补了 T-251 例外与压缩、cwd 规则；地图核对见票据收尾。
- 未证实项“排队输入的会话记录 cwd 严格相等”：用 T-249 worker 的真实会话记录核对，记录里每条消息的 cwd 都跟着 `cd` 走（`/workbench/app/panels` 等），所以属实，是同一类问题：worker 在子目录时用户往窗格里排的输入永远绑不上回合，窗格一直忙、回收不了。`panes.ts` 的排队绑定改用同一条工作区规则（`8e546df51`）。新测试 `test_t251_queued_subdir.ts`：`red/queued_subdir.json`（`ab912013b` 源码）子目录项失败；`green/queued_subdir.json` 全过，前缀相同的兄弟目录与工作区外仍不绑定。
- 收件箱送达没有断言：端到端测试先补了 `issue_delivered_to_executor`（要求回执 delivered），在 `8e546df51` 上跑绿态失败（`green/e2e-untrusted-r3.json`）。查夹具数据库：回执是 `pending / role_session_missing`，问题的 `controller_launch` 正是派发 worker 的那个终端。原因是收件箱只送进前台正在跑 CLI 的已批准主控终端（`panes.ts` 的 `controllerThreads` 要求 `foregroundCli === held.cli`），夹具里的执行主控终端只是批准过角色的 zsh，前台没有 CLI；T-216 规定这时保存 pending 回执，主控 CLI 就绪后由 `resumeControllerInbox` 补送。所以是检查写错了期望，不是缺陷。检查改为 `issue_sent_through_inbox`：直接读夹具数据库的送达回执，要求问题发给派发它的执行主控，最后一条回执是 delivered、queued，或等角色就绪的 pending（`cce9e9635`）。变异 `no-delivery`（只记录、不交收件箱）应在这一项失败。这个夹具证明不了真正送进主控 CLI，复审 02 正是指出这一缺口，补证见下一节。

## 复审 02 与处理

同一模型只读复审 `d5cb1da53`（范围 `ab912013b..HEAD`），结论 INCOMPLETE，原文见 `reviews/review-02.md`：第 2、3、4 项（文案、README、排队绑定）认可，未发现新的产品缺陷；第 1 项（符号链接）保留“未证实”，明确不据此要求按真实路径解析；缺的是“问题真的送进在线执行主控”的证据，以及能抓住“只记录不送达”的反例。按规则不开第三轮审查，由实现者补证：

- 端到端测试加场景 `untrusted-online`：照 T-216 的做法，在项目终端里真起一个 Claude Code（脚本化接口），经 `a2a request executor` 申请、批准成为执行主控，再派 worker 走不可信回合。检查 `issue_reached_executor_cli`：执行主控 CLI 发给模型的请求里带着这条问题的编号，且收件箱回执指向主控终端。
- 第一次在线运行（`green/e2e-untrusted-online.json`，`407b29bed`）FAIL：主控其实已收到（`controller_requests: 1`），失败的是我要求数据库最后一条回执为 delivered。收件箱只在交接时写一次回执（当时是 queued），之后的状态由 `inbox_list` 现算、不追加行，所以是检查写错。改为回执 queued 或 delivered 且指向主控终端（`7f01355c9`）。
- `green/e2e-untrusted-online-r2.json`（`7f01355c9`）PASS，全部 7 项检查通过，包括 `issue_reached_executor_cli`。
- `mutants/e2e-online-no-delivery-r2.json` FAIL，只在 `issue_reached_executor_cli`、`issue_sent_through_inbox` 两项（主控收到 0 次、没有回执），其余 5 项照常通过。
- `red/e2e-untrusted-online.json`（`94abc1347`）FAIL：窗格不结束、没有问题、主控收不到、回收与再派都失败。
- 产品源码自 `8e546df51` 起没有再改，`cce9e9635` 以后只改测试与证据。

## 设计自查（design-integrity，实现者自查）

- 没有新增 fallback、重试或兼容分支。真不可信的回合不放宽：请求仍不执行，只是改为经中继原有的结果记录记成拒收，以后同一请求只重放拒收。
- `turnRefused` 是门禁的新方法，只由后台在不可信回合的 Stop 里调用，不进命令表，worker 与主控调不到。
- `turnRefused` 不取任务操作锁：它不改任务状态，只追加一条问题记录（自身一个数据库事务）；收件箱投递自带按条目的锁，投递失败记为回执、不抛错。若同时有人 `revise`，问题可能指向刚被撤销的 attempt，只是多一条说明，不改状态。
- attempt 已不是当前的（已撤销或换人）时只记 `turn_refused_not_current` 事件、不发问题：这种请求本来就会按 stale 拒收。
- `turnRefused` 自己抛错时（读任务或写问题失败），Stop 的转交按原有路径记 `stop_transfer_failed`、窗格标失败；拒收已先写进中继记录，重放也不会执行。这与其他转交失败的处理相同，没有另开路径。

## 重跑命令

在 `workbench/tests` 下：

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 test_t251_untrusted_turn_e2e.py --scenario untrusted --revision b013c477a --summary /tmp/t251-untrusted.json
```

`--scenario` 取 `cd`、`compact`、`untrusted`；`--revision <commit>` 从 Git 取那一版源码；`--mutant <名字>` 在当前源码副本上打变异。单元测试：`node workbench/tests/test_t251_hook_cwd.ts <源码根目录> <summary.json>`。

## 夹具状态

`red/e2e-cd.json` 是 cd 红态的第一版：等待条件写成等 `turn_end_signal`，旧代码在记这条事件之前就拒了 Stop，所以超时；改为等 Stop 的 `hook_received` 后重跑为 `red/e2e-cd-r2.json`。

测试夹具都在 `/private/tmp/t251-*`，跑完后已删除（含审查后的重跑与探针共 25 个目录，每个 250 个左右文件，12 MB 到 334 MB，共约 3.9 GB；带 `--revision` 的夹具含一份源码与依赖，所以更大）。草稿目录里的回归输出目录也已删除。仓库里只留本目录的文本摘要。
