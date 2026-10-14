# F1 定向冲突反事实交接

**READY：脚本已准备；业务结论仍 INCOMPLETE，未运行沙箱外七红/七绿。** 夹具修正提交 `a5c6d50c48fa856cf85fe7d2fefddda61f5d2ade`，产品仍为 `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`，acceptance 未改。

运行前须注意口径：当前按主控 #121 原文要求，七条红态均强制投递成功、显式重交成功、目标 verify 已执行，且三份凭据须先于目标。没有收到按阶段豁免的确认，因此没有替 01～05 放宽规则。这些目标本来发生在成功重交之前，严格门槛下会记 NOT_COVERED；即使命中其目标也不计红。若要按各案目标阶段列前置，先由主控明确再改清单。当前脚本会完整收齐这类不满足项，最终如实返回 INCOMPLETE，不用它们冒充通过。

## 由主控在沙箱外执行

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh conflict-red-final-01
```

新目录：`evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-01/`。目录存在即拒绝；不覆盖 final-05，不重试，不自动转入复审。需要沙箱外的仅为现有隔离测试的 Unix socket、真实进程读数与自建后台清理；不启动真实 Codex，不读 auth，新增真实模型回合 0。

八个子阶段：red-01～red-07 各运行一案；candidate 按原名单运行七案。06/07 的变体仅在 conflict rework 路径跳过对应守卫，保留 writeConflict、投递和显式重交。01～04 仍用 no-conflict-feedback，05 仍用 merge I/O 错分。原始变体代码只留 /tmp；提交的是原候选、完整变异配方、命令、输出及收据。

每条 result.json 中保存 target_assertion_id、target_failed、target_passed、required_preconditions、missing_preconditions、classification_issues、target_coverage、business_red、有序 conflict_evidence 与 cleanup_failures。目标未执行、前置缺失/假/晚到、errors/skipped/cleanup failure 都不能计红；清理 AssertionError 单列，避免被 unittest 的 failure 计数混入。顶层 run.json 的 not_covered 与 target_failures_not_red 会逐项列出，baseline 正常 exit 1 不会中断后续收集；缺报告、基础设施错误或超大证据仍停止保留现场。

只有七项 target business_red 均为 true、七项候选原测试全部通过、无跳过/错误/清理异常，顶层才 PASS。不会因为六、七两项命中而忽略其余未覆盖项。

## 已有局部检查

旧 classifier 表达式的内存变体为 9 项、19 failures/0 errors；修后 9 项通过。来自原 final-05 的两份误报另已复现 2 failures/0 errors。源码 helper 静态检查为七案、279 处绑定通过。具体再生成命令及首次探针错误保留说明见 `CONFLICT-RED-FINAL-IMPLEMENTATION-01.md`。

准备命令与产物：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/run-conflict-red-final-01.py --prepare-only
python3 -B evidence/2026-10-11-batch13/T-077/check-conflict-red-final-preparation-01.py
```

产物在 `conflict-red-final-01-preparation-01/`；四个变体均检查语法，源码/夹具/脚本按字节冻结。重放必须改用新 PREP/OUT，不覆盖现有证据。guard 固定产品、夹具提交与 exec/t077，之后只允许本卡证据提交；运行期间 HEAD 不得变。单文件超 5 MB 停下交主控归档。

本轮未修改产品、未修任何业务预期、未开展第二次审查。整票仍 INCOMPLETE，F1 待真实入口结果与主控安排的针对性只读复审。
