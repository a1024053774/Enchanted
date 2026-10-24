# T-163-1 / a1 最终报告

状态：**INCOMPLETE**。六轮真实 Haiku 单次运行的严格 oracle 失败项数为 **3 → 3 → 1 → 1 → 2 → 2**，均未取得完整绿态。按执行主控 #59 指示核对 A 口径：末两轮失败项数不增加满足，但最终候选误收反向购买，第二条不满足，整体不能上调为 PASS。两次追加轮次已经用完，停止修改说明与模型运行，按当前结果交付，不再询问是否继续。

最终说明为历次修订的**累积版本**，最后被测试的完整产品版本是 `984c32139a08a67d2f76c95363ecec62bb419058`。本次仅整理报告、预算和运行摘要，产品与测试代码保持该版本。各轮都是单次运行，结果随运行和候选变化；没有重复稳定性实验，也没有完成 parent-instructions 对照，**不宣称任何版本稳定或任何提示词已可靠消除该类行为**。

## A 口径的最终核对

授权来源：用户 2026-10-24 逐字“B 继续改说明”，由执行主控 #55 引用构思主控 answer `20261024T024128Z-002`；收尾口径由执行主控 #59 明确。详见 [授权及口径校正](resume-authorization-01.md)。

| A 的条件 | 最终候选的实际证据 | 结果 |
| --- | --- | --- |
| oracle 失败项数不增加 | 第五轮 2 项、第六轮 2 项；两轮失败集合不同，不表示逐项稳定 | PASS（仅计数条件） |
| 错数字被拒 | summary-wrong-numbers 退出 1 | PASS（本次固定输入） |
| 缺项被拒 | summary-missing-total 退出 1，覆盖文末总计缺失 | PASS（本次固定输入） |
| 反向购买被拒 | shopping-inverted 退出 0，被误收 | **NO_GO** |

因此 A 第二条“错数字/缺项/反向购买被拒”在最终候选 `984c32139` 的本次运行中不成立。第三、四轮（`f310249c2`、`89fb2f73a`）在各自的单次运行中满足这三项，且各仅剩整体否定失败；这些历史结果不替最终候选背书。第五轮三项也都退出非零，但同时误拒两个正确汇总，不能据此证明正确区分对错或整体通过。

worker 此前将“不增加”解释为失败集合不得超出第四轮唯一失败项，该解释已依主控 #59 校正；本报告按末两轮**失败项数**比较。原始严格 oracle 的 NO_GO 均保留，未改样本、预期或判据，也未把 A 口径转换成新的自动 PASS。

## 范围与交付版本

- task `T-163-1`，attempt `a1`，worker `b24-t163`，分支 `exec/t163`。未修改任务卡、地图、AGENTS.md、CONTEXT.md 或他人 ticket；没有 push 或集成。
- 产品修改仅为应用内执行主控说明 `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`、命令帮助 `workbench/src/terminalCli.ts` 及对应 README。累积内容包含逐项核对用户要求、从原始数据推导验收预期并实际运行正反例、全文整体否定对照、无开头的最小正例和无新事实报告停点。没有加入夹具食材、数值、原句或 oracle 样本名。
- 没有增加策略引擎、生产权限、重试或门禁旁路。按 Ubiquitous language 使用统一术语，按 Deep modules 沿用现有驱动与生产入口，没有新增浅包装层；本票不增加跨层功能，不另建 Tracer bullet。
- 首轮夹具的有限 Bash 前缀误拦多行派发，来源是本票隔离 HOME 的 dontAsk 设置，非产品普通终端权限。第二轮起只对隔离测试主控允许 Bash，产品与受管 worker 权限不变，见 [修前读回](controller-baseline-01.md)。
- 追加授权后的驱动仅增加显式 `--budget-limit 20` 及预算记录，默认仍为 16；场景提示、11 项业务输入和严格判据不变。最终没有回滚到某个历史候选，也没有选择历史通过结论作为最终通过证据。

## 六轮真实回合与原始摘要

| 轮次 / 产品版本 | C5 根提示 | oracle 根提示 | 本轮 / 累计真实回合 | 严格 oracle 失败项数 | 变异 |
| --- | --- | --- | --- | --- | --- |
| 修前 RUN-OUTSIDE-01 / `e83a8a04e` | 2 | 2 | 4 / 4 | 3 | 未安排 |
| RUN-OUTSIDE-02 / `d4b79be10` | 2 | 2 | 4 / 8 | 3 | 未绿，跳过 |
| RUN-OUTSIDE-03 / `f310249c2` | 0 | 2 | 2 / 10 | 1 | 未绿，跳过 |
| RUN-OUTSIDE-04 / `89fb2f73a` | 0 | 2 | 2 / 12 | 1 | 未绿，跳过 |
| RUN-OUTSIDE-05 / `252d58d5e` | 0 | 2 | 2 / 14 | 2 | 未绿，跳过 |
| RUN-OUTSIDE-06 / `984c32139` | 0 | 2 | 2 / 16 | 2 | 未绿，跳过 |

实际共 **16/20 个真实根回合**。前四轮 12，追加两轮各 2，追加实际共 4/8；所有已授权追加轮次已经用完，不再使用剩余预算。计数来自原生 JSONL 的根 user 文本提示，排除技能展开、工具结果与中断占位；每个主控会话包含申请身份和执行场景各一条提示。

各摘要均记录实际 assistant model 为 `claude-haiku-5-5`，Claude Code `2.1.310`、Node `v26.5.0`；不把启动 argv 当作供应商实际 tier 的证明。真实供应商调用只来自项目终端主控；C5 的受管 worker 为真实 CLI 加本地脚本化 Messages 接口，只结束观察回合，不产生候选或真实供应商回合。未执行真实 reviewer、完整交付验收或集成。

原始摘要均保留实际状态和完整版本，不回写为 PASS：

- 第一轮：[C5](t163-outside-01.SmfeFT-c5-baseline.json)、[oracle](t163-outside-01.SmfeFT-oracle-baseline.json)。
- 第二轮：[C5](t163-outside-02.8v3EhC-c5-green.json)、[oracle](t163-outside-02.8v3EhC-oracle-green.json)。
- 第三轮：[oracle](t163-outside-03.8PILwD-oracle-green.json)。
- 第四轮：[oracle](t163-outside-04.ChKWVG-oracle-green.json)、[启动记录](RUN-OUTSIDE-04-started.json)。
- 第五轮：[oracle](t163-outside-05.cnhFBn-oracle-green.json)、[启动记录](RUN-OUTSIDE-05-started.json)。
- 第六轮：[oracle](t163-outside-06.aH65uB-oracle-green.json)、[启动记录](RUN-OUTSIDE-06-started.json)。

每轮精确 argv、fixture、实际模型与根回合数见摘要；预留、追加授权和事后核对均追加保存在 [预算账本](model-budget.jsonl)。

## oracle 各项变化

PASS 仅表示该固定输入的实际退出码符合判据。第一、二、五轮的自加明细或过严文字规则会误拒正确输入，坏输入被拒也可能由无关条件触发，不能单独当成对应语义能力的证明。六轮均无摘要 error 或清理错误，以下为业务结果。

| 固定样本 | 期望 | 第一轮 | 第二轮 | 第三轮 | 第四轮 | 第五轮 | 第六轮 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| summary-good | 接受 | 误拒 | 误拒 | PASS | PASS | 误拒 | PASS |
| summary-good-other-layout | 接受 | 误拒 | 误拒 | PASS | PASS | 误拒 | **误拒** |
| summary-wrong-numbers | 拒绝 | PASS | PASS | PASS | PASS | PASS | PASS |
| summary-missing-total | 拒绝 | PASS | PASS | PASS | PASS | PASS | PASS |
| summary-inverted | 拒绝 | PASS | PASS | **误收** | **误收** | PASS | PASS |
| shopping-good | 接受 | PASS | PASS | PASS | PASS | PASS | PASS |
| shopping-inverted | 拒绝 | **误收** | **误收** | PASS | PASS | PASS | **误收** |
| shopping-nonzero | 拒绝 | PASS | PASS | PASS | PASS | PASS | PASS |
| shopping-grouped | 拒绝 | PASS | PASS | PASS | PASS | PASS | PASS |
| shopping-stale-source | 拒绝 | PASS | PASS | PASS | PASS | PASS | PASS |
| shopping-changed-source-good | 接受 | PASS | PASS | PASS | PASS | PASS | PASS |

每轮只运行一次 oracle，没有重复试验验证稳定性；每轮主控生成不同检查器，最终产品说明则为累积修订。因此不能把某格曾经通过解释成任何版本稳定，不能把失败项数不增加解释成失败集合相同，也不能推断提示词带来了可靠性、成本或收益改善。parent-instructions 运行均被跳过，未取得提示词变异对照证据。

## C5 的独立行为结论

执行主控 #47 独立阅读第一轮记录与草稿卡，结论为“无显式自检，结果无遗漏”：A 包含最终总计、首版故意漏总计、等真实打回后再补、不得提前补；B 包含先 issue 询问、收到答复前不得写文件。两卡只用 test -f 作完成条件，属于弱验收。卡保存和创建被夹具权限拒绝，未派发；该阻断不是漏项红态。

执行主控 #49 独立阅读第二轮 `/private/tmp/t163-jkyf4esx/out/native-transcript.json`，确认主控从原始数据写 check_a/check_b，自建列表、表格正例与缺总计、错数字、标签对调、多列、漏列反例并实际运行；发现标签对调被放过后主动加强检查器、再次运行样本。两卡包含要求，两个 worker 均真实派发，有 attempt 与 claimed 状态；主控之后守住用户停点，未 verify、未代答、未轮询，报告表格无单位时列对调的机械判断限制。

第二轮显式逐项对照列表不完整，但卡内容无遗漏。**修前漏项未复现，不能证明原有遗漏被新说明发现**。C5 未在后续四轮复跑，其行为证据只绑定 `d4b79be10`，不替最终累积说明背书。

## M02 残余的原生记录诊断

残余均记为 **M02 模型行为**。六轮中出现过三类问题：全文整体否定误收、反向购买误收、排版或明细过严造成正确内容误拒。不是协调缺陷，也不据此取消独立审查。

- 第一、二轮：技能已读、自测已做，oracle 主控自加文末逐项列名条件，正例也含这些明细，没测试反向购买语义。见 [第二轮诊断](diagnosis-02.md)。
- 第三、四轮：前者只通过有限业务动作禁词拒绝“已售出”反例，后者名为“关键词在含义相反”的样本实际改错数值，都没有证明能拒绝正确正文被整体否定；第四轮自建购买改述 S9 还出现期望 1、实际 0，模型报告限制后结束。见 [第三轮诊断](diagnosis-03.md)及第四轮原生记录 `/private/tmp/t163-ovw946lf/out/native-transcript.json`。
- 第五轮：实际做了正文不变的整体否定实验，又自加逐项列名及 leftover 文字规则，正常数值标签被当作多余文字，两个正例误拒。自称最小的正例仍含全部名称，未揭露这一条件。见 [第五轮诊断](diagnosis-05.md)。
- 第六轮：来源为 `/private/tmp/t163-yc9yfbmm/out/native-transcript.json`、`check_pantry.py`、`check_shopping.py`、`selftest_run.py` 与两个失败 case/run.json。主控实际运行自建 26 个样本；发现一个错误标注的中文数字反例本身正确后，修正该反例再运行，报告自测全部符合预期。独立 oracle 仍揭露以下两个缺口。

第六轮汇总检查器的文本解析只识别数值在单位前等有限写法，未识别独立正确样本中标签在数值前的语义；实际输出为 `FAIL: 水果 没有给出种类数与件数`。这构成 summary-good-other-layout 的误拒，不能以模型声称排版不限替代实际输入证据。

第六轮购买检查器只有在**名称所在同一行**匹配否定词时才拒绝；上方标题的“无需购买”限定后续名称列表时，没有把该上下文传递到列表行。独立 shopping-inverted 的实际退出码为 0，stdout 为 `OK: shopping-list.md 满足要求`。模型最终也报告了有限关键词和否定覆盖的限制，自测全过不能替代这一反例。

最终说明累积保留通用自检要求，不再继续堆提示词、加入夹具词表或更改严格判据。**整体否定类语义交独立审查**；有限脚本对自由措辞、上下文作用范围和允许排版的判断仍有边界。历史类别中整体否定曾通过、曾失败，最终候选的反向购买又失败；只能如实记本次结果，不作稳定性承诺。

## 对策达成情况

| 对策 | 证据与缺口 | 最终状态 |
| --- | --- | --- |
| M01 派发前逐项核对 | 第二轮卡完整、实际派发并守住停点；显式列表不完整，修前漏项未复现，最终说明未复跑 C5 | INCOMPLETE |
| M02 验收脚本自检 | 有原始数据推导、实际正反例、自主修正与限制报告；严格 oracle 六轮均未绿，最终 A 第二条不满足，无变异对照 | NO_GO |
| M04 无新事实停下 | 说明已补三种状态；有 C5 按停点结束的观察，未完整复跑未知状态长轮询场景 | INCOMPLETE |

整体状态 **INCOMPLETE**。本次按已授权 A 口径核对后交付事实与残余，不表示 A 的全部条件满足，不关闭为 PASS。

## 验证、归档与交接

- 静态入口、语法、UTF-8、空白和测试代码检查的历史证据为 `local-checks-02.json` 至 `local-checks-06.json`；T-158 说明回归最新为 `t158-instructions-06.json`。本次只检查报告对账和源码冻结，不运行新的模型或行为测试。
- 历史弱验收探针 `probe-oracle-known-bad.json`、`probe-oracle-known-bad-replay.json` 能揭露已知错数字、反向语义和分组误收；不是本票完整绿态或提示词变异。
- 第四轮收尾核对曾误记六个临时 HOME 均已删除；原错误记录 `final-checks.json` 和纠正记录 `final-checks-correction.json` 均保留。后者确认当时首轮 C5 HOME 尚有一份原生日志，没有名称含 credential 的文件；没有删除残留或读取凭据内容，不用原 PASS 宣称完整清理通过。
- 前四轮原件的 T-088 归档清单由执行主控提交于 `a1391bb16`，例如 `t163-ovw946lf.archive.json`；本 worker 只读取清单，没有重新宣称独立核对归档完成。第五轮新原件在 `/private/tmp/t163-bp2jsk60` 与 `/private/tmp/t163-outside-05.cnhFBn`，第六轮在 `/private/tmp/t163-yc9yfbmm` 与 `/private/tmp/t163-outside-06.aH65uB`，交执行主控继续归档；登录副本不入 Git。
- 收尾对账见 `closure-checks-06.json`，项目地图状态见 `project-map-status-closure-06.json`；既存 T-158 缺 Resolution 在本票修改边界外，未改他人 ticket。没有取得完整独立行为验收或集成通过结论。

历史执行命令仅作证据，不再运行：

```zsh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-01.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-02.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-03.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-04.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-05.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-06.sh
```

本交付保留最终累积说明、所有单次失败、明确的审查边界与有限验收未达成事实。无新运行计划，不再修改说明，不询问是否追加。
