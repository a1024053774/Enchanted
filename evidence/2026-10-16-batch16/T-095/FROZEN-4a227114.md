# T-095-1：第 4 回合独立真实读回与冻结

**两形态独立真实验证 PASS；整体 INCOMPLETE。** 第 4 回合现场及原件回放中，默认折叠、展开都读出 `waiting_controller_answer` / “等待主控回答”，身份正确。skip 后即时、30 秒、60 秒均退出等待显示并保守报 unknown；没有解决事件，正常 working 回落仍未证明。按完整 Acceptance 仍为 NO_GO，不把局部通过上调为整票 PASS。未 submit、独立审查、验收或集成。

本次提交后冻结，完整 SHA 见交付末行。task T-095 / attempt a1 / worker s16-t095 / session `983db526-dfe8-473a-857b-b3f2af0af582` / launch `launch-4b1abba18e87460da9cbacec04905c78` / ready_rev 1；基线 `3c9016d0230223945f0e16543b230a047c2ad032`。产品版本固定为 `faa2b9b3b9ac6195012fc8ea88e6e6d73dee2bf4`，与第 4 回合一致；本次仅增补证据、报告与归档工具的清单选项，不改产品或合同测试。运行前报告逐字保存在 [CANDIDATE-faa2b9b3.md](CANDIDATE-faa2b9b3.md)，上一失败冻结见 [FROZEN-866166b6.md](FROZEN-866166b6.md)。原始 run、投影 JSON、退出码和失败均保留。

## 第 4 回合：独立真实验证

原件位于 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/green-anchor-independent-20261018T135446Z-2626001e`，225 文件、196,652 字节。版本、完整 argv、阶段及清理见 `run.json` 与 `records/launches.jsonl`；摘要见 [real-anchor-independent.archive.json](real-anchor-independent.archive.json)。Codex 0.163.0、Herdr 0.9.4；模型配置 gpt-6.1-sol / xhigh / 请求 fast，不据此证明供应商实际 tier。本次数据在产品冻结后生成，未据此修改解析器，属于新的独立边界证据。

- worker：`t095-probe-71d17066e9`；launch：`launch-t095-probe-32ee664e4b1b45249a3a9b8bcde50904`。
- pane：`wF:p6M`；terminal：`term_65e1dbd8342734a`；native session：`01a14f4b-a96a-7cb0-b480-a697871a66f7`。
- turn：`01a14f4b-dcdf-7f31-8f49-54c1c890049e`；问题 call：`call_a8a2609be80f4580a6f7b262d2758984`，原生日志第 14 条。

操作者记录来自执行主控 #118 / 主控 #9，采集脚本的 `operator_declaration` 与之相符：SHELL_READY 前台 -zsh、CODEX_IDLE 正常；提交后只观察默认折叠，**首次 COLLAPSED 前没有展开**；之后 Shift+← 展开并确认 EXPANDED，Ctrl+] skip 后确认 CANCELLED；延后 30 秒、60 秒采集期间没有人工输入。这与第 2 回合“先展开核对再折叠”的操作分别记录，不混用。

| 阶段（UTC） | 读屏命令 / 实际投影 | 原始 Herdr | agent-status 实际状态 / 退出码 | 机械依据 |
| --- | --- | --- | --- | --- |
| 折叠 13:55:52 | 020–025 / 026 | blocked | 等待主控回答 / 0 | visible、detection 第 3 行均有 `? 1 question · 18s`；两次 get 同为 blocked；无冲突。 |
| 展开 13:56:03 | 027–032 / 033 | blocked | 等待主控回答 / 0 | 两份读屏第 8 行均同条出现 `⌃] skip` 与 `⇧→ main prompt`；两次 get 同为 blocked；无冲突。 |
| skip 后即时 13:56:15 | 034–039 / 040 | working | unknown / 2 | 两份读屏无面板锚点，有普通活动结构；native pending，记录 `screen_native_conflict`。 |
| 后续 30 秒 13:56:46 | 041–046 / 047 | working | unknown / 2 | 同上；新增原生记录也没有解决事件。 |
| 后续 60 秒 13:57:16 | 048–053 / 054 | working | unknown / 2 | 同上；截止点仍不能证明已解决。 |

五个投影的 worker / launch / native UUID 均与启动记录一致。直接读取上述 stdout、exit 后，又以保存的 before / after / visible / detection 和各 native 字节截止点执行实际 `scripts/agent-status`，结果五项全与现场投影一致，身份、只读调用检查均通过。输入见 [real-anchor-independent-inputs.json](real-anchor-independent-inputs.json)，读回见 [anchor-live-readback.json](anchor-live-readback.json)。

读回命令不启动真实模型：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --inputs evidence/2026-10-16-batch16/T-095/real-anchor-independent-inputs.json --report <新报告路径>
```

本次进程退出 1；`replay_status=PASS`、`matches_original_projection=true`，完整回落合同 `regression_status=NO_GO`，总状态 INCOMPLETE。工具保留“关闭后应为 working”的原验收期望，没有把期望改成 unknown 来制造全绿。假 Herdr 只用于回放保存的原件，不是新的真实边界；产品内部逐次读屏未全部单独保存，现场投影 stdout 仍是原始依据。采集器自身 `status=INCOMPLETE`、`collection_complete=true`，也不代表功能整体通过。

## 已知限制：skip 后无法证明解决

前三个投影读取 89,498 字节 / 20 条原生记录；后两项读取 96,693 字节 / 27 条。首次 request 之后只有 `accepted:true` 的收件回执，没有对应问题的答案或跳过事件。新增第 21–27 条包括同 turn 的 sleep 返回、Extension / Reasoning item 完成、再次 sleep 和 token 记录；没有新 turn 或整个 turn 完成，不能据此解决问题。

因此只能证明“不再显示面板”，不能证明“已解决”。屏幕普通活动、Herdr working 与日志 pending 冲突时持续 unknown；生产中这类 skip 会失去可确认的普通 working 状态，直到取得可核对的解决事实。按主控 #115 保留保守行为，不把 accepted、普通后续输出或 item 完成当作解决。真实普通回落仍 INCOMPLETE；新增真实探针预算已用尽。

## 当前规则

完整合同见 [UI-STRUCTURE.md](UI-STRUCTURE.md)。等待正判只使用屏幕锚点与 Herdr blocked，原生会话身份、记录完整性和读取前后稳定性仍先核对；原生日志不再作为额外的等待正判条件，也不比较问题数量。

- 折叠：最后 12 个非空可见行内，忽略行首空白，存在 `? N question` 或 `? N questions` 的正整数计数前缀。前缀后任何内容均忽略，包括年龄后缀；不校验标题、队列行、回答快捷键、输入框或底栏。
- 展开：同一可见行同时出现 `⌃] skip` 和 `⇧→ main prompt`。上方残留输出、标题、enter、选项列表和后续无关文本均不参与判定，两标记不能分处两行。
- visible 与 detection 都存在任一锚点，且读取前后 Herdr `agent_status=blocked`，才输出 `waiting_controller_answer` / “等待主控回答”，附 worker / launch / pane / native session。两次的形态、计数和无关内容可以不同。
- 只有锚点、只有 blocked，或两份读屏对锚点存在与否不一致，均 unknown；`conflicts` 记录各屏幕是否有锚点、Herdr 原值和保守决定。blocked 配空屏也记录缺少屏幕印证。

原生日志仍只读启动记录绑定的 native UUID，不按文件名猜；身份或原生记录不可核对、不完整、读取中状态改变时仍 unknown。两边均无等待信号时，普通 working / idle 使用原有活动行、输入框、底栏和原生无 pending 的依据；原生 pending 时仍 unknown。`accepted:true` 不解决问题，普通同 turn 输出、新 turn 或 item 完成都不猜作答案。

旧的标题 / 整屏 / 选择编号校验，以及“原生 pending + blocked + 普通活动画面就判等待”的路径已删除。唯一入口仍是 `scripts/agent-status`；未改 dispatch、launcher、Herdr、工作台、gates、地图或全局配置，原生读取模块也未改。没有新增产品状态存储或自动回答。

## 三份原件回归

输入参与了修改，以下只算离线回归，不能替代新独立真实验证。索引只在临时夹具中重建，原始 worker / launch / native UUID / cwd 保留，原生日志按各投影字节截止点复制；没有补入合成答案。

| 原始 run | 折叠 / 展开 | skip 后 | 范围与判断 |
| --- | --- | --- | --- |
| red-20261018T110936Z-f4d263d1 | unknown / 等待 | unknown | 折叠屏幕只有 Working、没有锚点；按新规则是 blocked 单边成立，必须 unknown 并留冲突。展开有同条双标记。原 run 未保存 launches，夹具从归档 start 回复及已核对的 native header 重建绑定；不补称当时已有该启动记录。 |
| green-20261018T125458Z-76e72ee1 | 等待 / 等待 | unknown | 两形态都有锚点且 blocked；关闭无解决事件，保守 unknown。 |
| green-independent-20261018T131803Z-9e55a235 | 等待 / 等待 | 即时、30 秒、60 秒均 unknown | 年龄后缀与前置输出不再影响锚点识别；延后日志仅有 sleep 返回和继续执行，没有问题解决信号。 |

这不是把 red 折叠强判成等待。主控明确要求两来源印证，缺少锚点时不能用原生 pending 补足。2026-10-17 T-094 的 working 仍只有执行主控 / 用户报告；2026-10-18 四次真实运行的面板阶段均为 blocked，原 ticket 的 working 红态仍未复现。第 1 次红态的 blocked 与早先报告的 working 不一致，如实保留，不能上调。

实际历史投影保持原样：首轮 green 和 green-independent 的现场状态分别仍是三个 unknown、五个 unknown。新表是当前代码对原件的回归结果，不能改写原版本的失败结论。

## 检查与保留的失败

详情见 `anchor-checks.json`，完整输出与夹具见 `anchor-repair.archive.json` 的源目录。所有报告均新建；旧失败没有覆盖。

| 范围 | 结果 |
| --- | --- |
| 新合同下的修前原件回放 | **FAIL，11 项中 3 项失败**：red 无锚点折叠被旧路径错判等待；green-independent 两形态仍 unknown。源码固定为上一冻结 866166b6；这是新合同反例，不补称原始 working 红态。 |
| 修后原件回归 | **PASS，11 项**；最终串行报告也覆盖全部 11 项，矩阵如上。 |
| 最终入口合同 | **PASS，85 项，串行**，`contract-serial.json`。覆盖双来源组合、任意后缀、无标题 / 无选项 / 无底栏、残留输出、不同计数、同条控制标记、历史计数不在底部、读取与身份异常、普通 working 和保守回落。 |
| 单边放行坏副本 | **被拒绝**。把锚点 AND blocked 改成 OR，只有锚点和只有 blocked 两例都错判等待，被业务状态断言拒绝；`one-sided-mutant.json` 保留代码和原件。 |
| 空屏冲突记录 | 修前已返回 unknown 但缺少冲突，专项 FAIL 保留；修后补齐，专项与最终合同 PASS。没有改普通 working 的不可读保护。 |
| 第 4 回合脚本接线与凭据隔离 | **PASS，0 个真实探针根回合**。显式假 Herdr / Codex，核对总预算 4、单次提示、无代按键、延后只读采集、关闭自建 pane、删除隔离 HOME，及假凭据 canary 不入归档。 |
| 第 4 回合独立真实验证 | **两形态 PASS**；关闭后即时、30 秒、60 秒 unknown，正常 working 回落 **INCOMPLETE**，完整合同 **NO_GO**。现场和本次离线读回一致。 |
| 项目地图 | `anchor-live-map-status.txt`：0 problems / 0 stale living docs。 |

## 已知限制：3 秒 Herdr 读取期限

并发末轮保留两份 **FAIL，根因未确定**：`contract-final.json` 的 `working-command-context`（2026-10-18T13:41:32.542819Z），与 `archives-final.json` 的 `archive-red-expanded`（13:41:32.547032Z）。两项均在第一个假 Herdr get 超过原有 3 秒期限，退出 2、state unknown、reason `herdr_timeout`，尚未取得 raw_state。完整失败报告和夹具位于 `offline-native-anchor-repair-20261018T134759Z`；没有覆盖或删掉。接近同时失败只是时序事实，不能据此断定 CPU、调度或并发就是根因，也不能声称真实生产 Herdr 当时发生了超时。

生产影响：`scripts/agent-status:183` 的默认期限是**每次** Herdr get / read 3 秒；调用超时由第 33–40 行转为 unknown，进程退出 2。Herdr 繁忙或读取延迟超过 3 秒时，即便真实面板正在待答，本次也只能得到 unknown，可能暂时遮住等待状态；调用方须保留诊断并在之后再次读取，不能把 unknown 当作 working、idle 或已解决。没有自动重试、没有调高期限、没有修改 Herdr server。随后同期限串行 85 项 PASS 只说明那一次完成，不证明超时根因已解决，也不证明负载下可靠性改善。

零模型复现（报告路径必须新建）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --archives-only --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新报告路径>
```

## 归档与冻结审查

累计真实探针 **4 / 4 根回合，剩余 0，自动答案 0**。第 4 回合由主控在沙箱外执行，本 worker 只读回。原生工具调用为一次 request_user_input_async 和 sleep；未执行命令或改文件。`run.json` 记录 pane 已关闭、隔离 HOME 已删除、夹具为空并移除 scratch；本次只读核对 HOME 和 fixture 路径均不存在，不再操作已关闭 pane。原始 run 已直接保存在外置盘。

主控已复制 `anchor-repair.archive.json`：**PASS，732 文件、6,886,506 字节**；归档到 `offline-native-anchor-repair-20261018T134759Z`。本次逐项核对全部相对路径大小、总文件数和总字节数，与原清单及回执相符；见 [anchor-repair-confirmed.archive.json](anchor-repair-confirmed.archive.json)。回执 `originals_deleted=false`，源及两次超时失败均保留。

本次新增派生读回原件共 **57 文件、602,404 字节**，暂存 `/tmp/t095-offline-native-evidence-tsy3snus`，待主控沙箱外复制；原生前缀与临时 SQLite 不入仓库。清单见 [anchor-live-readback.archive.json](anchor-live-readback.archive.json)，只复制、不删除，不产生模型回合。外置盘未挂载、源变化或目标存在均停止。命令：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --manifest anchor-live-readback.archive.json --apply
```

本次冻结请求见 [REVIEW-REQUEST.md](REVIEW-REQUEST.md)，由主控另开干净只读 reviewer 会话，传入交付末行完整 SHA。未自行启动 reviewer、submit、验收或集成；不追加探针。冻结表示候选和证据可审，不表示整票 PASS。
