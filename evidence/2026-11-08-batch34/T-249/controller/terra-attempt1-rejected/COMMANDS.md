# 重放与原始输出

机械核对不依赖夹具或产品 worktree，在本仓库根运行：

```sh
python3 evidence/2026-11-08-batch34/T-249/terra/check_observations.py
python3 evidence/2026-11-08-batch34/T-249/terra/check_observations.py evidence/2026-11-08-batch34/T-249/terra/wrong-commit.json
python3 evidence/2026-11-08-batch34/T-249/terra/check_observations.py evidence/2026-11-08-batch34/T-249/terra/mixed-file.json
```

预期依次退出 0、1、1；红态副本仅更改观察值，不改 oracle。原输出已保存。`capture_oracle.py` 记录了采集 Git 细节的命令；它用于原始夹具还存在时重采，不是上述机械重放的依赖。操作前 oracle 来自主控独立准备脚本，非产品代码。

常规测试从候选 `18c108fcaed1c4ecf51831f2272578a3b09427be` 的 `/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-249-1-a5` 运行。三项命令各自设置 `TMPDIR=/private/tmp/t249-terra-20261108-01/tmp`、`TMP` 和 `TEMP` 为相同值：

```sh
python3 acceptance/T-249/check_git_graph.py
node --test workbench/tests/test_t249_git_host.mjs
python3 workbench/tests/test_t249_outside_safety.py
```

原始 stdout/stderr 连同退出码分别保存在 `acceptance.log`、`node.log`、`outside.log`。重放产品测试需要该固定候选和依赖，原临时目录清理后需另建授权夹具目录。包与父候选产品代码等价检查命令：

```sh
git diff --exit-code 1243bc15f979976967cfd2d5cdd3a2acce6df635 18c108fcaed1c4ecf51831f2272578a3b09427be -- workbench acceptance
```
