# T-076-2 legacy-green-02交接

状态：**INCOMPLETE**。主控 #59 批准的F14已落实；动态结果待执行。真实回合 **0/8**。

本次修改仅为旧卡helper的`executor.model: fixture → gpt-6.1-sol`，以及对应审计。`audit_legacy_scope.py`将`ManagedDeliveryCLI.create()`完整正文与起点仅替换这一字符串后的文本逐字比较；cli、effort、其他字段和断言都不变。Panes约束及产品逻辑未改。

旧交接diff保留为`legacy-acceptance-hunks.pre-F14.diff`；当前`legacy-acceptance-hunks.diff`重新冻结，新增F14一行。原`outside-legacy-green-01/`及诊断收据不动。01的F10红态有效，W07是夹具准备失败，后续未运行。

从主checkout直接执行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh legacy-green legacy-green-02
```

脚本重新冻结候选，沿原单阶段顺序：F10/W07来源变异体红态 → 候选来源拒绝与受管冻结C → 8/9/18 → T-075/T-076-1其余回归。第一处非预期失败停止，不重试，不覆盖01，不运行真实Codex/P-review。具体检查范围和沙箱外边界沿[首次交接](HANDOFF-legacy-green-01.md)。

主控已澄清01所报顶层“exit 0”是`tail`的管道退出码；不是runner成功，01仍为INCOMPLETE。没有为此修改runner或旧证据。

静态准备收据为`legacy-ready-checks-02.json`，再生成时使用新输出名：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-02.json
```

当前完整验收仍为INCOMPLETE，静态准备PASS不替代业务结果。按主控要求，交回READY后停止，等待沙箱外结果。
