# T-095-1：第 5 回合已回答读回与最终冻结

**整体 INCOMPLETE / NO_GO，不交付整票 PASS。** 提交 A 后即时、30 秒、60 秒均离开“等待主控回答”，满足选 B 的这个回落条件，实际均为 unknown。展开正判 PASS；本次默认折叠无 UI 锚点，按规则必须 unknown，符合保守保护，却未满足本样本的“折叠待答正判”。日志有明确 A 应答和 turn 完成，当前解析器未识别该格式。候选交独立审查，不追加探针。

task T-095 / attempt a1 / worker s16-t095 / ready_rev 1；session `983db526-dfe8-473a-857b-b3f2af0af582`，launch `launch-4b1abba18e87460da9cbacec04905c78`。基线 `3c9016d0230223945f0e16543b230a047c2ad032`；产品仍为 `faa2b9b3b9ac6195012fc8ea88e6e6d73dee2bf4`，第 5 回合采集器为 `66b824a5bf15312eb2a88bd6ec7cce7e70155ab3`。本次只补证据、修报告工具的空 identity 处理、更新文档和归档清单选项。产品、合同测试、dispatch、launcher、Herdr、工作台、gates、地图、全局配置未改。完整冻结 SHA 见交付末行；未 submit、独立审查、验收或集成。

验收依据为用户选 B：main `0e92f78ec6824265cdfcbb9387ba4b454d7eee7f` 上 T-095“裁定”、answer `20261018T140451Z-ideation-answer-001` 及主控 #120 / #123。红态=修前无独立等待状态；回落=离开等待，unknown 允许。主控 #115 的屏幕锚点与 blocked 双来源印证规则不变。运行前报告见 [READY-66b824a5.md](READY-66b824a5.md)，旧完整合同 NO_GO 见 [FROZEN-4a227114.md](FROZEN-4a227114.md)，历史失败不回写。

## 第 5 回合现场与实际入口读回

原件：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/answered-20261018T165159Z-ee1a8372`，**225 文件、178,811 字节**。Codex 0.163.0、Herdr 0.9.4；模型配置 gpt-6.1-sol / xhigh / 请求 fast，不证明供应商实际 tier。run 为 INCOMPLETE，collection_complete=true，采集完成不等于验收通过。摘要见 [real-answered.archive.json](real-answered.archive.json)。

- worker `t095-probe-2f240f63b2`；launch `launch-t095-probe-0689a92778ff4e2e889efe97ddcb6bcf`。
- pane `wF:p6Q`；terminal `term_65e20374d202a4e`；native UUID `01a14fed-e894-7181-8690-8af96d512c04`。
- turn `01a14fee-1c11-7a02-afef-8949d4254d9e`；问题 call `call_678d50e5fcee4210b64a0cdfe24fd617`。

操作者 #123 / 主控 #11：SHELL_READY 为 -zsh，CODEX_IDLE 正常；提交约 11～20 秒只观察默认折叠，没有展开即确认 COLLAPSED。实际保存画面为 Working (26s)，没有问题计数。随后 Shift+← 展开并确认 EXPANDED；光标在 A，只按一次 Enter，约 5 秒后面板消失，Worked for 59s、Herdr done，确认 ANSWERED。30/60 秒采集期间无输入。操作者估计时间与保存读屏分别记录，不改成同一个数值。

| 阶段（UTC） | 采集 / 投影命令 | 原值 → 实际状态 / exit | 判断 |
| --- | --- | --- | --- |
| 折叠 16:53:14 | 020–025 / 026 | blocked → unknown / 2 | screen_anchor_herdr_conflict；保护规则符合，等待正判 NO_GO。 |
| 展开 16:53:30 | 027–032 / 033 | blocked → 等待主控回答 / 0 | 两屏第 6 行同条 skip / main prompt；身份正确，PASS。 |
| A 后即时 16:53:50 | 034–039 / 040 | done → unknown / 2 | native_user_response_uncorrelated；已离开等待。 |
| A 后 30 秒 16:54:20 | 041–046 / 047 | done → unknown / 2 | 同上，未卡住等待。 |
| A 后 60 秒 16:54:51 | 048–053 / 054 | done → unknown / 2 | 同上，未卡住等待。 |

答后三个独立采集画面均为 Worked for 59s 和普通输入框，无面板；前后 Herdr get 均 done。归档 worker / launch / pane / terminal、绑定记录和原生日志头另行核对一致。产品在原生异常处提前返回，尚未读屏或输出完整 identity，故三项 identity=null、anchors={}；不能把空字段冒充完整读屏或 native clear。

**答后离开等待这个状态条件 PASS；完整原生投影仍 INCOMPLETE。** 没有输出 idle / clear。完整回放身份输出检查与本次折叠正判不通过，不能把局部状态条件上调为整票 PASS。

## 日志确有 A 应答，产品尚未识别

最终绑定日志 **99,578 字节、30 条**；折叠、展开现场投影截止为 **93,008 字节、20 条**。

| 行号 / UTC | 机械事实 |
| --- | --- |
| 12 / 16:52:52.362 | 唯一 request_user_input_async，call 为上述问题 call。 |
| 15 / 16:52:52.428 | accepted:true，只有收件回执含义。 |
| 22 / 16:53:44.899 | sleep 被 new input 中断，仅作为时序事实。 |
| 24、25 / 16:53:44.902、.903 | user message / UserMessage，固定 send_user_message_question_reply 标记内为 JSON，answer=A。 |
| 27 / 16:53:46.443 | 模型公开回复 ANSWER_RECEIVED。 |
| 30 / 16:53:46.455 | 同 turn 的 task_complete，last_agent_message=ANSWER_RECEIVED。 |

questionItemId 可解码为 `["request_user_input_async","call_678d50e5fcee4210b64a0cdfe24fd617",0]`，与唯一请求 call_id、索引及 UserMessage 的 thread / turn 一致。这里只解析机械 JSON 字段，不按问题自然语言匹配。**本次存在可关联应答和 turn 完成证据**，不能沿用 skip 的“无应答/解决事件”表述。

没有现有解析器处理的 function_call_output.answers 应答映射。`scripts/native_questions.py:130` 仅把 pending 后的 UserMessage 记为未关联事件，第 168–169 行报 native_user_response_uncorrelated；第 131 行“该格式没有 call id”的旧注释不覆盖新原件。产品未解析包围标记内的 questionItemId，未报告 resolved / clear。本轮只冻结事实，不据这份独立数据修产品，也不以 task_complete 单独清除问题。

## 折叠锚点缺失的验收影响

本次两屏都无计数或展开锚点，只有 blocked，按双来源规则必须 unknown；不能用 native pending 补足、不能降成 working。**符合保护规则，不等于满足折叠待答正判；本样本正判 NO_GO。** 第 1 回合 red 也无锚点，第 4 回合则出现计数并正判。现有采样不能区分锚点出现较晚还是本次一直不出现，不能推断原因或频率。

生产中，真实待答可能持续显示未知，主控无法仅靠此命令发现所有默认折叠问题；本次展开后可识别。已知限制不自动成为验收豁免，是否接受这种覆盖范围交审查和主控裁定，本 worker 不上调。

## 回放及保留的失败

已直接读取原 stdout / exit，再执行实际 scripts/agent-status 回放五阶段，状态、原因、原值、冲突均与现场相同。输入见 [real-answered-inputs.json](real-answered-inputs.json)，报告见 [answered-readback.json](answered-readback.json)：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --inputs evidence/2026-10-16-batch16/T-095/real-answered-inputs.json --report <新报告路径>
```

退出 1，INCOMPLETE，matches_original_projection=true；完整投影检查 replay_status / regression_status 均 NO_GO：折叠未正判，答后完整 identity 输出不可得。调用均只读；前两项四次 get/read 完成，后三项在原生异常处仅执行第一个 get。完整输出缺失不等于归档身份不符，后者已另行核对。

答后原 unknown 投影没有 native bytes / lines。回放逐项标明采用最终 99,578 字节归档，不能声称精确复原原读取截止点；事件逻辑时间早于采集也不能推定落盘时序。回放不代替现场投影，也不算第二次独立运行。

报告工具原先遇 identity=null 会抛 TypeError，失败输出和部分夹具已保留。本次仅让工具如实记录 unavailable，完整身份判据未放宽；同输入可输出五项报告，仍 NO_GO。这是报告工具缺陷，不是新的产品红态。

- [before-status-B.json](before-status-B.json)：修前无独立等待入口和状态，两形态 blocked 原件逐字节回放，新红态 PASS。2026-10-17 working 仍无 worker 原件，不补称旧红态复现。
- 第 4 回合两形态独立真实 PASS；skip 三阶段 unknown 按 B 满足离开等待，见 [skip-B-readback.json](skip-B-readback.json)。该 run 无解决事件的限制保留，不能推广到本次已回答 run。
- 同一产品的既有回归 11 项、串行合同 85 项 PASS、AND→OR 坏副本被拒绝，原件保留；本次产品与合同测试未改，未重跑大套件。旧独立失败不改写。
- **并发两次 herdr_timeout 根因未定。** offline-native-anchor-repair-20261018T134759Z 的 contract-final.json / working-command-context（13:41:32.542819Z），及 archives-final.json / archive-red-expanded（13:41:32.547032Z），均在首个假 Herdr get 超过 3 秒，unknown / herdr_timeout / exit 2。原失败及夹具保留；同时发生不证明原因。生产每次 get/read 默认 3 秒，Herdr 繁忙或延迟超限可能遮住真实等待，返回 unknown；须留诊断再读，不能当 working 或已解决。未改期限、重试或 server；串行 PASS 不证明根因解决或负载可靠性改善。

## 预算、归档、冻结

真实探针 **5/5，剩余 0，自动答案 0**；本轮 worker 新增真实模型回合 0。不再运行历史探针脚本、不重试、不 resume、不自动回答。日志仅一次 request_user_input_async 和一次 sleep，无模型命令或文件操作。run 记录 pane 关闭、隔离 HOME 删除、空 fixture / scratch 移除；只读核对 HOME / fixture 均不存在，不操作已关闭 pane。

answered-preparation 包 **300 文件、1,439,478 字节**，全部相对路径大小、总数、总字节与回执核对 PASS，originals_deleted=false，见 [answered-preparation-confirmed.archive.json](answered-preparation-confirmed.archive.json)。真实主原件已在外置盘。

新增派生包 **93 文件、996,342 字节**，含报告工具失败和夹具，待沙箱外复制；见 [answered-readback.archive.json](answered-readback.archive.json)。只复制、不删除、0 模型回合，缺盘、源变化、目标存在均停止：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --manifest answered-readback.archive.json --apply
```

answered-final-map-status.txt：0 problems / 0 stale living docs。最终 [REVIEW-REQUEST.md](REVIEW-REQUEST.md) 交主控另开干净只读 reviewer，必须传本次 FROZEN 的完整 SHA。冻结表示可审，不表示整票通过。
