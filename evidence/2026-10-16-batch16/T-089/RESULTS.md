# T-089-1 worker 交付记录（2026-10-17）

状态：PASS（本任务卡的实现与 worker 自检）。本地验证、主控外置盘验证及获准的 S3 组合基线对照均通过，抽取已完成。原入口 main() 的起点失败事实保留，未改审计器或 acceptance/。独立审查和门禁验收仍为 INCOMPLETE，由主控后续执行；本报告不宣称整票已验收或集成。

任务：T-089 / a1 / s16-t089；ready_rev 1；起点 c544b29049861998e11eeb7344b457103fab3c98。启动与会话信息见 `session.json`；任务原文见 `task-card-T-089-1.md`。

## 当前候选

`workbench/tests/archive_evidence.py` 提供命令和共用归档函数：挂载检查、拒绝覆盖、复制后核对文件名/数量/总字节及逐字节相等、清单无校验值，全部核对及清单写完后才删除原件，整个读写子进程有期限。失败保留原件和已创建的副本，不重试、不回退。证据生产者须先停止。

类别：目录名 run/fixtures 或 run-/run_/fixtures-/fixtures_ 前缀，以及含 run.json 的目录；文件为 .tar.gz、.bin、.sqlite/.sqlite3 及对应 -wal；名称含 monitor 且以 .log/.jsonl/.txt 结尾的日志。类别外不动；根目录 run.json 摘要保留。被作为输入读取的小文件可用重复的 `--keep` 相对路径保留；若处于待归档的运行目录中，整个运行目录保留。任务卡模板只新增一句。

`run_s3_regression.py` 已删除原归档函数，直接导入共用实现；调用处保留原先大于 5 MiB 的筛选阈值、原归档目的地与 replay 命令。没有保留第二份运行时实现。

```sh
python3 -B workbench/tests/archive_evidence.py evidence/<批次>/<ticket> --timeout 120 --keep <可选输入相对路径> --replay python3 <证据生产脚本及参数>
```

## 验证

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
| S3 rebased CAS 对照 | PASS；`s3-rebased-baseline-01/check.json` 与 `s3-rebased-candidate-01/check.json` 均退出 0、1 个用例、0 失败/错误/跳过；主控 #2 的组合基线裁定见 `controller-decision-01.md` |
| S3 归档函数边界对照 | PASS；`s3-archive-baseline-01.json` 与 `s3-archive-candidate-01.json` 均通过；恰好 5 MiB 保留，5 MiB + 17 字节（5,242,897 字节）的文件归档，内容保持一致 |
| 本票原始 CAS 输出归档 | PASS；三个 `cas.archive.json` 对应外置盘 8/7/8 个文件、1,762,304 / 43,800 / 1,738,320 字节；`s3-final-readback.json` 再次核对实物与清单一致，仓库原目录已移除 |
| project_map status | 完整主仓库 PASS（0 problems/0 stale）；稀疏 worktree 3 处缺文件，主控裁定不补写，见 `map-status-*.json` |
| 独立审查与门禁 | INCOMPLETE；交主控新开只读 reviewer 并按受管流程执行 |

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
