# T-024 独立只读审查：原始返回

审查角色：`acceptance-auditor`；配置为 `gpt-5.6-luna`、max reasoning。此配置记录不是供应商实际档位的证明。审查通过 `behavioral-acceptance-review` 发起，使用新的只读上下文，不读取实现者对话，不修改或重跑探针。它是完成后的独立审查，不是本次运行的实时 monitor。

以下保留原返回，不将其改写为 PASS：

```text
STATUS: INCOMPLETE
TARGET: evidence/2026-10-06-m1-batch1/T-024/run-08/；源码 .upstream/herdr@c4653a4f10502601ac110b12b2c45a5f7134082b
EVIDENCE:
- 独立 jq 复核通过：两客户端均为 endpoint generation 1、server 0.9.3，并共享同一 boot ID。
- 原始事件流包含不同 workspace 的独立 stty 尺寸、随机 nonce 输入、CLI focus 广播负面对照及探针清理。
- 收尾 git status 相比审查开始新增 M .project-map/MAP.md 与 M AGENTS.md；冻结候选/差分已变化，按规则停止。
FINDINGS:
- [P1] AGENTS.md（工作区状态，行号不适用） — 审查期间差分发生变化，无法确认结论仍对应同一冻结候选；不能出具 PASS。
COUNTEREXAMPLE:
- 公共 CLI workspace focus w1 实测将两个客户端变为 [w1,w1]，独立焦点 oracle 判定 false；该已知广播路径被拒绝。随机 nonce 与尺寸哨兵也会拒绝常量输出或忽略输入的实现。
LIMITATIONS:
- 候选或分支在审查期间移动；未继续运行检查，也未启动或停止任何 server。
```
