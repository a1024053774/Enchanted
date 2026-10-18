# T-095：第 4 回合之后的冻结审查请求

**两形态独立真实 PASS；整体 INCOMPLETE，完整 Acceptance 仍 NO_GO。** 请求执行主控另开干净的只读 reviewer 会话，审查本次冻结候选。实现者没有自签审查，本文件不是接受结论。

## 固定对象

- 仓库：`/Users/luckye/Documents/Code/a2a-wt-t095`；task T-095 / attempt a1 / worker s16-t095 / ready_rev 1。
- 候选是本文件所在的冻结提交。主控必须把本次 `T-095 FROZEN <sha>` 的完整 SHA 传入审查任务，不能只传可移动分支名；缺少固定 SHA 时返回 INCOMPLETE。
- 产品代码版本：`faa2b9b3b9ac6195012fc8ea88e6e6d73dee2bf4`，与第 4 回合现场版本一致。其后的本次提交只补证据、报告及归档命令的清单选项；`scripts/agent-status`、`scripts/native_questions.py`、`scripts/test_agent_status.py` 未变。
- 比较基线：`3c9016d0230223945f0e16543b230a047c2ad032`。不得改 dispatch、launcher、Herdr server、gates、地图或全局配置，不存在第二套生产状态写入。
- 只读，不修复、不 submit、验收或集成，不操作已关闭 pane。真实探针已用 **4 / 4 根回合，剩余 0，自动答案 0**；不启动新探针、不重试、不 resume、不自动答题。审查会话由主控另行派发，本请求不代为启动。

## 重建标准

先读 `.project-map/tickets/T-095-*.md` 和任务卡，结合主控 #115 / 主控 #8 的最新明确标准：

1. 折叠只认屏幕底部 `? N question` 或 `? N questions` 的正整数计数前缀，任意后缀不影响。当前实现把底部定义为最后 12 个非空行，忽略行首空白。
2. 展开只认同一控制条同时含 `⌃] skip` 与 `⇧→ main prompt`；上方残留输出、标题、选项编号、enter 或整屏形状不参与判定。
3. 两份读屏 visible / detection 均有锚点，且前后 Herdr `agent_status=blocked`，才是 `waiting_controller_answer` / “等待主控回答”，附 worker 与 launch 身份。只有其中一方成立或两份读屏不一致时 unknown，记录冲突；不能用原生 pending 补足缺少的 UI 锚点。
4. 原生会话仍按启动记录的 native UUID 只读绑定，身份、日志完整性和读取稳定性不可核对时 unknown。普通 working 保留机械活动结构与无 pending 的要求；skip 后日志无解决事件时继续保守 unknown，作为已知限制，不把 `accepted:true`、普通后续输出或 item 完成当作已解决。

以上锚点与 blocked 规则替代先前对标题、整屏或原生 pending 的等待正判要求；不改变原生身份和完整性保护。完整实现说明见 `UI-STRUCTURE.md`，但实现者文档、85 项合同与新增测试均不是独立 oracle。

原始红态要求“两形态当前为 working”；2026-10-18 四次受控运行面板阶段的 Herdr 原值均为 blocked。2026-10-17 T-094 的 working 仍只有执行主控 / 用户报告，worker 未取得其原件。此缺口不能用 skip 后 working 补证，也不能自行修改 ticket 或上调验收。

## 首先核对的独立原件

目录：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/green-anchor-independent-20261018T135446Z-2626001e`，225 文件、196,652 字节。该 run 在 faa2b9b3 冻结后产生，产品未再根据这份输入修改；先前三份真实输入参与过解析器修改，只是回归证据。

| 范围 | 原件位置与预期检查 |
| --- | --- |
| 版本、完整 argv、单次输入与清理 | `run.json`、`version.stdout`、`records/launches.jsonl`；代码为 faa2b9b3，`collection_complete=true`；采集器整体仍打印 INCOMPLETE，不是自动验收。 |
| 默认折叠 | command 020–025 的采集；command 026 的真实 agent-status stdout / exit。计数含年龄后缀 `? 1 question · 18s`，两份读屏均有锚点，前后 blocked。 |
| 展开 | command 027–032；command 033 投影。同条 `⌃] skip` / `⇧→ main prompt`，前后 blocked。 |
| skip 后即时 / 30 秒 / 60 秒 | command 034–039 / 041–046 / 048–053；实际投影 040 / 047 / 054。UI 无锚点、原值 working，native pending，保守 unknown。 |
| 原生会话 | `native-bound.jsonl`，UUID `01a14f4b-a96a-7cb0-b480-a697871a66f7`。前三投影 89,498 字节 / 20 条，后两项 96,693 字节 / 27 条；不得把后来的尾部提前给早期投影读取。 |

身份：worker `t095-probe-71d17066e9`，launch `launch-t095-probe-32ee664e4b1b45249a3a9b8bcde50904`，pane `wF:p6M`，terminal `term_65e1dbd8342734a`。问题 call 为 `call_a8a2609be80f4580a6f7b262d2758984`，第 14 条发起，只有 accepted 收件回执。

操作者来源是执行主控 #118 / 主控 #9：SHELL_READY -zsh，CODEX_IDLE 正常；首次 COLLAPSED 前只观察、没有展开。然后 Shift+← 展开，Ctrl+] skip；30 秒和 60 秒只读采集期间无任何输入。不得与第 2 回合先展开再折叠的操作混用，也不推断操作差异的因果关系。

## 待独立复核的结果和限制

现场 command 026 / 033 及当前入口回放均为“等待主控回答”，退出 0，身份正确、无冲突；关闭后的三个阶段均 unknown，退出 2，reason `screen_native_conflict`。后者证明等待显示已退出，不能证明问题已解决或普通 working 已恢复。原生第 21–27 条仅有同 turn 的 sleep 返回、Extension / Reasoning item 完成、再次 sleep 和 token 记录，没有问题解决、新 turn 或整个 turn 完成事件。安全 unknown 不等于完整回落 Acceptance PASS。

可在只读审查中运行零模型回放，报告须用新临时路径：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --inputs evidence/2026-10-16-batch16/T-095/real-anchor-independent-inputs.json --report <新临时报告路径>
```

预期五状态为 waiting / waiting / unknown / unknown / unknown，进程退出 1：身份、只读入口与原投影一致性 PASS，完整正常回落合同 NO_GO，总状态 INCOMPLETE。回放通过显式假 Herdr 喂入原采集，执行真实 `scripts/agent-status`，只重建临时 SQLite 索引，保留 worker / launch / native UUID / cwd 和原生日志前缀。它不能替代现场原投影，也不能重建当时未逐次保存的产品内部读屏。

**两次 herdr_timeout 根因未定，必须保留为已知限制。** 外置盘 `offline-native-anchor-repair-20261018T134759Z/reports/contract-final.json` 的 `working-command-context`（13:41:32.542819Z）与 `archives-final.json` 的 `archive-red-expanded`（13:41:32.547032Z）均在第一个假 Herdr get 超过 3 秒，实际 unknown / herdr_timeout / exit 2。完整失败夹具已归档，不能用随后串行 85 项 PASS 抹去失败或宣称根因解决。这里观察的是假 Herdr，不补称实际生产超时已经复现。

生产 `scripts/agent-status:183` 默认每次 Herdr get / read 期限 3 秒，第 33–40 行将超时转 unknown。真实 Herdr 繁忙或延迟超限时会暂时读不到等待状态，调用方必须保留诊断、之后再次读取，不能消费成 working 或已解决。没有自动重试、期限调整或 server 修改；审查需评估这项可用性限制，不把保守输出说成没有生产影响。

## 审查重点和输出

按 [behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 审查一个固定候选，将结构风险一起审查，不重复派第二个自审。能力范围：状态编排、异步事件、身份范围、CLI 交互和原生文件解码；模型意图理解、检索和生产发布为 N/A。

核对唯一入口、原生 UUID 绑定与日志完整性、锚点和 blocked 的双向冲突、普通 working 的机械依据、无面板时 pending 的归属，以及异常是否掩盖未实现行为。按 Deep modules 检查原生模块是否隐藏必要复杂性；不为兼容、fallback 或另一套状态路径放宽合同。

反事实报告与原件位于上述 offline-native-anchor-repair 归档：修前 11 阶段中 3 项失败；修后原件回归 11 项通过；AND 改 OR 的单边放行坏副本被状态断言拒绝；串行入口合同 85 项通过。它们都由实现者提供，审查须检查 oracle、已知坏实现和元变换是否足以支持主张，不能把固定样本回放当作独立验收。第 4 回合才是未参与修改的新真实输入；只有一次两形态正例，不支持可靠性或负载改善主张。

旧真实失败、旧报告和当前派生报告位置见 RESULTS.md 及各 archive 清单。`anchor-repair-confirmed.archive.json` 已核对 732 文件 / 6,886,506 字节；当前 57 文件 / 602,404 字节派生读回尚待沙箱外复制，主原件已在外置盘。不因归档成功给业务 Acceptance 背书。

按 skill 要求报告 STATUS / TARGET / EVIDENCE / FINDINGS / COUNTEREXAMPLE / LIMITATIONS，重复问题需要时补 RULE；每项发现有确切文件与行号、可达反例及证据层级。候选变动时停止并返回 INCOMPLETE，不在审查中修复。独立审查未完成、原始 working 红态缺失、正常回落未证明、超时根因未定，均应留在结论中；不得判整票 PASS。
