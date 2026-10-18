# T-095-1：独立探针读回与冻结审查

**INCOMPLETE / NO_GO。** 独立真实探针的折叠、展开、即时 skip 后、延后 30 秒和 60 秒五次现场投影均为 unknown；`scripts/agent-status` 对归档原件的回放得到相同状态、原因和冲突。两种形态未通过；关闭后的正常回落也未证明。旧样本回归通过不能替代这次独立失败。未 submit、独立审查、验收或集成。

本次按主控 #113 / 主控 #7 只读回、补证据并冻结。产品代码仍为独立探针实际运行的 `96464ecf49523e6e306c3c03fea5ad9f2897951b`；本次只修改读回 / 归档工具和文档，未修解析器。完整冻结提交号见交付末行。task T-095 / attempt a1 / session `983db526-dfe8-473a-857b-b3f2af0af582` / launch `launch-4b1abba18e87460da9cbacec04905c78` / ready_rev 1；基线 `3c9016d0230223945f0e16543b230a047c2ad032`。

前一修复候选报告逐字保存在 [CANDIDATE-96464ecf.md](CANDIDATE-96464ecf.md)，更早失败冻结见 [FROZEN-afe160292.md](FROZEN-afe160292.md)。历史结果不改写、不上调；本报告是本次新的读回结论。

## 独立现场与原件回放

原件：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/green-independent-20261018T131803Z-9e55a235`；225 文件、197,119 字节，直接采集到外置盘。清单为 `real-independent.archive.json`。worker `t095-probe-358b387119`、launch `launch-t095-probe-15930f352f8142208e64fd47f1af7ac9`、pane `wF:p6H`、原生 UUID `01a14f2a-0834-7453-a50a-bc87fd434e83`。五次现场投影均已绑定该身份，不是索引或身份缺失导致失败。

| 阶段 / 原件投影命令 | Herdr | 状态与原因，现场 / 回放一致 | 判断 |
| --- | --- | --- | --- |
| collapsed / 026 | blocked | unknown，`incomplete_folded_question_panel` | **NO_GO**。真实计数行为 `? 1 question · 16s`；当前计数全行匹配不接受年龄后缀。 |
| expanded / 033 | blocked | unknown，`incomplete_question_panel` | **NO_GO**。Working 与 Queued follow-up 之前还有可见输出片段 `  • B`；当前逻辑只从第一行剥离机械前缀，随后标题区校验失败。 |
| cancelled / 040 | working | unknown，`screen_native_conflict` | **INCOMPLETE，正常回落未通过**。屏幕为普通活动，原生仍 pending；保留来源冲突，未误报 working 或已解决。 |
| cancelled-followup-30s / 047 | working | unknown，`screen_native_conflict` | **INCOMPLETE**。日志增长到 27 条，仍无问题解决信号。 |
| cancelled-followup-60s / 054 | working | unknown，`screen_native_conflict` | **INCOMPLETE**。仍为同一 pending 与普通活动的冲突。 |

五次命令均退出 2。脚本 `collection_complete=true`，pane close 成功、隔离 HOME 与空 scratch 已删除，且本 worker 只读核对路径确已不存在；采集完成不等于功能通过。脚本状态本来就保守保留 INCOMPLETE，本次功能结论来自上述状态投影与读屏，不是仅看脚本的总状态。

**人工记录（执行主控 #113 / 主控 #7）：** SHELL_READY 时为 -zsh，无更新提问；CODEX_IDLE 为空闲输入框。提交约 11 秒首次观察到 blocked、Working 和问题计数，**没有预先展开，直接输入 COLLAPSED**。随后 Shift+← 展开采集，Ctrl+] skip 后输入 CANCELLED；延后两次只读采集期间没有任何输入。实际折叠采集读数为 Working (20s) 与 `? 1 question · 16s`，与首次观察时间分别记录，不混为一条读数。`operator_collapsed_before_first_expand=true` 是操作者声明，不冒称自动按键日志；脚本没有代按键或自动答案。

读回命令：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --inputs evidence/2026-10-16-batch16/T-095/real-independent-inputs.json --report <新报告路径>
```

`independent-readback.json` 为 INCOMPLETE、`replay_status=PASS`、`regression_status=NO_GO`，退出 1。这里的 PASS 只表示只读入口、身份与读回过程有效；五项业务状态全部不满足原合同，且 `matches_original_projection=true`。界面边界由明确的假 Herdr 返回原始 get/read，运行实际 `scripts/agent-status`；不操作已关闭的 pane，不启动 Codex。仅把启动记录的 `native_store` 重定位到临时索引，worker / launch / UUID / cwd 和各阶段原生前缀字节不变。外层采集早于现场投影内部读取，不能还原未保存的内部每次屏幕；现场 stdout 本身另存在上述原件命令中。

## 96464ecf 实现的结构与本次缺口

标记组合、数值与位置规则、依据和局限见 [UI-STRUCTURE.md](UI-STRUCTURE.md)。本机包元数据确认版本 0.163.0；二进制包含异步提问渲染模块路径及控制文案，见 `ui-structure-source.json`。没有取得 Rust 渲染源码，不能将这些字符串当作完整控制流证明。

- 折叠：完整普通输入框与底栏之前，不依赖前面的 Working 行，紧邻 `• Queued follow-up inputs / ? N question(s) / ⇧← to answer`。N 为正数、单复数正确，两份读数一致，并与已绑定原生日志的 pending 问题总数一致。
- 展开：非空标题、唯一选中编号行和完整 `enter submit / ⌃] skip / ⇧→ main prompt` 控制条；标题前允许当前 Working、Queued follow-up 两种机械前缀。`option N/M` 可有可无；没有计数提示时要求可见列表从 1 开始连续、无重复。有计数提示时支持旧原件只显示选中项的布局，并核对选中值和可见编号。
- 继续支持旧原件的“无专属提示活动画面 + Herdr blocked + 本会话完整 pending 提问”组合；单独 blocked 或 Working 都不足以证明提问。
- 不匹配 T-095、A/B、问题意图或特定正文；不同计数、选项数、选中位置和标题均有入口级检查。未识别、截断、身份不符、计数冲突、两份读数不一致均 unknown；普通 working 的机械依据保持不变。

产品仍只有 `scripts/agent-status` 一个读取入口。不改 dispatch、launch-worker、工作台、门禁或全局配置；`native_questions.py` 本轮未变。没有第二份产品状态，没有针对测试的产品分支。

## 回落：已有后续事件，仍不能证明已解决

本轮初始三次投影读取 93,193 字节 / 20 条；延后两次读取 99,028 字节 / 27 条，完整归档也是 99,028 字节。回放按每次投影的实际截止点截取，未把后续事件补进先前阶段。新增第 21–27 条为：同一 turn 的 sleep item 完成、匹配 sleep call_id 的返回、token 记录、Reasoning item 与记录、再次调用 sleep 和 token 记录。时间为 13:20:07.980 至 13:20:09.773 UTC，位于即时采集结束后的 30 秒窗口内。没有新的 `task_started` 或 turn 完成事件。

这些是 **sleep 的后续执行事件**，不是问题 call_id `call_830e5d7699f9448383c13c45fa9d96bc` 的答案或 skip 解决事件；item 完成也不是整个 turn 完成。原生 pending 未被清除。60 秒截止点仍没有更多记录，最终于 13:20:42.379360 UTC 结束采集与清理。只能证明“不再显示面板”，不能证明“已解决”。详情和稀疏事件元数据见 `real-independent.archive.json`，原始记录保留在外置盘。

`skip-tail-investigation.json` 是前两次的历史调查：当时完整红、绿归档分别 40 / 20 条，均没有 skip 后事件。现在新增了上述第三次证据，不改写旧调查，也不把本轮后来取得的事实补称为早已取得。

红态中，问题未回答时模型已经有同 turn 后续输出和继续执行，故普通输出本身不能作为清除问题的事实。也没有证据证明 turn 完成或新 turn 就必定清除该 UI 请求。相关合成反例确认这些事件不会被本读取器当作解决；它们不构成 Codex 实际生命周期的证明。

`accepted:true` 始终只是接收回执。当前只接受关联同 call_id 的正式答案映射作为解决信号；该分支的合成验证不能替代真实 async skip。原生 pending 与普通 Working 冲突时继续 unknown，不靠计时、后续文字或新 turn 猜测清除。

## 检查：离线回归与真实验证分开

详见 `ui-repair-checks.json`；完整输出、失败夹具、已知坏源码与 mutant 均保留在 `ui-repair.archive.json` 指向的源目录。摘要没有替换原始输出。

| 检查 | 结果与边界 |
| --- | --- |
| 修前合同 | **FAIL，87 项中 8 项失败**，正好覆盖缺失的折叠 / 无计数展开结构，以及缺少来源冲突记录；源码为前一冻结候选。保留 `contract-before.json`，不是无关启动失败。 |
| 修后合同 | **PASS，89 项**；`contract-frozen.json`。新增了计数、选中位置、不同前缀、截断、引用、来源不符，以及普通后续输出 / turn 完成 / 新 turn 不擅自解决的反例。单复数反例将原生计数也设为 2 后另经真实入口核对通过。 |
| 两种旧真实面板回归 | 修前 unknown / unknown，修后 **等待 / 等待**；`panels-before.json` 与 `panels-frozen.json`。输入参与了修改，只算回归，不能独立证明真实绿态。 |
| 关闭合同回归 | `close-limit-after.json` 为等待 / 等待 / unknown，退出 1，**INCOMPLETE / NO_GO**；没有把关闭项排除后宣称整个合同通过。`--panels-only` 明确只核对前两项。 |
| 针对性坏实现 | 移除单复数校验时，在原生计数也匹配的输入上错判等待；`grammar-mutant.json` 被预期 unknown 的业务断言拒绝。坏副本与失败原件保留。另以移除 Working 上下文的折叠结构做反例，修前失败，最终合同已通过，防止提问状态依赖模型是否仍在计算。 |
| 当前 worker 普通 working | **PASS，仅普通工作状态**；`ordinary-frozen.json`，真实只读 get/read 与本 worker 的原生绑定，未增加探针根回合。 |
| 新探针离线接线 | **PASS，0 个真实模型根回合**；`independent-probe-wiring-final.json`。显式假 Herdr / Codex，核对单次提示、首次折叠声明、两次只读延后采集、身份与清理。 |
| 拒绝凭据作为原生日志 | **PASS，0 个真实模型根回合**；`independent-probe-reject-auth.json`。保留假凭据 canary 检查，错误日志头不发布绑定、不归档凭据。 |
| 独立真实绿态 | **已运行，NO_GO / INCOMPLETE**；五次 unknown，见本报告首节。它在实现冻结后首次生成并读回，本次没有照着它修改产品。 |
| 项目地图 | `independent-frozen-map-status.txt`：0 problems / 0 stale living docs。 |

可复现的零模型命令（报告路径必须新建）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --panels-only --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --report <新报告路径>
```

## 旧真实失败和人工介入保持原样

- 2026-10-17 T-094 的 working 来自主控 / 用户报告，本 worker 未取得当时原件。2026-10-18 红态、首轮绿态及本次独立探针的面板阶段均为 blocked。原 ticket 要求的“两种形态当前为 working”仍未复现，不能勾选。
- 首轮真实绿态运行的是 `504abc34ad2df27fa60b7cc998c499c122143d98`，三个现场投影仍是 unknown / unknown / unknown，原始 command 026 / 033 / 040 不变，见 `real-green.archive.json` 与 `green-readback-01.json`。
- 该轮 **COLLAPSED 前操作者曾先 Shift+← 展开核对，再 Shift+→ 折叠**；之后才采集，再展开和手动 Ctrl+] skip。不能将它记作从未展开的默认折叠态，也不推断这次操作与布局变化的因果关系。
- 先前 1,764 文件、5,498,933 字节的外置盘归档已读回核对 PASS，原件未删除，见 `native-offline-confirmed.archive.json`。

## 归档确认、冻结和审查

主控已执行的 UI 修复证据归档已逐文件名称与字节数读回核对：**PASS，717 文件、4,325,347 字节**，原件未删除。见 `ui-repair-confirmed.archive.json`。其中也保留前轮 34 文件的派生读回；先前执行前的 INCOMPLETE 清单继续保留为历史记录。

本次新增派生读回报告和夹具共 56 文件、617,372 字节，完整源保留在 `independent-readback.archive.json` 指向的 `/tmp` 目录。外置盘复制仍待主控在沙箱外运行以下零模型命令；仓库没有纳入 sqlite 或完整 fixture：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --manifest independent-readback.archive.json --apply
```

真实面板探针累计 **3 / 3 个根回合，剩余 0**；本轮 1 根、0 自动答案，只有一次提问与 sleep 工具调用，没有模型命令或文件工具调用。不再次启动、重试或 resume 真实探针。完整原始 argv 仍在 run.json；版本为 Codex 0.163.0、Herdr 0.9.4，模型请求 gpt-6.1-sol / xhigh / fast，不将请求配置当作供应商实际 tier 证明。

当前冻结只交付证据与审查材料。新的 [REVIEW-REQUEST.md](REVIEW-REQUEST.md) 针对本次冻结候选，由执行主控另开干净只读会话；实现者不自签独立审查，不将旧 89 项合同 PASS 或旧样本回归 PASS 用于接受本次独立失败。`T-095 FROZEN <sha>` 不表示整票 PASS。
