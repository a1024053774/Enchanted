# T-075-2 结果

状态：**PASS（T-075-2 本卡）**。修复版本 `3386c4cd3a4e44b5b58d5a46a780fb99f9aa637a` 的 52 项正例测试全部通过，五个变异体均触发业务失败、0 errors。一次独立审查原始结论为 FAIL；唯一 P2 已先取得真实业务红态，再以最小修复转绿，执行主控在 `⟦主控 #22⟧` 明确审过并同意修复 diff。原审查与失败记录原样保留，没有第二轮审查。

**T-075-2 完成，待后续卡，待主控关闭。** T-075 保持 open；本卡不证明编排后台、真实 Codex 窗格或 Electron 可用。

## 版本与范围

- task：T-075-2；T-075 `ready_rev: 2`；派发身份：`s12-t075-2`。
- 任务原始起点：`e5e7dbb841131935aac0bd061649a55e7a1e7d20`，不因主控后续提交而移动。
- 实现轮次开始 HEAD：`1bd31350cce60085b35b66047251f735c2e0358d`。实现/审查候选为 `1273b17e933cd0bb279a20e6b237dbbd2f054db3`；最终代码版本为 `3386c4cd3a4e44b5b58d5a46a780fb99f9aa637a`。两次提交均含九项自动尾注。报告与证据收尾提交不改变该代码版本，提交号在交付消息给出。两轮变异源码分别在 `mutants-01/`、`mutants-02/`，不覆盖。
- 使用本机 Node 26.5.0、Git 2.52.0、Python 3.11.14；没有联网下载、安装、构建或新增依赖，未改用户全局或共享 checkout 的 Git 配置。旧验收脚本只配置各自新建的临时 Git 夹具。
- 夹具和工作目录位于 /tmp；运行证据归档在本目录。没有读取或写入正式工作台数据目录，也没有操作用户 Herdr server。
- 执行器 CLI 词表按决定 01 固定为大小写精确的 **`Claude Code`**、**`Codex`**；已实现校验，其他写法拒绝。
- 公开错误码继续使用 `oracle_failed`，仅为保持公开错误预期；事件保存失败的完成条件序号与真实退出码。不保留旧 oracle 注册入口。

## Git 探针的三轮事实

| 轮次 | 结果 | 原因、证据及处理 |
| --- | --- | --- |
| [normal-01](probe-git-normal-01/result.json) | INCOMPLETE：协议组合失败 | 同一事务更新检出工作分支并显式 symref-verify HEAD，Git prepare 拒绝重复更新 HEAD；按决定 01 停止，完整现场保留。技术答复见决定 02。 |
| [normal-02](probe-git-normal-02/result.json) | INCOMPLETE：fixture-error | 独立 symref-verify 成功；新事务 prepare 成功，实际有分支锁与 HEAD 锁。并发 symbolic-ref 被正确拒绝，exit=1；worker 错把夹具预期限定为 128，尚未到后续场景就失败。失败不是协议缺陷。 |
| [normal-03](probe-git-normal-03/result.json) | PASS：正常/拒绝协议 10/10 | 按决定 03 将相关夹具判断修正为任意非零拒绝，并继续核对原 HEAD、分支、索引、文件及 reflog 未变。使用新脚本和标签，前两轮记录未覆盖。 |

第三轮的十项：独立 symref-verify；实际分支/HEAD 锁及并发拒绝；主 worktree 干净快进；linked worktree 干净快进；未被检出的工作分支只更新引用；无冲突暂存/未暂存/未跟踪修改保留；覆盖型暂存修改拒绝；覆盖型未暂存修改拒绝；覆盖型未跟踪文件拒绝；prepare 前引用已变 X 时 CAS 拒绝。

第三轮完整命令与 stdout/stderr/exit 在 [commands.json](probe-git-normal-03/commands.json)，字面预期与检查结果在 [assertions.json](probe-git-normal-03/assertions.json)。每个场景都保存操作前后 refs、HEAD、索引、文件原文与 reflog。原始目录为 `/tmp/a2a-t075-2-git-9ph3_ag3`，归档为 [artifacts.tar.gz](probe-git-normal-03/artifacts.tar.gz)。

重现时使用新标签：

```sh
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/card-2/probe-git-rev3.py probe-git-normal-repro-04
```

首轮和第二轮分别用 `probe-git.py`、`probe-git-rev2.py`，脚本保留不改；更换一个不存在的 `probe-git-*` 输出标签即可重现。现有标签拒绝覆盖。

## HEAD 锁与 reflog 的结论

**PASS（本机 Git 2.52.0 的已测场景）**：在实际检出的目录启动 `update-ref --stdin`，只排队工作分支 `M G` 更新时，prepare 同时创建 `refs/heads/main.lock` 和该 linked worktree 的 `HEAD.lock`。此时并发 update-ref 与 symbolic-ref 均被拒，abort 后 HEAD、分支和文件保持原样。证据见 [实际锁](probe-git-normal-03/branch-update-locks-prepared-locks.json) 和该轮完整命令。

成功集成时，工作分支 reflog 与实际检出目录 HEAD reflog 各增加一条。主目录、linked worktree 与无冲突脏目录均已读回确认；未检出的工作分支没有修改其他 detached 目录。

因此在已测场景的 prepare→commit 区间，HEAD 切换被 Git 自己的锁阻止，不再把此区间写成无保护窗口。**仍有读回 HEAD→prepare 的窗口**；按决定 02/03，门禁应在操作锁内核对检出目录身份，并沿用单机、参与者可信的冻结前提，不新增策略、兜底或第二条集成路线。现有探针在夹具操作锁内验证该顺序，不能替代未来对产品门禁的验收。

本地依据仅包括 Git 2.52.0 手册 `/opt/homebrew/opt/git/share/doc/git-doc/git-update-ref.html`、`git-read-tree.html` 和上述真实探针，没有联网资料。

## 已完成的中断探针交接

执行主控已运行原探针脚本，副本为 [outside-sandbox-probe-01.sh](outside-sandbox-probe-01.sh)，原始收据为 [outside-probe.keY5Us](outside-probe.keY5Us/stdout.txt)。其实际命令见该目录 `command.sh`。当前 `outside-sandbox.sh` 已改为后续产品验收脚本，不能把它当原探针的历史版本。

```sh
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/card-2/probe-git-interrupt.py --controller-run --label probe-git-interrupt-repro-02
```

脚本只运行 [probe-git-interrupt.py](probe-git-interrupt.py) 的三个窗口：目录更新前；目录已更新但 CAS 前；CAS 已完成但记账前。每个场景在 /tmp 新建仓库与 linked worktree，经 ps 核对本次启动的 owner CLI 的 PID、PPID 和 argv 后，只对该 CLI 发送 SIGKILL；不向 Git 子进程发信号，不删锁。原意图、注入点、命令 I/O、信号记录、引用和目录状态均保留。新进程从原意图恢复，并再重放一次，要求只补缺失的 CAS/reflog，CAS 后不得再次写 Git。

中断探针结果为 PASS，三个窗口、182 条断言全部通过。worker 已回读 [interruption-summary.json](probe-git-interrupt-outside-probe.keY5Us/interruption-summary.json)、断言与六份恢复/重放记录，核对原意图未变、只补缺失 CAS/reflog、最终目录干净。原目录 `/tmp/a2a-t075-2-git-1_2u5xx9` 及完整归档保留。它证明 Git 协议窗口；产品门禁的新恢复窗口另行验证。

## 候选实现与本地证据

任务卡命令已接入唯一 CLI：生成/校验/保存/指定版本读回、注册快照、认领时起点和唯一写入者绑定。受管 create 删除旧三个参数；路径检查同时覆盖 B→C 与 G→M；完成条件以 argv 在 M worktree 执行；九项尾注中 Task/Attempt/Session/Role 决定归属。无尾注通过既有追加式用户输入层保存 action 与派生介入，来源为“推断：缺尾注”，同 attempt/commit 去重。提交文件数、增删行数及检查结果写入原始事件。

集成只操作项目工作分支；先持久原意图，用已验证的 Git 事务与双树快进保护检出目录，并核对真实读回。原 refs/a2a/integration 不再读取或写入；已有历史引用保持不动。操作锁、fence、旧 attempt、CAS 期望旧值和中断恢复的原门禁仍保留。

| 证据 | 结果与范围 |
| --- | --- |
| `baseline-bindings.json`、`red-initial-01/`、`red-expanded-01/`、`red-additional-01/` | 固定原始起点副本，14 个不同新测试在起点失败。失败位置是新卡入口不存在，属于新接口 expected-red，不冒充路径/尾注行为已到达。全部原始输出保留。 |
| `tracer-01/` | PASS；分叉 G/C 合并为 M，独立完成条件同时读到两边内容；验收前分支仍 G，集成后分支和目录到 M，重放无第二次 reflog。已按决定 01 回报 `T-075 TRACER READY`。 |
| `green-initial-01/` | 首批 7 个测试 PASS。 |
| `green-expanded-01/` | 扩展 12 个测试 PASS。 |
| `green-additional-01/` | ticket 来源/修订与非快进 Git 结果两个新增测试 PASS；脏目录测试追加核对引用后再核对错误码，复跑 PASS。和前项合计 14 个不同测试。 |
| `green-coop-01/` | 中间候选经卡 1 runner 的交付 8/8 PASS；修复版完整三套回归见下方最终验收表。 |
| `mutant-path-01/` | 1 个业务失败、0 errors：取消路径限制后越界 verify 被错误接受。 |
| `mutant-trailer-01/` | 1 个业务失败、0 errors：放行别的任务尾注后 verify 被错误接受。 |
| `mutant-dirty-01/` | 3 个业务失败、0 errors：跳过目录保护后，在三种脏修改下工作分支错误地从 G 到 M。 |
| `mutant-fast-forward-01/` | 1 个业务失败、0 errors：取消祖先检查后，故障边界返回的非快进 M 被错误集成。 |

每个新测试运行目录的 `run.json` 包含精确命令、完整 CLI/Git stdout/stderr/退出码、失败文本、实际入口和夹具路径；`artifacts.tar.gz` 保存全现场。示例重现：

```sh
/opt/homebrew/bin/python3.11 -B workbench/tests/test_task_cards_e2e.py --output evidence/2026-10-10-batch12/T-075/card-2/cards-repro-01
```

起点及变异体的精确 `--gate` 路径见 `baseline-bindings.json`、`mutants-01/manifest.json`；对应 `*.command.json` 保存具体用例参数。变异源码、单点补丁及候选源码差异已冻结，原目录在 /tmp，没有修改正常门禁来跑变异体。第三项变异失败观察的是实际工作分支错误推进，不是导入/环境错误。

## 沙箱外产品验收结果

该轮脚本已保存为 `outside-sandbox-acceptance-01.sh`。重现整轮时运行：

```sh
bash evidence/2026-10-10-batch12/T-075/card-2/outside-sandbox-acceptance-01.sh
```

执行主控已运行脚本，收据为 [outside-acceptance.snbKuo](outside-acceptance.snbKuo/summary.tsv)。脚本退出 0，十项结果与预期退出码一致。worker 又核对了原始断言、失败原因、介入记录和源码归档，见 [读回记录](outside-acceptance-audit-01.json)。这是审查前候选的记录；修复版另有全套回归。

| 检查 | 结果 | “推断：缺尾注” action / 人工介入 |
| --- | --- | --- |
| coop | PASS，8/8 | 4 / 4 |
| recovery | PASS，9/9 | 9 / 9 |
| run | PASS，18/18 | 9 / 9 |
| red-window | expected-red：起点不识别 `--card`；不是环境或导入错误 | 不计为通过 |
| green-window | PASS；9 条业务断言 | 见该夹具原始状态 |
| green-cas | PASS；3 条业务断言 | 见该夹具原始状态 |
| mutant-cas | 3 条 BUSINESS_RED：放过错误旧值、覆盖外部写入、错误 accepted | 有效反事实 |

各旧套件目录的 `inferred-interventions.json` 给出只读数据库统计和输入/介入关联；计数分别来自本次候选的运行，不引用迁移卡的旧证据。run 的外部 runtime 是隔离替身，不代表真实 Codex/PTY 验收。

新恢复窗口在目录已快进而引用未 CAS 时仅终止本测试创建并经 ps 核对的门禁 CLI；已证明恢复同一 intent、恰好一次引用推进、重放幂等。起点版本的新接口红态、候选绿态与全部现场分别保留。

四个其余变异体早已在本地隔离数据上执行，见前表原始输出；它们没有 ps/进程终止需求。与这次 CAS 变异体合计五个，都有业务断言失败且没有测试 errors，当前没有剩余未运行的变异体。

每轮使用 `outside-acceptance.*` 唯一标签，保存 stdout/stderr/退出码；非预期退出就停止。原探针和此前测试产物不覆盖。原型窗口与产品验收分开报告，真实模型/窗格仍不在本卡范围。

## 一次独立审查与修复闭环

审查候选 `1273b17e933cd0bb279a20e6b237dbbd2f054db3`，基线为本卡起点。审查采用全新上下文，只读检查冻结源码、公开合同和原始证据，没有读取 worker 对话、RESULTS 或实现理由；模型请求及边界见 `review-request-01.json`。审查原文完整保存在 [independent-review-01.txt](independent-review-01.txt)，不改写其 FAIL 结论。

唯一发现为 P2：第一条完成条件退出 0 后，开始第二条只更新 command_intent，仍保留上一条 v.result。若第二条运行时中断，interruptVerification 的 `??=` 不会产生当前命令的未知结果，旧记录会把第二条意图与第一条成功结果并列。这影响历史证据准确性；审查没有发现它能绕过新的完整验收或直接集成。

已新增 `workbench/tests/test_completion_recovery.py`，经真实 CLI、SQLite 与 Git，在第二条独立 oracle 屏障处终止所属 CLI；断言第二条退出/输出为未知、第一条完整结果保留、新 verification 在新 M worktree 重跑两条命令。第一条会在夹具控制目录追加真实执行记录，用于独立核对重新执行，不能仅凭结果数组声称重跑。

执行主控已运行红态，收据 [outside-review-red.qcD7XT/red-verdict.json](outside-review-red.qcD7XT/red-verdict.json) 为 EXPECTED_BUSINESS_RED。worker 回读确认：1 个业务失败、0 errors，三个断言分别抓到第二条退出码为上一条的 0、输出为 `FIRST_CONDITION_OK`、argv 仍指向第一条命令。首条成功记录保留和新 verification 重跑全部命令的其他断言仍成立，故失败范围明确；读回记录见 `review-red-audit-01.json`。

红态脚本保存在 `outside-sandbox-review-red-01.sh`，全部失败现场保留。随后仅在持久化下一条命令意图前增加 `delete v.result`，已完成的 `v.results` 不动；实现增加一行说明注释。修复及已用于红态的新增测试提交为 `3386c4c`。供主控审阅的精确差异为：

```sh
git diff 1273b17e933cd0bb279a20e6b237dbbd2f054db3 3386c4cd3a4e44b5b58d5a46a780fb99f9aa637a -- workbench/src/gates/core.ts workbench/tests/test_completion_recovery.py
```

执行主控用当前 `outside-sandbox.sh` 跑完同一复现的绿态、14 项任务卡测试、交付 8/恢复 9/编排 18、新增目录更新恢复窗口与 CAS 正例，以及从修复候选重新生成的五个变异体。三套旧测试的缺尾注计数重新读取。启动前核对源码/测试与修复提交一致，输出使用新的 `outside-review-green.*` 标签。

```sh
bash evidence/2026-10-10-batch12/T-075/card-2/outside-sandbox.sh
```

最终收据：[outside-review-green.SC1xPN/summary.tsv](outside-review-green.SC1xPN/summary.tsv)。脚本退出 0，十二项调用均符合预期；worker 回读结果、断言和变异失败原因，并将 40 个源码文件与运行前归档逐字节比较，一致。详见 [final-acceptance-audit-01.json](final-acceptance-audit-01.json)。

| 修复版检查 | 结果 | 缺尾注 action / 人工介入 |
| --- | --- | --- |
| green-commands：双完成条件中断 | PASS，1/1，12 条业务断言 | — |
| green-cards：任务卡、路径、尾注、分支 | PASS，14/14 | 各场景另有原始记录 |
| coop | PASS，8/8 | 4 / 4 |
| recovery | PASS，9/9 | 9 / 9 |
| run | PASS，18/18 | 9 / 9 |
| green-window：目录更新后 CAS 前中断 | PASS，1/1，9 条业务断言 | — |
| green-cas：外部写入竞争 | PASS，1/1，3 条业务断言 | — |
| path / trailer / dirty / fast-forward / cas 变异体 | 全部 business-red；失败数分别为 1 / 1 / 3 / 1 / 1；全部 0 errors | — |

合计 52 项正例测试；预期失败的变异体单列，不混入正例通过数。P2 绿态确认当前第二条结果为未知、第一条完整结果保留、新 verification 重跑两条命令。代码修复没有更改业务预期或旧验收白名单。

主控批准原话（本会话 `⟦主控 #22⟧`）：

> 修复 diff（3386c4c）我已审过：每条完成条件执行前先清掉 v.result，同意。

按任务卡仅做一次 fresh-context 审查；原 FAIL 不改成 PASS。最终本卡 PASS 来自修复红绿证据、修复版本完整回归及主控对修复 diff 的同意。

## 交付、证据与后续范围

- 本卡必做工作已完成；T-075 Resolution 记录“T-075-2 完成，待后续卡，待主控关闭”，保留 open，不勾选整张 T-075 的未完成条件。
- 所有方案失败、夹具错误、起点红态、审查红态及旧轮通过记录保留。嵌套 Git 夹具不登记为 gitlink；原目录保留，完整归档和顶层收据进入版本控制，交付文件清单见 `evidence-packaging-02.json`。
- 旧 acceptance 差异与批准的 A1–A10 一致，见 `acceptance-diff-audit.md`；新增回归位于 `workbench/tests/`。收尾地图检查及编码/链接检查见 `delivery-checks.json`，须为 0 problems、0 stale。
- 工作台 README 的地图登记由执行主控明确接管，在最终提交后处理（`⟦主控 #20⟧`）；worker 不改地图。
- 本卡没有启动真实被测 Codex、后台、PTY 或 Electron，不声称这些功能通过；产品独立审查自动化、打分、红态门禁和规则式检查属于 S2，worktree 命名清理与冲突回写属于 S3。没有 push，也没有性能、可靠性或成本收益主张。
