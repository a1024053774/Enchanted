# T-077 r1–r3 证据整理

2026-10-14，按主控 #96 整理。原始真实失败、预算账与诊断结论不变，不再运行模型。

- r1 的 `real-conflict-01/`、启动材料和 relay 诊断已在提交 da44c673 中保留。
- r2 的完整 `real-conflict-02/` 归档为 `real-conflict-02-evidence.tar.gz`（2,719 个文件，1,477,465 字节）。
- r3 的完整 `real-conflict-03/` 归档为 `real-conflict-03-evidence.tar.gz`（1,129 个文件，2,621,147 字节）。
- 归档条目逐文件与原文比较一致，清单和大小记录在 `real-evidence-archive-index.json`。原目录不删除、不修改；提交压缩归档及上层材料，避免把数千个逐命令输出文件重复加入 Git。
- REAL-APPROVAL-02/03、获批预算版、Launch 1 最终材料、DIAGNOSIS、诊断脚本、PLAN、答复副本及 journal 随本次证据提交。真实 r3 尾注失败保持 INCOMPLETE；本次受控证明结果另存，不回填或覆盖 r3 run.json。

在本 worktree 下恢复完整目录（目标目录已有文件时先选择新 checkout，避免覆盖）：

```sh
tar -xzf evidence/2026-10-11-batch13/T-077/real-conflict-02-evidence.tar.gz -C evidence/2026-10-11-batch13/T-077
tar -xzf evidence/2026-10-11-batch13/T-077/real-conflict-03-evidence.tar.gz -C evidence/2026-10-11-batch13/T-077
```

归档内原有的 fixture-artifacts.tar.gz 已保存 Git/SQLite/rollout 现场；其自建 CODEX_HOME 的 auth.json 未进入这些现场归档。外层归档不读取或复制用户 home。没有任何单个证据文件超过 5 MB；若后续受控运行生成超限文件，停止交主控归档。
