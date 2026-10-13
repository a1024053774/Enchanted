# T-076-2 reviewer异常修复交接

状态：**INCOMPLETE**。主控 #48 的两项结果已逐案读回：reviewer-red三项命中指定契约失败；wide-green的15项用例、13个变异体均符合预期，全部cleanup_failures为空，无超大文件。被测真实回合仍 **0/8**。

修复只涉及`core.ts`、`daemon.ts`、`stateConsistency.ts`：创建或回收出错时，同事务保存未知状态与issue，再保留原失败返回；启动时把未完成旧review标未知，不重建或续接。已成功回收的review不受启动扫描影响。历史review的异常只留诊断/issue，不改新attempt或已终结状态。没有重试、自动修复JSON、抹除失败或修改存储结构。

精确修复diff：[review-repair-01/reviewer-lifecycle.diff](review-repair-01/reviewer-lifecycle.diff)。起点为`outside-wide-green-01/candidate-and-harness.tar.gz`，前后文件与已保存结果读回在同目录。生成命令（再次生成需换目录）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/capture-review-repair.py --output evidence/2026-10-11-batch13/T-076/card-2/review-repair-01
```

本次只交一个合并的沙箱外阶段：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh review-green reviewer-green-01
```

按顺序执行8项：原三项reviewer故障信号原断言转绿；`tracer_success`、`tracer_review_needs_fix`、`tracer_run_waits`三条受影响正常路径；`widen_score_before_cas`、`widen_score_after_cas`两项确认新增启动扫描不破坏已完成review的评分恢复。不重跑wide-green的其余用例及13个变异体。每组失败停止，不重试；仍冻结当前源码、保留命令/数据库/Git/信号/完整夹具归档。

沙箱外动作仍仅自建socket、后台生命周期、ps和自建PID信号；无真实Codex、auth复制、真实hook安装、Electron或正式工作台操作。缺外置盘即退出。

8/9/18迁移暂需决定，详见[ISSUE-legacy-claim-provenance.md](ISSUE-legacy-claim-provenance.md)，收件箱 `20261011T184331Z-worker:s13-t076-2-issue-001`。F01要求保留真实claim，也明确规定生产接口容纳不了夹具来源时停止交设计。当前claim不产生运行时来源，不能仅补review/score参数就集成；因此尚未改旧断言或夹具、尚未准备完整回归阶段。建议批准受影响成功场景显式用受控dispatch准备，同时保留专门的claim/竞争/fence等测试；实施前再列准确helper/method清单。此问题不阻止本次8项reviewer修复验证。

静态检查命令：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-widen-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/reviewer-preparation-checks.json
```

该收据只证明语法、模块导入、既有变异目标、旧证据读回与地图/文件检查；绿态待执行主控运行。P-review准确argv/home/hook仍须单独逐次批准。本卡没有完成提交、真实闭环或交付独立审查。
