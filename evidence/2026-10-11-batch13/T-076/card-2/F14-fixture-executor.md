# T-076-2 F14：旧coop卡的executor准备（待批准）

状态：**INCOMPLETE／待F14批准**。原`outside-legacy-green-01/`不修改；本轮只读诊断，无新后台/模型调用。

## 分类与依据

本次W07没有到达来源守卫反事实。旧卡由`acceptance/test_coop_e2e.py:ManagedDeliveryCLI.create()`第148行设置`executor.model="fixture"`；`Panes.createPane()`要求模型为`gpt-6-astra`或`gpt-6.1-sol`且effort为xhigh。真实reviewer启动边界因此拒绝该卡。

数据库保存的事实表明reviewer错误处理已经执行：

- task=`check-b5f3a2c772bf45d28eeeef8b01494d2b`，attempt=`fb05226a-5b0f-4d00-a9a4-e2e07af8aab7`；候选=`cf1976b5a16981348c6d3fd33f6f45aa2aea5221`。
- 机械verification为passed，task为paused，review为unknown。
- event 93=`review_lifecycle_failed`，phase=create，error=`Error: worker_executor_mismatch`。
- event 94=`issue_issue`，blocking=true，保存审查ID与创建故障；issue表中同一条记录存在。
- event 95=`rejected`，verify返回gate_failure并保留原错误。

`test_quality_widen_e2e.py:reviewer_create_red`的已批准契约同时要求`not result['ok']`、paused、review unknown和issue；不是要求创建失败后verify仍返回成功。`requestReview()`先记录生命周期失败，再把原错误抛回。上述现场满足该契约，因此本次不改产品、不新增产品“修复红态”。机械结果与审查创建结果已分别保存，命令失败未把机械事实抹掉。

F10在同一来源变异体上命中MANUAL-CLAIM-SOURCE，前置通过。W07实际为测试准备失败，不能计为其预写红态；候选和全部后续回归未运行。

## F14准确变更请求

| 文件／helper／位置 | 原准备 | 拟准备 | 不变 |
| --- | --- | --- | --- |
| `acceptance/test_coop_e2e.py`，`ManagedDeliveryCLI.create()`，第148行card.executor.model | `"fixture"` | `"gpt-6.1-sol"` | cli=Codex、effort=xhigh、所有其他卡字段、oracle、claim/dispatch路径、所有业务断言 |

该helper被coop、Recovery、Run继承，因此一次修改统一其测试输入；不改`acceptance/test_recovery_e2e.py`。受控运行时仍明确标注fixture事实、无真实provider/模型执行，配置字符串不是实际模型证据。

获批后仅实施这个值，并将范围审计增加F14的完整helper精确比较：起点helper仅替换该字符串后须与候选逐字一致。现有交接diff先保留副本，再冻结包含F14的新diff；不扩大任何业务方法允许范围。不改Panes模型约束，不增加兼容路径或test mode。

## 读回与下一轮

诊断收据：[legacy-diagnosis-01.json](legacy-diagnosis-01.json)。再生成命令（换新输出）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/diagnose-legacy-green-01.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-diagnosis-01.json
```

主控报告总runner退出0；本目录未保存顶层shell退出收据，无法独立核实该0来自runner还是包装命令。已保存的两个子命令均退出1；总run.json为INCOMPLETE，当前及冻结runner在该状态的返回分支为1。不据此猜测并修改runner，也不把0当成功证据。

获批、修复并完成静态检查后，交新label `legacy-green-02`，保持先来源反事实再候选/回归的一阶段顺序。本轮仍0/8；F14批准前不修改该helper、不回复OUTSIDE-SANDBOX READY。
