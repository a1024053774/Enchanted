# T-095-1：UI 结构修复候选与独立验证交接

**INCOMPLETE。** 两种旧面板的离线回归已通过；新的独立真实绿态尚未运行。skip 后没有可关联的原生解决事件，因此关闭阶段仍只能证明“不再显示面板”，不能证明“已解决”，继续 unknown 并保留冲突。未 submit、独立审查、验收或集成。

本候选按主控 #109 / 主控 #6 修复、提交并冻结，完整提交号见交付末行。task T-095 / attempt a1 / session `983db526-dfe8-473a-857b-b3f2af0af582` / launch `launch-4b1abba18e87460da9cbacec04905c78` / ready_rev 1；基线 `3c9016d0230223945f0e16543b230a047c2ad032`。前一冻结 `afe1602920fe43b64232e6b7610e49a2f69cf46c` 的报告逐字保存在 [FROZEN-afe160292.md](FROZEN-afe160292.md)，其真实 INCOMPLETE / NO_GO 结果不改写、不上调。

## 修复了哪些机械结构

标记组合、数值与位置规则、依据和局限见 [UI-STRUCTURE.md](UI-STRUCTURE.md)。本机包元数据确认版本 0.163.0；二进制包含异步提问渲染模块路径及控制文案，见 `ui-structure-source.json`。没有取得 Rust 渲染源码，不能将这些字符串当作完整控制流证明。

- 折叠：完整普通输入框与底栏之前，不依赖前面的 Working 行，紧邻 `• Queued follow-up inputs / ? N question(s) / ⇧← to answer`。N 为正数、单复数正确，两份读数一致，并与已绑定原生日志的 pending 问题总数一致。
- 展开：非空标题、唯一选中编号行和完整 `enter submit / ⌃] skip / ⇧→ main prompt` 控制条；标题前允许当前 Working、Queued follow-up 两种机械前缀。`option N/M` 可有可无；没有计数提示时要求可见列表从 1 开始连续、无重复。有计数提示时支持旧原件只显示选中项的布局，并核对选中值和可见编号。
- 继续支持旧原件的“无专属提示活动画面 + Herdr blocked + 本会话完整 pending 提问”组合；单独 blocked 或 Working 都不足以证明提问。
- 不匹配 T-095、A/B、问题意图或特定正文；不同计数、选项数、选中位置和标题均有入口级检查。未识别、截断、身份不符、计数冲突、两份读数不一致均 unknown；普通 working 的机械依据保持不变。

产品仍只有 `scripts/agent-status` 一个读取入口。不改 dispatch、launch-worker、工作台、门禁或全局配置；`native_questions.py` 本轮未变。没有第二份产品状态，没有针对测试的产品分支。

## 回落：没有找到可证明已解决的后续事件

`skip-tail-investigation.json` 核对了原生 UUID 已绑定的完整红、绿归档，截止各自 pane 关闭。红态 40 条、绿态 20 条；最后原生时间分别为 11:12:37.212 UTC、12:56:04.930 UTC，均早于展开阶段结束，因此也早于操作者之后的 skip。没有 skip 后的同 turn 输出、新 turn 或完成事件可读回。原隔离 HOME 已删除，无法补查未保留的尾部；未扫描别的 worker 的记录。

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
| 新的独立真实绿态 | **NOT_RUN**；只有主控在本候选冻结后运行的新会话才计入第二层验证。 |
| 项目地图 | `ui-repair-map-status.txt`：0 problems / 0 stale living docs。 |

可复现的零模型命令（报告路径必须新建）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --panels-only --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --report <新报告路径>
```

## 旧真实失败和人工介入保持原样

- 2026-10-17 T-094 的 working 来自主控 / 用户报告，本 worker 未取得当时原件。2026-10-18 受控红态和首轮绿态的两种面板阶段均为 blocked。原 ticket 要求的“两种形态当前为 working”仍未复现，不能勾选。
- 首轮真实绿态运行的是 `504abc34ad2df27fa60b7cc998c499c122143d98`，三个现场投影仍是 unknown / unknown / unknown，原始 command 026 / 033 / 040 不变，见 `real-green.archive.json` 与 `green-readback-01.json`。
- 该轮 **COLLAPSED 前操作者曾先 Shift+← 展开核对，再 Shift+→ 折叠**；之后才采集，再展开和手动 Ctrl+] skip。不能将它记作从未展开的默认折叠态，也不推断这次操作与布局变化的因果关系。
- 先前 1,764 文件、5,498,933 字节的外置盘归档已读回核对 PASS，原件未删除，见 `native-offline-confirmed.archive.json`。

## 交给主控的新独立探针

主控 #109 追加授权 **1 个根回合**。先前已用 2 个，本次未启动新探针；本次运行后累计最多 3 个。不重试、不 resume、不自动答题，不等待并行名额。由主控在本 worktree 的沙箱外 Herdr 终端依次运行：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --manifest ui-repair.archive.json --apply
python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py --approve-one-root-turn --phase green-independent
```

第一条只归档，不调用模型；717 文件、4,325,347 字节，包含本次检查、失败夹具、坏副本，以及前轮尚待复制的 34 文件派生读回。源与异常现场全部保留。外置盘未挂载、源变化或目标存在均停止，不覆盖。当前清单仍为 INCOMPLETE，待主控复制后读回确认。

第二条默认不带批准参数只打印计划，见 `independent-probe-plan.json`。完整启动参数与模型保持 Codex 0.163.0 / gpt-6.1-sol / xhigh / 请求 fast；只复制 auth.json 到隔离 HOME，不写全局配置，不让模型运行命令或改文件。

操作仍为 SHELL_READY、CODEX_IDLE、COLLAPSED、EXPANDED、CANCELLED。**首次 COLLAPSED 之前只观察默认折叠，不能先展开或先展开再折叠；若已经展开则终止，不重投。** 收到 CAPTURED collapsed 后再 Shift+← 展开，收到 CAPTURED expanded 后仅按界面提供的 Ctrl+] skip。脚本在即时关闭阶段采集完成后，再于 30 秒、60 秒截止点只读采集并投影，以保留可能的后续事件；不发送新提示或答案。总期限仍为 240 秒；最后只关闭自建 pane、归档绑定原生文件、删除隔离 HOME 与空 scratch。

采集完成仍是 INCOMPLETE，需按原件判断两形态、身份和已知回落限制。独立审查在新探针读回后另发；`REVIEW-REQUEST.md` 明确标为旧冻结候选的历史请求，不能给当前修复候选背书。`T-095 READY <sha>` 仅交付冻结代码与脚本，不表示整票 PASS。
