# T-205 独立审查报告

审查状态：`PASS`  
结论：**可合并**

---

## 1. 修复层级与设计原则核对

1. **是否在根因层**：
   - 是。问题根因在于门禁在拒绝请求时只输出机器代码（如 `oracle_not_found`、`stale_turn`），导致主控与用户缺乏直观的原因说明与操作指引。
   - 候选改动在 [refusals.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/refusals.ts) 建立了唯一的拒绝码解释字典 [`explainRefusal`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/refusals.ts#L53-L55)，并在所有对外输出回执通道统一接入：
     - [daemon.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L130-L133) 套接字回执注入 `explanation: { reason, next }`，供 `a2a` 命令行、MCP 工具与工作台前端读取；
     - [taskHistory.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/taskHistory.ts#L105-L110) 任务页时间线读取同一份解释并追加文件名明细；
     - [gateReceipts.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L12-L16) worker 窗格回执与记录页回执摘要使用同一份文案。
2. **是否触及票中“不做”**：
   - 票明确规定“**不做：改门禁的拒绝条件**”。
   - 经核对 [`A2AGates`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L171)（`core.ts`），所有门禁判定、拦截规则、校验条件均**零改动**。
3. **是否引入吞掉错误、兼容分支或平行路径**：
   - 原始 `result.error` 契约代码及 `result.details` 完整保留并原样返回；未覆盖的错误码返回 `null`，保持原样输出，没有吞掉任何错误。
   - 三处出口均调用单一事实源 [`explainRefusal`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/refusals.ts#L53-L55)，无平行分支或双写逻辑。

---

## 2. 文案与代码事实一致性核对

对 [refusals.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/refusals.ts#L17-L51) 中登记的全部 26 个拒绝码逐一核对 [`A2AGates`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L171) 与 [daemon.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts) 中的真实触发逻辑：

| 拒绝代码 | 代码事实与触发点 | 文案原因与下一步核对 |
| :--- | :--- | :--- |
| `invalid_task_card` | `core.ts:3820, 4487`：卡校验抛出 `TaskCardError`，携带 `field` 与 `reason` | **一致**。指明看回执的 field 与 reason，改卡后调用 `card_save`。 |
| `task_exists` | `core.ts:3840`：`create` 时库中已存在同名任务 | **一致**。指明换任务号或通过 `card_save` + `revise` 改卡。 |
| `unknown_task` | `core.ts:1191, 1196`：库中无此任务或项目未限定 | **一致**。指明核对任务名，跨项目写完整 id `<项目>+<任务>`。 |
| `project_not_opened` | `daemon.ts:382`：终端主控指定项目未在工作台打开，`details.opened` 列出已打开项目 | **一致**。提示用户在工作台先打开目录。 |
| `controller_required` | `core.ts:3442, 3649, 3763` 等：命令仅限已批准主控调用 | **一致**。引导运行 `a2a request` 并等待工作台批准。 |
| `executor_required` | `core.ts:4017, 4027, 4085`：`close`、`out_of_card`、`abandon` 仅限执行主控 | **一致**。指明转交执行主控或申请该角色。 |
| `oracle_not_found` | `core.ts:2196`：`oracle_paths` 文件不在基线 commit，`details.missing` 列出缺失清单 | **一致**。说明提交验收文件到工作分支或改卡路径后重派。时间线还能读出 `（缺：...）`。 |
| `path_overlap` | `core.ts:1311`：修改路径与进行中任务重叠，`details.conflicts` 列出重叠项 | **一致**。指明若能并行则加 `overlap_reason` 重发 dispatch，否则等待对方验收/回收。 |
| `command_unavailable` | `core.ts:1462`：子进程无法启动（找不到命令或无执行权限），details 带有 `reason` | **一致**。核对 details 中的命令信息并改卡重试。 |
| `run_blocked` | `core.ts:1660, 3020, 3948, 4450`：CLI 处于 blocked 状态（停在权限/确认框），无法推进或回收 | **一致**。指明查看 worker 窗格停在哪项提示并由用户处理。 |
| `worker_working` | `core.ts:3949, 4452`：会话仍在 `running` 回合中，门禁拒绝回收或停止 | **一致**。提示等回合结束后再试。 |
| `stale_turn` | `core.ts:4200`：已交付且非打回状态（无活动 `repair`）下新回合再次交付 | **一致**。准确解释了 attempt 已交付过不能再交；指明补改需走“`card_save` → `revise` → `reclaim` → `dispatch`”重派流程。 |
| `stale_attempt` / `stale_session` / `stale_fence` / `stale_thread` | `core.ts:4176-4183, 4201` 等：身份凭据或 attempt 绑定已陈旧失效 | **一致**。统一使用 `staleRunner`，提示 worker 结束回合，主控查当前状态。 |
| `stale_spec` | `core.ts:3995, 4179`：卡已采用新版本（`spec_rev` 递增） | **一致**。说明交付使用了旧卡版本，需按新卡重派。 |
| `not_submitted` | `core.ts:1772, 4076`：任务非 `submitted` 状态下尝试验收 | **一致**。指明等状态变成已交付再 `verify`。 |
| `repair_submission_required` | `core.ts:1771`：存在打回修复标记且未重新交付时尝试 `verify` | **一致**。指明等 worker 修复并重交后再验。 |
| `quality_rejection_limit` | `core.ts:2376, 3103`：打回次数达到上限（3 次） | **一致**。说明达到上限门禁不再接受修复，主控需改卡重派或关闭。 |
| `oracle_failed` | `core.ts:1968`：完成条件命令执行退出码非 0，打回给 worker | **一致**。说明完成条件未过已打回，等修复重交。 |
| `not_verified` | `core.ts:4080, 4314`：任务未达 `verified` 状态尝试 `integrate` | **一致**。指明须先 `verify` 且审查通过后再集成。 |
| `out_of_card_unjudged` | `core.ts:4318`：改动包含任务卡外文件且主控未判断 | **一致**。指明用 `out_of_card` 裁定 accept 或 reject。 |
| `score_required` | `core.ts:2864`：`integrate` 缺少 `score_file` | **一致**。提示准备打分 JSON 文件并在集成时传入。 |
| `already_accepted` | `core.ts:3987, 4087`：任务已集成 | **一致**。提示已完成，有新需求另建任务。 |
| `task_closed` | `core.ts:1573, 3989`：任务已关闭 | **一致**。提示任务已关闭不能再派发或改动。 |

同时核对 [RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/RESULTS.md#L11) 说明排除的 4 个代码（`invalid_path`、`oracle_modified`、`needs_reconciliation`、`identity_conflict`）：其来源多样或语境多变，排除不收录、保持仅输出代码的决定符合设计原则。

---

## 3. 测试有效性与证据核对

1. **测试入口与场景真实度**：
   - 测试脚本 [test_t205_refusal_explanations_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t205_refusal_explanations_e2e.py) 运行真实后台、socket、门禁，主控终端在真实 zsh 内执行真实 `a2a` 命令行，worker 为真实安装的 Claude Code 进程。
   - 构造两个真实失败场景：
     - 主控派发验收文件缺失的卡（触发 `oracle_not_found`）；
     - worker 交付后在窗格注入新指令触发二次交付（触发 `stale_turn`）。
2. **预期是否独立于实现输出**：
   - 9 项断言（保留原错误码、解释字段存在、时间线提取缺件文件名、窗格与记录页回执一致、下一步包含 `revise`/`reclaim`/`dispatch` 动作等）直接对照 [T-205](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-205-gate-refusal-explanations.md) 与用户试用报告 UAT-02，并非将实现输出反向写成断言。
3. **修前、修后及变异测试对照**：
   - [red-1.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/red-1.json)：首个失败断言退出，失败于 `a2a_reply_explains`；
   - [red-2.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/red-2.json)：修前工作区，精准捕获 6 项预期失败；
   - [red-3.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/red-3.json)：基于修前基准提交 `--revision a3ae46cf2` 独立重放，同样在 6 项上失败；
   - [green-1.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/green-1.json)：修后版本 9 项检查全部通过；
   - [mutant-reply-without-explanation.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/mutant-reply-without-explanation.json)：去掉套接字层解释，精准失败于 a2a 回执及两处对比；
   - [mutant-history-without-explanation.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/mutant-history-without-explanation.json)：去掉时间线解释，精准失败于两处时间线检查；
   - [mutant-receipt-without-explanation.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/mutant-receipt-without-explanation.json)：去掉 worker 回执解释，精准失败于回执检查与下一步指令检查。
   - [RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/RESULTS.md#L30-L39) 中的表格数据与所有 7 个 JSON 报告逐项核实完全一致。

---

## 4. 验收条件达成情况

- [x] **列出要覆盖的拒绝码**：已在 [RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/RESULTS.md#L9) 和 [refusals.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/refusals.ts#L17-L51) 中详列 26 个常见代码并说明未收录项。
- [x] **修前版本经真实入口：`oracle_not_found`、`stale_turn` 只显示代码；修后显示原因与下一步，代码仍在**：`red-3.json`（修前代码版本）与 `green-1.json`（修后）提供完整证据，代码字段 `error` 始终完好保留。
- [x] **主控经 a2a 或 MCP 拿到的拒绝回执带同样的说明**：`a2a call` 在测试中完整覆盖；MCP 服务端原样传递 daemon 套接字输出，行为与 a2a 一致。
- [x] **未做事项如实写明**：MCP 链路未单独写 E2E 用例、时间线检查未做 Electron 窗格截图，已在 [RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-205/RESULTS.md#L57-L60) 的“没做”一节中如实公开。文档已同步更新至 [SKILL.md](file:///Users/luckye/Documents/Code/a2a/workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md#L146) 与 [README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L1146)。

---

## 5. 问题清单

本次审查**未发现 P1（阻断）或 P2（缺陷）问题**。

记录 1 项观察（P3）：
- **位置**：[daemon.ts:460-464](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L460-L464)
- **场景**：`relay_receipts` 返回记录中，每条回执的 `summary` 由 [`receiptLines`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L10) 动态解析并带上了“原因”和“下一步”，而其内嵌的 `result` 字段保留的是门禁原始写入的数据（未带 `explanation` 对象）。
- **严重程度**：P3（低 / 仅作事实说明）。
- **说明**：界面展示门禁回执主要依据 `summary`，此表现与“代码与持久化记录保留原始契约、展示与对外回执附加解释”的整体设计原则相符，不影响业务与展示。

---

## 6. 结论

**`可合并`**

---

## LIMITATIONS

1. **未运行 Shell 命令与实际后台**：本次审查严格执行只读约束，未执行任何 shell 命令，未启动本地后台或运行测试脚本，所有测试数据均来自既有证据文件（`evidence/2026-10-27-batch28/T-205/*.json`）。
2. **MCP 独立测试缺口**：MCP stdio 接口依赖于 `terminalMcp.ts` 原样转发 daemon socket 回执的静态代码核对，未在真实 MCP 客户端中实测。
3. **GUI 渲染未核对像素**：时间线与记录页的展示核验基于 `task_history` 和 `relay_receipts` 的接口数据结构，未在 Electron 真实窗口中核对 UI 渲染或截图像素。