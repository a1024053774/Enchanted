# T-089 第三轮独立审查

候选：`ef3b1ade9e4511673435d8e28adaf2354a9240d3`；起点：`c544b29049861998e11eeb7344b457103fab3c98`。总体：**PASS**，依据 T-089@`144d5afee` 的新裁定及本轮独立重跑证据；未确认需修复的产品缺陷。

定稿时间：2026-10-17。本轮外置盘原件位于 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089/review-outside-03-pli_e93e/`，下文称外置盘根目录。已逐项读回命令、退出码、oracle、patch、原件、归档和清单，未沿用前两轮或 worker 的判定。审查 PASS 表示符合失败处理契约；删除 EIO、删除挂起两次归档操作的业务状态始终是 **INCOMPLETE**。

## 契约与范围

- 先读取主仓库的 reviewer 角色卡，再读取 T-088、任务卡及冻结候选原文；T-089 以 `git -C /Users/luckye/Documents/Code/a2a show 144d5afee:.project-map/tickets/T-089-evidence-archive-tool.md` 为准。worktree 的旧 ticket 不作本轮 oracle。
- 新裁定原文：“复制到外置盘、核对、写清单这一段不得丢原件。回收阶段失败就报 INCOMPLETE 并列出剩余原件，数据可从已核对的归档找回。”另按本轮派发要求核对回收失败有测试覆盖。
- 小目标：独立核实六条 Acceptance、S3 抽取和结构风险。非目标：不实现、不修复、不建立 worktree、不提交或集成、不调用模型、不写全局配置。只有本报告、`REVIEW-OUTSIDE-03.sh` 与本轮新建的 `/tmp` 目录有写入。
- 使用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review 和 document-writing。审查本身未开子 agent。
- 一次性副本：`/private/tmp/t089-review-03-xy2hcz72`，用 `git archive` 解出冻结路径；变异均在此目录。候选 HEAD 仍是冻结提交。启动时已有 `independent-review-02.md`、`REVIEW-OUTSIDE-02.sh` 未跟踪文件，未修改。

## 六条 Acceptance

| 条目 | 本轮状态 | 证据与范围 |
| --- | --- | --- |
| 1. 无命令的起点红态 | PASS | 起点 `git ls-tree` 无 `workbench/tests/archive_evidence.py`；独立夹具含 run 目录及 `.tar.gz`，同入口命令退出 2，原件完整。本地及外置盘均重跑；外置盘 `supplemental/red-entry/command.json` 保存 argv、输出和退出码。 |
| 2. 正常归档、外置盘字节与清单 | PASS | 真实外置盘 CLI exit 0。独立夹具包含嵌套超过 1 MiB 的二进制、空目录、中文路径、sqlite 两种后缀及各自 `-wal`、三种监视器日志。12 个归档文件的字节全部符合预先给定的夹具，生成 11 份清单；严格为 `original/archive/bytes/files/replay`，必需四字段均在，无校验值。原件回收后只留下保留项与清单。来源：外置盘 `checks/candidate-normal/{command,oracle}.json` 及磁盘产物。 |
| 3. 四反例、准备失败保全与回收失败 | PASS（失败处理契约） | 真实入口的未挂载、目标冲突、截断、已挂载但复制挂起均 exit 1，原件完整且不回退；另核实等长损坏、复制/核对/写清单的 EIO 和挂起。两次回收失败均 exit 1、stderr 为 `INCOMPLETE`、stdout 为空；剩余清单精确等于磁盘 `b.bin`，两份已核对归档的全部字节仍可恢复。来源：外置盘 `checks/candidate-*/{command,oracle}.json` 及下节逐项读回。 |
| 4. 被读取的小文件与类别外保留 | PASS | 三个样本从冻结提交的 T-075/card-5 原文取出，本地及真实盘入口后字节不变；普通 JSON、普通日志、非 tar 的 `.gz`、根 `run.json`、普通文本原样保留。`--keep run-protected/consumer.bin` 保留被读取的 `.bin` 及整个 run 祖先。未导入生产类别或比较函数作为 oracle。来源：外置盘 `checks/candidate-normal/` 的实际保留文件与冻结 `git show` 原文。 |
| 5. T-086 副本回放及引用 | PASS（本次引用范围） | 本地与真实盘均从冻结 `git archive` 解出 10,064 个文件、107,177,272 字节；归档 35 项、104,581,061 字节，剩余 141 个文件；逐份读清单与归档后能重建全部相对路径和字节，真实 T-086 未变。47 个带 evidence 路径的冻结源码文件均有逐文件引用/读取点清单，未见 T-086 引用；没有把未运行的历史业务测试写成通过。来源：外置盘 `supplemental/t086/{command,replay}.json`、`supplemental/reference-audit.json` 及原件逐字节读回。 |
| 6. project_map.py status | PASS（完整仓库）；稀疏目录有限制 | 定稿前完整主仓库 status 再次 exit 0：0 problems、0 stale；稀疏 worktree exit 1，有 README 与 `.grilling/a2a-gui-client.md` 缺失引起的 3 个问题、0 stale。起始命令及对应 HEAD 保存在外置盘 `reviewer-source/map-status-{primary,sparse}.json`；最新原始结果在本轮 `/tmp` 的 `map-status-final03-{primary,sparse}.json`。完整仓库检查与冻结候选的代码审查分开记录，没有把稀疏目录的非零结果写成通过。 |

本地复现命令：

```sh
python3 -B /private/tmp/t089-review-03-xy2hcz72/review_checks.py --root /private/tmp/t089-review-03-xy2hcz72/local-01
python3 -B /private/tmp/t089-review-03-xy2hcz72/supplemental.py --root /private/tmp/t089-review-03-xy2hcz72/supplemental-local-01
python3 -B /private/tmp/t089-review-03-xy2hcz72/candidate/workbench/tests/run_evidence_archive_checks.py --command /private/tmp/t089-review-03-xy2hcz72/candidate/workbench/tests/archive_evidence.py --output /private/tmp/t089-review-03-xy2hcz72/candidate-suite-local.json
```

以上命令均 exit 0；输出路径采用排他新建，复跑时须换一个新结果目录/文件，保留旧现场。本地模拟显式使用挂载点 `/`，不是实际外置盘证据；生产默认挂载点没有改动。

## 本轮外置盘原件读回

主控执行 `zsh evidence/2026-10-16-batch16/T-089/REVIEW-OUTSIDE-03.sh`。逐段原始记录 `source-snapshot.json`、`independent-entry-checks.json`、`candidate-regression-checks.json`、`replay-and-s3-readback.json` 均 exit 0、`hard_watchdog=false`。总日志在 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t089-review-outside-03.log`。

独立入口检查覆盖 13 个好候选场景与 4 个变异，无跳过。以下记录是产品命令实际结果；每一行的完整 argv、stdout、stderr、退出码与独立 oracle 均在外置盘 `checks/candidate-<场景>/`：

| 场景 | 实际结果与原件读回 |
| --- | --- |
| `normal` | exit 0；归档字节、类别、空目录、11 份清单、3 个真实输入样本及类别外保留项均重新核对。 |
| `unmounted` | exit 1；目标目录未创建，两份原件合计 4,199,183 字节完整，摘要不变。 |
| `collision` | exit 1；既有目标字节原样保留，两份原件完整。 |
| `truncated` | exit 1；副本被截为 7 字节，报大小不一致，两份原件完整。 |
| `corrupted` | exit 1；副本大小不变，在 1 MiB 后改字节被逐字节核对拒绝，两份原件完整。 |
| `copy-eio` / `verify-eio` / `manifest-eio` | 各 exit 1；两份原件逐字节完整；清单阶段失败保留已有副本及已写清单，不进入回收。 |
| `copy-hang` | 产品期限 0.75 秒，实际 0.784 秒 exit 1；报准备超时，两份原件完整。保留尚未刷完的部分副本，没有删原件。 |
| `verify-hang` / `manifest-hang` | 实际分别 0.929 / 0.797 秒 exit 1；报准备超时，两份原件完整。 |
| `delete-eio` | 实际 0.194 秒 exit 1；业务状态 `INCOMPLETE`，`a.bin` 已回收，剩余列表只有实际存在且字节完整的 `b.bin`；两份归档字节均与原始夹具一致。 |
| `delete-hang` | 实际 0.973 秒 exit 1；业务状态 `INCOMPLETE`，剩余列表及归档字节与上一行同样准确，超时原因明确。 |

定稿时再次读取所有上述原件与归档，而非只读检查器的 PASS 字段；还核对外置盘的三个候选源码与冻结 `git show` 字节相等、挂起夹具记录的 PID 均不存在。独立读回摘要保存在 `/private/tmp/t089-review-03-xy2hcz72/outside03-independent-readback.json`。未向外置盘追加写入。

## 准备与回收阶段

代码证据：`archive_evidence.py:145` 先复制全部计划，`:155` 核对全部计划，`:157` 写清单；`:218` 只有收到准备成功结果才在 `:222` 启动回收。`verify` 在 `:95` 核对逐文件名和大小，继而逐字节比较，强于只核对文件数和总字节数。准备阶段没有删除路径。

`run_phase` 在 `:190` 使用独立进程及期限，超时杀掉子进程并抛错；等待杀进程的后续时间也有界。回收错误在 `:223` 进入剩余原件核对并抛 `ReclaimIncomplete`；`:261` 输出 `INCOMPLETE` 后 exit 1。核对本身失败时明确列 `unverified_originals`，不捏造“已经删完”。

已提交的测试覆盖并非只靠报告：`run_evidence_archive_checks.py:125` 的 `reclaim_failure` 检查非零退出、归档字节、已删与未删项、结构化 `INCOMPLETE` 和剩余清单；`:207` 注册删除 EIO，`:208` 注册剩余状态不可读，`:212` 注册删除挂起。本轮外置盘实际运行冻结原测试的全部 9 个用例，`candidate-suite/results.json` 的 `errors=[]`、`skipped=[]`。其中删除 EIO、删除挂起命令均 exit 1、业务状态 `INCOMPLETE`；删除后状态不可读用例也 exit 1、`INCOMPLETE`，明确把 `b.bin` 列为 `unverified_originals`，没有假报剩余为空即完成。故回收阶段失败已有实际持续测试覆盖。

本地及外置盘删除 EIO、删除挂起均是实际 **INCOMPLETE 的归档操作**。独立 oracle 接受其错误处理，绝不把这些归档操作补称 PASS。`checks/candidate-delete-{eio,hang}/command.json` 保存完整 stderr；`oracle.json` 的 `observed_product_status` 仍为 `INCOMPLETE`。检查总结果也明确限定 `scope="oracle verdict only; observed reclaim failure remains INCOMPLETE"`。

## 独立变异证据

四个变异均只改一个位置，不改好候选、夹具或 oracle；完整 unified patch 在外置盘 `reviewer-source/mutants/<名称>/mutation.patch`。本轮逐份读回 patch；先运行同场景好候选，再运行变异，四个变异均被拒绝。

| 变异 | 单处错误 | 好候选与变异信号 |
| --- | --- | --- |
| `no-byte-compare` | 将 `if a != b:` 改为 `if False:` | 相同大小、在 1 MiB 之后改一个字节：好候选 exit 1 并保全原件；变异错误 exit 0，独立 oracle exit 1，拒绝。 |
| `collect-json` | 将普通 `.json` 加入归档类别 | 正常场景好候选 exit 0；变异错误搬走普通 JSON 与摘要 `run.json`，独立 oracle exit 1，拒绝。 |
| `reclaim-false-pass` | 将回收错误结构化状态从 `INCOMPLETE` 改成 `PASS` | 删除 EIO 的好候选报 `INCOMPLETE`；变异虽仍 exit 1，但伪报状态被独立 oracle exit 1 拒绝。 |
| `no-timeout` | 删除 `communicate(..., timeout=timeout)` 的期限 | 复制挂起的好候选 0.784 秒 exit 1，保全原件；变异 4.004 秒触发独立硬期限，产品进程 exit -9，独立 oracle exit 1，明确以产品超时不生效拒绝。 |

外置盘变异驱动命令、stdout/stderr/退出码保存在 `checks/*-mutation-command.json`；每个真实产品命令及 oracle 另存于 `checks/mutant-<名称>/`。四个驱动均 exit 1，拒绝原因分别是腐坏副本错误成功、类别误收、回收失败伪报 PASS、产品超时不生效；不是导入或设置失败。总结果 `checks/review-results.json` 无跳过。本地较早结果保留其当时的 skipped 记录，没有改写历史结果。

## S3 抽取与结构审查

**主控提出的两项组合基线本身不够证明调用行为等价。** rebased CAS runner 与直接调用归档函数的夹具分别通过，仍可能漏掉 `run_s3_regression.main()` 传错阈值/目的地或不调用归档。因此不把“CAS 1/0/0 + helper 对照”直接判为调用点覆盖。

这处缺口有额外的实际证据可补：审读冻结 `check_s3_main.py`，并本轮亲自读取 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089/s3-main-02-mpb065p2/` 的原始 command、driver、run.json、输入、大文件归档和边界文件。baseline/candidate 两份 runner 字节分别等于起点与冻结候选，候选 helper 也等于冻结原文；两次 actual main 均 CAS 1/0/0、exit 0，大文件 5 MiB + 32 字节搬迁，恰好 5 MiB 的文件保留，字节与独立输入一致，清单进入 `external_archives`。测试驱动只替换旧坐标 audit、隔离输出路径，并在原 `finish_evidence` 后加入两个输入文件；没有替换 main、归档调用或其参数。另记录的阈值/目的地变异正是这处调用点的反例。

本轮还用新的嵌套大文件、另一个大 `.bin`、恰好 5 MiB 的 `.bin`、小 sqlite 和零字节文件，在本地和真实盘直接对照起点原函数 AST 与新函数；两者均符合独立的 S3 大小契约。该对照通过，不能代替 actual-main 证据。原函数仅映射硬编码归档根目录，函数 AST 未改。外置盘原件为 `supplemental/prior-s3-main-readback.json`、`supplemental/s3-function-compare/comparison.json` 及其输入/产物。组合基线加上述 actual-main 调用点证据与反例，足以支持本票正常归档行为等价；没有把不同的异常恢复行为说成完全不变，也没有外推全套 S3 业务场景已重新运行。

`git diff c544b2904 ef3b1ade9 -- workbench/tests/run_s3_regression.py` 显示旧函数已删除，调用复用唯一实现，并明确传入原来的 5 MiB 阈值、原归档布局及 replay argv。新增 `files` 字段是清单补充，不替换必需字段。模板差异只有一个完整句子与空行，没有增加提示轮次。

按 design-integrity-review 检查本候选的异常边界：未确认静默吞错、自动重试、兼容分支或两份归档实现。超时后第二次有界等待不成功时仍向上抛超时；回收/剩余状态错误归本层报告，并保持非成功状态。`minimum_bytes` 是已有 S3 消费方明确需要的大小策略，不是无证据 fallback。本轮独立入口反例验证了这些错误路径的可见结果。

## 问题与限制

- 未确认需修复的产品问题；没有剩余待执行的本轮关键场景。完整仓库 status 为 0，稀疏目录的 3 个缺文件问题按上文原样报告。
- 本轮引用清单在外置盘 `supplemental/reference-audit.json`，逐文件列出 47 个源码文件、evidence 路径行号、读取点、是否涉及 T-086 和结果。它证明本次引用集合无交集，未声称全部历史业务测试通过。真实 T-086 只读，迁移发生在副本中。
- 挂起是本次夹具子进程受控 SIGSTOP、I/O 错误是文件操作边界的受控 EIO，均经真实 CLI 运行；没有真实卸载外置盘或造成设备故障。不外推无法及时响应 SIGKILL 的内核故障下进程必然已消失，也不声称并发生产证据时可安全归档；命令契约要求先停止证据生产者。
- 关键失败场景以本轮新目录重跑为准；S3 actual-main 使用已核对冻结源码的既有原始证据，并明确保留其审计替换限制。本轮不以两项组合基线单独背书调用点，也不复用第二轮失败判定。
- 未请求沙箱升级、未改候选；报告等待结果版本已保存在 `/private/tmp/t089-review-03-xy2hcz72/independent-review03-pending.md`，本轮外置盘原件保持只读。
- 初次解包遇到本机 Python 3.9 不支持 `tarfile.extractall(filter=...)`，未改候选；换新 `/tmp` 目录并明确检查 member 类型及路径后解包成功。此设置失败记录于 `setup-note.json`，不作产品红态。

T-089 REVIEW PASS
