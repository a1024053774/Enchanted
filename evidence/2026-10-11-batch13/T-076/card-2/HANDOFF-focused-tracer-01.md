# T-076-2：第一条质量串 Tracer bullet 的 focused green 交接

状态：**INCOMPLETE**。本轮按主控 #35 实现生产路径并准备验证；尚未运行候选绿态，不宣称产品通过。真实 Codex **0/8**，本脚本没有真实模型、auth 复制或 P-review 入口。

## 输入证据已核对

`outside-red-02` 的 stage-1/2/3 均 PASS，product_status=INCOMPLETE。stage-2 的11项均命中预写契约失败标识；stage-3 的8项既有保护对照全过，三个起点变异体分别命中 CONTROL-FENCE、CONTROL-FROZEN、CONTROL-PATH。没有cleanup失败或>5 MB文件。red-01 保留其原始INCOMPLETE。

## 本轮生产改动

- 原submit只在存在明确打回授权时允许同attempt、同原生身份的新交付回合重交C2；未被打回的候选仍冻结。交付保存当前回合实际模型/强度及launch来源，ACK不能覆盖这些事实。
- 路径、完成条件、尾注和有效“需修复”结论统一保存打回。前两次经现有登记/空闲队列回写；第三次issue+暂停，不再发修复消息。run保留原attempt等待修复，不把首拒当回收信号。
- 机械成功进入reviewing，新建独立reviewer、只读argv、独立home和session/thread/launch；后台核对有效结论的C、合同、角色及原生会话未复用。只有有效“可合并”才进入verified。
- reviewer最终JSON在匹配Stop之后由hook请求处理器写专用文件，再走现有relay。代码不剥fence、不局部提取；非法保存原文、上报、暂停。有效结论落库且idle之后回收reviewer，不开纯ACK回合。
- integrate要求执行主控`--score-file`。评分意图与原integration intent绑定，成功集成与最终score_recorded同事务落库，重放不重计；run等显式集成后才回收原worker。
- 新状态只在既有JSON/事件中记录；没有新增或迁移表。只读一致性检查器增加这些事件的重建规则，未修已知membership/attachment存储缺口。

源文件为`gates/core.ts`、`gates/qualityProtocol.ts`、`contracts/a2aGates.ts`、`gates/cli.ts`、`panes.ts`、`store.ts`、`relay.ts`、`relayFiles.ts`、`daemon.ts`、`stateConsistency.ts`及README。未修改旧acceptance断言、scripts、spec、地图或另一worker的checkout。

## 执行命令

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh focused-tracer focused-tracer-01
```

输出：`card-2/outside-focused-tracer-01/`。标签必须全新，已经存在则拒绝覆盖。执行前检查外置盘挂载和Node26.5，冻结当前候选（包括未提交的新模块/测试）与tracked diff；不构建/安装依赖、不修改共享输出目录。

阶段内顺序为：

1. 单独跑`tracer_success`：显式submit C1 → 完成条件拒绝 → 已登记gate修复 → 原native/attempt重交C2 → 机械全重跑 → fresh reviewer → B结论 → 主控带分集成 → 单次评分/引用读回 → 回收。
2. 第一条通过后跑其余10项受控场景：单独缺评分及缺notes、错C、Markdown包裹的非法结论、需修复到新C新审查、旧reviewer原生会话复用、第三次停止、writer伪交审查、run等待执行主控、当前交付缺模型上下文、错身份拒绝的单次评分计数。各场景的期望来自ticket/批准计划；身份值读回仅用于指向实际新建对象。
3. 重跑阶段3的8个既有保护对照。这些不是旧8/9/18完整回归。
4. 只读调用现有`scripts/score`中的`validate_scores`校验本夹具产生的评分payload；不运行真实打分命令，不写或导入`records/scores.jsonl`。
5. 每个独立候选副本只注入明确坏行为，再从同CLI入口观察以下9个业务失败。只有准确命中指定ContractFailure才算有效反事实。

| 变异体 | 预期命中 |
| --- | --- |
| wrong-c-accepted：不核对review结论C | TRACER-REVIEW-CANDIDATE |
| old-native-accepted：允许复用旧reviewer原生会话 | TRACER-REVIEW-REUSE |
| third-rejection-keeps-writing：到第4次才停 | TRACER-THIRD-STOP |
| markdown-extracted：擅自剥除JSON fence | TRACER-REVIEW-STRICT-JSON |
| score-invented：缺分时伪造默认分 | TRACER-SCORE-REQUIRED |
| score-fields-unchecked：跳过必填字段校验 | TRACER-SCORE-FIELDS |
| reviewer-writable：reviewer错误使用workspace-write argv | TRACER-READONLY-ARGV |
| prior-turn-score-facts：沿用上一回合模型事实 | TRACER-DELIVERY-CONTEXT |
| identity-refusals-not-scored：把已观察的错身份拒绝计数清零 | TRACER-SCORE |

这些错误路径仅存在于`/tmp`里的变异体副本，主checkout不安装默认分、fence剥除或任何兜底。

## 证据、停止与限制

沿用已取得红态的真实CLI/后台/relay/门禁/Git/SQLite夹具，只替换PTY和进程观察；受控原生记录并不是实际供应商记录。reviewer结论由独立测试输入提供，真实产品仍执行其身份/候选/协议核对；没有给门禁注入passed状态。只读argv对照只证明启动配置，实际沙箱写入拒绝仍由P-review实测。

任何候选业务失败、harness_error、清理错误或变异体未命中都会停止；没有自动修产品、重试或追加模型回合。保留完整argv/stdin/stdout/stderr、逐案断言、SQLite/Git读回、launch和原始回合输入、源快照和所有失败；自建后台脱离进程组，只停止核实PID的本夹具服务。大压缩包按原外置归档规则处理，剩余大文件列入oversize_files，不能直接提交。

本轮只交第一条贯通路径的候选，尚未加宽以下内容：

- red_commands的test_paths声明/执行，B+测试失败/C通过，以及工作分支项目规则冻结/执行；
- abandon/升级评分、后台scores_validate与用户评分导入边界；
- 评分在CAS前后中断的故障注入、reviewer创建/恢复/回收异常的完整证据；
- 8/9/18、T-075/T-076-1完整候选回归与最终独立交付审查；
- P-review真实只读探针、真实模型闭环、T-077统一worktree生命周期/R8联验。

deferred-contracts中的三次上限、审查身份/错C/需修复与独立缺分已有本轮受控案例/反事实准备，但**未运行前仍是INCOMPLETE**。第5项的放弃/格式/恢复未完整完成，第6项真实探针尚未批准启动。候选不能用于日常派发或作为整张T-076通过结论。

请回传`outside-focused-tracer-01/run.json`及首个失败的原始输出。按主控 #35，交接后停下；不自行执行Unix socket/ps/模型/进程信号，也不申请提权。
