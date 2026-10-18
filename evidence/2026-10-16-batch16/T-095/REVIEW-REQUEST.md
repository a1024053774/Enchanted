# T-095 冻结候选审查请求

**历史请求，固定对象为 `afe1602920fe43b64232e6b7610e49a2f69cf46c`。** 主控 #109 已要求修复 UI 解析并追加一次独立真实验证；本页以下保留该旧失败候选的请求内容，不能用于启动对当前修复候选的审查。当前状态以 RESULTS.md 为准，待新探针读回后再发新的冻结审查请求。

**状态：INCOMPLETE；请求独立审查，不请求直接验收通过。** 由执行主控另开干净的只读 reviewer 会话，固定完整候选 SHA 后交给它；实现者不自行派发或自签审查。本文件不是已完成的审查报告。

## 固定对象与范围

- 仓库：`/Users/luckye/Documents/Code/a2a-wt-t095`；task T-095 / attempt a1 / worker s16-t095 / ready_rev 1。
- 冻结候选：**本文件所在提交**，完整 SHA 由执行主控从本次交付末行 `T-095 FROZEN <sha>` 传入审查任务，不能只传可移动分支名。缺少该 SHA 时返回 INCOMPLETE。
- 产品代码版本：`504abc34ad2df27fa60b7cc998c499c122143d98`，也是绿态真实运行版本；本次冻结只增补证据、回放与归档工具，不修复产品逻辑。
- 比较基线：`3c9016d0230223945f0e16543b230a047c2ad032`。重点为 `scripts/agent-status`、`scripts/native_questions.py`、`scripts/test_agent_status.py` 及本目录的小输入、证据与脚本。
- 只读；不得修复、submit、集成、改 ticket、改 Herdr 或全局配置。不要运行真实探针、resume 或回答面板。红绿根回合共 2 / 2，剩余 0；本请求不增加模型预算。

## 独立判断依据

先按 `.project-map/tickets/T-095-*.md`、任务卡范围和主控已确认的事实源约束重建标准，再看原件；不要把实现者增加的测试或 RESULTS 当作独立 oracle。

1. 两种面板都应输出 `waiting_controller_answer` / “等待主控回答”，带正确 worker / launch 身份。未知、身份不符、缺事件和来源冲突必须 unknown，普通 working 也须机械依据。
2. 原始红态要求“两种形态当前为 working”，但 2026-10-18 两次探针的面板阶段都是 blocked；2026-10-17 T-094 的 working 仅有主控 / 用户报告。本候选不得声称已补齐原始 working 红态，也不得修改验收条件。
3. 真实绿态本身是否满足两种面板与关闭回落；旧红态回放 PASS 和合成答案分支不能替代它。
4. 仅按启动记录原生 UUID 查询自己的会话；禁止按文件名或问题自然语言猜测。不能把 `accepted:true` 当作已回答，不能用普通 UserMessage 文本推断 skip 或答案；来源冲突须记录。
5. 检查状态入口唯一、只读、副作用边界、异常转 unknown 的归属，以及是否出现掩盖根因的 fallback / 兼容路径。按 Deep modules 原则审查 `native_questions.py` 的接口是否隐藏了必要复杂性；不要把表面上的函数拆分当作设计证明。

## 可直接核对的原件

| 来源 | 路径与内容 |
| --- | --- |
| 红态 | `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/red-20261018T110936Z-f4d263d1`；同目录 `run.json` 与原始命令输出。 |
| 绿态 | `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/green-20261018T125458Z-76e72ee1`；原始投影 command 026 / 033 / 040、采集 command 020–025 / 027–032 / 034–039、`records/launches.jsonl`、`native-bound.jsonl`。 |
| 先前检查与坏副本 | `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/offline-native-20261018T125045Z`；`reports/` 完整输出与 `fixtures/` 冻结夹具，receipt 已读回核对。 |
| 当前回放摘要 | `green-readback-01.json`；小输入 `real-green-inputs.json`；派生夹具原件与待复制位置见 `green-replay.archive.json`。 |

操作者来源是执行主控 #106 / 主控 #5：**COLLAPSED 采集前曾先 Shift+← 展开核对问题，再 Shift+→ 折叠**；其后再次展开采集，最后 Ctrl+] skip。不要将本次采样记作从未展开的默认折叠态，不推断该操作与布局变化的因果关系。

## 已知未满足项与可证伪检查

当前现场投影与原件回放均为 unknown / unknown / unknown。折叠原因 `unverified_screen_tail`，展开原因 `composer_missing`，关闭原因 `screen_native_conflict`；不是导入、索引或身份错误。请独立复核，而不是仅据这段描述下结论。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --report <新的临时报告路径>
```

当前预期退出 1：回放一致性 PASS，业务合同 NO_GO，总状态 INCOMPLETE。该回放走真实命令入口，Herdr 边界由显式假进程返回原件；它不能证明新的真实界面运行，也无法还原未保存的现场内部逐次读数。

如需核对旧合同或针对性坏实现，使用 `scripts/test_agent_status.py --report <新路径>`、`--panel-contract` 或 `--full-native-red`。测试不应因本次业务失败而删改、跳过或把 unknown 当作正判通过。旧 mutant 的完整输出、代码与夹具已归档；特别核对“回执即解决”“泛 blocked 即提问”等坏实现确被业务断言拒绝。

## 审查输出

按 [behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 审查这个冻结候选；将结构异常边界等标记作为上下文，避免另起重复审查。需要确切文件 / 行号、可达反例、证据层级、已知坏实现是否被检出和局限；未取得的真实解决事件只能记 INCOMPLETE。审查期间候选发生变化即停止并返回 INCOMPLETE。

能力范围包括编排状态、异步事件、身份范围与 CLI 交互；模型意图理解、检索、生产发布为 N/A，不作收益推断。独立 reviewer 的结论和主控后续门禁结果另存，不能以本文件或实现者回放替代。若作发布判断，必须将已复现的业务失败计入 NO_GO，不得因安全 unknown 而判整票 PASS。
