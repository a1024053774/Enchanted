# T-089 第二轮独立审查

候选：`ef3b1ade9e4511673435d8e28adaf2354a9240d3`；起点：`c544b29049861998e11eeb7344b457103fab3c98`。日期：2026-10-17。总体：**NO_GO**。

两阶段修改修正了回收失败的状态表述，仍会在回收超时前删除部分原件，不满足 Acceptance 第 3 条第四反例。新增实际 `main()` 对照补上了首轮 S3 调用链缺口，本轮独立核对其原件后，认为足以支持本票抽取的成功路径行为等价；没有证明所有异常行为严格不变。

本轮 `REVIEW-OUTSIDE-02.sh` 已由主控在沙箱外执行，reviewer 已读回原始命令、输出、退出码和产物。11 个独立场景全部执行，无跳过；三个变异全部被拒绝。未改候选的删除挂起场景仍违反当前 ticket，见问题 1。验收条件的解释由执行主控交构思主控裁定，本报告不代选。

## 范围和独立性

先读 reviewer 角色、T-089、T-088 和任务卡，以六条 Acceptance 和 T-088 决定重建答案。第四反例来自构思主控增补，用户未逐条确认，按本次派发纳入审查。执行主控的组合基线裁定不视为用户放宽“不删原件”的授权。RESULTS 和 worker 的检查脚本及其 PASS 标签只作线索。

未实现、修复、提交、集成、调用模型 API、写全局配置或开子 agent。仓库只写本报告和 `REVIEW-OUTSIDE-02.sh`；其他写入均在本轮新建 `/private/tmp/t089-review-02-sk4a3a9e/`，下文称 `SCRATCH`。候选经 `git show`、`git diff c544b2904 ef3b1ade9` 阅读，必要路径通过 `git archive` 解出，没有新建 worktree 或 checkout。

下文 `OUTSIDE` 指 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089/review-outside-02-wrhqaqg5/`；`OUTSIDE/reviewer-source/` 保存本轮候选、三个变异 patch、独立 oracle 和此前本地文本证据，`OUTSIDE/checks/` 保存本轮真实外盘各场景。reviewer 已逐字节确认外盘归档模块等于冻结候选，审查脚本、变异实现和 patch 等于本轮临时副本。定稿读回摘要在 `SCRATCH/outside-02-readback.json`。

- **Tracer bullet**：独立输入经过真实归档 CLI，检查原件、外盘字节、清单和退出码。
- **Deep modules**：核对共用模块的复制、核对、期限、回收职责和是否残留第二份生产实现。
- **Ubiquitous language**：沿用归档类别、原件、清单、回放；区分引用有效和历史业务测试已执行。

## 逐条 Acceptance

| 条件 | 结论 | 来源、实际结果和界限 |
| --- | --- | --- |
| 1. 起点无可用入口 | PASS | `SCRATCH/supplemental-01/red/`：起点 git archive 副本，夹具含 run 目录与 tar.gz；新增命令不存在，CLI exit 2，原件字节不变，无归档目标。这是新契约红态。 |
| 2. 归档绿态、外盘字节与清单 | PASS（已测范围） | `local-01/candidate-normal/` 真实 CLI exit 0；11 个归档根、12 个原始文件，覆盖嵌套、中文路径、空目录、tar.gz、bin、两种 sqlite 和各自 WAL、三种监视器日志；11 个保留文件不变。另对最近外盘 T-086 现场通过清单重建，逐字节等于历史原件。同一独立夹具已在 `OUTSIDE/checks/candidate-normal/` 重复通过，真实入口/oracle 0/0；逐文件字节、空目录、保留文件和清单通过独立断言，reviewer 又读回真实样本和哨兵。 |
| 3. 未挂载、冲突、截断、挂起四反例 | NO_GO | 本地及本次真实外盘的未挂载、冲突、截断、等长损坏均 CLI exit 1、oracle 0，原件逐字节不变；缺盘不创建目标，冲突目标不变。外盘复制挂起约 1.074 秒由产品期限退出，全部原件保留。删除挂起约 1.962 秒 exit 1、oracle 1，a.bin 已删，因此四反例整体 NO_GO，见问题 1。 |
| 4. 输入小文件和类别外文件保留 | PASS（样本范围） | 独立夹具使用 `run_daemon_acceptance.py:97–99` 所读三个真实文件字节，归档后仍在。普通 JSON、普通日志、笔记、根部 run.json、bin.backup 原样保留。显式 `--keep run-protected/input.bin` 保留其 run 祖先。这些断言已在本地及本次真实外盘重复通过；reviewer 直接读回外盘三个真实输入和普通 JSON。工具不自动发现输入依赖，本报告不作此声称。 |
| 5. T-086 一次性回放和逐个引用核对 | PASS（引用与字节范围） | 冻结候选在 `/tmp` 副本经真实 CLI exit 0，35 项归档；10,064 文件、107,177,272 字节经清单重建完全相同，历史原件未变。最近外盘回放也重新重建并比对。冻结版本两个代码目录的 47 个 evidence 引用文件逐个列于附录，均无 T-086 引用；未重跑历史业务测试。 |
| 6. project_map status 0 problems | PASS（完整主仓库）；稀疏副本 INCOMPLETE | 本轮规定命令：完整主仓库 exit 0、Problems 0、Stale 0；稀疏副本 exit 1，README 缺失及其相关链接、.grilling/a2a-gui-client.md 链接共 3 problems，Stale 0。没有擅自补文件或改地图。输出在 `supplemental-01/map-primary.json`、`map-sparse.json`。 |

类别实现位于 `archive_evidence.py:56–63`：run/fixtures 本名、其 `-`/`_` 变体及含 run.json 的目录；tar.gz、bin、sqlite/sqlite3 及对应 WAL；名称含 monitor 的 log/jsonl/txt。独立夹具核对主要类别及类别外哨兵，T-086 回放覆盖实际 run.json 目录。没有声称覆盖任意日志命名或任意 SQLite 扩展名。

`regular_tree()` 与 `verify():95–107` 在任何回收前比较原件和归档的相对路径、逐文件大小映射，因而核对文件数和总字节数，再逐块比较所有字节。`prepare():155–163` 核对完所有项目才写清单，父进程收到结果才开始回收。清单必需字段 original/archive/bytes/replay 齐全，额外 files 是文件数，无校验值。模板 diff 仅增加一句摘要、小文件、外盘路径和清单规则，没有新增提示轮次。

## 问题 1：回收阶段超时仍删除部分原件（P1）

位置：`workbench/tests/archive_evidence.py:166–172, 221–229`；错误验收期望：`workbench/tests/run_evidence_archive_checks.py:149–155`。

T-089 Acceptance 第 3 条写明：“外置盘已挂载但读写挂起，归档须带读写超时，超时按失败处理、不删原件”。新候选只保证准备阶段超时前不删原件，回收仍逐项 unlink/rmtree 并受期限约束。第一项删除成功、第二项挂起时，期限到期仍会留下部分删除的原件。改报 INCOMPLETE 改善了诊断，未实现不删原件。

本轮 reviewer 自建夹具通过 `REVIEW-OUTSIDE-02.sh` 在真实外盘重新运行同一删除边界，随后独立读回 `OUTSIDE/checks/candidate-delete-hang/`：

- 被测 `OUTSIDE/reviewer-source/candidate/workbench/tests/archive_evidence.py` 与冻结候选逐字节相同。
- `injection/sitecustomize.py` 在 b.bin 的 Path.unlink 边界向自身发 SIGSTOP，其他 unlink 调原方法；真实 CLI 参数含 `--timeout 0.8`。
- 入口 exit 1，elapsed 1.961714375 秒，未触发检查器硬超时，reason 是 reclaim 阶段超时。
- `source/a.bin` 已不存在，`source/b.bin` 仍为 `second-original-02`；`archive/a.bin`、`archive/b.bin` 分别保持 `first-original-02`（17 字节）、`second-original-02`（18 字节）。
- stderr 准确报告 INCOMPLETE、phase reclaim、archive_verified true，remaining_originals 只列 b.bin；独立 oracle exit 1，唯一不符项为 a.bin 缺失。

真实 argv、stdout、stderr 和退出码在该场景的 `command.json`、`stdout.txt`、`stderr.txt`；独立判定在 `oracle.json`。reviewer 的定稿读回记录在 `SCRATCH/outside-02-readback.json`。此前读回主控的新候选现场 `checks-20261017T103307Z` 也见到相同结果，保存在 `supplemental-01/reclaim-current-readback.json`；本结论已有本轮独立夹具重复支持，没有沿用首轮候选的失败结论。

worker 新检查明确断言 a.bin 不存在，并将此算作通过，因此“九项 PASS”未证明当前 ticket 的不删原件条件。主控 #34 已说明会将“回收阶段可以部分完成”的验收解释交构思主控裁定；reviewer 按当前冻结条件报告 NO_GO，不代选、不修复、不把未裁定解释当成已放宽的验收。

删除 I/O 错误也在本轮本地及真实外盘重跑：先删 a.bin，b.bin unlink 抛 EIO，exit 1。两份归档字节完整，INCOMPLETE 和剩余原件准确；`local-01/candidate-delete-eio/` 与 `OUTSIDE/checks/candidate-delete-eio/` 的诊断 oracle 都为 PASS。这里的 PASS 仅证明准确报告回收未完成，不表示原件完整保留。本报告不新增“所有异常都必须原子回滚”的条件，也不据此豁免明确的超时条件。

本问题重复首轮失败类别。机械检查应继续在真实 CLI 删除挂起场景要求原件全部保留，不能改成断言首项已删除；无需用新增 prose 规则替代这个可执行检查。

## S3 抽取和结构审查

原组合基线（rebased CAS 加单独 archive_large_files 对照）本身不足：没有证明实际 runner 使用正确阈值、目的地和归档返回值。新增 `check_s3_main.py` 补了这个缺口。

本轮独立检查外盘 `s3-main-02-mpb065p2/{baseline,candidate,threshold-mutant,destination-mutant}/` 的 command、driver、run.json、清单、实际归档字节及 `/tmp` 实际 checkout 源码：基线 runner 等于起点原文；候选 runner 与共用模块等于冻结候选；两个变异各仅改 runner 一个位置。实际 main、原 CAS 方法、原归档调用和参数、原 finish_evidence、summary 均保留；替换是旧坐标审计、输出路径和固定归档根，finish_evidence 调原函数后加入独立输入。这些替换没有跨越被修改的调用边界。

基线与候选实际 main 都 exit 0，CAS 的 tests/failures/errors/skipped 都为 1/0/0/0。5 MiB + 32 字节文件迁移，恰好 5 MiB 文件留下；归档字节、清单、replay 和 summary 中 external_archives 均正确。阈值变异仍 exit 0，但大文件留在原处；目的地变异仍 exit 0，但落在 cas-wrong，独立读回均拒绝。证据：`supplemental-01/s3-independent-readback.json`。

因此，组合证据加实际 main 对照足以支持本票关注的成功路径抽取；原 S3 坐标审计入口自身的既有失效仍存在，未声称直接运行已经恢复，也未声称异常语义完全不变。

生产只留 `archive_evidence.archive_large_files` 一份实现，S3 直接 import 并传原来 5 MiB 阈值、归档根和 replay。minimum_bytes 服务于 S3 这个真实第二调用场景，没有留下旧函数 shim。结构审查未发现其他可确认的 fallback、重试或兼容路径问题。run_phase 超时后的有限等待用于避免永久阻塞，仍抛失败；状态核对失败记入 unverified_originals，没有吞为 PASS。问题 1 不能靠更准确的异常报告判通过。

## 变异证据

三个单处变异均来自 git archive 冻结副本，patch 在 `SCRATCH/mutants/<名称>/mutation.patch`。独立 oracle 不导入生产常量、选择器或帮助函数；预期来自 ticket。每例保存真实 argv、stdout、stderr、退出码和 oracle_exit_code。

| 变异 | 好候选对照 | 坏实现结果 |
| --- | --- | --- |
| no-byte-compare：if a != b 改 if False | 等长损坏好候选 CLI exit 1、oracle 0 | 本地及真实外盘坏入口均 exit 0 并删原件，oracle 1；已拒绝。外盘见 OUTSIDE/checks/mutant-no-byte-compare/。 |
| collect-json：把 .json 加入归档类别 | 同一正常夹具好候选入口/oracle 0/0 | 本地及真实外盘坏入口均 exit 0，普通 JSON 和根部 run.json 被归档，oracle 1；已拒绝。外盘见 OUTSIDE/checks/mutant-collect-json/。 |
| no-timeout：移除 communicate 的 timeout 参数 | 好候选真实外盘复制挂起约 1.074 秒由自身期限退出，入口/oracle 1/0，原件完整 | 坏入口约 5.009 秒被独立硬期限终止，exit -9、oracle 1；已拒绝。见 OUTSIDE/checks/mutant-no-timeout/，patch 在 OUTSIDE/reviewer-source/mutants/no-timeout/。 |

以下本地命令已执行，检查总进程 exit 0，证明本地范围符合预期及两个坏实现被拒绝。真实外盘结果另列于下一节：

```sh
python3 -B /private/tmp/t089-review-02-sk4a3a9e/review_checks.py --root /private/tmp/t089-review-02-sk4a3a9e/local-01
python3 -B /private/tmp/t089-review-02-sk4a3a9e/supplemental_checks.py
```

复跑第一条须改为新输出目录；第二条固定 supplemental-01，已保存现场，不应覆盖重跑。

## 真实外盘运行与定稿检查

主控 #34 转交主控 #7 回执：`REVIEW-OUTSIDE-02.sh` 已在沙箱外执行，rc 1，无残留进程。完整主控日志为 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t089-review-outside-02.log`。reviewer 独立读回 `OUTSIDE/independent-entry-checks.json` 和所有场景的命令、oracle 及相关产物：总进程 exit 1，未触发总硬期限，11 项全部执行，无跳过；唯一未被接受的场景是未改候选的删除挂起，三个预期错误实现均被拒绝。进程无残留来源为主控回执，reviewer 没有另做全局进程清点。

| 场景 | 真实入口退出码 | oracle 退出码 | 判定 |
| --- | --- | --- | --- |
| `candidate-normal` | 0 | 0 | PASS |
| `candidate-unmounted` | 1 | 0 | PASS |
| `candidate-collision` | 1 | 0 | PASS |
| `candidate-truncated` | 1 | 0 | PASS |
| `candidate-corrupted` | 1 | 0 | PASS |
| `candidate-delete-eio` | 1 | 0 | PASS（仅诊断契约） |
| `mutant-no-byte-compare` | 0 | 1 | NO_GO（变异已拒绝） |
| `mutant-collect-json` | 0 | 1 | NO_GO（变异已拒绝） |
| `candidate-copy-hang` | 1 | 0 | PASS |
| `mutant-no-timeout` | -9 | 1 | NO_GO（变异已拒绝） |
| `candidate-delete-hang` | 1 | 1 | NO_GO |

复现命令如下，脚本每次只在本票外盘下新建目录，不覆盖本次结果：

```sh
/bin/zsh evidence/2026-10-16-batch16/T-089/REVIEW-OUTSIDE-02.sh
```

脚本保存为指定的 02 文件，首轮 01 未修改；set -o pipefail，每段打印段名、输出目录、硬期限和退出码。最终报告保留所有失败现场，候选分支仍为冻结提交。报告按原有 UTF-8、无 BOM、LF 保存并回读；定稿再次运行规定 status，完整主仓库仍为 0 problems / 0 stale，稀疏副本仍为相同 3 problems / 0 stale。没有修复或豁免这些范围外缺失路径，也没有留下尚未运行的本轮计划项。

## 附录：冻结版本的 evidence 引用

完整命令、原句和行号在 `SCRATCH/supplemental-01/frozen-reference-files.json`，来自冻结候选的 git grep，没有用当前主仓库后来新增代码替代。下表每项 PASS 仅表示其引用不属于本次 T-086 搬迁集合；没有重跑历史业务测试。

| 文件 | 引用核对 |
| --- | --- |
| `acceptance/test_coop_e2e.py` | PASS |
| `acceptance/test_dispatch_session_e2e.py` | PASS |
| `acceptance/test_inbox_e2e.py` | PASS |
| `acceptance/test_recovery_e2e.py` | PASS |
| `acceptance/test_run_e2e.py` | PASS |
| `workbench/tests/archive_evidence.py` | PASS |
| `workbench/tests/archive_t081_capability_run02.py` | PASS |
| `workbench/tests/audit_legacy_scope.py` | PASS |
| `workbench/tests/check_t081_capability_paths.py` | PASS |
| `workbench/tests/check_t081_capability_run03.py` | PASS |
| `workbench/tests/collect_t081_closeout.py` | PASS |
| `workbench/tests/commit_t081_closeout.py` | PASS |
| `workbench/tests/commit_t081_duplicate_fix.py` | PASS |
| `workbench/tests/commit_t081_review01.py` | PASS |
| `workbench/tests/diagnose_t081_capability_run02.py` | PASS |
| `workbench/tests/prepare_daemon_mutants.py` | PASS |
| `workbench/tests/prepare_s3_baseline.py` | PASS |
| `workbench/tests/prepare_t081_capability.py` | PASS |
| `workbench/tests/prepare_t081_capability_run02.ts` | PASS |
| `workbench/tests/prepare_t081_capability_run03.ts` | PASS |
| `workbench/tests/prepare_t081_capability_run04.ts` | PASS |
| `workbench/tests/run_daemon_acceptance.py` | PASS |
| `workbench/tests/run_evidence_archive_checks.py` | PASS |
| `workbench/tests/run_p_review.py` | PASS |
| `workbench/tests/run_s3_regression.py` | PASS |
| `workbench/tests/run_t076_green.py` | PASS |
| `workbench/tests/run_t076_legacy_green.py` | PASS |
| `workbench/tests/run_t076_quality_real.py` | PASS |
| `workbench/tests/run_t076_quality_red.py` | PASS |
| `workbench/tests/run_t076_quality_widen.py` | PASS |
| `workbench/tests/run_t076_real.py` | PASS |
| `workbench/tests/run_t081_absent_case.py` | PASS |
| `workbench/tests/run_t081_bad_worker_suite.py` | PASS |
| `workbench/tests/run_t081_capability_recheck.py` | PASS |
| `workbench/tests/run_t081_capability_turn.py` | PASS |
| `workbench/tests/run_t081_cas_suite.py` | PASS |
| `workbench/tests/run_t081_commit_scope.py` | PASS |
| `workbench/tests/run_t081_duplicate_case.py` | PASS |
| `workbench/tests/run_worker_delivery.py` | PASS |
| `workbench/tests/t081_capability_home.py` | PASS |
| `workbench/tests/test_command_evidence.py` | PASS |
| `workbench/tests/test_t081_archive_ownership.py` | PASS |
| `workbench/tests/test_t081_capability_audit.ts` | PASS |
| `workbench/tests/test_t081_cleanup.py` | PASS |
| `workbench/tests/test_t081_commit.py` | PASS |
| `workbench/tests/test_t082_review_boundary_e2e.py` | PASS |
| `workbench/tests/test_worktree_lifecycle_e2e.py` | PASS |

T-089 REVIEW NO_GO
