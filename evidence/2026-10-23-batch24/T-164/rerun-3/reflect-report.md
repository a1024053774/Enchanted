# 复盘报告：demo-repo

快照时点：2026-10-24T13:48:55.163Z（包中 since 为 null，范围从最早记录开始）

## 范围

- 依据：只读了复盘包 `package.json`。没有打开轨迹归档、项目目录和工作台数据目录，所以下文只描述包里记录的事实。包里没写原因的地方，明确标为“包中未记录”，不做猜测。
- 任务：包中 `tasks` 只有两张票。
  - T-A：状态 `reviewing`，文档类，S。
  - T-B：状态 `claimed`，文档类，S。
- 用户指令里提到的 T-C 不在 `tasks` 中，包中只在一条主控消息里提到“C 仍等原卡前置”。T-C 是否已创建，包中无法确认。

## 这段时间发生了什么

时间均为 UTC（包中原始时间）。

| 时间 | 事件 | 依据 |
|---|---|---|
| 13:26:30 | 执行主控角色获批 | user_inputs[0] |
| 13:27:53 | 用户下达三票任务、分派与门禁约束 | user_inputs[1] |
| 13:29:43 / 13:29:48 | T-A 两次 `invalid_task_card` 打回（派发前） | gate_checks |
| 13:30:21 | 用户答复：从 main 新建 `dogfood` 分支 | user_inputs[2] |
| 13:30:30 / 13:30:34 | A a1、B a1 会话创建 | metrics.model_use.sessions |
| 13:32:31 | 用户要求对 A 首候选做一次真实 verify，形成打回 | user_inputs |
| 13:32:32 | B 提出 issue cf65：shopping.md 是否分组（非阻塞） | issues[0] |
| 13:32:46 | A 首候选 5510c3c 的 completion 失败，随后 `oracle_failed` 打回 | gate_checks |
| 13:33:04–13:33:53 | 用户两次向 A 的终端输入范围说明并回车 | user_inputs（intervention 114/115、133/134） |
| 13:33:33 | 用户在面板答复 B：不分组，平铺列出零库存物品 | panel、user_inputs |
| 13:34:31 | A 修复重交 68803065 后 completion 通过 | gate_checks |
| 13:35:25 | A 独立审查结论“需修复”，打回 `independent_review` | reviews、gate_checks |
| 13:35:37 | A 自报 issue 7f47：完成条件 check_a.py 过宽 | issues[1] |
| 13:36:53 | B 验证失败，`path_boundary` 打回 | gate_checks |
| 13:39:41 | 用户答复两问：不新建替代票，按原目标 revise→reclaim→重派；B 的 allow/deny 冲突可在原目标内修正 | user_inputs |
| 13:40:37 | B 提出阻塞 issue 6dd5：任务卡中 shopping.md 同时在 allow 与 deny | issues[2] |
| 13:41:13 | A a2 会话创建 | metrics.model_use.sessions |
| 13:45:40 | 用户通报：B a2 的 Codex 启动失败（bootstrap 超时，-32603），裁定不停线 | user_inputs |
| 13:45:53 | B 被 `identity_conflict` 打回 | gate_checks |
| 13:45:58 | A a2 completion 失败，`oracle_failed` 打回 | gate_checks |
| 13:46:15 | A 提交 caa797e 重交（按提交时间推断，包中无直接字段） | commit_trailers |
| 13:48:41 | 用户通报 A a2 已重交 caa797e | user_inputs |
| 13:48:48 | A a2 completion 与 verification 通过；独审会话 1c5f12ee 创建 | gate_checks、metrics |

**快照状态（观察，不构成收益结论）**

- T-A：reviewing。a2 交付已通过验证，独审尚无结论记录。
- T-B：claimed。`identity_conflict` 打回后未见后续记录，阻塞 issue 6dd5 没有关闭字段。
- 集成票数 0，`scores` 为空，`first_time.integrated` 为 0。

## 门禁与打回

gate_checks 共 19 条：

- `rejected` 6 条：`invalid_task_card` 2、`oracle_failed` 2、`path_boundary_failed` 1、`identity_conflict` 1。
- `delivery_rejected` 4 条：`completion` 2、`independent_review` 1、`path_boundary` 1。
- `completion_check` 4 条，`verification_result` 5 条（failed 3、passed 2）。

逐次说明：

1. **T-A 派发前两次 `invalid_task_card`（13:29:43、13:29:48）**：包中未记录具体原因。
2. **T-A 首候选 completion 失败 → `oracle_failed`（13:32:46）**：这是用户设计的打回演练。任务卡明确首候选故意漏掉总计（依据 user_inputs 13:27:53），所以这次打回符合预期。
3. **T-A 独审打回 `independent_review`（13:35:25）**：原因见下一节。
4. **T-A a2 completion 失败 → `oracle_failed`（13:45:58）**：包中未记录具体失败的检查项。
5. **T-B `path_boundary` 打回（13:36:53）**：包中没有直接写出打回原因。它与 6dd5 指出的 allow/deny 冲突时间相邻，6dd5 也说“门禁必然失败”。两者的关联是推断，需要对照 path_boundary 的详细记录确认。
6. **T-B `identity_conflict` 打回（13:45:53）**：包中未说明原因。它与 B a2 的启动超时之间是否有关，包中也没有说明。

数据注意点：

- `rejections[]` 的 `count` 语义不清。`independent_review` 的 count 为 2，但 gate_checks 中只有一条对应事件；两条 `completion` 记录的 count 都是 1。
- gate_checks 19 条中，15 条的 `check` 字段为 null，只有 `delivery_rejected` 写了检查名。这让“哪一项没过”只能靠推断。

## 审查

- **A 独审（会话 3576534a，13:35:25，1 回合，medium）**：结论“需修复”。
  - 问题：`check_a.py` 对候选内容过宽。变异 M4 把水果行改为“水果：4 件（苹果 3 件）”，检查仍 PASS，因为类别段落中出现了正确数字 3；变异 M5 把总计行改为“全局总计：3 件（另有 6 件待补货）”，检查同样 PASS。
  - 判断：候选 `inventory.md` 的内容与期望一致，缺陷在完成条件，不在产物。
  - 值得注意：门禁 completion 已在 13:34:31 通过，独审仍找出了门禁漏过的问题。
- **A a2 独审**：审查会话 1c5f12ee 在 13:48:48 创建，模型 unknown，回合为 null，包中无结论记录。
- **B 独审**：B 未到交付独审阶段，无记录。
- **打分与集成**：两票均无记录。用户要求“独审通过后按证据打分、经 integrate 集成”，目前还没有发生。

## 用户的注意力消耗

包中共有 14 条用户输入记录，时间跨度约 22 分钟（13:26:30–13:48:41）。

分类：

- 审批 1 条（执行主控角色获批）。
- 总任务指令 1 条，约 500 多字，里面包含分派、模型、门禁、revise 规则、回合上限等十余条约束。
- 问答 2 条：分支选择（13:30:21）、B 的分组问题（13:33:33）。后者属于需要用户决定的业务问题。
- 主控指令 6 条。其中 5 条以“新事实：”开头，是用户把状态变化转述给主控：
  - 13:32:31 要求触发 A 的真实打回。
  - 13:34:23 通报 A 已修复重交。
  - 13:36:09 通报 A 独审需修复。
  - 13:45:40 通报 B a2 启动失败。
  - 13:48:41 通报 A a2 已重交。
- 直接输入 worker 终端 4 条记录（2 段说明加 2 次回车，intervention 114/115、133/134）。包中没有说明为什么需要回车。它与用户在 13:27:53 说的“worker 调用工具时输入一次”相符，可能是工具调用确认，需要核对轨迹才能确定。
- “无新事实就停”这类收尾规则在 6 条主控消息中重复出现。

观察：用户的时间大部分花在中继状态和现场操作上，不在业务决策上。门禁结果和审查结论发生后，主控没有自己发现，用户要转述才能推进。

## 模型使用

数据来自 `metrics.model_use`，并与提交尾注（Model、Effort）交叉核对。

| 角色 | 会话 | 模型 | effort | 回合 |
|---|---|---|---|---|
| 执行主控 | 1db10a88 | unknown（请求值为 null） | unknown | 未记录 |
| worker A a1 | 46e72ed2 | claude-haiku-5-5 | medium | 6 |
| 审查员 A #1 | 3576534a | claude-haiku-5-5 | medium | 1 |
| worker A a2 | 1da78f0e | claude-haiku-5-5 | medium | 4 |
| worker B a1（Codex） | 8b252677 | zcode/GLM-5.3-Flash | max | 6 |
| worker B a2（Codex） | 51773fcf | unknown（请求 zcode/GLM-5.3-Flash） | unknown | 未记录（启动失败） |
| 审查员 A #2 | 1c5f12ee | unknown（请求 claude-haiku-5-5） | unknown | 未记录 |

- 记录到的 Claude 回合：11（worker A 与审查员，全部为 claude-haiku-5-5）。GLM 回合：6。
- 未覆盖的会话：3（执行主控、B a2、审查员 #2）。
- 执行主控的回合数为 null，所以无法核对“Claude 真实回合上限 60”是否被遵守。
- 包中没有记录同时运行的 Codex 会话数，无法核对“最多 2 个”。

## 做得好的

1. **打回演练按设计发生**：A 首候选在 completion 阶段失败并被 `oracle_failed` 打回，之后按卡补齐重交。依据：gate_checks 13:32:46；user_inputs 13:32:31。
2. **门禁拦住了问题交付**：本期共 6 次 `rejected`，包括 B 的 path_boundary 与 identity_conflict、A 的两次 oracle_failed。集成数为 0，没有错误交付进入集成。依据：gate_checks；`first_time.integrated` 为 0。
3. **独立审查找到了门禁漏过的问题**：completion 通过之后，独审用变异用例（M4、M5）发现 check_a.py 过宽。依据：reviews；gate_checks 13:34:31 与 13:35:25。
4. **歧义问题走 issue 流程**：B 在写业务文件之前提出 cf65，用户约 61 秒后在面板答复（13:32:32→13:33:33），B 随后继续。依据：issues[0]；panel；user_inputs 13:33:33。
5. **worker 主动自报验收缺陷**：A 在独审结论发生后 12 秒内提交 issue 7f47。依据：issues[1]；reviews 13:35:25 与 issues 13:35:37。
6. **失败与候选被保留**：commit 5510c3c、68803065、f998b82、caa797e 都在历史中；轨迹归档有 5 份。依据：commit_trailers；trajectory_archive。
7. **提交可追溯**：7 个提交中 5 个带尾注（Task、Attempt、Session、Model、Effort、Launch）。依据：commit_trailers。
8. **重派节奏**：用户在 13:39:41 给出 revise→reclaim→重派的指示，A a2 会话于 13:41:13 创建。依据：user_inputs 13:39:41；metrics.model_use.sessions。

## 要改的

1. **派发前没有拦住 allow/deny 冲突（T-B）**
   - 依据：issues[2]（6dd5，blocking，13:40:37）；gate_checks 13:36:53 的 path_boundary 打回。
   - 现状：`invalid_task_card` 只在 T-A 上出现过两次，T-B 的冲突直到交付后才暴露。
2. **验收脚本过宽，且没有受保护（T-A）**
   - 依据：reviews 的 M4、M5 PASS 记录；issues[1]（7f47）；panel 13:36:09 中用户要求“须在仓库受 oracle_paths 保护”。
   - 现状：任务卡没有要求负向变异用例，也没有规定保护路径。
3. **任务卡缺少输出格式约定（T-B）**
   - 依据：issues[0]（cf65）问“是否按类别分组”，用户 13:33:33 才答复。
   - 现状：这个问题不阻塞，但多了一轮往返。
4. **门禁记录不完整**
   - 依据：gate_checks 19 条中 15 条 `check` 为 null；`invalid_task_card` 无原因字段；`rejections[].count` 语义不清（independent_review 为 2，但只有一条事件）。
   - 现状：很多打回原因只能靠推断，复盘难以精确归因。
5. **模型与回合采集缺失**
   - 依据：metrics.model_use 中执行主控、B a2、审查员 #2 为 unknown，回合为 null。
   - 现状：“Claude 回合上限 60”和“Codex 并发上限 2”都无法核对。
6. **状态变化靠用户转述**
   - 依据：user_inputs 中 5 条“新事实”（13:32:31、13:34:23、13:36:09、13:45:40、13:48:41）。
   - 现状：门禁结果、审查结论、worker 退出都没有推送给主控；用户在 13:36:09 转述的是 13:35:25 的结论。
7. **worker 终端需要人工回车**
   - 依据：user_inputs 中两条 `action`（`\r`，13:33:06、13:33:53）。
   - 现状：包中未说明原因。需要核对轨迹后确认是否为工具调用确认。
8. **B 的基础设施问题未闭环**
   - 依据：user_inputs 13:45:40（Codex 启动 bootstrap 超时，-32603）；gate_checks 13:45:53（identity_conflict）。
   - 现状：两者的关系包中未说明；T-B 仍为 claimed；issue 6dd5 没有关闭字段，无法确认是否已处理。
9. **无尾注提交来源不明**
   - 依据：commit_trailers 中 409ae96（09:40:32-04:00，即 13:40:32Z）没有尾注，时间位于 B 与 A a2 的提交之间。554b8b2 是 main 的初始提交，不属于任务产物。
10. **T-C 无记录**
    - 依据：tasks 中只有 T-A、T-B；panel 中只有一句“C 仍等原卡前置”。

以上各项都是包中可直接核对的事实。看板的当前状态只作为观察记录，不据此判断收益。
