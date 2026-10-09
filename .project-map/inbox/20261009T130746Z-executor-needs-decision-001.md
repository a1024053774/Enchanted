---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-061"]
created_at: "2026-10-09T13:07:46.178751Z"
schema: 1
title: "T-061 验收口径：synara_e2e_review 是否一并修"
id: "20261009T130746Z-executor-needs-decision-001"
---

# T-061 验收口径冲突：synara_e2e_review 是否随数字解析一起修

**问题**：T-061 的修法是把 `codexAppServerManager.ts:4990` 的 `[a-z_]+` 放宽为允许数字。worker 用实际 manager 对父修订目录的全部 116 个工具做了两种帧的探针：带显式 tool_name 时 116 个全部免确认；缺 tool_name 时 113 个免确认，`a2a_submit`、`a2a_raise`、`synara_e2e_review` 三个仍弹确认。放宽解析会让已在目录里的 `synara_e2e_review` 也在缺字段帧下免确认，与 ready_rev 1 Acceptance 第 3 项"目录内其他工具的免确认结果与修复前逐一相同"字面冲突。证据：evidence/2026-10-09-batch11/T-061/decision-needed.md、catalog-baseline.json。

**选项**：
- A（推荐）：修订第 3 项为"目录内其他 113 个工具前后逐项一致；已在目录中的数字名字 `synara_e2e_review` 同样修复"。理由：它本来就在免确认目录里，带 tool_name 的帧已经免确认；缺字段时弹确认是同一个解析缺陷，不是目录范围的扩大。免确认范围仍只由目录决定。
- B：保留 `synara_e2e_review` 在缺字段帧下的确认，为 a2a 工具加工具级解析特例。代价：引入特例分支，与"放宽解析"的目标相悖。

**最小选择**：A，T-061 升 ready_rev 2，只改第 3 项措辞，补第三个工具的红绿证据。

**当前处置**：T-061 暂停（红态已保留，未改解析器）；不影响 T-056～T-058 关键路径。
