# T-121 第 4 轮复审（候选 06276f2a8，对比 99c3c9fba）

## 结论

**可合并，但有前提**：RESULTS.md 要补齐（目前停在 fa3ee8c67），下面两条测试缺口要补上，或者如实写成"只有探针覆盖"。本轮没有发现阻塞级的产品缺陷。

review-03 的 B2、S1'、S2'、建议 1 和建议 2 都修好了，我用真实后台的探针逐项核对过。新改动里有两个分支，e2e 测试拦不住它们的变异体（见应修 S3、S4）。按项目规则"新测试必须在已知坏实现上失败"，这两条在 RESULTS 里不能写 PASS。

我全程只读，没有改仓库。临时文件都在 `/private/tmp/t121-rev04/` 下。工作区里有一个未跟踪的 `evidence/2026-10-21-batch19/T-121/ui-07/`，不是我写的，我没动。进程里还有 10 个 `/private/tmp/t118-ui-*` 的 Enchanted Test 进程，是早先 T-118 UI 测试留下的，不是我启动的，我也没动。

## review-03 各项核对

**B2 已修好**，位置 `workbench/src/daemon.ts:178-182`、`225-237`、`250-252`。探针结果在 `/private/tmp/t121-rev04/probe-result.json`：

- 操作员保存的草稿没有归属。终端对它执行 card_show、create、card_save v1，都返回 `card_draft_not_owned`；card_save v0 返回 `card_version_conflict`。所以终端不能以 v0 抢占已存在的无主草稿：门禁的版本检查（`gates/core.ts:3297`）挡住了。
- 两个项目的终端同时首存同一个 id，跑了 10 次：每次只有一方成功，`card_draft_owned` 事件各只有 1 条，归属与胜方一致。不过这 10 次里，败方都在预检阶段就被拒（返回 `card_draft_not_owned`），没有出现两边都过预检的交错。读代码看，就算两边都过了预检，败方也会在门禁得到 version_conflict，不会写归属事件，结果仍然一致。
- 终端占用某个 id 后：别的项目终端 v1 返回 `card_draft_not_owned`，操作员 v0 返回 `card_version_conflict`。
- 草稿归属和 create 之后的任务归属一致：create 要求 草稿归属 = 角色所在项目 = input.project。
- review-03 说的预检与执行之间的时间差（TOCTOU），在终端之间已经封住：别的项目终端不能 create 本项目的草稿。

**S1' 已修好**（`daemon.ts:193`）：先校验 wait_seconds 再建申请。e2e 的 `request_without_wait_refused` 核对了没有留下申请记录。

**S2' 已修好**（`daemon.ts:198-202`、`647`）。

- 先关闭再批准，跑 20 次，20 次都返回 `request_not_pending`。
- 先批准、随即关闭（间隔 0–28ms），跑 15 次，15 次都是 `ended/asker_gone`，role 为 null。
- 只发请求就立刻关闭，跑 10 次，0 次留下申请。
- 探针结束时后台存活，没有 client_connection_error 记录。
- 剩下一个理论窗口：轮询定时器先于 close 事件触发、而此时对端其实已经死了的情况下，循环会返回 approved，在 finally 里清掉 asker.gone，再把结果写进已死的连接，角色留在 approved。没有确认回执（ack）的协议做不到完全消除这个窗口，我也没有复现出来。建议在 RESULTS 里列为已知边界。

**建议 1 和 2 已修好**（`daemon.ts:173-174`）：终端的 answer_issue、answer_issues、attach、run 都返回 `role_command_not_scoped`，e2e 中是 `user_answer_and_run_commands_not_for_terminals`。我顺带核对了还留在放行清单里的 `disposition`：`core.ts:3273` 传入的 actor 是 "executor"，dismiss、snooze、reopen 要求 user，关闭 blocking 问题也要求 user（`core.ts:742-746`），所以不会被记成用户的处置。

## 阻塞

无。

## 应修

**S3：`approved → end(asker_gone)` 分支没有 e2e 覆盖**

- 位置：`daemon.ts:201`。
- 我把这一行删掉做成变异体 `approved-not-ended`，用 e2e 副本 `/private/tmp/t121-rev04/mtest.py` 跑：**PASS，43 项**，变异没有被拦下。变异确实生效了：变异定位断言要求唯一匹配，path_first 指向变异源码副本。
- 同一个变异体用我的探针跑，"批准后随即关闭"一项变成 `approved`、role=ideation（`/private/tmp/t121-rev04/probe-mutant-result.json`）。
- 原因：e2e 的 7b（`test_t121_role_request_e2e.py:350-366`）和 9 都是关闭或杀进程发生在批准之前，走的只是 pending 撤回分支。
- 要补一个"先批准、随即关闭"的检查，再配上对应的变异体。

**S4：card_save 遇到"别的项目终端所有的草稿"这个分支没有 e2e 覆盖**

- 位置：`daemon.ts:234`。
- 删掉这一行做成变异体 `foreign-owned-save`，e2e 同样 **PASS，43 项**。
- 原因：e2e 里的 `other-2` 是操作员存的，没有归属，所以 card_save_next 是被 235 行（无主且 v≠0）拦下的，不是 234 行。
- 我的探针覆盖了这一分支：`other_terminal_after_squat` 返回 `card_draft_not_owned`。
- 要补一个"另一个项目的终端先存，本项目终端再追加"的检查。

**S5：变异体 drafts-unowned 的注释和实际改动不符**

- 位置：`test_t121_role_request_e2e.py:96-99`。
- 注释写的是"第二版候选的规则：任意未创建的 id 都开放"，但实际只删了 card_show 和 create 的归属检查，card_save 的两条检查还在（我和已提交的 -10 文件都得到 `card_save_next=card_draft_not_owned`）。
- 完整的旧行为由 `--revision 99c3c9fba` 证明。RESULTS 里不要把 drafts-unowned 说成"恢复了第二版规则"。

## 建议

1. **close 监听器里抛错会让后台挂掉**（`daemon.ts:647`、`198-202`）。`asker.gone` 在 `connection.once("close")` 里调用 `roleRequests.withdraw/end`，也就是同步的 `store.event` SQLite 写入。如果这次写入抛错（磁盘满、数据库被锁等），就成了 EventEmitter 监听器里的未捕获异常。我 grep 过，没有 `uncaughtException` 处理，进程会退出。这和请求路径的做法不一致：请求路径把写入失败转成 `event_write_failed`，并标记 observer 为 failed。我没有实测，触发条件也少见。建议按请求路径的做法记下故障，而不是吞掉错误。
2. **草稿归属写在 orchestration store，卡版本写在 gates 库，两次写入不是原子的**（`daemon.ts:250-252`）。门禁成功之后，如果 `store.event` 抛错或者后台被杀，这个 id 就永久没有归属。之后本项目终端对它 show、create 都会被拒，v0 也会冲突，这个 id 对终端来说就废了。不会越界，但应该写进已知边界。
3. **非终端调用方（操作员、受管主控窗格）不受草稿归属约束。** 探针里，操作员能用 proj 终端的草稿在 other 项目执行 create（ok），之后 proj 终端 status 返回 `role_project_mismatch`。这符合"操作员可信"的威胁模型，但要在 RESULTS 里写明：归属只约束终端角色。
4. **任务 id 是全局命名空间。** 一个终端主控可以对任意尚未存在的 id 做 v0 占用，别的项目之后就用不了这个 id。这是 B2 修法固有的取舍，应该列为已知边界。
5. `draftOwner` 每次都按 `type + json_extract` 扫一遍 orchestration_events，而这张表没有 type 索引（`store.ts:31`）。事件多了之后会变慢，目前只是性能隐患。
6. `daemon.ts:7` 的 `type Asker` 插在两条 import 之间，属于格式问题。

## RESULTS.md 必须写明的事实

- 已提交的 RESULTS 还写着"候选 fa3ee8c67""总状态：待复审""review-02（待填）"（`RESULTS.md:5`、`7`、`91`）。需要：
  - 补上第 3 版候选 99c3c9fba 和第 4 版候选 06276f2a8 两行；
  - 补上 review-02、review-03、review-04 的结论；
  - 补上 green-07～10、mutant-*-08/09/10、red-candidate3-10、regress-*-03/04/05、ui-06 这些已提交文件的引用。
- 第 4 版候选的 green 结果：PASS，43 项。红态证据：`--revision 99c3c9fba` 失败在 `other_project_draft_refused`（card_show、card_save_next、create 都返回 ok）。
- 变异体各自的失败点：
  - `no-withdraw` 失败在 7b 第 2 轮的辅助断言"后台没有出现待批准的申请"（第 1 轮已被批准，角色被占用），不是失败在 `closed_asker_cannot_be_approved` 这个具名检查。
  - `drafts-unowned` 只回退了 card_show 和 create 的归属检查（见 S5）。
- S3、S4 的两个变异体都能通过 e2e。两项要么补测试，要么写成"只有探针覆盖"，不能写 PASS。
- 已知边界：
  - 批准与关闭之间的残余窗口（无确认回执）；
  - 草稿归属只约束终端，操作员和受管主控不受约束；
  - 任务 id 全局唯一，终端可以占用尚未使用的 id；
  - 归属事件与卡版本不是原子写入；
  - close 监听器里写入抛错会让后台退出；
  - 原有边界保留：操作员凭据可读，界面批准防不住有意绕过的 agent。
- `ui-07/` 还没有提交。如果要引用，要写明它对应哪个构建和哪次提交。

## 我实际运行的命令和结果

1. `python3 workbench/tests/test_t121_role_request_e2e.py --summary /private/tmp/t121-rev04/green.json`：**PASS，43 项**，退出码 0。
2. `--mutant drafts-unowned --summary /private/tmp/t121-rev04/m-drafts.json`：**INCOMPLETE**，退出码 1，21 项后失败在 `other_project_draft_refused`（card_show 和 create 返回 ok，card_save_next 仍被拒）。path_first 是变异源码副本，变异确实生效。
3. `--mutant no-withdraw --summary /private/tmp/t121-rev04/m-nowd.json`：**INCOMPLETE**，退出码 1，35 项后失败在"后台没有出现待批准的申请 ('proj','ideation')"。
4. `--revision 99c3c9fba --summary /private/tmp/t121-rev04/rev3.json`：**INCOMPLETE**，退出码 1，21 项后失败在 `other_project_draft_refused`（card_show、card_save_next、create 都返回 ok）。
5. 探针 `python3 -I /private/tmp/t121-rev04/probe/probe.py /Users/luckye/Documents/Code/a2a /private/tmp/t121-rev04/probe-result.json`：退出码 0，结果见上文。
6. 同一个探针跑在变异源码 `/private/tmp/t121-rev04/mutsrc`（删掉 `daemon.ts:201`）上：批准后随即关闭的情况变成 approved/ideation，说明探针能区分这个变异。
7. e2e 副本 `python3 /private/tmp/t121-rev04/mtest.py --mutant approved-not-ended` 和 `--mutant foreign-owned-save`：两者都是 **PASS，43 项**，变异都没有被拦下（S3、S4）。
8. 用 pgrep 查过，我启动的后台都已停止。

没跑的：

- 变异体 `pending-authority`、`history-in-zdotdir`、`zdotdir-dropped`、`refusal-unrecorded`、`task-widens-scope`；
- T-107、T-109、T-111、T-118 回归；
- 打包版 GUI 和真实 Claude、Codex（ui-06、ui-07 没有复核）；
- `project_map.py status`；
- close 监听器里写入抛错（只读了代码）；
- 两个首存请求真正交错着都通过预检的情况（没有复现出来，只读了代码）。