# T-076-2：F01的手工claim评分来源需要决定

状态：**BLOCKED（仅旧回归夹具迁移）**。来源为静态接口核对，尚未把旧回归跑出的前置错误当作产品红态。reviewer三项已获红态的修复独立推进，准备一次focused green后交回。

## 事实

- `acceptance/test_coop_e2e.py:161`的`claim()`调用真实claim，多个集成场景沿用它；Recovery的`setup_candidate()`（`:361–372`）同样用claim，run的guard场景继承这个setup。
- `workbench/src/gates/core.ts:2566`的真实claim将`thread_id`置空，不创建运行时或启动记录。`:2811–2819`只有非空thread的submit才读取sessionFacts并保存`attempt.delivery`。
- `core.ts:3011`的integrate要求`attempt.delivery`；因此给手工claim加上合法review和score_file仍不能集成。旧测试运行时提供`sessionFacts`本身解决不了这个分支，它不会被调用。
- 已批准PLAN §7.1/F01明确要求“手工 claim 用例中真实 claim/竞争/fence 检查仍保留”，并写明“若生产接口无法容纳这一边界，停止提交详细设计，不能增‘test mode’”。现在核对到了该未知项；未改旧断言、未伪造delivery或passed、未为测试增加生产开关。

## 最小选项

建议批准一个补充夹具白名单：只把需要完整集成的旧成功场景的执行准备显式迁到受控`dispatch`，由真实submit保存受控运行时来源；`claim`竞争/持久化/任务隔离、fence、撤销和冻结候选断言仍保留原真实入口。Recovery9项业务断言不改，原Git/oracle屏障与CAS次数不改；它们的setup通过明确受控运行时准备worker，reviewer通过外部显式结论，执行主控经CLI带分集成。fixture报告逐例标明手工claim还是受控dispatch，不能把两者混称。需要由主控确认此方案是否满足F01的原边界，再列准确helper/method清单后实施。

另一个选项是定义“没有受管CLI启动来源的手工claim怎样打分并集成”的产品合同；这涉及来源字段与可追溯性，不应由本worker自行补unknown/虚构launch，须构思主控决定。

本次只请求上述fixture准备方式的明确决定；没有请求放宽生产门禁。独立reviewer、实际交付来源、CAS和必填评分仍必须经过原产品核对。已有wide-green的15项及13个反事实不受此问题影响。
