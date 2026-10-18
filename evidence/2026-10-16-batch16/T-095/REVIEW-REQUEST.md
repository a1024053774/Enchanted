# T-095：第 5 回合之后的最终冻结审查请求

**worker 结论：INCOMPLETE / NO_GO，请独立审查，不直接接受。** 答后离开等待的状态条件 PASS；第 5 回合折叠无锚点而 unknown，符合保护规则，但该样本没有正判等待；应答格式未解析，完整原生投影仍不可得。第 4 回合两形态真实 PASS 和旧失败均保留，不用其中一次覆盖另一份反例。

## 固定候选和权限

- 仓库 `/Users/luckye/Documents/Code/a2a-wt-t095`；task T-095 / attempt a1 / worker s16-t095 / ready_rev 1。
- 对象为本文件所在的最终冻结提交。主控须把本次 `T-095 FROZEN <sha>` 的完整 SHA 传给新的 reviewer；不能只传分支名，未固定 SHA 返回 INCOMPLETE。
- 比较基线 `3c9016d0230223945f0e16543b230a047c2ad032`。产品为 `faa2b9b3b9ac6195012fc8ea88e6e6d73dee2bf4`，第 5 回合采集器为 `66b824a5bf15312eb2a88bd6ec7cce7e70155ab3`；本次没有据新原件修产品或合同测试，只补证据并修报告工具的 null 处理。
- 只读，不修复、不 submit、验收或集成，不改 ticket、Herdr、配置，不操作已关闭 pane。探针预算 **5/5，剩余0，自动答案0**；禁止再运行真实探针、重试、resume 或自动答题。历史脚本保留作记录，不能再带 approve 运行真实会话。
- 执行主控另开干净只读 reviewer；本 worker 没有自签审查，也没有代为启动审查会话。

## 先重建标准

读取任务卡及 main `0e92f78ec6824265cdfcbb9387ba4b454d7eee7f` 的 `.project-map/tickets/T-095-worker-awaiting-controller-answer-state.md`“裁定”节，结合 answer `20261018T140451Z-ideation-answer-001` 与主控 #120 / #123。当前 worktree 的票没有合入该裁定，不得仅用旧 Acceptance 判断：

1. 红态为修前读取没有独立等待状态，不再要求两形态原值 working。旧 working 报告没有 worker 原件，2026-10-18 面板实测为 blocked，不能改写。
2. 等待内部值 waiting_controller_answer，显示“等待主控回答”，附 worker / launch。折叠为底部 `? N question` / `? N questions` 正整数计数前缀，任意后缀不影响；当前实现的底部范围为最后12个非空行。展开为同条 `⌃] skip` / `⇧→ main prompt`；visible / detection 均有锚点且前后 blocked 才正判。缺来源、不可读、身份/记录异常、冲突均 unknown，冲突留证。不用标题、自然语言意图、整屏结构或原生 pending 补缺失锚点。
3. 回落是离开等待，unknown 满足；答完仍是等待才违反这个状态条件。**不要把必须 idle、clear 或现有解析器必须生成 resolved 重新加入选 B 的验收。** 对来源、身份完整性的未完成检查单列，不用任何错误输出的“非等待”字符串独自证明真实已回答。
4. 原生回答、解决与 turn 完成事实分别记录；accepted 不是答案，task_complete 单独也不解决问题。

实现者报告、85 项合同及新增测试均不作独立 oracle。按用户新裁定重建标准，再核对真实入口与原件；折叠无标记时的保护规则合规，与折叠待答识别覆盖范围分开判断。限制能否接受交主控裁定，不自行放宽，也不把未知上调。

## 第 5 回合必读原件

`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/answered-20261018T165159Z-ee1a8372`，225 文件 / 178,811 字节。run.json、version.stdout、records/launches.jsonl 证明版本、完整 argv、1 根提示、手工 A / Enter 及清理；collector 为 INCOMPLETE、collection_complete=true，不是自动验收。

| 阶段 | 原始采集 / 实际投影 |
| --- | --- |
| 默认折叠 | 020–025 / 026：两屏只有 Working (26s)，无 question 锚点；blocked → unknown，screen_anchor_herdr_conflict，exit2。 |
| 展开 | 027–032 / 033：第6行同条 skip / option 1/3 / main prompt；blocked → 等待，exit0。 |
| A 后即时 | 034–039 / 040：Worked for 59s，无面板；done → unknown，native_user_response_uncorrelated，exit2。 |
| A 后30秒 / 60秒 | 041–046 / 047、048–053 / 054：同上，未卡住等待。 |

身份：worker `t095-probe-2f240f63b2`，launch `launch-t095-probe-0689a92778ff4e2e889efe97ddcb6bcf`，pane `wF:p6Q`，terminal `term_65e20374d202a4e`，native UUID `01a14fed-e894-7181-8690-8af96d512c04`。turn `01a14fee-1c11-7a02-afef-8949d4254d9e`，问题 call `call_678d50e5fcee4210b64a0cdfe24fd617`。

操作者 #123：首次 COLLAPSED 前仅观察、没有展开；然后 Shift+←。A 已选中，只按一次 Enter，无数字1、skip 或额外提示；约5秒后面板消失，确认 ANSWERED；之后无输入。不要与第2回合先展开再折叠或第4回合 skip 的记录混用。

## 两个关键边界

**折叠覆盖。** 第5回合没有锚点，unknown 符合双来源规则；这是该次待答未正判的真实样本。第1回合 red 也缺锚点，第4回合有锚点且两形态 PASS。不能据单次采样断言锚点只会迟到或一直不出现，不能估计可靠性。请判断这项覆盖缺口对 Acceptance 的影响，不能用“有保护性 unknown”自动证明等待识别成功。

**真实 A 应答存在。** native-bound.jsonl 最终99,578字节/30条；折叠、展开截止93,008字节/20条。第12条发起请求，第15条 accepted；第24/25条是固定 send_user_message_question_reply 中的 JSON，answer=A，questionItemId 可解码为 `["request_user_input_async","call_678d50e5fcee4210b64a0cdfe24fd617",0]`，thread / turn 一致。第27条公开回复 ANSWER_RECEIVED，第30条同 turn task_complete。不能写成“本次没有应答”。没有现有解析器使用的 function_call_output.answers 映射。

`scripts/native_questions.py:130` 仅记录 pending 后的 UserMessage，第168–169行报未关联；第131行的旧注释未覆盖此格式。`scripts/agent-status:203` 先读原生状态，异常使答后三项在读屏和完整 identity 输出前返回，因此 identity=null、anchors={}。归档启动记录/原生日志头/前后get目标已另行核对一致；空输出字段不代表会话错绑，也不代表已完成 native clear。审查需将“状态已离开等待”与“完整投影缺失”分开，不把答后 unknown 本身改判成新标准下的卡住失败。

## 回放、反例与限制

零模型复核：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --inputs evidence/2026-10-16-batch16/T-095/real-answered-inputs.json --report <新临时报告路径>
```

五状态应为 unknown / waiting / unknown / unknown / unknown，matches_original_projection=true，退出1，完整投影检查 NO_GO。后三项只有首个 get；因没有完整 identity 输出，报告工具保留完整检查不通过。答后原投影未记录原生字节截止点，回放明确使用最终绑定归档，不能称精确重建当时读取边界。报告工具先前 TypeError 和部分夹具也已保存；本次修工具只为报告负例，不改变产品或放宽完整检查。

其他独立边界：第4回合 green-anchor-independent-20261018T135446Z-2626001e 的026/033为等待、040/047/054在skip后unknown；两形态真实 PASS 与第五回合缺口并存。前三份参与过解析器修改的 red / green / green-independent 仅为回归。新红态 before-status-B.json 证明起点无状态及两形态原值回放；AND→OR 坏副本被拒绝，答后仍展开的元变换被判据拒绝。实现者测试和离线替身不能替代真实答复证据。

**并发两次 herdr_timeout 根因未定。** offline-native-anchor-repair-20261018T134759Z/reports/contract-final.json 的 working-command-context（13:41:32.542819Z）与 archives-final.json 的 archive-red-expanded（13:41:32.547032Z），首个假get超过3秒、unknown/exit2。原失败和夹具保留；不补称实际生产超时已复现。生产每次get/read默认3秒，繁忙或延迟超限会暂时遮住真实等待；须保留诊断再读，不能当working或解决。未加重试、改期限或server；串行85项PASS不证明根因解决或负载可靠性改善。

answered-preparation 的300文件/1,439,478字节已按清单和回执核对PASS；本次派生包93文件/996,342字节待沙箱外复制，见 answered-readback.archive.json。真实主原件已在外置盘。归档成功不能替业务 Acceptance 背书。

## 独立审查方式

按 [behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 审查单个固定候选，将结构风险一起检查，不重复自审。能力范围为状态编排、异步事件、身份范围、CLI交互和文件解码；模型意图理解、检索、生产发布为N/A。核对唯一入口、UUID绑定、unknown归属和冲突、普通working机械依据、异常是否掩盖未实现格式；按 Deep modules 检查原生模块是否隐藏必要复杂性。

按skill输出 STATUS / TARGET / EVIDENCE / FINDINGS / COUNTEREXAMPLE / LIMITATIONS，重复问题需要时补RULE；发现须有确切文件与行号、可达反例和证据层级。重建标准后独立判断，不把worker结论当oracle。候选改变时停止并返回INCOMPLETE，不追移动目标、不在审查中修复。最终是否可按已知限制接受由主控依证据裁定；本worker未提交整票PASS。
