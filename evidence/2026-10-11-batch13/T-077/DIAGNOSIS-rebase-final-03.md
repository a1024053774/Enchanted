# final-03：adapter 参数缺失与 11/18 的原因

状态：**INCOMPLETE**。这是夹具签名与 runner 提前停止的问题；本轮不改产品或 acceptance 的业务断言。原始 `outside-rebase-final-03/` 和 `rebase-final-03.console.txt` 保留原样。

## 参数在哪一层丢失

`outside-rebase-final-03/run/run.json` 保存了唯一 error：`acceptance/test_run_e2e.py:549` 以 `owner="current-owner"`、`overlap_reason="Test historical reclaim while the current owner remains active"` 调用 claim，Python 在进入 adapter 方法体前抛 TypeError。没有到达此次 claim 的 CLI，更没有证据表明产品拒绝了这个理由。

父级 `acceptance/test_coop_e2e.py` 的 claim 已接受 overlap_reason，并把非 None 的原值作为 `--overlap-reason` 交给 CLI。合流后的 `DaemonLifecycle.claim` 仍是旧签名，仅接受 task/owner。生产 `workbench/src/gates/cli.ts` 的 claim、dispatch 均允许该参数，core 的 claim 路径检查接收 `args.overlap_reason`；因此修复归属 adapter。

修复涵盖两个分支：手工 claim 把 task、owner 和理由传给原父级实现；转换为受管 dispatch 的分支把理由原样作为真实 CLI 参数发送，仍保留原 runtime-mode 和评分准备。没有传理由时不额外发送该选项。没有捕获 TypeError、生成理由、忽略理由或更改产品检查。

## 为什么只跑了 11 项

原 run.json 的 `original_methods` 有全部 18 项，`expected_tests=18`、`collection_errors=[]`。unittest 输出中第 11 项正是上述历史 reclaim 场景；runner 构造器使用 `failfast=True`，所以余下 7 项没有执行。这是运行中提前停止，不是只收集到 11 项。原报告正确保留为 INCOMPLETE。

runner 改为 `failfast=False`，保留所有失败和 errors，继续执行原套件各项。结果增加 `executed_methods`、`unexecuted_methods` 和 failfast 记录；PASS 同时要求实际执行序列等于原始 18 项列表、tests_run=18，以及无失败、错误、跳过或收证据残留。其他固定回归套件也执行完整列表；顶层阶段仍在失败套件完成收证据后停止，不自动重试。

## 局部反事实与限制

四个局部检查覆盖：手工传参、受管 dispatch 的 CLI 参数、无理由时不新增选项，以及第 11 项故意抛错后仍执行到第 18 项且结果仍为失败。其预期来自主控 #118 的参数传递和完整执行要求。这里只记录 fixture 客户端边界与 unittest 调度，不把录制参数的对象称为真实门禁。

修前 `regression-fixtures-red-04/`：4 项中 2 errors（两条路径均因旧签名拒绝理由）、1 failure（只执行到第 11 项），无理由例通过。修后 `regression-fixtures-green-04/`：4 项全部通过。故意注入的内部 error 仍使内部结果 wasSuccessful=false；外部检查验证这个失败没有被转换为通过。

再生成修后局部检查（新目录，不覆盖旧输出）：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/check-regression-fixtures-04.py --output evidence/2026-10-11-batch13/T-077/regression-fixtures-replay-04
```

实际 CLI、门禁事件与 Git 行为仍须在主控执行的 `rebase-final-04` 全量阶段验证；当前不称其为 PASS。产品冻结为 `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`，本轮新增真实模型回合 0。
