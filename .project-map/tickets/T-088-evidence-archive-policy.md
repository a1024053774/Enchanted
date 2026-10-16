---
id: T-088
title: 证据体量：大块原始输出归档到外置盘，仓库只留摘要与清单（decide）
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## 背景

2026-10-15 执行主控报告 `evidence/` 约 4.3 GB，T-081 一票 780 MB、约 5.4 万个文件（无单个文件超过 5 MB，未 push）。项目要开源，这个体量进 Git 历史会让克隆很重。内置盘余量也偏紧（T-085 审查员副本曾把它写满一次，现约 17 GB）。

## 用户已定（逐字，2026-10-15，会话"a2a-构思主控"）

问题"evidence 目录已约 4.3 GB……证据怎么存？"，用户选"大块归档到外置盘 (Recommended)"，选项原文："今后新证据只把摘要、清单、RESULTS.md 留在仓库，原始 run 目录和 fixtures 压缩包放 /Volumes/WD-Elements，仓库里留路径和清单。已提交的历史不改写。会改"证据进入版本控制"的规则，我拉一张 decide 票再写进 AGENTS.md。"

## 决定（2026-10-16，用户逐字作答，会话"a2a-构思主控"）

用户说："T-088 的六条细节和 T-087开工"，随后以选择题逐项作答：

1. **留与归档**，用户选"文本摘要留，run 目录归档 (Recommended)"。仓库留：RESULTS.md、审查报告、controller-decision、命令脚本、run.json 摘要，以及任何被测试或门禁当输入读取的小文件（例如 `run_daemon_acceptance.py` 读的 `controller-decision-01.md`、`outside-sandbox.sh`、`readback-timing-probe.py`）。归档到外置盘：整个 run/fixtures 目录、`*.tar.gz`、`*.bin`、sqlite 及 `-wal`、监视器日志。
2. **清单格式**，用户选"不带，只记路径、大小、归档位置 (Recommended)"。不带校验值；原目录删除前核对文件数与总字节数一致即可（`run_s3_regression.py` 的 `archive_large_files` 现行做法是逐字节比较后再删，沿用）。
3. **生效点与历史**（原第 5、6 条），用户选"新批次起生效，历史不动 (Recommended)"。从 `evidence/2026-10-16-batch16` 起；已提交批次不改写、不迁移；开源前是否瘦身历史，等用户提出另开票。

## 构思主控按已有规则推出的默认（用户未逐条问，异议可随时改）

- **缺盘**：归档写入时外置盘未挂载就报错退出，不回退内置盘（AGENTS.md 构建规则已有同样原则）。读旧归档缺盘时，清单里的路径让提示指向 `/Volumes/WD-Elements`，不静默跳过。
- **门禁与脚本对证据路径的依赖**：我查了：`workbench/src/`、`scripts/` 不把 `evidence/` 当输入读（只有 `scripts/launch-worker:57` 一条注释引用）；`workbench/tests/` 与 `acceptance/` 里有测试读固定的几个小文件，按上面第 1 条留在仓库，不悬空。
- **布局沿用现有先例**：`/Volumes/WD-Elements/a2a-evidence/<批次目录>/<ticket>/…`，外置盘上已有 batch13～15（约 382 MB）；仓库侧每个被归档的文件或目录留 `*.archive.json`（字段：original、archive、bytes、replay），就是 `run_s3_regression.py` 现在写的那种。
- **现状数字（2026-10-16 实测）**：`evidence/` 4.8 GB、163,155 个文件（git 跟踪 136,623 个）、`.git` pack 825 MiB；T-081 一票 836 MB，`full-04` 一个目录就 180 MB、11,958 个文件。外置盘空余 806 GiB。

## 完成条件

- [x] 用户已作答第 1、2、5、6 条（见上）；第 3、4 条为按已有规则推出的默认。`AGENTS.md` 的"证据和交付"已追加条款（2026-10-16）；任务卡模板不在构思主控写入范围，由 T-089 修改。
- [x] 改规则后的 build 票是 [T-089](T-089-evidence-archive-tool.md)。
- [x] `project_map.py status` 0 problems（关闭前复跑）。

## 说明

- 来源：执行主控完成报告 `20261015T152406Z-executor-report-001`，用户本人在构思主控会话里选择了方向。
- 本票关闭后、T-089 合入前：执行主控从 batch16 起新证据只把摘要写仓库，原始大块输出尽量写到外置盘布局下；归档脚本由 T-089 提供。

## Resolution

2026-10-16 关闭，结论 PASS（决定类，无运行证据）：新批次（`evidence/2026-10-16-batch16` 起）只把文本摘要与 `*.archive.json` 清单留在仓库，run/fixtures 目录、`*.tar.gz`、`*.bin`、sqlite 与监视器日志归档到 `/Volumes/WD-Elements/a2a-evidence/<批次目录>/<ticket>/`；清单不带校验值；缺盘报错；已提交历史不改写。用户作答第 1、2、5、6 条；第 3、4 条是构思主控按已有规则推出的默认，用户未逐条确认。规则已写入 `AGENTS.md` 的"证据和交付"。落地由 [T-089](T-089-evidence-archive-tool.md) 做，尚未标就绪。
