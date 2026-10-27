# T-198 独立只读审查

STATUS: NO_GO

TARGET: `/Users/luckye/Documents/Code/a2a`，HEAD `bb447be5010a825ffa36dfe56b714682037a520c` 上的未提交候选。审查的七个源码／说明文件与本目录 `change.diff` 的对应部分逐项一致，审查结束时这些差异和 HEAD 均未变化。测试副本与仓库原件字节一致。依据为 T-198 任务卡与 T-196 第 2 条，T-197 仅核对与本轮相关的交互。

RELEASE: NO_GO

## FINDINGS

### [P1] 打回没有撤销此前的放行，旧候选重现后可以绕过主控的最新决定

位置：`workbench/src/gates/core.ts:4011`，关联 `:2143`、`:4256`。

`accept` 把判断存入 `task.out_of_card_judgement`，但后续 `reject` 只记事件并调用 `rejectDelivery`，没有撤销这份判断；提交另一个候选时也没有清除它。`outOfCardJudged` 只检查存下的候选 SHA 及路径包含关系，不检查后来的打回。

已在当前候选的生产门禁入口 `A2AGates.call`、真实 Git 和 SQLite 上复现以下流程，worker 运行观察与独立审查边界由夹具控制：

1. C1 修改 `allowed.txt` 和卡外的 `extra.txt`，验收后主控先 `accept` C1。
2. 集成前主控改变决定，`reject` C1，理由要求删除 `extra.txt`。
3. worker 提交 C2，仍含 `extra.txt`；验收后主控再次 `reject`。
4. worker 把自己的分支恢复到 C1，再以同一 attempt 显式交付。C1 不等于刚被打回的 C2，因此通过 `repair_requires_new_candidate`。
5. 重验后主控没有重新放行，`integrate` 却返回 `ok:true`，任务成为 `accepted`，`main:extra.txt` 实际存在。

证据：`lifecycle-06.json` 的 `rejected_candidate_reappears`；完整相关事件见 `lifecycle-events-06.json`。其中最终 C1 为 `c074ef1c0b1ad0ac5ab07f710f7c3a9c26a20c5e`，最终记录仍使用理由 `Initially accepted.`；评分正确记下两次 `path_boundary` 打回，却没有阻止这次错误放行。作为对照，尚未放行的 C2 集成确实被 `out_of_card_unjudged` 拒绝。

建议：在主控打回时撤销当前放行；在交付切换候选及 `invalidate` 时明确结束旧判断的有效期，避免旧 SHA 重现时恢复旧权限。判断应属于当前有效的 attempt／规格／任务卡及文件集合。保留同一 attempt、同一候选与清单因工作分支前进而重验时的放行，不能简单要求 `verification_id` 永远相同。将上述 C1 → C2 → C1 场景加入真实后台回归；验收预期是最后一次集成仍返回 `out_of_card_unjudged`，再次明确放行后才允许写入。

### [P2] 主控操作说明没有写明自动 run 会因卡外未判断而暂停

位置：`workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md:27`、`workbench/src/terminalCli.ts:37`；同类表述见 `workbench/README.md:219`。

这些段落仍无条件说明主控身份结束或额度用完后，run 自己集成并记“未评分”，skill 还称会一直等到任务结束才返回。新增卡外门禁后，真实代码走相同 `integrate` 检查；未放行时，run 返回 `out_of_card_unjudged`、`outcome:paused`，任务保持 `verified`，worker 未回收。该结果已在 `lifecycle-06.json` 的 `run_with_ended_controller` 复现。

README `:453` 已写明“自动集成时也停在这里”，但上述操作入口没有同步限定。主控照第 6 步派发后离开，会收到暂停而不是承诺的集成结果。

建议：在这几处统一写明自动集成仍须已有有效的卡外放行；没有判断时暂停并保留现场，待主控重新取得角色后判断、集成。保留验收文件、Git 元数据等硬拒绝条件。

## EVIDENCE：已检查的行为

| 项目 | 结果与证据边界 |
| --- | --- |
| 卡外文件不再直接终止验收 | 当前源码 `checkPaths` 记录 `verification.out_of_card` 与事件；本轮隔离探针进入 `verified`。未判断时集成拒绝、空白理由拒绝、带理由后集成均已运行。 |
| 工作分支前进后的重验 | 本轮实际推进 `main`，触发 `integration_compare_failed` 和新 verification；同一 C、同一清单的原放行仍有效，最终集成成功。新 verification ID 与判断记录中的旧 ID 不同。 |
| 新候选与旧判断 | C2 不会直接沿用 C1 的放行；C1 后来重现却会恢复旧放行，见 P1。当前比较允许清单子集，不是集合相等；本轮未据此单独声称存在第二条可达绕过。 |
| revise、revoke | `invalidate` 不清除判断，存储匹配也未绑定 attempt／规格／任务卡。分别经公开命令撤销或采用 v2、回收旧 attempt、重新派发，再重交旧 SHA；两次都先被 `git_metadata_changed` 拦截，因为保留的旧 worker 分支持有该提交。未观察到这两条流程发生错误集成，也不能据此声称判断本身已经失效。 |
| 冲突返工 | 静态追踪：冲突进入 `rework`；原 attempt 返工必须提交不同于 `prior_candidate` 的提交，重新跑门禁并作新审查；新 C 不匹配旧判断。替换 worker 的流程经过 `invalidate`。本轮未实际注入合并冲突；旧判断残留的问题归入 P1 的生命周期修复建议。 |
| 主控离开后的 run | 本轮用受控的 ended 主控状态运行生产 `run`；未放行的卡外文件使其暂停，工作分支未写入该文件。没有绕过判断；说明问题见 P2。 |
| 验收文件同时在卡外 | 本轮修改未被 allow 的 `oracle.py`，生产 `verify` 返回 `oracle_modified` 并生成 `repair.check:oracle`。没有交给主控放行。 |
| Git 元数据守护 | 本轮改 worker 仓库 config，`verify` 返回 `git_metadata_changed`，进入打回，`repair.check:path_boundary`。检查仍在 `checkPaths` 之前。 |
| 打回、worker 文案和计分 | reject 继续走 `rejectDelivery`；本轮事件与最终评分核对到 `path_boundary:2`。`panes.ts:1281` 对 `out_of_card_rejected` 使用主控未放行的开头，普通失败保留原开头；提供的 `green.json` 记录了 worker 实际收到的清单、理由和完整反馈。 |
| 任务页与旧事件 | 运行生产 `taskHistory`：新卡外事件为 `passed:null` 并显示待主控判断；放行／打回包含清单与理由；旧 `forbidden` 事件仍显示失败及旧清单。只验证数据投影，没有运行 Electron 页面。 |
| 审查员与调用权限 | `core.ts:2605` 明确列出卡外清单并要求逐项判断。新命令加入请求 schema，终端的任务命令集合由此生成；worker 的调用仍受 `request` 的调用者校验限制，不因新增命令获得放行权限。这部分为静态检查，原绿态提供了审查员输入清单的运行证据。 |
| T-197 交互 | accepted attempt 不再占路径，只影响认领；T-198 的集成仍受判断与 Git 合并约束。本轮未重验 T-197 的完整行为，不替其另行审查作结论。 |

## COUNTEREXAMPLE：提供的测试与红／绿／变异证据

- 已读完 `test_t198_out_of_card_e2e.py`，本目录副本与仓库原件一致。它通过后台 socket、项目终端身份、真实 Claude Code 交互进程、Git 和门禁观察结果；模型接口是脚本化假服务，审查结论也是夹具输入。预期卡外路径来自外部 `TASKS` 输入，未从生产常量或实现生成答案。
- `red-bb447be50.json` 在业务断言 `out_of_card_waits_for_judgement` 失败，路径检查直接返回 `path_boundary_failed`。`red-01-oracle-order.json` 是早先断言顺序先触发验收文件检查的红态，不能替代调整顺序后的红态；两个原件均保留。
- `green.json` 记录 7 项 PASS：等待判断、验收文件仍拒收、审查员得到清单、未判断不能集成、空白理由拒绝、带理由放行并集成、打回反馈到 worker。该记录的 `revision:null`，没有独立冻结源码的标识，因此本轮不把它单独当成当前候选的完整通过证明。
- 两个变异均在业务断言被拒绝：`boundary-still-fails` 失败于等待判断，`integrate-unjudged` 失败于未判断不能集成。JSON 的汇总状态写作 `INCOMPLETE`，其中的实际错误均为对应断言失败，不是缺依赖或进程崩溃。
- 新测试 `:313` 至 `:339` 只覆盖单向 accept／reject，没有覆盖放行被撤销后旧候选重现。上述已知坏行为能通过现有七项检查；本轮独立探针将其判为 FAIL，退出码为 1。

## 做过的检查与命令

所有新文件、Git 夹具、数据库与日志均在 `/private/tmp/t198-review1` 下；没有修改目标仓库、checkout、切分支、提交或操作用户后台。探针中的提交和分支操作只发生在本目录内新建的隔离仓库。

```sh
# 候选与规范检查（目标仓库内只读）
git -C /Users/luckye/Documents/Code/a2a rev-parse HEAD
git -C /Users/luckye/Documents/Code/a2a status --short
git -C /Users/luckye/Documents/Code/a2a diff -- workbench/src/contracts/a2aGates.ts workbench/src/gates/core.ts workbench/src/gates/taskHistory.ts workbench/src/panes.ts workbench/src/terminalCli.ts workbench/README.md workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md

# 本轮完整探针；报告路径必须尚不存在
cd /private/tmp/t198-review1
node lifecycle-probe.mjs lifecycle-06.json > lifecycle-06.log 2>&1
# 结果：NO_GO，退出码 1；8 个场景记录，7 项局部 PASS、1 项 FAIL。
# 重现时将两个 lifecycle-06 文件名改成新名称，保留原证据。

node /Users/luckye/Documents/Code/a2a/workbench/src/terminalCli.ts help > terminal-help.txt
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a
```

候选起始差异与身份在 `candidate-at-start.diff`、`candidate-at-start.json`，结束比对在 `candidate-stability.json`；未使用散列。`project-map-status.txt` 为结束检查：Problems 0，stale living docs 1，退出码 1；所指为本轮之外的 `findings/README.md` 与 `findings/2026-10-27-native-session-ids.zh-CN.md`，未擅自修订。

探针探索产物也保留：`lifecycle-01` 为缺 non_goals 的任务卡拒绝；`02` 为夹具没有初始化 relay 表而在评分时报错；`03.log` 为夹具导入名错误；`04` 已复现 P1，随后重交旧提交被 Git 守护拒绝；`05` 已复现 P1，随后验收文件夹具在首次交付后又换候选，被 `candidate_conflict` 拒绝。它们不是完整验收通过记录。`06` 修正夹具设置后完成上述八个场景，并仍检出 P1。当前脚本对应 `06` 的重现命令。

## LIMITATIONS

- 未重跑可选的 Claude Code 全流程脚本。其夹具固定在 `/private/tmp` 创建目录，原生运行时还固定创建 `/tmp/a2a-requests-*`；为遵守本轮“运行产物只写本目录”的要求，没有改动生产路径来迁就运行。提供的红／绿／变异原件只作既有证据审计，未称为本轮重跑结果。
- 本轮新增探针控制 worker 的原生身份观察、主控 ended 状态与独立审查成功：`requestReview`／`requireReviewed` 在夹具中替换。它证明范围判断、交付生命周期、Git 集成和持久化结果，不证明原生 CLI 权限、真实模型判断质量或真实审查员全流程。生产 `out_of_card`、`outOfCardJudged`、submit、verify 的机械检查、integrate、run 与评分代码均未替换。
- 未运行真实合并冲突、后台重启、Electron 视觉检查及完整回归；这几项不能报告 PASS。修复 P1 后应在真实后台补充同一反例，并保留原红态及正例：同候选／同清单的工作分支前进重验仍能集成。
- 审查范围内候选稳定；项目存在其他脏改动和范围外 living doc 告警，本报告不对它们作合并背书。

结论：需修复
