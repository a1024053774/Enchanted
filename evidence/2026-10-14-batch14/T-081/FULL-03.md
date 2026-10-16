# T-081 full-03 交接（主控 #166）

状态：INCOMPLETE。runner 已修正并取得局部修前/修后证据；完整 full-03 尚未运行。full-01、full-02 及其临时源码快照保留原样。

## 根因与修正

full-02 的真实异常发生在第一个 `t075-coop` 回归结束后：子套件已 PASS（8/8、0 failures/errors、清理正常），并自行生成 `fixtures.tar.gz`。runner 又对同一路径执行 `tarfile.open(..., 'x:gz')`，因此 FileExistsError；不是门禁拒收、正例集成或顶层 RESULTS 写入失败。原 traceback 仍见 `full-02/run.json`。

runner 现在按现有子套件的真实归档契约指定唯一写入者。自行归档的七种子套件只核对普通归档文件存在，不重写；缺失时报错，不由父流程补造。其余夹具由 runner 独占创建归档，遇到意外已有文件仍报错并保留。不会用 append、覆盖或捕获 FileExistsError 后继续的方式掩盖问题。

检查后续直接调用还发现，旧候选快照只复制 workbench，打分 schema 子套件却需要 `scripts/score`、`scripts/launch_records.py`、`scripts/record_io.py`。runner 现把这三个已有文件一起冻结、复制和归档；不改文件内容。打分夹具也由 runner 保存完整归档。

局部证据：

- `archive-red-01/run.json`：旧 runner 在已完成子套件的真实收据和归档副本上复现 FileExistsError；另证明旧逻辑会静默补建缺失的子套件归档。
- `archive-green-01/run.json`：修后四个归档边界检查全部通过，包含原有异常文件不被覆盖。仅执行收尾函数，未启动 daemon 或模型。
- `score-source-check-02/run.json`：旧快照在原打分 suite 入口因缺少 score 文件失败（harness_error，不计门禁红态）；使用 runner 实际组装语句生成的新快照后，原 suite 的 34 项检查通过，主仓分数记录未写入。
- `score-source-check-01/` 保留准备检查脚本的一次定位错误：同时选中了冻结循环和复制循环，数量检查报错。它不是产品失败，也没有替换或覆盖后续证据。

本轮只改 runner，新增局部归档检查脚本；11 个坏行为案例、3 个正例、四项追溯观察及所有原有验收断言均未改。

## 主控沙箱外完整重跑

```sh
python3 -B workbench/tests/run_t081_bad_worker_suite.py --output evidence/2026-10-14-batch14/T-081/full-03
```

使用新目录，从头运行，不从 full-02 的失败位置续跑。应完整取得四项双版本观察、11 案变异红态与候选结果、3 个正例、误拒绝计数、全部回归和地图检查。rc=0 且 `controlled_status: PASS` 才说明该受控流程干净结束；总体仍保持 INCOMPLETE，因为 6a、6e 契约裁定、第 7 项和独立交付验收尚未关闭。

第 7 项第一回合的提示词、准确 argv/hook、任务卡与隔离 home 材料集中列于 [能力检查审批包](CAPABILITY-REVIEW.md)。本轮只做材料生成及只读核对，未复制 auth、未生成 home、未启用 hook、未启动真实 worker。

T-081 FULL-03 READY
