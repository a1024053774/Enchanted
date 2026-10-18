# T-095 独立探针之后的冻结审查请求

**历史请求，固定对象为 `866166b6b7384f478eea4956741a331e6d2bc622`。** 主控 #115 已更改为锚点与 blocked 的识别合同，并指定第 4 个独立探针；本页以下保留上一次冻结的请求，不用于启动当前锚点候选的审查。当前状态以 RESULTS.md 为准；新探针读回后再针对新的冻结版本发请求。

**状态：INCOMPLETE / NO_GO；请求独立审查，不请求直接接受。** 由执行主控另开干净的只读 reviewer 会话。实现者没有自签审查，本文件不是审查结论。

## 冻结对象

- 仓库：`/Users/luckye/Documents/Code/a2a-wt-t095`；task T-095 / attempt a1 / worker s16-t095 / ready_rev 1。
- 候选是本文件所在的冻结提交。执行主控必须把本次 `T-095 FROZEN <sha>` 的完整 SHA 传入审查任务；不能只传可移动分支名。未固定 SHA 时返回 INCOMPLETE。
- 产品代码：`96464ecf49523e6e306c3c03fea5ad9f2897951b`，与独立真实探针一致。本次只增补证据、读回 / 归档工具和报告；`scripts/agent-status`、`scripts/native_questions.py`、原合同测试、dispatch、launcher 与 gates 均未改变。
- 比较基线：`3c9016d0230223945f0e16543b230a047c2ad032`。重点审查状态读取器、原生身份绑定、结构判定、异常转 unknown 的归属，以及证据是否支持 Acceptance。
- 只读，不修复、不 submit 或集成，不改 ticket、Herdr 或配置，不操作已关闭 pane。真实面板探针已用 **3 / 3 根回合，剩余 0**；不启动新探针、不重试、不 resume、不自动答题。审查会话本身由主控另行派发，本请求不代为启动。

## 先重建标准，再看实现者报告

以 `.project-map/tickets/T-095-*.md`、任务卡与已确认的机械事实约束为准。两个 UI 形态均应识别为 `waiting_controller_answer` / “等待主控回答”，带 worker / launch；普通 working 也需机械依据。身份不符、不可读、事件不完整与来源冲突时 unknown，冲突必须记录。不能把 `accepted:true` 当作问题已解决，不能按自然语言猜答案或 skip。

原始红态要求“两种形态当前为 working”，但 2026-10-18 三次受控运行的面板阶段都是 blocked。2026-10-17 T-094 的 working 仍只来自执行主控 / 用户报告，本 worker 未取得其原件。这个缺口不能用别的阶段补证，也不能自行修改验收条件。

`RESULTS.md`、89 项旧合同 PASS 和实现者新增测试都不是独立 oracle。新的真实数据在 96464ecf 冻结后生成，本次没有据此修改产品，因此其失败是对该候选的独立反例。

## 首先核对的原件

目录：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/green-independent-20261018T131803Z-9e55a235`。

| 范围 | 原件位置 |
| --- | --- |
| 版本、完整 argv、人工确认与清理 | `run.json`、`version.stdout`、`records/launches.jsonl`；代码版本必须为 96464ecf。 |
| 默认折叠 | command 020–025 的采集，command 026 的实际 agent-status stdout / exit。 |
| 展开 | command 027–032 的采集，command 033 的实际投影。 |
| skip 后即时 / 30 秒 / 60 秒 | command 034–039 / 041–046 / 048–053 的采集；实际投影为 040 / 047 / 054。 |
| 原生会话 | `native-bound.jsonl`；UUID `01a14f2a-0834-7453-a50a-bc87fd434e83`。前三项投影按 93,193 字节 / 20 条，后两项按 99,028 字节 / 27 条读取。 |

操作者记录来自执行主控 #113 / 主控 #7：这次首次 COLLAPSED 前没有展开；只观察约 11 秒时的 blocked、Working 和问题计数后确认。再 Shift+← 展开、Ctrl+] skip；延后两次采集期间没有输入。不要与前一轮“先展开核对再折叠”的人工介入混合，也不推断两次操作与 UI 差异的因果关系。

## 已知结果，请独立复核

五个现场投影均 unknown，绑定的 worker / launch / native UUID 正确。折叠原因 `incomplete_folded_question_panel`，展开原因 `incomplete_question_panel`；后面三项为 `screen_native_conflict`。前两项是明确未满足的业务行为；后面三项满足保守 unknown 的安全约束，但正常回落仍未证明。

- 折叠原件出现 `? 1 question · 16s`，当前 `scripts/agent-status:26` 的全行匹配未覆盖年龄后缀。
- 展开时 Working / Queued follow-up 前有 `  • B` 可见片段。`question_frame` 只剥离开头的机械前缀，之后标题区校验失败，重点看 `scripts/agent-status:143` 与 `scripts/agent-status:150`。
- skip 后新增的是同 turn 的 sleep 返回、Reasoning item、再次 sleep 与 token 记录；没有问题 call_id 的解决、新 turn 或整个 turn 完成事件。item 完成不能冒充问题解决，普通后续输出也不能用来清除 pending。

可用当前报告工具复核保存的输入，命令不启动真实模型：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --inputs evidence/2026-10-16-batch16/T-095/real-independent-inputs.json --report <新的临时报告路径>
```

当前预期退出 1，五项 unknown；身份 / 只读入口检查通过，业务合同 NO_GO，总状态 INCOMPLETE。测试边界明确是假 Herdr 返回原始采集，执行真实 `scripts/agent-status`；它只复核保存的事实，不冒充新的真实运行。内部逐次读屏没有全部保存，故现场原始投影 stdout 仍是必读依据。

## 审查重点与输出

按 [behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 审查单个冻结候选，将结构风险一起审查；不要另起重复审查。能力范围为状态编排、异步事件、身份范围、CLI 交互与原生文件解码；模型意图理解、检索和生产发布为 N/A。

核对入口是否唯一、会话索引是否只按启动绑定的 native UUID 读取、无匹配时是否 unknown、UI / 原生冲突是否保守留证，以及 UI 规则是否过度依赖样本的显示边界。按 Deep modules 判断原生模块是否隐藏必要复杂性，检查异常处理、兼容 / fallback 路径是否掩盖未实现的行为。

独立结论需要确切文件与行号、可达反例、证据层级、已知坏实现是否被检出和局限。对于重复出现的显示变体漏识别，说明什么入口级或元变换检查能检出，并指出放在哪里；不能仅建议再加一条口头规则。候选变化时停止并返回 INCOMPLETE，不在审查中修复。

旧合同、mutant 与失败夹具已在外置盘 `offline-native-ui-repair-20261018T131124Z`，717 文件 / 4,325,347 字节已读回核对。当前派生读回的原件与待复制路径见 `independent-readback.archive.json`；原始真实 run 已归档。不要以归档成功、脚本采集完成、89 项合同 PASS 或安全 unknown 代替两形态业务正判。若作接受或发布判断，本候选已有独立真实业务失败，不能判整票 PASS。
