# T-078 #192/#193：材料 revision lineage 修复交接

旧 `09b-stage-a-01/result.json` 保留为红态：`Executable packet is stale; no spawn`、`spawned=false`、无 root/进程。

`run-09b.py` 现在要求：

- 材料 revision 是当前 HEAD 的祖先；
- `revision..HEAD` 只包含本票证据目录变更；
- `workbench/`、`scripts/`、`run-09b.py`、`prepare-09b-executable.py` 出现差异即拒绝。

新 [commit-09b-run-03.sh](commit-09b-run-03.sh) 会以当前提交为 source，冻结 `09b-executable-materials-03`，再运行 revision spy。spy 绿态接受当前祖先/证据 lineage，`workbench/src/claudeLaunch.ts` 反例拒绝，`spawned=false`，不启动阶段 A。

请运行：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-09b-run-03.sh
```

运行后再用新 materials-03 重新签 stage-A approval；本轮不执行 runner、不启动 daemon/API/target。

T-078 09B-RUN READY
