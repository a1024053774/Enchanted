# T-095-1 候选交付（2026-10-18）

**INCOMPLETE。** 本候选实现了本次真实展开布局的“等待主控回答”，以及可靠读数所需的身份核对修正；折叠形态仍为 unknown。没有运行真实绿态，也没有完成独立审查或集成。本报告与源代码绑定所在候选提交，task T-095 / attempt a1 / session `983db526-dfe8-473a-857b-b3f2af0af582` / launch `launch-4b1abba18e87460da9cbacec04905c78` / ready_rev 1；基线 `3c9016d0230223945f0e16543b230a047c2ad032`。

## 原件结论

原始目录与文件数/字节数见 `real-red.archive.json`，详细读回见 `REAL-READBACK.md`。原件未修改，仓库只保存被测试读取的小输入与文本记录。

- 折叠：Herdr 两次都为 **blocked**；visible / detection / ANSI 只有 Working、普通输入框与底栏，没有提问专属控制条。**不能据此正判等待主控回答，本候选输出 unknown**。
- 展开：Herdr 两次仍为 **blocked**；选择行加 `enter submit`、`⌃] skip`、`option N/M`、`⇧→ main prompt` 形成专属结构。本候选输出 `waiting_controller_answer` / “等待主控回答”，附 worker / launch / pane 身份，不匹配问题正文。
- 主控手动 Ctrl+] skip 后：Herdr 为 working，普通活动画面恢复；原件回放输出 working，不沿用上一条等待状态。
- **原 ticket 要求的“两种形态当前读成 working”没有复现，不能勾选。** 本轮 raw blocked 不能改写成 working，也不能用退出阶段的 working 补证。隔离配置的观察不否定原始 T-094 记录；两次不同的原因尚未确定。
- 原件只有 1 个根回合，0 个自动答案，没有命令/文件工具调用。用户当场允许本次临时 4 个并行的转述记在 `real-red-readback.json`，不扩展到新运行。

## 实现与边界

唯一状态入口为 `scripts/agent-status --root <保存 records 的 checkout> --launch <id>`。只读启动记录和明确 pane 的 Herdr get/read；不改 dispatch、工作台、门禁、地图或全局配置，不保存第二份产品状态，不发送答案或按键。

读前读后核对 worker / pane / terminal / cwd 与状态代次，重读启动记录，拒绝旧 launch 被后续同 pane 启动取代。原件证明 `revision` 会随同一进程的显示变化，现只作观察字段。隔离运行可能没有 Herdr 原生身份字段：有绑定或可观测原生身份时严格核对；两端都没有且启动时也未绑定时，仅报告 `native_binding=launch_terminal`，不谎称核对了原生身份，不替代门禁身份。

提问识别要求两份当前读数都有完整控制条、标题区域和一致的选择位置。截断、混合布局、身份不符、读数变化或 `blocked + Working` 均保持 unknown。普通 working 仍需两份完整活动结构与 Herdr working 值共同支持。

## 检查

| 范围 | 结果与复现 |
| --- | --- |
| 合同与真实原件回放 | **PASS，46 项**。`PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新路径>`；`panel-and-contract-after-02.json`。其中折叠的预期是安全 unknown，不是本票两种形态都正判的通过证明。 |
| 严格两形态正判合同 | **未满足**。`PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --panel-contract --report <新路径>`；`panel-contract-after-01.json` 仅 `real-collapsed` 失败。旧候选两形态都失败见 `panel-contract-before-01.json`。 |
| 针对性反事实 | **成功拒绝坏实现**。删去提问正判分支，展开原件变 unknown，见 `question-detector-mutant-01.json`；将 generic blocked + activity 错判提问也被拒绝，见 `generic-blocked-mutant-01.json`。冻结坏副本保留在报告的 fixture 路径。 |
| 当前 worker 普通活动真实入口 | **PASS，仅普通活动**，见 `implementation-live-ordinary.json`。不新增模型回合，不是提问绿态。 |
| 绿态脚本接线 | **PASS，仅显式假 Herdr/Codex 的离线接线，0 个真实模型回合**。`PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/check-green-probe-wiring.py <新报告路径>`；`green-probe-wiring-02.json` 依次记录 unknown / waiting_controller_answer / working，并核对身份、单次提示、无按键和清理。首轮缺少 sys 导入的失败保留在 `green-probe-wiring-01.json`，已修复。 |
| 清理 | **PASS**。`/tmp/t095-panel-pg9mo4yh` 只剩空目录，已 rmdir，未删文件；见 `red-temp-cleanup.json`。失败合同夹具与坏副本仍保留在各报告所指 `/tmp`，尚未搬到外置盘。 |
| 项目地图 | `implementation-map-status.txt`，0 problems / 0 stale living docs。 |

## 交给主控的未决点

当前已确认的方向是“只认面板 UI 结构组合”。本次折叠原件没有这类专属结构；Herdr blocked 本身覆盖多种 Action Required，因此仅靠它不能补出问题类型。若要满足折叠形态也正判，需要主控确认增加可绑定、覆盖问题提出和解决的结构化事实来源，或取得折叠时专属 UI 事实。本候选不自行扩展事实源或改变验收条件。

真实绿态仍由主控运行，不自动触发；预算最多剩 1 个根回合。绿态命令如下，但本候选尚不能让折叠项通过，建议先裁定上述事实源，再使用最后一根预算：

```sh
python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py --approve-one-root-turn --phase green
```

更新后的脚本把探针启动记录放在该 run 自己的 records 内，采集两种布局和手动 skip 后调用实际 `agent-status`，把 JSON 及退出码保存进同一个外置盘 run。完整启动 argv、手动操作、原始读数、状态投影和隔离 HOME 清理均可核对；不会替操作者按键，也不自动回答。新的 `T-095 READY <sha>` 只交付此候选，不表示本票已经 PASS。
