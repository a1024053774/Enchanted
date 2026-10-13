# managed_frozen等待边界修复

状态：**INCOMPLETE（端到端待验证）**。原03证据保留；本轮仅修F09/F05内的受控actor输入顺序，不改产品、Stop匹配、回执逻辑或既有业务断言。

## 03读回

W07来源变异体实际命中`W07-MANUAL-SOURCE`，1 failure/0 errors；Git从B=`20d8f7a6d423fa497df113b12e2bf267b2ac332a`变为C=`1a30b26fc5470ebefabffd5607cc942fdbdec6ac`。因此这次W07红态成立，不是前置报错。

managed_frozen的dirty拒绝正确。事件36结束T1，45开始ACK T2，56结束T2，窗格idle且active为空。夹具没有再次pane_dispatch，就写入short/base/C/duplicate请求，并再次发送已结束的T2 Stop。事件69–73将四个新请求拒为relay_requires_current_stop；事件74记录stop_not_matched。relay_requests/results只含dirty，task仍claimed、C为空、交付turn为空。产品没有应当启动却漏启动的T3；错误在fixture假定idle能自行产生新请求回执。

## 最小修改

新增`LegacyQuality.begin_worker_turn()`，只在两处使用：dirty的ACK结束后，和合法C批次的ACK结束后。helper要求原worker idle、原生身份不变、前一turn结束、无active/queued/failed；通过真实pane_dispatch登记新的执行主控输入，再等待指定新回合busy。随后核对原attempt和repair=null，证明这只是新输入，不是质量打回授权。

原worker_submit保持不变；不把Stop不匹配改成成功，不补数据库结果、不重试请求。原文件保留为`test_quality_legacy_e2e.py.before`，精确diff见`readback-01/fixture-fix.diff`。

## 全流程静态核对

| 步骤 | 进入条件／明确输入 | 等待出口与独立预期 |
| --- | --- | --- |
| 初次派发与dirty | start_worker经pane_release，worker T1 busy；工作区有未提交修改 | dirty请求经匹配Stop拒绝；ACK T2 busy，再结束为idle；candidate仍空 |
| 新工作回合 | 前一ACK T2 idle；显式pane_dispatch | T3 busy且active.nativeTurn=T3；同原生身份、同attempt、repair为空 |
| clean HEAD与同C重放 | 在T3恢复干净；同一B批次含短SHA、base、合法C、同C新request_id | 短SHA/base拒绝、合法C/同C成功；一次有效delivery；合并回执只开启T4，结束后idle |
| 冻结候选反例 | T4 idle后显式pane_dispatch | T5 busy；无打回授权，在worktree提交later_bad C2 |
| C2拒绝 | 在T5经匹配Stop交付C2 | 无授权的新交付turn先被拒；原C与delivery字段不变；ACK T6结束为idle |
| verify | worker已idle T6，worktree HEAD为C2，门禁冻结C仍为C1 | 机械检查使用冻结C1；reviewer工作区HEAD=C1，不能使用C2 |
| 独立review | fresh reviewer原生记录存在，首次release后其自身T1 busy | 合法同C结论经Stop/B/relay；result落库后reviewer回收；无ACK追加回合 |
| 带分集成与回收 | 有效review绑定C1，worker仍idle T6 | Git到C1且不等C2；一次score、一轮有效delivery；原生worker身份核对后reclaim |

全场景共7次受控输入（worker三次、ACK三次、reviewer一次），在配置上限10以内。它们是合成输入，不计为真实Codex回合；真实仍0/8。

评分预期未改：identity_version=4，分别对应dirty、短SHA、非HEAD的base、无授权新turn的C2；同C重放不计第二次delivery。两条pane_dispatch来源是executor，不生成user input或人工介入；缺少质量打回记录，不能据此替换冻结候选。

## 再生成

下面仅解析保存证据并记录静态边界表，不运行后台或模型：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/managed-flow-repair-01/diagnose.py --output evidence/2026-10-11-batch13/T-076/card-2/managed-flow-repair-01/readback-01
```

再次运行换新output。完整绿态须由主控执行legacy-green-04取得，不能用本读回结果替代。
