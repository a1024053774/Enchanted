# T-076-2 legacy-green-06交接

状态：**INCOMPLETE**。05已通过coop8、recovery9及前置正反例；run因driver在review requested时过早推进而失败。已补有期限的就绪等待并完成离线复放，完整run及后续结果待执行。真实回合 **0/8**。

事件已证实同一review在475毫秒内正常requested→running。此次只修F09的fixture driver：固定attempt/C/review，等running及运行身份齐备；失败、unknown、换绑定或12秒超时即停，状态查询受剩余期限约束。不改产品、不改run/Recovery断言、期限或屏障，不重试创建。相关五个run方法及MultiTurn路径表见[修复记录](run-review-wait-repair-01/README.md)。

主控直接执行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh legacy-green legacy-green-06
```

按原单阶段重新冻结与检查，第一处非预期失败停止。05及之前目录保留；不运行真实Codex/P-review，沙箱外范围不变。

静态收据为`legacy-ready-checks-06.json`；再生成命令（换新output）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-06.json
```

离线fixture复放不替代端到端绿态。完整T-076仍INCOMPLETE，交回READY后停下等主控执行。
