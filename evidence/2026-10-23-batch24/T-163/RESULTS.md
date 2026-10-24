# T-163-1 / a1

状态：INCOMPLETE。RUN-OUTSIDE-03 的 oracle 仍为 NO_GO，仅剩 summary-inverted 被误收，无环境错误。C5 的较早候选已实际派发且主控独立确认行为符合要求（显式逐项核对列表不完整）。按主控 #50 授权做最后一次通用说明修订，等待 RUN-OUTSIDE-04；若仍未绿，停止修改并交主控转构思主控决定。

## 范围与入口

- 工作分支 `exec/t163`，产品基线 `e83a8a04e`；完整版本写入运行摘要的 `product_revision`。
- 应用内主控说明位于 `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`，命令帮助位于 `workbench/src/terminalCli.ts`。产品修改只涉及这两个说明入口及对应 README 说明；不做策略引擎。
- 使用项目的 Ubiquitous language：执行主控、任务卡、attempt、门禁入口。沿用已有 Fixture/Electron 驱动，不新建生产包装层（Deep modules）。本票是提示词修复，不跨生产层增加功能，不另建 Tracer bullet。

## 修前复跑

主控命令：

```zsh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-01.sh
```

`test_t163_controller_e2e.py` 支持 `--summary <新路径>`、`--revision <提交>`、`--mutant parent-instructions`。同一场景提示用于修前与修后，变异把两个产品说明入口恢复为本票基线，不改变输入或 oracle。

1. C5：真实 Haiku 执行主控经界面批准后，按原场景派两个受管任务。A 首版应故意漏总计、等真实验收打回后再补；B 必须先上报分组问题，等回答后才写文件与交付。两 worker 启动后执行主控结束回合。脚本保存实际采用卡的版本、后台状态、原生工具记录与截图，交主控独立做语义核对。不会用几段字串匹配把“已自检”判成通过；C5 自动摘要保持 INCOMPLETE。
2. 验收脚本：另一个干净的真实 Haiku 执行主控根据原始 pantry 数据和明确的文档要求生成两个 Python 检查程序。测试用未提供给模型的输入执行它们，覆盖正确文档、另一种正确排版、错数字、漏总计、反向语义、非零库存、分组、原始数据变化后的旧答案与新正确答案。退出码、标准输出和错误保存到各 case/run.json。业务失败才是红态，环境失败不算。

真实供应商模型仅用于项目终端主控，指定 `claude-haiku-5-5`；C5 的受管 worker 使用真实 CLI 加本地脚本化 Messages 接口，只结束观察回合，不写候选，不形成验收证据。本次不运行真实 reviewer 或集成，不把本票的派发检查宣称为完整交付旅程。

两场景各预留 2 个真实根提示，RUN-OUTSIDE-01 实际合计 4/16；共享追加式 `model-budget.jsonl`，失败预留不自动释放。根提示数从各自原生 JSONL 读回，技能展开与工具结果不另算。摘要保留实际 assistant model；仅启动 argv 不算供应商模型事实。

模型行为有随机性。如果修前未复现，不能把过去 T-155 的失败冒充同场景红态；交回主控决定下一步，不改提示诱导失败、不自动重试。

## 修前结论与本次修改

主控 #47 的独立结论与 worker 读回见 `controller-baseline-01.md`。oracle 的错误来自验收脚本自加未要求的明细条件、忽略反向语义；没有环境错误，构成本次红态。C5 要求均已写入草稿卡，但无显式逐项自检，且未派发；不把这次运行写成遗漏复现。执行主控已明确要求据此继续修提示词。

两个说明入口补了三项判断要求：

- 派发前把每条用户要求对应到任务卡并列核对结果，尤其是顺序、等待和演练首版；漏项先改，首版演练不替代最终完成条件。
- 验收从原始数据推导，保存卡前实际运行正确、明显错误的样本；核对数字与含义的对应，拒绝错数字、反向语义与缺项，接受未限定排版的正确内容；保留样本、命令和退出码，不擅加条件，不以文件存在或关键词出现代替验收。
- 区分暂时未完成、明确拒绝与结果未知；报告原始错误、最后确定事实、具体停点和缺少的事实，无新事实停止轮询，未知写入不自动重发。

夹具权限根因在本票生成的临时 settings，不在产品启动器。修正为仅对隔离测试主控允许 Bash，保留 dontAsk 和子 agent 禁用；产品与受管 worker 的权限未改。RUN-OUTSIDE-02 中绿态与旧说明变异使用相同夹具设置，场景输入与业务 oracle 未改。

RUN-OUTSIDE-02 实际新增 4 个真实根提示，累计 8/16；oracle 未绿，变异按计划跳过。C5 真实派发，独立判断见执行主控 #49 与 `diagnosis-02.md`；T-158 说明回归 PASS。

对照记录证明两个场景都加载了新版规则并实际自测，oracle 失败来自样本预期跟随自加的明细条件、缺少反向含义反例。再次修改将三条规则移出派发步骤，明确单独写验收脚本也适用；要求判据逐条追溯用户要求，先独立定样本预期，含没有额外明细的最小正例和关键词相同但含义相反的反例，不能修改预期或补无关明细凑通过。未改测试代码、场景提示、11 个业务样本或通过判据。

RUN-OUTSIDE-03 实际新增 2 个真实根提示，累计 10/16，变异因未绿而跳过。原生记录证明它做了汇总反向上下文样本，但该样本必然命中检查器的有限业务动作禁词；对正文整体真实性被否定的输入仍误收，见 `diagnosis-03.md`。本次说明只补全文断言、业务动作与内容有效性之区别，以及未参与识别规则编写的改述复验，不列夹具原句或食材数字。

最后一轮 RUN-OUTSIDE-04 仅做 oracle 绿态及 parent-instructions 变异，预计最多 4 个真实根提示、累计最多 14/16；若绿态失败，仅新增 2 回合、跳过变异，不再修改说明或复跑，写清达成情况与残余失败后交主控转构思主控决定验收判据。脚本用一次性启动记录防止重复启动这一轮。不复跑 C5；此前 C5 结论只绑定 `d4b79be10`，不拿它替新说明的未运行行为背书。

```zsh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-04.sh
```

## 当前验证与限制

- PASS：Python 编译、`--help` 与 diff 空白检查（未启动后台、Electron 或模型）。首次 py_compile 默认缓存目录被沙箱拒绝；改用允许的 `/private/tmp/t163-pycache` 后通过，这不是产品红态。
- PASS：本次修改后的 Python 编译、RUN-OUTSIDE-02 shell 语法、真实 `a2a help` 入口和 UTF-8/空白检查，见 `local-checks-02.json`。收尾 project-map status 仍仅有 T-158 缺 Resolution，stale living docs 为 0，见 `project-map-status-02.json`。
- PASS：第三轮说明修改后的真实 CLI help、RUN-OUTSIDE-03 语法、UTF-8/空白，以及测试代码与 `d4b79be10` 无差异，见 `local-checks-03.json`；T-158 说明回归见 `t158-instructions-03.json`。地图状态仍仅有同一项范围外问题、stale living docs 为 0，见 `project-map-status-03.json`。
- PASS：第四轮说明的 CLI help、RUN-OUTSIDE-04 语法、UTF-8/空白及测试代码未改检查，见 `local-checks-04.json`；T-158 回归见 `t158-instructions-04.json`。地图仍仅有既存 T-158 Resolution 问题、stale living docs 为 0，见 `project-map-status-04.json`。
- PASS：将 T-155 历史弱验收原样交给本票输入探针，正确输入被接受，错数字、反向语义和分组四个坏样本揭露弱验收。结果见 `probe-oracle-known-bad.json`（首次内联运行）与 `probe-oracle-known-bad-replay.json`（下面命令重放）。这只证明测试可抓住已知坏检查器，不是本票真实模型修前红态。
- PASS：修前真实 Haiku oracle 检出误拒和反向语义误收；两个摘要无环境错误，实际模型与 4 个根提示已核对。这是有效失败证据，不是产品通过。
- NO_GO：RUN-OUTSIDE-02 的 oracle 仍误拒两个正确汇总、误收反向购买语义，摘要无环境错误；完整保留，不改判据。诊断见 `diagnosis-02.md`。
- NO_GO：RUN-OUTSIDE-03 的 oracle 在 11 个业务样本中只失败 summary-inverted；两个正确汇总和反向购买语义本次被正确处理。仍不是绿态，不将一次模型输出当成稳定性或收益证明。诊断见 `diagnosis-03.md`。
- INCOMPLETE：C5 漏项红态未复现；RUN-OUTSIDE-02 的 C5 无遗漏且自测发现标签对调后修正，但显式逐项核对列表不完整。最新说明的 oracle 绿态、提示词变异和独立行为验收待运行，不能上调结论。
- PASS：`test_t158_revise_retry_e2e.py --check instructions` 在 RUN-OUTSIDE-02 通过，摘要为 `t163-outside-02.8v3EhC-t158-instructions.json`。本次规则移位后另做同一静态入口回归（不调用模型）；RUN-OUTSIDE-03 按主控要求仅含 oracle 与变异。
- M04 的三种状态与无新事实停点已加入同一主控说明；本卡指定的两个场景不会完整证明未知状态长轮询已消除，不能宣称可靠性或收益已改善。
- 会话开始 project-map status：既存 `T-158 closed without a Resolution`，stale living docs 为 0。该 ticket 在修改边界外，已向主控报告，未改地图或他人 ticket。

## 提示词对策在真实 haiku 上的达成情况与残余失败（截至 RUN-OUTSIDE-03）

| 对策 | 实际证据与限制 | 状态 |
| --- | --- | --- |
| M01 派发前逐项核对 | 修前卡内容已无遗漏，漏项红态未复现；第二轮卡完整、实际派发且守住停点，显式逐项核对列表不完整。最新说明未再跑 C5。 | INCOMPLETE |
| M02 验收脚本自检 | 第二、三轮均实际运行自建正反例；第三轮仍接受正文整体被否定的汇总，oracle 未绿。最新候选待第四轮，旧失败不覆盖。 | NO_GO |
| M04 无新事实停下 | 说明已补三种状态和停点；C5 有按用户停点结束的证据，但未完整复跑未知状态长轮询场景。 | INCOMPLETE |

当前不声明 DELIVERED；这是按派发要求提交 RUN-OUTSIDE-04 后的暂停点。独立行为审查留在真实绿态与候选冻结之后，不以作者自检替代。

历史弱验收探针的重放命令：

```zsh
PYTHONPYCACHEPREFIX=/private/tmp/t163-pycache python3 evidence/2026-10-23-batch24/T-163/probe_oracle_known_bad.py --summary evidence/2026-10-23-batch24/T-163/probe-oracle-known-bad-replay.json
```

再次运行时必须换新的摘要路径；原始 case 目录保留在摘要的 `fixture` 路径，交主控按 T-088 归档。
