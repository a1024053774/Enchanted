---
id: T-089
title: 证据归档脚本：把批次里的大块原始输出搬到外置盘并留清单，并改任务卡模板
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

落实 [T-088](T-088-evidence-archive-policy.md) 的决定（用户 2026-10-16 作答，细节与逐字引用见该票）。从 `evidence/2026-10-16-batch16` 的新批次起，仓库只留文本摘要，整个 run/fixtures 目录、`*.tar.gz`、`*.bin`、sqlite 及 `-wal`、监视器日志归档到 `/Volumes/WD-Elements/a2a-evidence/<批次目录>/<ticket>/`，仓库里留 `*.archive.json`（original、archive、bytes、replay）。

1. 一个归档命令，把 `evidence/<批次>/<ticket>/` 下符合"归档类别"的文件或目录搬走并写清单。写归档前外置盘未挂载就报错退出，不回退内置盘；原目录删除前核对文件数与总字节数一致（沿用 `workbench/tests/run_s3_regression.py` 的 `archive_large_files` 逐字节比较做法，把它抽成这个命令能复用的函数，不留两份实现）。
2. 任务卡模板（`.project-map/templates/task-card.md`）加一句：摘要写仓库，原始大块输出写外置盘归档路径；不增加额外提示轮次。
3. 一次回放：选一个已有批次（建议 T-086，约 120 MB、几十个 run 目录）在一次性副本里演练归档，证明仓库侧引用不悬空：`workbench/tests/`、`acceptance/` 里读 `evidence/` 的路径逐个核对，被当输入读取的小文件仍在仓库。**不要对真实的已提交批次执行搬迁**（用户决定"历史不动"）。

## Acceptance

- [ ] 红态：在没有这个命令的当前 `main` 上，对一个含 run 目录与 `.tar.gz` 的夹具批次，没有可用入口把它们搬走并留清单。
- [ ] 绿态：夹具批次归档后，仓库侧只剩摘要与 `*.archive.json`；外置盘上文件字节与原件一致；清单字段齐全。
- [ ] 反例（每个都要在真实入口失败并保留现场）：外置盘未挂载；目标文件已存在；归档后字节不一致（用被截断的副本模拟）。三种都不得删除原件、不得回退内置盘。另加第四个（构思主控 2026-10-17 增补，用户未逐条确认）：外置盘已挂载但读写挂起，归档须带读写超时，超时按失败处理、不删原件。
- [ ] 被测试或门禁当输入读取的小文件（`run_daemon_acceptance.py` 读的三个文件为样本）不被归档；归档类别以外的文件原样保留。
- [ ] 一次性副本里对 T-086 回放：核对引用不悬空，列出每个读 `evidence/` 的测试及其结果。
- [ ] `project_map.py status` 0 problems。

## 说明

- 来源：T-088 的 build 票；构思主控建票。尚未标 ready，等用户说开工再派；与 T-078、T-082、T-087 的文件基本不重叠，但 `workbench/tests/run_s3_regression.py` 是 T-077 的回归入口，改它要先在基线上取绿态。
- 写入范围（预期）：新归档命令放 `scripts/` 或 `workbench/tests/`（执行时定）、`.project-map/templates/task-card.md`、`workbench/tests/run_s3_regression.py`（抽函数）、本票证据。
- 用户决定"历史不改写、不迁移"；开源前是否瘦身历史另议，不在本票。

## 就绪

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："那现在都idle了，让他继续啊，漏掉的也开工"，构思主控据此标就绪（`ready_rev: 1`）。
