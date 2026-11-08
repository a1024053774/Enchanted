# T-251 证据摘要（2026-11-07）

分支 `fix/t251-untrusted-turn`，父提交 `94abc1347`。修复提交 `b013c477a`（源码、测试、技能），`ab912013b` 只改测试读 `status` 的字段和票据。`b013c477a..ab912013b` 之间 `workbench/src` 没有改动。

测试环境：真实编排后台、门禁与 Claude Code，Messages API 由脚本应答，零次厂商模型调用，不起 Electron（`workbench/tests/scripted_claude.py`）。hc 缓存用 `ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache`。

## 三个场景

| 场景 | 做法 | 修前（`--revision 94abc1347`） | 修后（`--revision b013c477a`） |
| --- | --- | --- | --- |
| cd | worker 在 Bash 里 `cd` 进工作区子目录后写文件、submit | `red/e2e-cd-r2.json` FAIL：`delivered_at_turn_end`、`no_hook_judged_foreign` | `green/e2e-cd.json` PASS |
| compact | 回合中途送一条与真实记录同形的 `source: "compact"` SessionStart，再 submit | `red/e2e-compact.json` FAIL：同上两项 | `green/e2e-compact.json` PASS |
| untrusted | 回合中途送一条 cwd 在工作区以外的钩子（真不可信），再 submit | `red/e2e-untrusted-r2.json` FAIL：窗格停在 busy，Stop 被拒 `current_turn_untrusted`，回收被拒 `worker_working`，再派被拒 `already_claimed`，`status` 里没有问题 | `green/e2e-untrusted-r2.json` PASS |

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
| `turn-stays-busy` | 拒收后窗格仍记为 busy | `mutants/e2e-turn-stays-busy-r2.json` FAIL：`turn_ended_not_running`、`old_attempt_reclaimed`、`new_worker_dispatched` |

单元测试 `workbench/tests/test_t251_hook_cwd.ts`：`red/hook_cwd.json`（父提交）拒了子目录、`..` 回到工作区内、extra 目录及其子目录、Codex 子目录；`green/hook_cwd.json` 全过，反例（工作区外、前缀相同的兄弟目录、`..` 逃出、相对路径、缺 cwd、未授予的 extra 目录）都拒。三个单元变异：`mutants/unit-prefix.json`（字符串前缀比较）、`unit-nonormalize.json`（不规范化 `..`）、`unit-exact.json`（严格相等）各判失败。

## 回归

- `green/t207_interrupted_turn_hooks.json` PASS（被打断回合的钩子语义）。
- `regression/t157_turn_identity.txt` PASS；`relay_role.txt` PASS；`relay_core.txt` 无失败；`native_final_read.txt` 无失败。
- `regression/relay_scope.txt` INCOMPLETE，4 项失败；在父提交 `94abc1347` 上同样 4 项失败（`relay_scope-parent-94abc1347.txt`），是已有问题，不是本票回归。
- 没跑全量测试：本票改动集中在 Claude worker 的钩子与 Stop 路径和一个新的门禁方法，上面这些测试覆盖这些路径。

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

测试夹具都在 `/private/tmp/t251-*`，跑完后已删除（14 个目录，每个 250 个左右文件，12 MB 到 334 MB，共约 2.5 GB；带 `--revision` 的夹具含一份源码与依赖，所以更大）。草稿目录里的回归输出目录也已删除。仓库里只留本目录的文本摘要。
