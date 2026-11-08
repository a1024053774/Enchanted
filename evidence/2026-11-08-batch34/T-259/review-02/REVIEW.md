# T-259 唯一一次针对性独立复审

STATUS: PASS

SUMMARY: No findings。首轮 P1 归档中断反例在新冻结候选上独立复跑通过；限定的中断恢复范围及拒绝条件未发现新反例。来源为独立只读审查会话 `/root/t259_independent_review`，gpt-6.1-sol high；没有正式安装或数据库修改。

TARGET: `2083f72e4f43d6bc84be2ef57b5fef49f65e1bcb`，仓库 `/private/tmp/a2a-t259-repair-20261108`；本轮修复基线 `fb96f5aee181035a1fc810ead1e952dba10cbef8`。审查前后 HEAD 相同、工作树干净。

EVIDENCE:

- 首先重跑原独立反例，PASS，退出 0，10 项检查通过。真实 PTY 创建后首次身份读取失败，确认停止；真实归档落盘后注入后续执行丢失；正常重启 daemon 后同一 attempt 成功回收、释放原路径、允许新 attempt，重复回收成功，无任务输入。结果见 `original-counterexample.json`。
- 从契约核对 core.ts:4609 的归档前停止证明和事件位置，以及 core.ts:4521 对同 task/attempt/launch、晚于位置的归档事实核验；恢复仍经过创建身份及输入检查，之后才保存 reclaimed 与释放路径。
- 限定恢复边界共 104 项通过，退出 0，见 `recovery-boundaries.json` 与 `recovery_boundaries.ts`。包括归档前后中断、脏工作区、完成保存后清理前中断；缺阶段记录、旧归档、异 attempt、错误 shell、晚到输入均拒绝并保留路径。
- 独立加入三个未见条件：归档后新增原生会话 `unseen-post-archive-native-20261108`、排队输入 `unseen-post-archive-queued-20261108`、恢复时操作锁。分别返回 preparation_input_unproven、preparation_input_unproven、operation_busy，原 attempt 未释放。
- 独立复跑忽略归档顺序的变异，按预期 FAIL、退出 1；“拒绝回收”和“保留路径”业务断言失败，非夹具错误。见 `mutant-archive-order.json`。
- 审查已读取候选原始 310 项、普通入口 9 项、归档中断入口 11 项、四种变异及 T-253/T-170 回归证据；不把新测试自身当作 oracle。没有修改 panes、schema、权限、公开接口或冻结验收。
- 测试私有 core 与夹具已清理；本目录只保留文本。项目地图 Problems 0、Stale 0。

复跑命令（原脚本同时归档在候选 review-01 目录，输出必须用新名称）：

```sh
PYTHONPATH=/private/tmp/a2a-t259-repair-20261108/workbench/tests ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 /private/tmp/t259-review-20261108-independent/archive_gap_e2e.py --summary /private/tmp/t259-review-20261108-rereview/original-counterexample.json
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache node /private/tmp/t259-review-20261108-rereview/recovery_boundaries.ts . /private/tmp/t259-review-20261108-rereview/recovery-boundaries.json
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/run_t259_checks.py --mutant ignore-archive-order --summary /private/tmp/t259-review-20261108-rereview/mutant-archive-order.json
```

FINDINGS: 无新增发现。首轮 P1 反例关闭；第一次 FAIL 报告照旧保留。

COUNTEREXAMPLE: 原 unknown_pane 归档中断可恢复；缺阶段、旧归档、外来归档、错 shell、晚到输入/原生会话、排队输入和锁冲突均拒绝；忽略归档顺序的坏实现被拒绝。

LIMITATIONS: 唯一一次定向复审，不是全仓审查或全套测试。真实本地 daemon/socket/PTY，使用无模型等待程序；不是模型能力验收。以真实归档后异常与正常后台重启构造中断，没有 SIGKILL。未安装正式应用；不代替用户对敏感变更的批准。检索/记忆能力 N/A。

RULE: 首轮要求的 pane_archived→reclaimed 中断已纳入 `test_t259_preparing_reclaim_e2e.py --archive-gap`，并由原独立脚本验证通过。
