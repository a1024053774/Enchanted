# T-163-1 / a1 最终报告

状态：INCOMPLETE。四轮真实 Haiku 运行后，oracle 的失败项为 **3 → 3 → 1 → 1**，没有取得完整绿态。第四轮仍接受正文整体被否定的汇总；全部 parent-instructions 变异因 oracle 未绿而跳过。按执行主控 #50、#52 的停止要求，不再修改说明、不再运行模型，交执行主控转构思主控决定验收判据。交付本报告不表示 T-163 验收通过。

## 交付范围与版本

- task `T-163-1`，attempt `a1`，worker `b24-t163`，分支 `exec/t163`。任务卡、oracle 与通过判据没有修改。
- 最后被真实模型测试的产品版本：`89fb2f73a7a141d4e61c1095105bb1e6340d5628`。此后只整理本票报告、预算与运行摘要，产品说明和测试代码冻结。
- 产品修改仅为应用内主控说明 `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`、命令帮助 `workbench/src/terminalCli.ts` 及对应 README。三条要求是：派发前逐项对照用户要求；从原始数据独立确定验收预期并实际运行正反例；区分暂时未完成、明确拒绝、结果未知，无新事实报告停点。后续说明补充最小正例、断言含义和有限词表的覆盖限制，不含夹具食材、数值或原句清单。
- 没有增加策略引擎、生产权限、重试或门禁旁路。沿用 Ubiquitous language 与现有 Fixture/Electron 驱动；按 Deep modules 原则没有新增生产包装层。本票不增加跨层功能，不另建 Tracer bullet。
- 首轮夹具的有限 Bash 前缀误拦多行派发。确认来源是本票隔离 HOME 的 `dontAsk` 配置，非产品普通终端启动参数；第二轮起仅在隔离测试主控允许 Bash，产品与受管 worker 权限不变。详见 [修前读回](controller-baseline-01.md)。

## 每轮真实回合与 oracle 结果

| 轮次 / 产品版本 | C5 根提示 | oracle 根提示 | 本轮 / 累计真实回合 | oracle 失败项数 | 变异 |
| --- | --- | --- | --- | --- | --- |
| 修前 RUN-OUTSIDE-01 / `e83a8a04e` | 2 | 2 | 4 / 4 | 3 | 未安排 |
| RUN-OUTSIDE-02 / `d4b79be10` | 2 | 2 | 4 / 8 | 3 | 未绿，跳过 |
| RUN-OUTSIDE-03 / `f310249c2` | 0 | 2 | 2 / 10 | 1 | 未绿，跳过 |
| RUN-OUTSIDE-04 / `89fb2f73a` | 0 | 2 | 2 / 12 | 1 | 未绿，跳过 |

实际合计 **12/16 个真实根回合**，也未超过最后一轮累计 14 的限制。余下预算不构成继续运行授权。计数来源为原生 JSONL 中有文本的根 user 提示，排除技能展开、工具结果、中断占位；每个主控会话含申请身份和执行场景各一条根提示。运行摘要均记录实际 assistant model 为 `claude-haiku-5-5`，Claude Code `2.1.310`、Node `v26.5.0`；不把请求 argv 当作供应商实际 tier 的证明。

真实供应商调用只来自项目终端主控。C5 的受管 worker 使用真实 CLI 与本地脚本化 Messages 接口，只结束观察回合，不写候选，不贡献真实供应商回合。没有真实 reviewer、完整交付验收或集成。

各轮原始摘要（保留原状态，不回写为 PASS）：

- 修前：[C5](t163-outside-01.SmfeFT-c5-baseline.json)、[oracle](t163-outside-01.SmfeFT-oracle-baseline.json)。
- 第二轮：[C5](t163-outside-02.8v3EhC-c5-green.json)、[oracle](t163-outside-02.8v3EhC-oracle-green.json)。
- 第三轮：[oracle](t163-outside-03.8PILwD-oracle-green.json)。
- 第四轮：[oracle](t163-outside-04.ChKWVG-oracle-green.json)、[一次性启动记录](RUN-OUTSIDE-04-started.json)。

完整产品版本、启动命令、临时目录、实际模型和回合数在各摘要中；预留与事后核对记录追加保存在 [预算账本](model-budget.jsonl)。

## oracle 各项变化

下表的 PASS 仅指该输入的实际退出码符合固定判据。前两轮有自加明细导致的误拒，坏输入被拒也不能单独证明识别了对应语义错误。四轮均无摘要 `error` 或清理错误；这些是业务失败，非环境失败。

| 固定样本 | 期望 | 修前 | 第二轮 | 第三轮 | 第四轮 |
| --- | --- | --- | --- | --- | --- |
| summary-good | 接受 | 误拒 | 误拒 | PASS | PASS |
| summary-good-other-layout | 接受 | 误拒 | 误拒 | PASS | PASS |
| summary-wrong-numbers | 拒绝 | PASS | PASS | PASS | PASS |
| summary-missing-total | 拒绝 | PASS | PASS | PASS | PASS |
| summary-inverted | 拒绝 | PASS | PASS | **误收** | **误收** |
| shopping-good | 接受 | PASS | PASS | PASS | PASS |
| shopping-inverted | 拒绝 | **误收** | **误收** | PASS | PASS |
| shopping-nonzero | 拒绝 | PASS | PASS | PASS | PASS |
| shopping-grouped | 拒绝 | PASS | PASS | PASS | PASS |
| shopping-stale-source | 拒绝 | PASS | PASS | PASS | PASS |
| shopping-changed-source-good | 接受 | PASS | PASS | PASS | PASS |

第二轮后 `test_t163_controller_e2e.py` 的场景提示、11 个业务样本与判据均未改变。没有以换样本、改期望或补明细使结果转绿。每轮为不同的模型生成结果；这些观察不是独立对照实验，不能证明可靠性、成本或收益改善。

## C5 的独立行为结论

执行主控 #47 独立阅读首轮原生记录与草稿卡，结论为“无显式自检，结果无遗漏”：A 含最终总计、首版故意漏总计、等真实打回再补、不得提前补；B 含先 issue 询问、收到答复前不得写文件。两卡完成条件只有 `test -f`，属于弱验收。多行 card_save/create 被夹具权限拒绝，未派发；不能将该阻断当作模型漏项红态。

执行主控 #49 独立阅读第二轮 `/private/tmp/t163-jkyf4esx/out/native-transcript.json`，确认：

- 主控从原始数据生成 check_a/check_b，构造列表、表格正例与缺总计、错数字、标签对调、多列、漏列反例并实际运行；发现标签对调被放过后主动加强检查器，再运行样本。
- 两卡含首版漏总计等打回、B 先问分组再写的顺序；两个 worker 均真实派发，有 attempt 与 claimed 状态。
- 派发后守住用户停点，未 verify、未代答、未轮询；说明了表格无单位时列对调的机械判断限制，交独立审查。
- 显式“逐项对照用户原话”的列表不完整，但卡内容无遗漏。

因此 C5 在该候选上有真实派发与自检行为证据；**漏项修前红态未复现，不能证明“原有漏项被新说明发现”**。第三、四轮按主控要求没有重跑 C5，第二轮结论只绑定 `d4b79be10`，不替最新说明背书。

## 残余失败的原生记录诊断

前两轮诊断见 [第二轮对照](diagnosis-02.md)：两个场景都读到新版说明并实际自测，oracle 却把未要求的逐项食材名加进判据和正例，没测试反向购买语义。

第三轮诊断见 [汇总反向语义](diagnosis-03.md)：确实构造“已售出数量”的汇总反例，但检查器只用有限业务动作禁词表，样本必然命中；对整段正文真实性的否定仍未识别。

第四轮来源为 `/private/tmp/t163-ovw946lf/out/native-transcript.json`、`run_cases.py`、`check_pantry.py`、`check_shopping.py` 和 `summary-inverted/run.json`：

1. 技能展开包含最新“有限禁词表只证明命中过的词”规则，排除未加载新版说明的解释。模型自建 25 个样本，原始工具回执为“共 25 个样本，不符 1 个”“runner exit=1”。
2. 汇总自测中名为 `N10-关键词在含义相反` 的反例，实际把类别种类数与件数改成错误值，检验的是数值含义对应；没有保持正确正文、再否定其整体真实性或有效性。不能用样本名称证明覆盖了断言含义。
3. 汇总检查器 `check` 仍按类别、表头、单位与总计解析数字，没有核对全文对这些数字作出的整体断言。独立 summary-inverted 在正确正文前否定它是实际库存，仍退出 0，stdout 为 `PASS`。这是第四轮 oracle 唯一失败，完整保留。
4. 另有模型自建的购买改述反例 `S9-改述含义相反(未入禁词表)`：原始回执明确为“期望=1 实际=0”。模型报告了有限词表的限制，把它交独立审查，没有修到自测全绿便结束。该额外失败不在固定 11 项 oracle 表中，也必须保留，不能以固定 shopping-inverted 通过掩盖。

可核对的残余是：模型会执行自测并报告部分限制，但未稳定区分“检查数字关系”与“检查全文实际断言”，也未把所有已经构造出的明显反例修到拒绝。不能从记录推断模型内部原因。按约定停止，不继续堆提示词、补夹具词表或改验收判据。

## 提示词对策在真实 haiku 上的达成情况

| 对策 | 证据与缺口 | 最终状态 |
| --- | --- | --- |
| M01 派发前逐项核对 | 第二轮卡完整、实际派发并守住停点；显式逐项核对列表不完整，修前漏项未复现，最新候选未复跑 C5。 | INCOMPLETE |
| M02 验收脚本自检 | 有真实原始数据推导、正反例运行、主动修正和限制报告；最后 oracle 仍失败，且自建 S9 也未拒绝。未取得绿态或 parent-instructions 变异证据。 | NO_GO |
| M04 无新事实停下 | 说明已补三种状态；有 C5 按用户停点结束的观察，未完整复跑未知状态长轮询场景。 | INCOMPLETE |

整体仍为 **INCOMPLETE**，不得据此关闭为 PASS。未取得完整独立行为验收或集成结论；执行主控将把材料交构思主控决定验收判据，本 worker 不自行变更。

## 验证、原件与交接

- 静态入口及语法、UTF-8、空白、测试代码未改检查通过，见 `local-checks-02.json`、`local-checks-03.json`、`local-checks-04.json`。T-158 说明回归通过，最新为 `t158-instructions-04.json`。这些不是模型行为绿态。
- `probe-oracle-known-bad.json` 与 `probe-oracle-known-bad-replay.json` 证明测试能揭露 T-155 历史弱验收的错数字、反向语义和分组问题；不是本票真实模型绿态，也不是未运行的提示词变异。
- 最终只核对报告、摘要、预算和编码，不再运行模型或修改产品。`final-checks.json` 的轮次、12 回合、失败集合与源码冻结对账成立，但其中“六场景 HOME 均已删除”误记了核对范围：当时实际只检查四个 oracle HOME。补充检查在首轮 C5 HOME 存在时失败，原记录不覆盖，以 `final-checks-correction.json` 纠正：六场景中五个 HOME 不存在，首轮 C5 HOME 仍有一份原生 JSONL，没有名称含 credential 的文件；仅核对路径，未读取凭据内容或删除残留。这是 worker 收尾报告核对错误，不能将原 PASS 解释为完整清理通过。
- 收尾 `project-map-status-final.json` 仍仅有既存 T-158 缺 Resolution，stale living docs 为 0；该问题在修改边界外，不改他人 ticket。
- 四轮临时输出目录依次为 `/private/tmp/t163-outside-01.SmfeFT`、`/private/tmp/t163-outside-02.8v3EhC`、`/private/tmp/t163-outside-03.8PILwD`、`/private/tmp/t163-outside-04.ChKWVG`；每场景 fixture 路径见摘要。原生记录、脚本、样本、退出码和截图保留，完整原件及上述 C5 日志残留由执行主控按 T-088 归档，本 worker 未核对外置归档完成。登录副本不入证据或 Git。

历史执行入口如下，仅用于记录精确命令；本任务不再执行这些入口：

```zsh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-01.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-02.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-03.sh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-04.sh
```

本交付为状态如实保留的最终材料，等待执行主控转交决定；没有 push、集成、修改地图或关闭 ticket。
