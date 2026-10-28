# T-203 独立审查报告

本审查为只读独立审查，基于文件读取比对候选差异 [`/private/tmp/t-203-review/change.diff`](file:///private/tmp/t-203-review/change.diff)、相关源码、票面需求与 `evidence/2026-10-27-batch28/T-203/` 证据。

---

## 1. 修复在根因层与方案符合度

- **根因对齐**：
  1. 回包卡死根因是原协议要求审查员在最后一条回复中手写包含 14 个顶层字段的深层嵌套 JSON，模型极易漏括号（如 UAT-02 中末尾遗漏 `}`）；
  2. 问题卡同号根因是原编号逻辑以会话（thread）维度做自增计数，每次审查重试都会创建全新 thread，导致同一次交付的连续两张卡均为“问题 1”。
- **方案实现（用户定“工具按字段提交”）**：
  - [workbench/src/reviewResult.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/reviewResult.ts) 新增 `review_submit` 工具与 `submit` 命令行入口，严格限定审查员仅提供 `verdict`、`findings`、`report` 三项（`FIELDS = ["verdict", "findings", "report"]`）；
  - 工具在调用当场加载门禁生成的 `review-template.json` 补齐身份与版本字段，并立即通过门禁既有的 [`reviewRequest`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/qualityProtocol.ts#L46-L64) 函数核对；不合格时即刻返回字段错误及修复提示（`hints`），审查员可在同一回合内更正重试，以最后一次成功落盘（原子重命名为 `review-result.json`）为准；
  - [workbench/src/daemon.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L851-L871) 在审查员回合结束（Stop）时直接读取 `review-result.json`，再次执行 `reviewRequest` 校验，未放宽任何门禁校验规则；
  - 旧的“最后一条回复必须是 JSON”协议被彻底移除：若未生成 `review-result.json`，直接抛出 `review_result_missing` 暂停任务，不再尝试从 `stop.last_assistant_message` 解析回包；
  - [workbench/src/gates/core.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2353-L2360) 将 `issueNumber` 改为按 `attempt_id` 计数，使 worker、审查员以及系统问题在同一 attempt 内部统一番号。
- **“不做”与设计原则核对**：
  - 未放宽门禁对回包内容的检查（`qualityProtocol.ts` 零改动，14 个字段、行号类型、必需变异节校验完全保留）；
  - 未改变审查判断逻辑本身；
  - 未引入对旧协议的兼容 fallback 分支、重试或错误吞噬机制。

---

## 2. 安全与边界

- **防篡改与目录隔离**：
  - 审查员在调用 `review_submit` 时，若传入 `verdict`、`findings`、`report` 以外的任何键（如试图注入 `task`、`attempt`、`candidate_commit`、`fence` 等），`saveReviewResult` 的 `Object.keys(given).some(key => !FIELDS.includes(key))` 断言会立即抛出 `review_fields` 异常予以阻断；
  - 工具写入文件严格限制在请求目录内部（`${directory}/review-result.json.<uuid>.tmp` 重命名为 `${directory}/review-result.json`），审查员参数无法控制写入路径或穿越至请求目录之外；
  - 审查员工作目录（一次性副本）与只读工作树（`review.workspace`）边界保持不变，门禁在验证前核对副本未越界、工作树洁净度与候选 commit SHA。
- **启动检查（`reviewLaunch`）核对**：
  - [workbench/src/gates/core.ts](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2490-L2542) 的 `reviewLaunch` 门禁对三家支持 MCP 的 CLI 均执行了严格比对：
    - **Claude Code**：核对 `argv[15] === "--mcp-config"`，且参数必须精准匹配 `claudeReviewMcp(launch.request_dir)`；
    - **Codex**：核对 argv 包含 `codexReviewMcp(launch.request_dir)` 派生出的全部 `-c mcp_servers.enchanted.*` 参数；
    - **opencode**：通过 `managed({ ..., reviewServer: reviewMcpServer(launch.request_dir) })` 生成基准并在 `boundary` 中逐项校验 `launch.env.OPENCODE_CONFIG_CONTENT`；
  - 若 `launch.request_dir` 缺失或与实际 argv 不符，门禁当场阻断（如 `test_t146_reviewer_hooks-2.json` 所示，报 `review_launch_boundary`）。
- **agy 提交命令受控性**：
  - agy 在交互模式下不暴露 MCP 工具，改为在派发提示中提供显式命令 `reviewResult.ts submit <请求目录> <文件路径>`；
  - 后台在回合结束时仅从自身记录的 `pane.record.request_dir` 读取并复核结果，agy 即使传入伪造的目录，后台也不会读取；且 `submit` 逻辑完全共用 `saveReviewResult`，同样强制校验 `reviewRequest`，无法逃逸检查。

---

## 3. 文案与代码事实一致性

- [workbench/README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L65-L95)：准确记录了 `review_submit` 工具按字段提交、身份字段模板补齐、回合结束后台读取 `review-result.json`、缺失时按 `review_result_missing` 拒收、四家 CLI 各自的工具挂接/调用机制，以及问题卡按 attempt 计号。每句话均与代码行为一致；
- [workbench/roles/reviewer.md](file:///Users/luckye/Documents/Code/a2a/workbench/roles/reviewer.md#L130-L132)：删除了原“整条最终消息直接被 JSON.parse 解析”的要求，明确改为使用 `review_submit` 仅提交三项，说明最后一条回复不再被读取；
- [workbench/app/IssuesPage.tsx](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L108-L117)：对 `review_result_missing` 提供了精准解释（“审查员结束回合时没有用 review_submit 交出合格的结论……”），同时保留原 `review_json` 文案兼容历史展示，且正确展开保留的 `protocol.raw`；
- [findings/2026-10-27-mcp-per-session.zh-CN.md](file:///Users/luckye/Documents/Code/a2a/findings/2026-10-27-mcp-per-session.zh-CN.md#L35-L43)：补充了真实实测中 Claude Code 延迟挂载与 ToolSearch、Codex 0.164 在 `exec` 环境需经 `ALL_TOOLS` / `tools.mcp__enchanted__review_submit` 调用、opencode 在 `execute` 代码中调用、agy 使用命令提交的细节，与探针证据完全吻合。

---

## 4. 测试区分度与测试有效性

- **主测试与对比断言**（[workbench/tests/test_t203_review_submit_e2e.py](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t203_review_submit_e2e.py)）：
  - **修前红态**：`red-2.json`（针对基准 `--revision a3ae46cf2`）运行同一三连审查场景，8 项断言全数失败（无工具调用、回包按 `review_json` 拒绝、任务未达 `verified`、三张问题卡均为“问题 1”）；
  - **修后绿态**：`green-5.json` 8 项断言全部 PASS（错误 verdict 当场拒收并提示、缺 line 字段当场拒收、无结果回合按 `review_result_missing` 暂停、同一意见修正后被门禁顺利接收并达 verified、问题卡编号分别为 1 与 2）；
  - **变异体验证（Mutants）**：
    - `mutant-per-thread-number.json`：编号恢复按 thread 计数，精准失败于 `issue_numbers_distinct`（cards: `[1, 1]`）；
    - `mutant-tool-skips-check.json`：工具端跳过 `reviewRequest`，坏字段被工具收下，精准失败于即时校验断言；
    - `mutant-stop-reads-last-message.json`：后台恢复读取最后一条回复，精准失败于 `review_result_missing` 及收下断言。
- **独立预期来源**：
  - 测试预期直接源自 UAT-02 第 2 轮试用现场故障与 T-203 票面规格（少括号卡死、当场纠错指导、按 attempt 统一编号），非倒推实现输出。
- **表格与数据一致性**：
  - `RESULTS.md` 中的主测试表格、探针表格、回归表格的数据、状态、参数与各 JSON 文件记录一致。
- **旧测试未被削弱**：
  - 涉及审查回包的 20 个既有测试（如 `test_t107`, `test_t122`, `test_t123`, `test_t124`, `test_t127`, `test_t131`, `test_t140`, `test_t141`, `test_t146`, `test_t160`, `test_t177`, `test_t179`, `test_t180`, `test_t187` 等）均升级为经 `review_submit` 提交；
  - `test_t122` 删除了过时的 `rejected` 场景（因审查员已无法自行注入不匹配的 `candidate_commit`），保留了未调工具直接结束的 `malformed` 场景，预期由 `review_json` 转为 `review_result_missing`；
  - `test_t127` 额外增加了 `review_submitted_by_tool` 断言，验证加强；
  - `test_t160` 将原 `accept-fenced` 变异体更新为验证 fenced 回复触发 `review_result_missing`，界面按钮引导恢复测试保持完整。

---

## 5. 验收标准与证据核对

| 票面验收标准 | 状态 | 证明材料 |
| --- | --- | --- |
| 1. 方案定下并写进本票 | **已完成** | [T-203-review-submission-robustness.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-203-review-submission-robustness.md#L20-L29)“方案（2026-10-27 定）”一节完整记录。 |
| 2. 修前版本经真实入口：审查员回包少一个括号审查卡死；修后同样意见被收下，格式不对仍拒收并说明 | **已完成** | `red-1.json`/`red-2.json` 证明修前卡死；`green-5.json` 证明格式错误当场被拒说明、同一意见收下并 `verified`；真实 CLI 探针 `codex-real-probe-1.json`, `opencode-real-probe-1.json` 及全流程 `real-t187-opencode-agy-1.json`。 |
| 3. 同一 attempt 的多张问题卡编号不重复 | **已完成** | `green-5.json` 产出两张卡编号为 1 与 2；`mutant-per-thread-number.json` 证明未修改时为 `[1, 1]`。 |

未跑项与限制已如实列入 `RESULTS.md`“没做”小节。

---

## 发现的问题清单

### 问题 1：RESULTS.md 记录的单元测试缺失对应结果 JSON 文件
- **位置**：[`evidence/2026-10-27-batch28/T-203/RESULTS.md:71`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-203/RESULTS.md#L71)
- **失败场景**：文档第 71 行记录单元测试通过列表中包含 `test_t160_protocol_idle`，但在证据目录 [`evidence/2026-10-27-batch28/T-203/unit/`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-203/unit/) 下未发现该测试的产物文件（而 `test_t141_reviewer_contract-2.json`、`test_t146_reviewer_hooks-3.json`、`test_t141_launch_contract-3.json` 均存在）；虽然在 `regression/` 目录下有全流程 `t160-1.json` 通过证据，但该独立状态单元测试未归档对应 JSON 报告。
- **严重程度**：P3

### 问题 2：RESULTS.md 记录的文件名与磁盘实际文件命名存在前缀差异
- **位置**：[`evidence/2026-10-27-batch28/T-203/RESULTS.md:73`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-203/RESULTS.md#L73)
- **失败场景**：文档第 73 行说明“`test_t112_reviewer_startup` 在 HEAD（`*-head.json`）与本次改动上都失败”，磁盘上的实际文件名连词线与前缀为 `t112-reviewer-startup-1.json` 与 `t112-reviewer-startup-head.json`（无 `test_` 前缀且采用中划线），查阅证据索引时存在轻微名称出入。
- **严重程度**：P3

---

## 审查结论

**结论**：`可合并`

修复正中根因，完全遵照用户选定的“工具按字段提交”方案，未放宽任何质量检查规则，权限与目录隔离机制健全；主测试与变异体对比严密，多家 CLI 真实探针及回归测试证据充分。所发现的问题均为证据归档记录层面的 P3 级细节瑕疵，不阻碍代码合并。

---

## LIMITATIONS

1. **未在用户真实交互 UI 中重走端到端审查**：主测试及多数回归测试使用真实 CLI 二进制与本地脚本化 Messages/API 模拟器运行，未启动真实大模型进行完整的 Electron 界面手工交互测试（与 RESULTS.md“没做”说明一致）。真实模型在真实 CLI 下的挂载与调用已由 `codex-real-probe-1.json`、`opencode-real-probe-1.json` 及 `real-t187-opencode-agy-1.json` 单独取证证明。
2. **审查员权限为只读模式**：本独立审查严格在只读环境下进行，未执行任何 shell 命令，未重新运行或生成新的测试证据，依赖对已有代码差异与留存 JSON 证据的交叉静态验证。