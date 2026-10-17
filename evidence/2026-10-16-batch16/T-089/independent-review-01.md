# T-089 独立审查 01

候选：`115dc1a622ce578fc8119cdc2675b39a5b4e70cf`；起点：`c544b29049861998e11eeb7344b457103fab3c98`。审查日期：2026-10-17。总体：**NO_GO**。真实入口在删除阶段超时后已删除一项原件，违反 Acceptance 第 3 条“超时按失败处理、不删原件”。三个变异均已被拒绝；其余已测外盘场景符合预期。S3 组合基线仍未覆盖被修改 runner 的实际调用链，抽取行为等价证据为 INCOMPLETE。

本报告按 reviewer 角色卡，只审查冻结候选；未实现、修复、提交、集成、调用模型或修改全局配置，未开子 agent。仓库写入仅本报告与 `REVIEW-OUTSIDE-01.sh`。变异与检查产物位于 `/private/tmp/t089-review-01-fg12j_8o/`，已由脚本保留到外置盘目录。下文 `OUTSIDE` 指 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089/review-outside-01-y4md2lhw/`；`OUTSIDE/reviewer-source/` 保存一次性候选、变异 patch、独立 oracle 和本地证据，`OUTSIDE/checks/` 保存本次真实外盘各场景。审查已逐字节确认外盘运行的归档模块与冻结候选一致。

## 契约与审查方法

答案取自 T-089 Acceptance 六条、T-088 的用户决定和本次派发。worker 的 RESULTS 与检查脚本只用于找入口和证据，未导入为 oracle。第四个“已挂载但读写挂起”条件按 ticket 的增补审查；它来自构思主控，用户未逐条确认，不改称用户决定。

- **Tracer bullet**：独立输入经过真实 `archive_evidence.py` CLI、目标文件、清单与原件读回；没有直接调用生产内部函数来替代入口验证。
- **Deep modules**：共用归档模块承担复制、核对、超时和清理；检查是否留下第二份生产实现，以及失败边界是否覆盖完整操作。
- **Ubiquitous language**：沿用“归档类别、原件、清单、回放”，区分引用核对结果与历史业务测试通过。

候选原文通过 `git show 115dc1a62:<路径>` 和 `git diff c544b2904 115dc1a62 -- <路径>` 读取；一次性候选通过 `git archive 115dc1a62` 解出归档模块、S3 runner、任务卡模板，无 worktree、checkout 或其他 Git 写操作。

## 逐条 Acceptance

| 条件 | 结论 | 独立依据与界限 |
| --- | --- | --- |
| 1. 起点红态 | PASS | 将起点的既有 S3 文件解到一次性目录；同一独立夹具包含 run 目录与 `.tar.gz`，调用新增归档命令 exit 2，缺少该文件。`supplemental-01/red/command.json` 与 `oracle.json`。这是新增契约红态，不宣称既有缺陷。 |
| 2. 归档绿态、外盘逐字节一致、清单齐全 | PASS（已运行范围） | `local-02/candidate-fixture/`：独立指定 13 个归档根、14 个原始文件，含嵌套、非 ASCII 路径、空目录、两种 sqlite 及各自 WAL、三种监视器日志。真实入口 exit 0；目标逐文件字节与输入一致，清单字段和值正确。同一独立夹具已在真实外盘 `OUTSIDE/checks/candidate-fixture/` 通过，入口/oracle exit 0/0；目标逐文件字节、空目录和清单均通过独立断言。主控较早的 `external-checks-01.json` 现场亦已读回，未代替本次冻结候选证据。 |
| 3. 未挂载、目标存在、截断、挂起四反例 | NO_GO | 本次真实外盘前三种及等长损坏均入口 exit 1、oracle 0，原件逐字节不变；未挂载路径无目标创建，冲突目标未变。复制挂起约 0.832 秒入口 exit 1，全部原件保留。删除挂起约 0.837 秒入口 exit 1、oracle 1：`a.bin` 原件已删除，`b.bin` 保留，产品仍称“保留原件”。命中增补的第四反例之“超时……不删原件”，见问题 1；因此四反例整体不能通过。 |
| 4. 输入小文件及类别外文件原样保留 | PASS（已测样本） | 从主仓库读取 `run_daemon_acceptance.py:97–99` 指定的三个真实文件字节，放入独立夹具，经真实命令后仍逐字节相同。本地及本次真实外盘中，普通 JSON、普通日志、`.bin.extra`、笔记和根部 `run.json` 亦原样保留。另验证显式 `--keep run-protected/input.bin` 保留该输入及其 run 祖先；没有据此声称能自动发现所有输入依赖。 |
| 5. T-086 一次性副本回放与引用核对 | PASS（引用与字节范围） | 未搬迁真实已提交 T-086。只读主控已归档的一次性副本，经 35 个清单重建相对文件集，与仓库原件 10,064 文件、107,177,272 字节逐字节一致。独立 `rg` 在完整主仓库的 `workbench/tests/` 与 `acceptance/` 查 T-086 引用无命中，exit 1。逐文件证据位置与结果见下文。未把历史业务测试写成已重跑。 |
| 6. project_map status 0 problems | PASS（完整主仓库）；稀疏副本 INCOMPLETE | 本次运行规定命令：完整主仓库 exit 0，Problems 0、Stale 0；稀疏 worktree exit 1，README 缺失及其链接、`.grilling/a2a-gui-client.md` 链接共 3 个问题、Stale 0。候选未改地图、术语表与这些缺失文档；不将稀疏副本的状态上调为 PASS。 |

归档类别实现位置为 `workbench/tests/archive_evidence.py:45–51`：run/fixtures 名称及其 `-`/`_` 变体、含 `run.json` 的运行目录；`.tar.gz`、`.bin`、`.sqlite`/`.sqlite3` 及对应 `-wal`；文件名含 monitor 的 `.log`/`.jsonl`/`.txt`。本次有独立正例及类别外哨兵；没有将任意 SQLite 扩展名或任意日志命名均已覆盖写成结论。

`verify():84–96` 在原件删除前比较原件、目标的相对文件名及逐文件大小映射，因而核对文件数和总字节数，再逐块比较所有字节。清单 `original/archive/bytes/replay` 齐全，额外字段为 `files`，没有校验值。模板 diff 仅新增一句摘要、小文件、外置盘路径与清单规则，没有新增提示轮次。

## 变异与可重放证据

独立 oracle 不导入生产常量、选择器或模板。每个变异仅替换一个位置；patch 位于 `mutants/<名称>/mutation.patch`。命令、stdout、stderr、退出码、失败后读回和 oracle 退出码分别保留于各场景目录。好候选先通过相同场景，再运行坏实现。

复跑本地已完成的入口检查（输出必须是新目录）：

```sh
python3 -B /private/tmp/t089-review-01-fg12j_8o/review_checks.py --root /tmp/t089-review-01-repeat
python3 -B /private/tmp/t089-review-01-fg12j_8o/supplemental_checks.py --output /tmp/t089-review-01-supplement-repeat
```

| 变异 | 单处改动 | 完成条件与结果 |
| --- | --- | --- |
| no-byte-compare | `if a != b:` 改为 `if False:` | 等长损坏反例。好候选真实入口 exit 1、oracle 0；变异真实入口 exit 0 并删除原件，oracle exit 1。`local-02/mutant-no-byte-compare/`，已拒绝。 |
| collect-json | 把 `.json` 加入文件归档类别 | 同一正常夹具。好候选入口/oracle 0/0；变异入口 0、oracle 1，因普通 JSON 与 `run.json` 被归档。`local-02/mutant-collect-json/`，已拒绝。 |
| no-timeout | 去掉 `communicate(..., timeout=timeout)` 的期限参数 | 复制边界受控挂起。好候选约 0.832 秒入口 exit 1、oracle 0，原件不变；变异约 5.004 秒由独立硬超时终止，入口 exit -9、oracle 1，已拒绝。见 `OUTSIDE/checks/mutant-no-timeout/`。 |

本地入口检查总进程 exit 0，表示好候选通过且两个已跑变异被 oracle 拒绝。本次真实外盘的三个变异亦全部被拒绝：no-byte-compare、collect-json 的坏入口仍 exit 0，但 oracle exit 1；no-timeout 由独立硬期限终止，oracle exit 1。整个外盘检查 exit 1 的原因是未改候选的 delete-hang 违反契约，而非预期的变异失败。

## 问题与证据缺口

### 1. 整体期限在原件回收中到期，失败后已有原件被删除（P1）

位置：`workbench/tests/archive_evidence.py:152–156, 172–180`。对应 **Acceptance 第 3 条** 的第四反例：“外置盘已挂载但读写挂起，归档须带读写超时，超时按失败处理、不删原件”。前三个反例和复制阶段挂起已通过；本问题针对同一超时操作进入删除阶段后的承诺，不新增“所有失败都必须回滚”或“失败时不得有清单”的验收要求。

**复现方式与实际结果。** 主控运行本报告的 `REVIEW-OUTSIDE-01.sh`，源码为从冻结提交解出的未改候选，使用真实 CLI。一次性夹具在已挂载的外盘 review 目录创建两份原件：`a.bin`（15 字节）、`b.bin`（16 字节）。通过 `PYTHONPATH` 的 `sitecustomize.py` 只替换文件系统调用边界：`Path.unlink` 遇到 `b.bin` 时写下本次子进程 PID 并向自身发 `SIGSTOP`；其他 unlink 仍调用原方法。因此两份文件已复制、逐字节核对并写清单，第一份原件按候选逻辑删除，子进程才在第二份删除前暂停。CLI 参数为 `--mount-point /Volumes/WD-Elements --timeout 0.8`，独立硬期限为 5 秒。

实际约 **0.837 秒**由产品自身期限处理，真实入口 **exit 1**，没有触发独立硬超时；stderr 为“归档失败：归档读写超时；保留原件与已有副本”。读回确认 `source/a.bin` 已不存在、`source/b.bin` 字节未变，两份 archive 字节均与原始输入一致，两个 `.archive.json` 均存在。oracle exit 1。这里确认的是“超时失败后原件不全”，**没有观察到归档数据字节丢失**。

完整复现材料均在 `OUTSIDE/checks/candidate-delete-hang/`：`command.json` 给出准确 argv、退出码与耗时，`injection/sitecustomize.py` 给出边界注入，`oracle.json` 和 `readback.json` 给出判定；原件、目标与清单现场均保留。全套可用文末脚本重放到新的 review 目录，不复用或覆盖本次现场。

**真实使用中的可达性。** 可达的是“统一期限在逐项回收原件时到期”。`relocate()` 在同一个子进程里执行全部复制、核对、清单写入和 `unlink/rmtree`；父进程的单次 `communicate(timeout=...)` 覆盖这些步骤，既不区分准备与提交，也不在超时后恢复已删原件。正常用户输入可以包含很多文件或目录：复制/核对已消耗大部分期限时，回收本身的耗时、源盘元数据延迟或进程调度暂停即可让期限落在两次删除之间，不需要修改候选，也不依赖原件必须位于外盘。与之相邻的 I/O 错误路径亦已在内置盘 `/tmp` 夹具复现：删除第二项报错，第一项已删，证据在 `OUTSIDE/reviewer-source/supplemental-01/delete-error/`。

本次 `SIGSTOP` 是确定性时序注入，**不是已观察到真实外置盘在内核中挂死**。夹具把 source 和 archive 均放在外盘，日常 source 通常在内置盘；日常外盘若只在复制或核对中挂起，当前复制挂起检查确实能保住原件。本报告不把该差异抹掉。拒收依据是：产品把清理期间到期也报告成同一种“归档读写超时”，而 ticket 对该超时结果要求“不删原件”；候选的实际阶段边界无法保证它。若主控希望只对复制/核对阶段承诺保留原件，需要明确调整实现边界或回交契约决定，不能让 reviewer 静默缩小现行文字。

oracle 同时记录“失败路径留下成功清单”。**这仅作额外观察，不是独立拒收理由**：ticket 没有要求失败时必须删掉清单，保留它们有助于诊断。即使不使用这条断言，仅 `a.bin` 原件缺失就足以让第 3 条失败；不应为了让检查变绿删除这些证据。

**最小修法方向。** 把有期限的归档准备阶段与原件回收的提交边界分清：在仍可能返回“超时失败、原件保留”的阶段内只复制、核对和准备记录，不逐项销毁原件；父进程确认准备阶段完成后，再进入明确的原件回收阶段，清理未完成应保留可恢复状态并准确报告，不能回到现有那条原件完整的超时错误。若坚持用同一整体期限覆盖全部删除，则须保留可恢复的完整原件集合，处理期限落在部分删除之后的恢复；单纯加长 timeout、吞掉异常、改成成功或修改提示语都不能满足现行契约。本报告不指定新的 API 或代替主控放宽失败语义。

建议将本次删除阶段超时反例保留在真实 CLI 完成条件中，与复制挂起并列；它能直接检查阶段边界，防止仅证明“复制挂起时不删原件”后把结果外推到整个操作。

### 2. S3 组合基线不足以证明修改后的调用链等价（P2，验收证据缺口）

位置：`workbench/tests/run_s3_regression.py:167–170`；证据脚本 `evidence/2026-10-16-batch16/T-089/check_s3.py:42–45`、`check_s3_archive.py:50–56`。

已读取基线/候选 `check.json`，并与外置盘归档中两份原始 `cas/run.json` 逐项比较，相同。两者 CAS 均为 1 tests / 0 failures / 0 errors，是真实通过的独立 CAS 场景，但执行的是 `run_s3_rebased_regression.py`。该 runner 不导入 `run_s3_regression.py` 或归档模块，也不调用 `archive_large_files`；替换后的 S3 runner 没有在此路径执行。

另一个 `check_s3_archive.py` 对照从起点 AST 取旧函数、直接调用新共用函数，验证一份 5 MiB + 17 字节文件迁移与一份恰好 5 MiB 文件保留。它证明这个函数正常路径的阈值和字节行为，不能覆盖 `run_s3_regression.main()` 的传参、调用位置、异常传播和最终证据输出。把实际 runner 调用的阈值或目标改错，现有两段检查仍会绕过该调用。

因此组合仅支持“CAS 业务场景通过 + 共用函数单夹具正常路径通过”；**不足以支持整个抽取行为等价**。最小补证应让基线/候选通过同一个实际 runner main 及归档调用，强制产生超过阈值的证据，独立核对小文件保留、归档字节、清单路径和最终运行收据。旧坐标审计失效的裁定只解释为什么换基线，不能替代这一连接证据。

## T-086 引用逐文件结果的范围

独立字节重建证据：`supplemental-01/t086-readback.json`；主控回放入口、35 个清单位置、44 个源码文件逐项引用位置与分类：`t086-external-01.json`，可读表格为 `reference-audit.md`。这 44 行的结果是“引用不在本次 T-086 搬迁集合”，**不是 44 项业务测试执行通过**。

真正读取历史输入的清单包含：`archive_t081_capability_run02.py`、`audit_legacy_scope.py`、`check_t081_capability_paths.py`、`check_t081_capability_run03.py`、`collect_t081_closeout.py`、`commit_t081_closeout.py`、`commit_t081_duplicate_fix.py`、`diagnose_t081_capability_run02.py`、`prepare_s3_baseline.py`、`prepare_t081_capability_run02.ts`、`prepare_t081_capability_run03.ts`、`prepare_t081_capability_run04.ts`、`run_daemon_acceptance.py`、`run_p_review.py`、`run_t076_green.py`、`run_t076_legacy_green.py`、`run_t076_quality_real.py`、`run_t076_quality_widen.py`、`run_t081_bad_worker_suite.py`、`run_t081_capability_turn.py`、`run_t081_duplicate_case.py`、`t081_capability_home.py`、`test_command_evidence.py`、`test_t081_archive_ownership.py`、`test_t081_capability_audit.ts`、`test_t082_review_boundary_e2e.py`、`test_worktree_lifecycle_e2e.py`（均在 `workbench/tests/`）。逐文件均未发现固定引用 T-086；实际直接读路径见上述 JSON。其余命中为输出、同次读回或记录引用，其中 `acceptance/test_coop_e2e.py`、`test_dispatch_session_e2e.py`、`test_inbox_e2e.py`、`test_recovery_e2e.py`、`test_run_e2e.py` 不读本次搬迁集。

没有运行这些历史业务测试、真实 CLI 模型轮次或其他批次迁移；静态路径核对不外推任意动态输入或未来批次均安全。三个小文件样本另经真实入口验证，不只依据字符串无命中。

## design-integrity-review

本变更触及验收入口，按 behavioral-acceptance-review 审核，同时检查结构风险。生产 S3 旧归档函数已删除，只保留导入与一次实际调用；AST 提取旧函数仅用于证据对照，不是第二份生产路径。`minimum_bytes` 为现有 S3 阈值语义与新 CLI 类别语义的明确两个用途，不是未经需求支持的兼容 shim。未发现新增重试、内置盘 fallback 或静默成功分支。

`except subprocess.TimeoutExpired: pass` 只出现在 kill 后的有限回收等待，随后必抛超时；不是将归档失败吞为成功。CLI 对预期 I/O/值/运行错误转 exit 1 也保留诊断。主要结构问题是问题 1 的提交/清理边界与期限覆盖；主要验收缺口是问题 2 的真实调用链未执行。没有为了本次审查修改这些实现。

## 外置盘执行结果与剩余缺口

主控运行：

```sh
zsh evidence/2026-10-16-batch16/T-089/REVIEW-OUTSIDE-01.sh
```

脚本已通过 `zsh -n`，使用 `set -o pipefail`。先检查挂载，再只在 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089/` 下新建 review 目录；不卸载盘、不写其他外部位置、不启动模型。每段打印输出目录、硬超时及退出码，保留独立 oracle、补充检查脚本、候选、变异 patch、本地与外部输出。复制挂起、第三变异和删除挂起均有独立硬期限；进程回收只限本次夹具写下的 PID。

主控已运行该命令：建立目录与源码保存均 exit 0；独立入口检查约 7.127 秒 exit 1，整段未触发 75 秒硬期限。六个好候选场景（fixture、unmounted、existing-target、truncated、same-size、copy-hang）符合预期，三个变异全部被拒绝，candidate-delete-hang 不符合第 3 条。主控报告无残留进程。审查已只读核对原始 wrapper JSON、完整日志、oracle、注入代码及失败现场，并逐字节确认实际运行的归档模块绑定本报告候选。

原始执行记录为 `OUTSIDE/independent-entry-checks.json`、同目录 `.stdout.txt` / `.stderr.txt`，总表为 `OUTSIDE/checks/summary.json`；完整主控日志在 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t089-review-outside-01.log`。本次 reviewer 读回记录保留在 `/private/tmp/t089-review-01-fg12j_8o/outside-final-readback.json`，没有写回或清理外盘现场。

剩余要求：修复问题 1 并为新候选重新证明超时保留原件；为问题 2 补足实际 S3 runner 调用链的前后对照。问题 1 为已复现的 NO_GO，问题 2 为独立的 INCOMPLETE 证据缺口。候选如变更，本次通过场景不能替新候选背书。

T-089 REVIEW NO_GO
