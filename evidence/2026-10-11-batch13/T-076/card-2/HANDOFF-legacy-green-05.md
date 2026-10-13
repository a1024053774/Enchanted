# T-076-2 legacy-green-05交接

状态：**INCOMPLETE**。04已通过来源反事实、两个新候选场景及coop8；Recovery第二项仅在cleanup发生fixture重复驱动错误，剩余检查未运行。F06/F09修复和离线复放已完成，动态回归待主控执行。真实回合 **0/8**。

adapter现在按原verify handle及完整attempt/C/review绑定只驱动一次审查；cleanup重读不会再驱动已完成的review，不改历史响应。未知/变更绑定拒绝而不重试。Recovery源码、9项断言、屏障、CAS计数和产品逻辑不变。完整静态路径表与依据见[recovery-cleanup-repair-01/README](recovery-cleanup-repair-01/README.md)。

主控直接执行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh legacy-green legacy-green-05
```

沿原单阶段顺序重新冻结，第一处非预期失败停止，不重试。04及之前的失败目录保留，不启动真实Codex/P-review。原scope/hunk审计继续核对Recovery逐字不变。

静态准备收据为`legacy-ready-checks-05.json`。再生成命令（换新output）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-05.json
```

离线复放不当作Recovery绿态，完整T-076仍INCOMPLETE。按要求交回READY后停止，等待执行结果。
