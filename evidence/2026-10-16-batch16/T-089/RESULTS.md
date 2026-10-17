# T-089-1 worker 交付记录（2026-10-17）

当前状态：PASS（修复后的 worker 自检）。主控 #5 要求的阶段边界修复和实际 S3 main 补证已完成，主控 #6 沙箱外执行 rc 0，九个归档场景、实际 main 基线/候选及两个调用处变异、新 T-086 回放全部符合预期。独立审查 01 对旧候选 `115dc1a622ce578fc8119cdc2675b39a5b4e70cf` 的 NO_GO 原文保持不变；新候选的独立审查与门禁仍为 INCOMPLETE，由主控另开 reviewer，不宣称整票已验收或集成。

任务：T-089 / a1 / s16-t089；ready_rev 1；起点 c544b29049861998e11eeb7344b457103fab3c98。启动与会话信息见 `session.json`；任务原文见 `task-card-T-089-1.md`。

## 当前候选

`workbench/tests/archive_evidence.py` 提供命令和共用归档函数。修复后，准备子进程执行挂载检查、拒绝覆盖、复制、相对文件名/数量/总字节及逐字节核对、清单写入，完全不删除原件；该阶段超时保留全部原件。父进程收到准备完成结果后，再启动独立的原件回收阶段。回收失败或超时返回 exit 1 和 INCOMPLETE，确认归档已经完成并核对，列出剩余原件；不再声称全部原件保留。准备、回收和失败后的状态核对分别有期限；状态无法读取时列入 unverified_originals，不误报已回收，不重试。证据生产者须先停止。

类别：目录名 run/fixtures 或 run-/run_/fixtures-/fixtures_ 前缀，以及含 run.json 的目录；文件为 .tar.gz、.bin、.sqlite/.sqlite3 及对应 -wal；名称含 monitor 且以 .log/.jsonl/.txt 结尾的日志。类别外不动；根目录 run.json 摘要保留。被作为输入读取的小文件可用重复的 `--keep` 相对路径保留；若处于待归档的运行目录中，整个运行目录保留。任务卡模板只新增一句。

`run_s3_regression.py` 已删除原归档函数，直接导入共用实现；调用处保留原先大于 5 MiB 的筛选阈值、原归档目的地与 replay 命令。没有保留第二份运行时实现。

```sh
python3 -B workbench/tests/archive_evidence.py evidence/<批次>/<ticket> --timeout 120 --keep <可选输入相对路径> --replay python3 <证据生产脚本及参数>
```

## 旧候选的验证记录

| 要求 | 状态与证据 |
| --- | --- |
| 新命令契约红态 | PASS；`red-revision-proof.json` 证明起点无入口；含 run 与 tar.gz 的同一夹具在 `red-fixture-01.json` 失败 |
| 本地归档与保留规则 | PASS；`local-checks-final.json`，真实命令子进程，显式注入 / 挂载点与 /tmp 目的地；不冒称真实外置盘 |
| 缺盘、冲突、截断、同长度损坏 | PASS（本地）；各失败且原件逐字节保持，未创建内置盘替代位置 |
| 反事实 | PASS；`no-verification-mutant-01.json` 拒绝删除核对步骤的变异，截断和同长度损坏均被测试识别 |
| 三个真实输入文件 | PASS；`t086-local-02.json` 中复制自真实 T-075 的样本，经入口后不变 |
| T-086 副本回放 | PASS（本地）；10,064 文件 / 107,177,272 字节，归档 35 项 / 104,581,061 字节；清单重建等于原件，原仓库未变 |
| evidence 引用 | PASS（范围核对）；`reference-audit.md` 逐文件列出 44 个源码文件的用途与结果；没有重跑历史业务验收 |
| 真外置盘与受控挂起 | PASS（主控运行）；`external-checks-01.json` 六个场景按预期，errors/skipped 为空；主控报告运行后没有残留 archive_evidence 进程 |
| T-086 外置盘回放 | PASS（主控运行）；`t086-external-01.json`：10,064 文件 / 107,177,272 字节，归档 35 项 / 104,581,061 字节，余 141 文件，原件不变 |
| 原 S3 入口起点状态 | NO_GO（既有状态）；旧审计拒绝，见 `s3-baseline-local-01/check.json` 和 `issue-s3-baseline.md`；没有业务用例执行，不算绿态 |
| S3 rebased CAS 对照 | PASS（仅 CAS 业务场景）；`s3-rebased-baseline-01/check.json` 与 `s3-rebased-candidate-01/check.json` 均退出 0、1 个用例、0 失败/错误/跳过；未经过被修改 runner 的 main，不足以证明抽取调用链等价 |
| S3 归档函数边界对照 | PASS（仅直接函数正常路径）；`s3-archive-baseline-01.json` 与 `s3-archive-candidate-01.json` 证明 5 MiB 边界与字节，但未覆盖 main 的传参、调用位置和 summary；原组合证据因此 INCOMPLETE |
| 本票原始 CAS 输出归档 | PASS；三个 `cas.archive.json` 对应外置盘 8/7/8 个文件、1,762,304 / 43,800 / 1,738,320 字节；`s3-final-readback.json` 再次核对实物与清单一致，仓库原目录已移除 |
| project_map status | 完整主仓库 PASS（0 problems/0 stale）；稀疏 worktree 3 处缺文件，主控裁定不补写，见 `map-status-*.json` |
| 独立审查与门禁 | 审查 01 对旧候选为 NO_GO；新候选的独立审查与门禁为 INCOMPLETE，交主控另开只读 reviewer 并按受管流程执行 |

首轮 keep 祖先目录错误的现场在 `local-checks-01.json`；修正后证据保留于后续编号，不覆盖失败结果。

## 复现与交接

真实外置盘及受控挂起已由主控执行（只写本票外置盘下新建测试目录，原始夹具与清单在那里保留）：

```sh
zsh evidence/2026-10-16-batch16/T-089/controller_checks.sh
```

S3 原入口的历史坐标审计问题由主控 #2 裁定：不在本票修复，用组合证据验证抽取。主控 #3 已运行完整 pipeline，rc 0，顺序为两个 baseline 通过、应用抽取补丁、两个 candidate 通过、归档本票输出。起点命令如下，候选仅将 phase 改为 candidate 并使用新的输出路径；已有输出不覆盖：

```sh
python3 -B evidence/2026-10-16-batch16/T-089/check_s3.py baseline --rebased --output evidence/2026-10-16-batch16/T-089/s3-rebased-baseline-01
python3 -B evidence/2026-10-16-batch16/T-089/check_s3_archive.py baseline --output evidence/2026-10-16-batch16/T-089/s3-archive-baseline-01.json
```

沙箱内 rebased CAS 尝试在 `/bin/ps` 被权限拒绝，属于环境错误，见 `s3-rebased-baseline-local-01/check.json`；不记为业务红态或绿态。该尝试启动的夹具 daemon 已经由其自己的门禁入口核对 PID/状态目录后停止，`sandbox-fixture-cleanup.json` 确认 PID、套接字和 PID 文件都不存在。

完整命令为 `zsh evidence/2026-10-16-batch16/T-089/controller_s3_pipeline.sh`；分步脚本为 `controller_s3_baseline.sh` 与 `controller_s3_candidate.sh`。pipeline 是本次起点到候选的执行记录，补丁已应用，不能在当前候选直接重复应用；复现须从指定起点开始，并把输出参数改为新目录。主控日志及完成来源见 `controller-decision-02.md`。

独立审查及门禁验收仍由主控执行，不以 worker 自检代替。未写禁止修改的 .project-map/ 其他文件。

交付检查：Python 语法、UTF-8 无 BOM、修改路径边界与唯一运行时归档函数检查均 PASS；最终 status 见 `map-status-completion-*.json`。源码的 Git 空白检查通过；已执行的原始 `s3-extraction.patch` 保留三个空行的单空格上下文标记，因此该补丁记录不参加源码尾空白检查，不修改其输入现场。

## 审查后修复 01

裁定与替换点见 `controller-decision-03.md`；独立审查原文和原外置盘现场不改。删除阶段不是仍可能返回“准备超时、全部原件保留”的阶段：父进程必须先收到准备全部完成的结果，随后才发起原件回收。

红态：新增真实入口删除 EIO 检查在旧实现失败，见 `reclaim-red-01.json`；a.bin 已回收、b.bin 保留、归档完整，但旧实现未报告阶段和剩余原件。当前测试对已知坏提交 115dc1a62 的同一反事实也成立，见 `reclaim-parent-red-02.json` 和 `reclaim-counterfactual-02.json`。独立审查的删除挂起红态见审查报告记录的 `checks/candidate-delete-hang/`。修复后的本地七场景通过，见 `reclaim-local-green-04.json`，包含删除 EIO 及剩余原件元数据不可读时的未知状态；复制挂起和删除挂起只由主控在沙箱外运行。

主控 #6 已在沙箱外运行，rc 0：

```sh
zsh evidence/2026-10-16-batch16/T-089/controller_review_fix_01.sh
```

该脚本以新命令快照运行九场景（含复制挂起、删除挂起、删除 EIO 及回收状态不可读）；`check_s3_main.py` 让起点与候选经过实际 main，强制大文件，检查清单和 summary，同时拒绝阈值与目的地两个调用处变异；最后重新回放 T-086。原始输出只写本票外置盘新目录，仓库留文本结果。

| 本次证据 | 结果与范围 |
| --- | --- |
| `reclaim-external-green-01.json` | PASS；9 场景、errors/skipped 均空。复制挂起约 2.033 秒，全部原件不变；删除挂起约 0.964 秒、删除 EIO 约 0.107 秒，均 exit 1、archive_verified 为 true，剩余原件准确为 b.bin，不再宣称全部原件保留；状态元数据不可读时明确列入 unverified_originals |
| `s3-main-02.json` | PASS；起点与候选都运行原始 CAS 用例和实际 run_s3_regression.main()，各 1 个用例、0 失败/错误/跳过。5,242,912 字节的强制文件归档且字节一致，恰好 5,242,880 字节文件保留，清单路径及 summary.external_archives 一致；阈值和目的地变异虽 main exit 0，oracle 均判 NO_GO |
| `t086-external-02.json` | PASS；10,064 文件 / 107,177,272 字节，归档 35 项 / 104,581,061 字节，余 141 文件，仓库原件不变；三个真实输入样本及引用范围核对仍通过，不把历史业务验收写成已重跑 |
| `repair-final-readback-01.json` | PASS；worker 只读核对外盘 CLI 快照、实际 main 候选源码均与当前文件逐字节相同；回收诊断和实际运行收据、归档字节一致 |

主控 #6 报告真实 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077` 在运行前后均不存在，运行结束无残留进程；worker 另做只读事后检查，确认挂载中的外盘上该目录不存在，不补称独立事前观察。完整回执及日志路径见 `controller-decision-04.md`。实际 main 的测试替换点和理由仍见 `controller-decision-03.md`，没有修改审计器文件、acceptance/ 或 main 参数。

新候选使用本轮新证据，不沿用旧候选的通过结论。`independent-review-01.md` 与 `REVIEW-OUTSIDE-01.sh` 均原文提交，独立审查 01 的 NO_GO 不修改为 PASS。
