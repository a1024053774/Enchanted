# T-150 冻结候选只读核对（2026-10-23）

以下为 `t150_acceptance` 新上下文子 agent 按 behavioral-acceptance-review 技能返回的报告。它是 worker 侧的有界核对，正式 reviewer、门禁验收与集成仍由执行主控负责。此后只补证据文档，没有再改测试或产品。报告正文如下：

STATUS: PASS
TARGET: 4aefa2b3a884fde62c6bb72d074165111496f016

EVIDENCE:
- 从 T-150 任务卡、ticket、授权收件箱及 T-091、T-096、T-119、T-139 重建契约；未读取 RESULTS.md、ASSERTIONS.md 或实现讨论。
- 对比父版本：产品代码及其他测试未改；跨窗 key、iframe、未知窗口拒收、错误凭据防护、迟到凭据撤销、空布局持久化检查保留。选择模型调整符合现行票据。
- 独立运行冻结候选：`node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs --revision 4aefa2b3a884fde62c6bb72d074165111496f016 --summary <新路径>`，退出 0；默认运行中的九个变异均被指定业务断言拒绝。
- 审查者在临时测试副本中替换项目、任务、attempt、问题及模型等标识，使用随机新输入后通过。
- 原始输出、退出码及复现命令：`/tmp/t150-acceptance-final-ma2d4q7r/audit-summary.json`。结束时候选未变，工作区干净；地图检查 0 problems、0 stale。

FINDINGS:
- 无。

COUNTEREXAMPLE:
- 独立运行 `--mutant no_key`：退出 1，命中保留的 `test_t091_pane_ipc.mjs:246`——`Unregistered pane key was accepted`；属于业务断言失败。
- 关闭竞争、空布局、iframe 等其余变异也命中对应断言，未将导入失败或进程崩溃算作红态。

LIMITATIONS:
- 结论仅覆盖真实 main/preload 模块在 VM 中的契约逻辑；Electron、传输、凭据及文件系统边界由夹具提供，无真实 GUI、后台、CLI、权限执行或发布证明。
- 未审查交付说明文档；正式审查、门禁验收与集成仍由执行主控负责。
- 随机输入探针首次调用误传互斥参数，失败现场保留于临时目录；修正调用后通过，不计作产品红态。

RULE:
- 不适用。

## 证据副本与重放

小型文本输出复制到 [audit-01/audit-summary.json](audit-01/audit-summary.json) 所在目录；临时目录未删除。worker 冻结提交复跑也保存在 `audit-01/worker-frozen-replay.json`，退出 0。

随机输入副本以相对冻结测试的 `audit-01/unseen-inputs.patch` 保存，不引入第二个测试入口。重放时先取出冻结测试，再应用该补丁：

```sh
probe=$(mktemp /tmp/t150-audit-XXXXXX.mjs)
git show 4aefa2b3a884fde62c6bb72d074165111496f016:workbench/tests/test_t091_pane_ipc.mjs > "$probe"
patch "$probe" < evidence/2026-10-23-batch23/T-150/audit-01/unseen-inputs.patch
node --experimental-vm-modules "$probe" --source "$PWD" --summary /tmp/t150-audit-unseen-NEW.json
```

`--summary` 要使用新的路径。原审查命令与退出码见保存的 `audit-summary.json`；重放用相同生产版本，避免把后续产品变更当作本候选证据。
