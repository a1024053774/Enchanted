# T-162-1 / a1 交接

状态：INCOMPLETE（修前真实红态已确认，候选已实现，等待主控运行 RUN-OUTSIDE-02）。

worker：b24-t162。分支：exec/t162。起点：c01742804。

## 主控 #32 后续：候选与证据

主控在沙箱外运行 RUN-OUTSIDE-01，退出 0，修前产品为 NO_GO。原始摘要为 `red-20261024T003707Z-17506.json`，夹具为 `/private/tmp/t162-3yx8jzyc`。摘要中角色决定输入为空、项目终端主控 turns 为 0，记录页和指标页断言均失败；已保留同前缀日志与两张截图，没有覆盖红态。

本次 Tracer bullet 贯通角色决定、统一输入表、读取接口与记录页；`roleRequests.decide` 在同一 SQLite 事务写入决定事件和用户输入，二者互相带 id/事件序号。仅操作员亲自的决定进入该方法；自动拒绝和过期仍走原有事件路径，不新增用户输入。不修改 `gates/core.ts` 或权限判断。

指标继续统计原有两类后台事件，评分计算不改。无来源的会话 turns 为 null；有来源、区间内没有对应记录时为已记录 0。汇总有未覆盖会话时保持未知，另列已记录部分和未覆盖会话数。逐会话可展开事件序号、时间、提示 id 或日志文件/位置；说明项目终端、人工输入回复、CLI 回执与 Reflect 的覆盖范围，以及打回原因的分母。

本地证据：

| 检查 | 结果 | 文件 |
| --- | --- | --- |
| SQLite 事件夹具：未知、已记录 0、区间边界、来源、跨项目、汇总 | PASS，13 项 | `metrics-fixture-01.json` |
| 同一夹具跑修前 c01742804 | NO_GO，缺陷断言失败，无初始化错误 | `metrics-fixture-01-parent.json` |
| 未知改成 0、零改成未知、删除来源、忽略区间四种变异 | 均为 NO_GO，预期行为断言失败 | `metrics-fixture-01-<变异名>.json` |
| 标准前端构建与 TS 语法检查 | PASS；Vite 仍有现有大 chunk 提示 | `build-check-01.json` |
| 脚本语法、内嵌 Python 语法、UTF-8/换行、diff 空白 | PASS | 本 session 执行；不是行为验收 |

构建命令：`node app/build.mjs --slot t162-check-01`（cwd `workbench`）；构建后已清理该检查的临时输出和缓存。夹具重放命令：

```zsh
node workbench/tests/test_t162_metrics_sources.mjs --summary /private/tmp/t162-metrics-new.json
node workbench/tests/test_t162_metrics_sources.mjs --revision c01742804 --summary /private/tmp/t162-metrics-parent-new.json
node workbench/tests/test_t162_metrics_sources.mjs --mutant unknown-as-zero --summary /private/tmp/t162-metrics-mutant-new.json
```

绿态与变异外部运行入口：

```zsh
zsh evidence/2026-10-23-batch24/T-162/RUN-OUTSIDE-02.sh
```

脚本绑定开始时的候选提交，并在结束时核对候选未变化。它运行真实 Electron 绿态与三种变异（缺输入、未知为零、破坏事务），包括批准、拒绝、自动拒绝、重复决定、过期、故障注入回滚、未知/零/两个已记录回合与展开来源。测试里的零和两个已记录回合来自明确标出的独立事件夹具，不冒称真实 CLI 计数。

相关已有回归：T-121 角色申请权限/生命周期、T-133/T-134 记录与四个指标、T-133/T-107 原生终端主控提示与层级。最后只读复核 T-133/T-107 的隔离 Claude 原生日志：核对两个主控确有根提示，同时指标诚实显示未覆盖。既有回归运行真实 Claude CLI、模型为 `claude-haiku-5-5` 的本地脚本化 Messages 接口；不是供应商真实模型验收，供应商模型回合消耗为 0（上限 6 未使用）。

真实 Electron 修后绿态、端到端变异、已有回归和原生日志复核均待 RUN-OUTSIDE-02；不据本地夹具称这些通过。按派发约定，提交脚本后停下请主控运行，再由主控另开只读独立审查；尚不宣称 DELIVERED。

范围外文档冲突已非阻塞上报 `20261024T004613Z-worker:b24-t162-issue-001`，见 `OUT-OF-SCOPE.md`；没有修改 Codex 提示采集或其验收文件。大的原始夹具均在 summary 指向的 `/private/tmp` 中，留待主控按 T-088 归档。

## 主控 #30 后续

主控批准了所需的局部写入边界（修订卡 `1b5d6a8b5`，本分支按文执行）。已新增 `workbench/tests/test_t162_role_records_metrics_e2e.py` 与 `RUN-OUTSIDE-01.sh`：真实 Electron 中批准一个申请，确认后自动拒绝同角色竞争申请，再亲自拒绝新的申请；核对统一输入记录、关联事件与记录页，同时核对无原生计数证据的主控与汇总不显示为已知零。此轮不启动模型。

尚未修改产品行为。真实 Electron 运行属于沙箱外工作，按派发约定提交脚本后停下，由主控执行：

```zsh
zsh evidence/2026-10-23-batch24/T-162/RUN-OUTSIDE-01.sh
```

脚本在 `c01742804` 源码上跑同一测试，写入带时间与随机后缀的新 summary、日志及截图；夹具留在 `/private/tmp/t162-*`，由主控按 T-088 归档。只有明确的缺陷断言失败才算红态，环境或夹具失败返回 INCOMPLETE。请回传 summary 路径后继续修复。

本地静态检查 PASS：`zsh -n evidence/2026-10-23-batch24/T-162/RUN-OUTSIDE-01.sh`、测试 `--help`（含 Python 导入与语法检查）、`git diff --check`。这些不算行为验收。前端文案规则使用已合并旧技能内容的 `frontend-production/references/look-and-copy.md`。

## 首次交接记录（a7ef82099）

## 已核对

已读取 COMMON-FIX、任务卡、T-162 ticket、对应 F04/F06 报告、项目地图、CONTEXT.md、intent.md，以及记录页、指标页、后台角色决定入口和现有端到端夹具。

会话开始运行：

```zsh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

结果：退出 0，Problems 0，Stale living docs 0。

代码位置核对发现任务卡边界不符，详见 [NEEDS-DECISION.md](NEEDS-DECISION.md)。阻塞上报：`20261024T003142Z-worker:b24-t162-issue-001`。建议允许局部修改 `daemon.ts` 的角色决定入口与 `roleRequests.ts` 的 `decide` 写入处；尚未获得批准。

## 验收状态

| 条件 | 状态 | 证据或缺口 |
| --- | --- | --- |
| 真实 Electron 修前红态 | INCOMPLETE | 尚未运行；边界问题发现后按 worker 规则停下 |
| 批准/拒绝进入统一用户输入记录，并关联角色事件 | INCOMPLETE | 未修改产品代码 |
| 主控回合与原生日志一致，或明确显示未知/未覆盖 | INCOMPLETE | 未修改产品代码 |
| 已知坏实现、修后绿态、相关回归 | INCOMPLETE | 尚未添加或运行测试 |

没有调用真实模型，没有启动 Electron 或后台，没有申请提权，没有改动产品代码、验收文件、地图或术语表。仅新增交接文本与按角色卡要求追加的阻塞问题条目。本次不是完成交付，不宣称 DELIVERED。

后续在边界批准后，先编写并运行真实 Electron 红态复现，再修根因。若运行受沙箱限制，保存 RUN-OUTSIDE-NN 脚本并提交，由主控执行后回传结果；不以环境失败代替红态。
