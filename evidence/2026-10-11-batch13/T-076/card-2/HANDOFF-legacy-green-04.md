# T-076-2 legacy-green-04交接

状态：**INCOMPLETE**。03中的F10/W07红态已核对有效；managed_frozen失败已定位为夹具缺少新输入，现已修复，动态绿态待主控执行。真实回合 **0/8**。

dirty的ACK T2已经结束；旧fixture直接在idle写新请求并重发T2 Stop，产品正确拒绝未匹配Stop，没有启动ACK。只在新测试中补两次明确pane_dispatch：T2 idle→worker T3，T4 idle→worker T5。helper核对同attempt/原生身份和repair=null；产品Stop/门禁逻辑、worker_submit及原业务断言不改。

完整等待表、原始事件读回和修复diff见[managed-flow-repair-01/README](managed-flow-repair-01/README.md)。已静态走查dirty、short/base/同C批次、冻结C2拒绝、verify、fresh reviewer及带分集成/reclaim的每个等待边界；总计7次合成输入，小于既有上限10。没有把这些合成输入记为真实模型回合。

主控直接执行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh legacy-green legacy-green-04
```

单阶段顺序与沙箱外边界沿[03交接](HANDOFF-legacy-green-03.md)。重新冻结，先来源反事实再候选/8/9/18及其余回归；第一处非预期失败停止，不重试、不覆盖01–03，不启动P-review或真实Codex。

静态准备收据为`legacy-ready-checks-04.json`。再生成命令（换新输出名）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-04.json
```

本次修复不是产品缺陷修复；03保存的状态符合匹配Stop的合同。新完整运行尚未执行，静态检查不替代业务通过。按要求交回READY后停止。
