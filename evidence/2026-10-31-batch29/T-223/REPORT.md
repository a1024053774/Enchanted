# T-223 执行报告

**BLOCKED**。已通过真实 `Retrospectives.due()` 复现晚一小时的缺陷；隔离历史记录探针确认，满足票面正确结果与保留现有精确字符串去重时，旧错误 `scheduled_for` 可能无法阻挡同一周补跑。按本次用户指令第 4 条停止实现，等待主控交用户决定。未修改产品代码、README、测试或 `.project-map/`，未 commit、push；没有可交付的修复候选。

## 范围与身份

- 工作目录：`/Users/luckye/Documents/Code/a2a-worktrees/T-223`。
- 分支：`t223-due-spring-gap`；完整基线：`76f969963f6ee582460d357c317cb30b203bebe6`，开始与结束工作树均干净。
- 票面：`.project-map/tickets/T-223-retrospective-due-spring-gap.md`，`ready_rev: 1`；未修改票面。
- 环境：Node `v26.5.0`；两个运行探针均显式 `TMPDIR=/private/tmp TZ=America/New_York`。
- 本会话是 T-223 worker；未提供受管 attempt、session/fence、完整启动 argv 或可核验的实际模型/强度，不补造这些信息。使用本机 `project-map`、`evidence-first-testing`、`document-writing` 和 `reality-first-engineering` 的当前 SKILL.md；未取得独立 skill 版本号，不把技能名当版本证据。
- 阅读了仓库规则、MAP、票面、CONTEXT、intent、真实实现、直接调用方、README 与 T-136/T-137 测试入口；T-221 归档仅只读参考。未访问用户运行库，未知用户实际是否存有错误记录。

## 测试前失败方式清单

清单在探针脚本和第一次运行前写入 `FAILURE-MODES.md`；本报告复列其内容与当前覆盖状态。期望来自票面与手工日历推算，不读取实现输出生成答案。

| 编号 | 可能失败的方式 | 独立预期与证据状态 |
| --- | --- | --- |
| F1 | 跳过日当天查询，先 setHours 污染此前普通日的时刻 | 周一 02:30，03-08 中午查询；03-02 是 EST，02:30 加 5 小时应为 `2026-03-02T07:30:00.000Z`。真实红态已保存 |
| F2 | 目标日期本身为跳过日，结果随查询日变化 | 建议 03-08 02:30 顺延到 03:30 EDT，即 `2026-03-08T07:30:00.000Z`；应比较当天与次日。停止后未执行 |
| F3 | 本周未到点，回退一周落到跳过日 | 周日 02:30，03-15 01:30 查询，应为 `2026-03-08T07:30:00.000Z`。未执行 |
| F4 | 跳过日到规范后时刻之前查询，回退一周仍保留 03:30 | 周日 02:30，03-08 03:00 查询，应为 03-01 02:30 EST，即 `2026-03-01T07:30:00.000Z`。未执行 |
| F5 | 秋季重复时刻取错一次，或第二次再次触发 | 建议 11-01 01:30 取第一次 EDT，即 `2026-11-01T05:30:00.000Z`；两次 01:30 之间及之后均应核对。未执行 |
| F6 | 普通日被改变 | 03-16 周一 02:30 EDT，即 `2026-03-16T06:30:00.000Z`。未执行 |
| F7 | 跨月末回退错误 | 04-01 查询周一 02:30，应为 `2026-03-30T06:30:00.000Z`。未执行 |
| F8 | 跨年末回退错误 | 2027-01-01 查询周一 02:30，应为 `2026-12-28T07:30:00.000Z`。未执行 |
| F9 | 生效边界错误 | effective_from 等于 slot 可触发；晚 1ms 不可触发。未执行 |
| F10 | 到点边界或禁用行为错误 | 到点前取上周，等于 now 可触发，disabled 返回 null。未执行 |
| F11 | 已运行去重、项目隔离或手动记录语义错误 | 同项目同 key 不再运行，其他项目及手动记录不阻挡。本次只验证历史错误 key 精确去重，其余未执行 |
| F12 | 旧错误 key 与修后正确 key 不一致，导致同一周补跑 | 隔离库记录真实旧结果后核对两个 key 与真实 due()；风险已确认，触发停止条件 |

Ubiquitous language 沿用「复盘」「定期复盘」与 `scheduled_for`。本项探针直接调用现有领域方法，不新增包装或接口，保持 Deep modules；因停止在事实核对阶段，没有开始跨层 Tracer bullet。

## 红态与根因

`probe_due.mts red` 使用内存 SQLite，实例化真实 `Retrospectives`，调用 `saveSchedule()` 后调用真实 `due()`；没有另写日期算法，没有后台、UI、CLI 子进程或模型调用。

输入：America/New_York，每周一 02:30，2026-03-01 00:00 EST 起生效，查询 2026-03-08 12:00 EDT（16:00Z）。手算最近周一为 03-02，02:30 EST = 07:30Z。

实际返回 `2026-03-02T08:30:00.000Z`，晚一小时。`red-due.log` 保留完整 stdout/stderr、实际值、期望值、断言堆栈及 `exit_code=1`。失败点就是 F1 的 `assert.equal(actual, expected, ...)`，不是夹具、导入或环境错误。**修前红态验收 PASS**，不代表实现通过。

根因在 `workbench/src/retrospective.ts:59`：先在 03-08 调 `setHours(2,30,0,0)`，该日本地 02:30 不存在，原生 Date 规范成 03:30 EDT；随后 `setDate` 回退到 03-02，仍是 03:30，得到 08:30Z。第 61 行直接回退七天也要纳入修复核对：回退本身可跨过时区转换，已规范的时刻也可能被带到普通日期。不能只交换前两行就宣称 F3/F4 已覆盖。

预期最小方向是在每个目标日期确定后设置原始墙钟时刻，包括本周未到点时选择上周日期的分支；不添加重试、兜底或兼容路径。**未实施该方向**。

## 规则建议及依据（尚未落地）

建议保留 ECMAScript 原生 Date 的时区歧义规则：不存在的墙钟时刻按转换前偏移解释，相当于向前顺延跳过的时长；重复时刻取较早的一次。纽约 2026-03-08 02:30 因而是 03:30 EDT（07:30Z），2026-11-01 01:30 取第一次 EDT（05:30Z）。

依据：2026-10-31 查阅 [ECMAScript 21.4.1.26 UTC(t)](https://tc39.es/ecma262/multipage/numbers-and-dates.html#sec-utc-t)，算法对重复时刻选择最早的候选 instant，对跳过时刻使用转换前偏移；该节也提供纽约春秋转换示例。本报告只转述与本项有关的规则。它与现有 Date 操作一致，不建议另改为跳过整周或选第二次重复时刻。

即使保留这一规则，修正 F1 仍会改变既有错误 key。停止条件并不需要改用另一套夏令时规则才能触发。因此没有把建议写成已生效的代码注释或 README 契约。

## 历史记录风险与停止依据

**REALITY GATE: BLOCKED**。

- observed：`retrospective.ts:63` 只比较 `run.scheduled_for === slot.toISOString()`；`daemon.ts:86` 把 due 返回的 slot 传入 `prepare()` 保存，且在终端打开前即记录该 run。没有同一日历周身份可用于另行识别。
- measured：`probe_due.mts history` 先得到旧版真实结果 `08:30Z`，把它写入隔离库作为一个完整定期复盘记录。同项目同一查询，真实 due 返回 null；但同周普通查询日 03-07，真实 due 返回正确的 `07:30Z`。库里不存在 `07:30Z` 这个 key。探针所有风险断言通过，`history-risk.log` 保留输出，`exit_code=0`。
- inferred：若该周只存有旧错误 key，修复后按要求算出的正确 key 不被旧记录占用，`due()` 将允许再运行。这是修复后的推论，**不是已运行修后代码的绿态，也不是已观察到供应商真的补跑**。
- unknown：用户实际库是否有这类记录，以及是否接受升级后该周可能补跑。未访问用户数据，不能将「未知」写成「不存在」。

当前用户指令第 4 条原文：

> 如果你认为合理的规则会改变用户已经看到的行为（比如已存的 `scheduled_for` 会和修后算法对不上，导致同一周补跑），停下写进报告，不要自行决定。

本次事实符合该例，所以停止。没有自行修改去重、存储、历史记录或验收条件，也没有用兼容分支掩盖问题。这一停止来自当前用户指令，不是技能自行增加审批要求。

最小后续选择由主控交用户：

1. 明确接受历史错误 key 可能导致补跑，授权继续原范围修复，仍保留现有去重规则。
2. 若不能接受补跑，先另行授权并决定历史记录处理；这会触及本次禁止修改的去重/存储边界，不在本会话自行设计或实施。

## 改动、绿态、变异与回归

**产品改动：无。** `candidate.patch` 为 0 字节，是当前相对 HEAD 的空差异快照，不是已完成修复的冻结候选。worktree 完全干净。新增文件仅在指定的 T-223-evidence 目录。

修后绿态、回退顺序变异均 **INCOMPLETE**：没有修复候选，未做变异；本次已知坏基线上的 F1 断言红态不能冒称为修后变异。完整日历覆盖、T-136 与 T-137 当前日期 E2E 均未运行；触发用户停止条件后，没有继续启动大场景。未调用真实供应商模型，未连接或启动任何 Herdr/hc core。

| 验收/交付项 | 状态 | 证据或未完成原因 |
| --- | --- | --- |
| 测试前写失败方式清单 | PASS | `FAILURE-MODES.md`，先于探针创建 |
| 修前真实 due() 红态 | PASS | `red-due.log`，预期 F1 断言失败，退出 1 |
| 修后春季结果为 07:30Z | BLOCKED | 历史 key 风险触发用户停止条件，未改代码 |
| 目标跳过日、秋季重复时刻、普通日、月末、年末 | INCOMPLETE | 手工期望已列，修后验证未执行 |
| 规则写入代码注释与 README | BLOCKED | 建议及标准依据见上，未决定落地 |
| 生效边界、已运行去重等补充覆盖 | INCOMPLETE | 只运行历史错误 key 的隔离探针 |
| 先 setHours 后 setDate 的变异被新断言杀死 | INCOMPLETE | 无修后候选，未做变异 |
| T-136 当前日期 E2E | INCOMPLETE | 未运行，不沿用 T-221 通过结论 |
| T-137 当前日期 E2E | INCOMPLETE | 未运行，不沿用 T-221 通过结论 |
| agy 独立只读审查 | INCOMPLETE | 按用户要求由主控安排，本会话未做 |
| git diff --check | PASS | `final-diff-check.log`，退出 0；当前差异为空 |
| project-map status | PASS | 开始与结束均 Problems 0 / Stale living docs 0；结束输出见日志 |
| 不改地图、存储及去重、不 commit/push | PASS | `final-git-status.log` 为空，HEAD 保持基线 |
| 中文报告与 candidate.patch | PASS | 本报告及空差异快照已交付；修复交付整体仍 BLOCKED |

## 每次运行命令与复跑

以下行为探针均从 T-223 worktree 执行，脚本使用相邻目录的真实源码，不依赖 T-221 路径。表中的退出码是探针进程本身的退出码；首次运行用 shell 重定向保存 stdout/stderr，再追加 `exit_code=$?`。

| 次序 | 命令 | 结果/保存位置 |
| --- | --- | --- |
| 1 | `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` | 开始核对，退出 0，Problems 0 / Stale 0；原始输出在会话工具记录 |
| 2 | `TMPDIR=/private/tmp TZ=America/New_York node /Users/luckye/Documents/Code/a2a-worktrees/T-223-evidence/probe_due.mts red` | 退出 1，`red-due.log` |
| 3 | `TMPDIR=/private/tmp TZ=America/New_York node /Users/luckye/Documents/Code/a2a-worktrees/T-223-evidence/probe_due.mts history` | 退出 0，`history-risk.log` |
| 4 | `TMPDIR=/private/tmp git diff --check` | 退出 0，`final-diff-check.log` |
| 5 | `TMPDIR=/private/tmp python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` | 退出 0，`final-project-map-status.log` |
| 6 | `TMPDIR=/private/tmp git status --short` | 退出 0，无输出，`final-git-status.log` |
| 7 | `TMPDIR=/private/tmp git diff --binary HEAD` | 退出 0，输出保存为 `candidate.patch`，0 字节 |

复跑第 2、3 条即可重现红态与风险。`history` 模式明确断言源码仍为旧行为；未来修复后该模式会拒绝把新实现当作旧基线，应在此完整基线上复跑。请把复跑输出保存到新文件名，保留本次原始证据。第 4～7 条可直接重新核对工作树。

探针仅使用内存 SQLite；传入 `/private/tmp/t223-unused-no-files` 仅作为必需 root 字符串，没有调用 `prepare()` 或创建目录。db 在 finally 关闭，未生成磁盘夹具，无待清理的成功夹具或 /private/tmp 失败现场。失败证据是目录内的 `red-due.log`、探针脚本及其固定输入，均已保留。`history-risk.log` 中的 run 为合成隔离记录，不是用户数据。

本报告与脚本为 UTF-8、无 BOM、LF；保存后回读核对。范围内工作停在用户指定决策边界，未将 BLOCKED 上调为 PASS。


## 第二轮

本轮实现与本地验证 **PASS**；票面整体 **INCOMPLETE**，唯一未执行的票面验收为主控负责安排的 agy 独立只读审查。以下是第二轮结束时的当前状态，第一轮记录保持原文。

### 继续依据与范围

本轮用户消息明确传达主控核对后的决定：“结论是按原范围继续”，并要求保留精确字符串去重、采用已建议的 ECMAScript 规则。主控给出的前提是定期复盘在 2026-10-22 上线之后还未经历相关春季跳过日，所以第一轮合成历史风险不代表用户库已存在该记录。本会话依据本轮明确授权继续，不修改去重、存储或历史记录，也没有重新运行只适用于旧实现的 `probe_due.mts history`。

基线与分支未变：`76f969963f6ee582460d357c317cb30b203bebe6`，`t223-due-spring-gap`。未 commit、push，未改 `.project-map/` 或其他 worktree。运行入口固定 `TMPDIR=/private/tmp`；日期测试另显式 `TZ=America/New_York`。现有 Electron 构建脚本在测试自己创建的 `/private/tmp/a2a-build-*` 目录内使用其临时子目录，成功后由现有测试清理。

### 最小修复与规则

候选只有三份文件：

- `workbench/src/retrospective.ts`：先 `setDate` 选择目标日历日期，再 `setHours` 设置所请求的墙钟时刻；若本周未到点，退七天后再次应用日程里的原始小时、分钟。这样，跳过日上规范成的 03:30 不会被带到上周普通日。生效边界和精确 ISO 字符串去重保持原有代码。
- `workbench/README.md`：复盘日程段只写现行计算规则、春秋示例与既有去重行为，没有历史说明。
- `workbench/tests/test_t223_retrospective_due.ts`：新增 26 项真实 `Retrospectives.due()` 测试，每项独立内存 SQLite，手算期望写死；无日期算法副本，无后台、CLI、PTY 或模型调用。保存每项输入、实际值、断言与堆栈，报告文件使用独占创建，防止覆盖证据。

代码注释与 README 均采用 [ECMAScript UTC(t)](https://tc39.es/ecma262/multipage/numbers-and-dates.html#sec-utc-t) 的规则：不存在时刻用转换前偏移解释，向前顺延跳过的时长；重复时刻取较早一次。纽约 2026-03-08 的 02:30 因而是 03:30 EDT（07:30Z）；2026-11-01 的 01:30 取第一次 EDT（05:30Z）。这与第一轮查阅的标准及本轮明确指定的规则一致。

没有依赖、异常处理、重试、兜底、兼容分支、新接口或存储改动。仍沿用 Ubiquitous language；直接修复现有领域方法，不增加浅包装，符合 Deep modules。此次没有新的跨层功能，无需新增 Tracer bullet。

### 红态、绿态与两个变异

| 运行 | 结果 | 证据 |
| --- | --- | --- |
| 修改产品前，在原工作树基线源码上运行新增测试 | 26 项中 6 项断言失败，进程退出 1；首个失败为 F1，实际 08:30Z、期望 07:30Z | `r2-baseline-due.json`、`r2-baseline-due.log` |
| 从完整 Git 基线导出真实模块后再次运行同一测试 | 同样 6 项失败，首个为 F1；导出版本明确固定完整 SHA | `r2-exported-baseline/summary.json`、`due.json`、`due.log` |
| 完整修复候选 | 26/26 PASS，退出 0 | `r2-green-due.json`、`r2-green-due.log` |
| 变异 A：将本周目标的顺序改回先 setHours 后 setDate，保留回退分支修复 | F1 及相关 3 个 F11 场景失败；F1 的断言实际 08:30Z、期望 07:30Z，退出 1 | `r2-mutants/hours-before-date.json`、`.log` |
| 变异 B：只保留前两行的顺序修正，回退七天仍使用原第 61 行 | 两个 F4 场景失败，实际 03-01 08:30Z、期望 03-01 07:30Z，退出 1；F3 本身仍通过 | `r2-mutants/only-first-two-lines-fixed.json`、`.log` |

基线的六个失败为 F1、两个 F4、F11 同项目去重、F11 其他项目不阻挡、F11 手动记录不阻挡。所有失败都发生在测试中的真实结果与手工期望比较断言，不是导入、配置或运行环境错误。基线重放与两个变异脚本在确认预期失败被捕获后自身退出 0；其所运行测试进程的退出码 1 另有记录，不混为绿色产品结果。

变异运行在独立源码副本中，不替换候选文件；失败副本按要求保留。没有复用第一轮输出替第二轮背书。

### 失败方式覆盖与当前验收

| 条目 | 当前状态 | 本轮证据 |
| --- | --- | --- |
| F1：跳过日当天查询此前周一 | PASS | 期望 `2026-03-02T07:30:00.000Z`；基线红、候选绿、变异 A 红 |
| F2：目标日就是跳过日 | PASS | 当天规范后的 03:30 EDT 和次日查询均得到 `2026-03-08T07:30:00.000Z` |
| F3：回退一周落到跳过日 | PASS | 03-15 01:30 EDT 查询周日 02:30，得到 03-08 07:30Z |
| F4：规范时刻未到，回退一周不能保留错误的小时 | PASS | 03-08 03:00 及 03:29:59.999 EDT 查询均得到 03-01 07:30Z；变异 B 被这两项拦住 |
| F5：秋季重复时刻 | PASS | 第一次、两次之间、重复结束后都取 11-01 05:30Z；第一次之前取 10-25 05:30Z |
| F6：普通日 | PASS | 夏季 03-16 06:30Z、冬季 12-14 07:30Z |
| F7：月末 | PASS | 04-01 查询得到 03-30 06:30Z |
| F8：年末 | PASS | 2027-01-01 查询得到 2026-12-28 07:30Z |
| F9：生效时刻边界 | PASS | 生效时刻恰等于 slot 可触发，晚 1ms 返回 null |
| F10：到点与禁用边界 | PASS | 到点前取上周；等于、晚 1ms 取本周；disabled 返回 null |
| F11：去重、项目隔离、手动记录 | PASS | 同项目已跑不触发；其他项目、手动记录、另一周不阻挡；秋季第二次和跳过日次日不重复 |
| 修前真实 due 红态（票面第 1 项） | PASS | 两轮红态均保留，第二轮仓库测试在完整基线上拒绝旧行为 |
| 修后春季值、日历覆盖及规则注释/README（票面第 2 项） | PASS | 26 项全绿，规则写入两处；期望独立手算 |
| 两个指定变异 | PASS | 变异 A 由 F1、变异 B 由 F4 拒绝 |
| T-136 当前日期 E2E（票面第 3 项之一） | PASS | 2026-11-01 运行，13 项检查，退出 0 |
| T-137 当前日期 E2E（票面第 3 项之二） | PASS | 2026-11-01 运行，10 项检查，退出 0 |
| agy 独立只读审查（票面第 4 项） | INCOMPLETE | 用户指定由主控安排；本 worker 未做独立审查，不自行补称通过 |
| git diff --check | PASS | `r2-diff-check.log`，退出 0 |
| project-map status | PASS | `r2-project-map-status.log`，Problems 0 / Stale living docs 0，退出 0 |
| 候选冻结、包含新增文件 | PASS | `candidate-round2.patch`，10,562 字节；隔离基线上检查、应用并逐字节核对三份文件一致 |
| 不改地图、存储及去重，不 commit/push | PASS | `r2-git-status.log` 只有本轮三份文件；HEAD 保持基线 |

当前代码与文档的版本以冻结补丁为准。第二轮没有独立审查结论或发布结论；本地通过不代替 agy 审查。

### 当前日期回归与夹具

T-136：`r2-t136-summary.json` 状态 PASS、13 项检查。保存的日程在 2026-11-01 生效，注入 11-03 当地 10:00（15:00Z）时开始一次，提前一分钟不开始、同一时刻不重复、关闭后下一周不开始。测试还核对复盘包、权限、导入、建议、归档和启动失败范围。

T-137：`r2-t137-summary.json` 状态 PASS、10 项检查。覆盖 Reflect 会话树、结束角色、归属与分数、所选执行者的定期复盘、手动复盘入口、重启后保留设置。两个 E2E 均使用既有本地 scripted Messages 服务，不调用真实供应商模型；没有使用 Herdr 或 hc default core。

成功夹具 `/private/tmp/t136-e8so05d3`、`/private/tmp/t137-gyif2gj7` 已在测试自行停止后台与 Electron 后删除；其 `out/` 内容分别保存在 `r2-t136-artifacts/`、`r2-t137-artifacts/`，含截图和 Electron 日志，另有 `r2-t136-cleanup.json`、`r2-t137-cleanup.json`。原摘要里的 fixture 路径是运行当时的现场，成功现场已清理，交付证据以保留路径为准。成功补丁检查夹具也已清理。

以下是预期失败并保留的源码现场，无供应商凭据、用户数据或活跃后台：

- 明确基线红态：`/private/tmp/t223-baseline-alcq26p6`。
- 顺序变异 A：`/private/tmp/t223-hours-before-date-ycjrc31l`。
- 不完整修复变异 B：`/private/tmp/t223-only-first-two-lines-fixed-mzvmctan`。

候选全绿测试仅使用内存 SQLite，不创建磁盘数据库或目录，数据库逐项关闭。第一轮所有文件保持原样；本报告只追加本节。

### 第二轮运行命令与复跑

下列命令工作目录均为 `/Users/luckye/Documents/Code/a2a-worktrees/T-223`。为缩短书写，`E` 表示 `/Users/luckye/Documents/Code/a2a-worktrees/T-223-evidence`；这是任务路径变量，不改变 HOME 等系统变量。原始 stdout/stderr 与测试进程退出码保存在各自日志，脚本和 JSON 保存了完整 argv、输入与结果。

| 运行顺序 | 命令（E 展开为上述目录） | 产物 / 退出码 |
| --- | --- | --- |
| 1 | `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` | 会话开始检查，退出 0，Problems 0 / Stale 0 |
| 2 | `TMPDIR=/private/tmp TZ=America/New_York node workbench/tests/test_t223_retrospective_due.ts . "$E/r2-baseline-due.json"` | 产品修改前红态，`r2-baseline-due.log`，退出 1 |
| 3 | `TMPDIR=/private/tmp TZ=America/New_York node workbench/tests/test_t223_retrospective_due.ts . "$E/r2-green-due.json"` | 修后绿态，`r2-green-due.log`，退出 0 |
| 4 | `TMPDIR=/private/tmp python3 "$E/r2_mutants.py" --output "$E/r2-mutants"` | 两个预期变异被杀死，脚本退出 0；内部测试各退出 1 |
| 5 | `TMPDIR=/private/tmp python3 workbench/tests/test_t136_retrospective_e2e.py --summary "$E/r2-t136-summary.json"` | `r2-t136.log`，退出 0 |
| 6 | `TMPDIR=/private/tmp python3 workbench/tests/test_t137_reflect_e2e.py --summary "$E/r2-t137-summary.json"` | `r2-t137.log`，退出 0 |
| 7 | `TMPDIR=/private/tmp python3 "$E/r2_baseline.py" --output "$E/r2-exported-baseline"` | 从固定完整基线导出真实模块再取得红态；脚本退出 0，内部测试退出 1 |
| 8 | `TMPDIR=/private/tmp git diff --check` | `r2-diff-check.log`，退出 0 |
| 9 | `TMPDIR=/private/tmp python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` | `r2-project-map-status.log`，退出 0 |
| 10 | `TMPDIR=/private/tmp git status --short` | `r2-git-status.log`，退出 0 |
| 11 | `TMPDIR=/private/tmp git diff --binary HEAD`，接上 `TMPDIR=/private/tmp git diff --no-index --binary -- /dev/null workbench/tests/test_t223_retrospective_due.ts` 的 stdout | 顺序写入新 `candidate-round2.patch`；前者退出 0，后者退出 1（表示新文件差异），不是错误 |
| 12 | 隔离目录放入 `git show HEAD:workbench/README.md`、`git show HEAD:workbench/src/retrospective.ts` 后执行 `git apply --check "$E/candidate-round2.patch"`，再执行 `git apply "$E/candidate-round2.patch"` | 两次退出 0；逐字节比较三份候选文件一致，见 `r2-patch-check.log` |

当前复跑绿态用第 3 条并换成全新的输出文件名。复跑基线红态用第 7 条；复跑变异用第 4 条，均换新的输出目录，不覆盖任何已有证据。两个辅助脚本只往新建 `/private/tmp/t223-*` 源码副本写入，不改候选；基线脚本固定完整 SHA，变异脚本要求定位唯一并检查指定断言失败。E2E 用第 5、6 条并换新 summary 文件名，成功后按 cleanup 记录的办法保留 `out/` 再清理自己创建的 fixture。

补丁的新增文件由 `--no-index` 差异显式加入，没有暂存文件或修改 Git index。第一轮的空 `candidate.patch` 仍保留，第二轮审查应使用 `candidate-round2.patch`。

完成前检查三份候选文件和追加报告均为 UTF-8、无 BOM、LF，无替换字符；报告原有 12,388 字节前缀逐字节保持不变。本轮状态与限制另存 `r2-run.json`。


## 第三轮

本轮实现与本地验证 **PASS**；票面整体仍为 **INCOMPLETE**，第三轮冻结候选尚无主控提供的独立复验结论。本节是第三轮结束时的当前状态，不沿用第二轮通过结论替新候选背书。前两轮原文完整保留。

### 回归、范围与最小修复

主控在第二轮审查后将午夜跳过问题改判阻塞，并经真实 due() 复现。本会话只读核对主控目录的 `nuuk-probe.ts`、`nuuk-probe.log`，没有修改主控或审查目录。主控关于上线后窗口不存在向前转换的说明作为继续授权的背景，本会话没有另行宣称扫描了所有时区或访问了用户库。

第二轮回归的根因：`new Date(now)` 带入查询时刻的时分，随后 `setDate` 去目标日期。如果目标日期的这个墙钟时刻不存在，而且跳过延到午夜，中间值就被推到第二天。之后设置日程时分只能得到第二天的日程，去重 key 也随之变化。原来的回退分支还使用已经规范化的 `slot.getDate()`，会把规范后的星期日当成目标星期六再退一周。

当前 `due()` 仅从 `now` 读取本地年、月、日期和星期，用数字日历日期计算 `day - back`；用 `new Date(year, month, day, schedule.hour, schedule.minute, 0, 0)` 一次构造目标时刻。未到点时从同一组数字年月日再构造 `day - 7` 的上周日程。MakeDay 先按数字日期处理月末、年末溢出，最后才做 UTC(t) 转换，不经过携带查询时分的中间 Date，也没有正午或其他锚点。

保留 [ECMAScript UTC(t)](https://tc39.es/ecma262/multipage/numbers-and-dates.html#sec-utc-t) 既有规则：不存在时刻按转换前偏移解释、向前顺延跳过时长；重复时刻取较早一次。代码注释写明为何不携带查询时刻，README 补充直接构造与回退重构的现行语义，没有历史说明。精确 ISO 字符串去重、生效边界、存储格式都未改；没有依赖、兼容分支、重试、兜底或新接口。

候选仍只有三份文件：`workbench/src/retrospective.ts`、`workbench/README.md`、`workbench/tests/test_t223_retrospective_due.ts`。没有修改 `.project-map/`；分支仍是 `t223-due-spring-gap`，HEAD 仍为 `76f969963f6ee582460d357c317cb30b203bebe6`，未 commit、push。

### F12 清单、时区与手算过程

先在 `FAILURE-MODES.md` 末尾追加了第三轮 F12，再修改测试及修复产品。第一轮清单中旧编号 F12 的历史记录风险原文不动；从第三轮起 F12 明确指“查询墙钟时间在目标日期不存在，且跳过延至午夜，计算结果落错日”。

测试入口现在显式接收 `ZONE`，要求它与 `process.env.TZ` 完全一致，并只接受三组已定义时区：America/New_York、America/Nuuk、America/Scoresbysund。错设 TZ 的负例在导入产品前被断言拒绝，退出 1，未产生假绿色报告，见 `r3-wrong-tz.log`。

纽约原有 26 项输入和写死的期望值全部保留；与 `r2-green-due.json` 的原 cases 数组逐项直接比较一致。Nuuk 新增 12 项，Scoresbysund 对主控给出的同类转换再运行同样 12 项，共 50 项。都直接调用真实 `Retrospectives.due()`，各用独立内存 SQLite，没有复制日期算法、调用后台、CLI 或供应商模型。存储行只作为既有去重数据，测试输出保留实际值、期望值和断言堆栈。

手算采用主控给出的转换：2026-03-28 周六 23:00（-02）直接跳到 03-29 周日 00:00（-01）；2027-03-27 相同。

| 场景 | 日历与偏移推算 | 固定期望 |
| --- | --- | --- |
| 周六 10:00，03-29 或 04-02 的 23:30（-01）查询 | 最近周六是 03-28；上午仍是 -02，10:00 加 2 小时 | `2026-03-28T12:00:00.000Z` |
| 同项目已记录上述周六时刻 | 正确目标 key 已被使用 | `null` |
| 周六 23:30 本身在跳过段，03-29 中午查询 | 03-28 23:30 按转换前 -02 解释，加 2 小时；它是周日 00:30（-01） | `2026-03-29T01:30:00.000Z` |
| 在顺延后时刻之前：03-29 00:15（-01） | 此时是 01:15Z，未到 01:30Z；退至 03-21 周六 23:30（-02），加 2 小时 | `2026-03-22T01:30:00.000Z` |
| 恰在顺延后时刻：03-29 00:30（-01） | 正好 01:30Z，可触发本周 | `2026-03-29T01:30:00.000Z` |
| 下一周周六到点前：04-04 23:29:59.999（-01） | 本周 23:30 尚未到，重新构造上周缺失时刻 | `2026-03-29T01:30:00.000Z` |
| 下一周周六到点：04-04 23:30（-01） | 普通日 23:30 加 1 小时 | `2026-04-05T00:30:00.000Z` |
| 顺延后的目标 key 已记录 | 记录里有 03-29 01:30Z，不重复 | `null` |
| 2027-03-28 深夜查询周六 10:00 | 最近周六 03-27 10:00 仍是 -02，加 2 小时 | `2027-03-27T12:00:00.000Z` |
| 2027 顺延后时刻之前：03-28 00:15（-01） | 退至 03-20 周六 23:30（-02），加 2 小时 | `2027-03-21T01:30:00.000Z` |

另保留跳过前周六上午查询的普通对照。上述期望先按日历写死，没有取实现运行结果充当答案。

### 第二轮已知坏实现、基线与绿态

`r3_run.py round2` 从固定完整基线导出真实模块，应用原封保留的 `candidate-round2.patch`，再使用新增用例运行；不是在第三轮源码上凭空模拟第二轮。该快照纽约 26 项全绿，Nuuk 与 Scoresbysund 各 7 项失败，退出码均为 1。首个 Nuuk 失败实际为周日 `2026-03-29T11:00:00.000Z`，而应是周六 `2026-03-28T12:00:00.000Z`。已跑过周六的用例也返回这个错误 key，直接证实重复运行风险。

以下合并展示两个午夜跳过时区完全相同的失败值；两组的全部原始记录分别保存在各自 JSON/log 中。`null` 表示不应运行。

| 时区 | 失败项 | 实际值 | 手算期望 |
| --- | --- | --- | --- |
| Nuuk / Scoresbysund | F12/sunday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| Nuuk / Scoresbysund | F12/thursday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| Nuuk / Scoresbysund | F12/already-ran-Saturday | 2026-03-29T11:00:00.000Z | null |
| Nuuk / Scoresbysund | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/2027-sunday-late-query | 2027-03-28T11:00:00.000Z | 2027-03-27T12:00:00.000Z |
| Nuuk / Scoresbysund | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |

`r3_run.py baseline` 固定导出 `76f969963f6ee582460d357c317cb30b203bebe6`，纽约仍是 F1、两个 F4 及三个 F11 断言失败（6 项）；Nuuk 与 Scoresbysund 的两个普通周六 10:00 深夜查询及对应去重都正确，但“顺延后时刻未到，退至上一周”在 2026 和 2027 各失败一次。不能把基线的整个 Nuuk 组写成通过。

| 时区 | 失败项 | 实际值 | 手算期望 |
| --- | --- | --- | --- |
| America/New_York | F1/spring-query-for-earlier-Monday | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F4/gap-query-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| America/New_York | F4/one-ms-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| America/New_York | F11/already-ran-same-project | 2026-03-02T08:30:00.000Z | null |
| America/New_York | F11/other-project-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F11/manual-run-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| Nuuk / Scoresbysund | F12/before-normalized-slot | 2026-03-22T02:30:00.000Z | 2026-03-22T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/2027-before-normalized-slot | 2027-03-21T02:30:00.000Z | 2027-03-21T01:30:00.000Z |

完整第三轮候选三组全绿：纽约 26/26，Nuuk 12/12，Scoresbysund 12/12，各退出 0；结果见 `r3-green/summary.json` 与对应时区的 JSON/log。原有 F1–F11 全部通过，F12 的正常目标、缺失时刻、回退、边界和去重均通过。所有红态都失败在 `assert.equal(actual, c.expected, c.name)`，没有用导入失败或环境错误充当回归证据。

### 三个变异及实际失败值

变异在独立源码副本中运行，未替换当前候选；失败现场全部保留。`r3_mutants.py` 对三组时区都运行，并要求每个变异被指定断言杀死；脚本自身退出 0 表示预期反例已捕获，不表示其内部产品测试通过。完整命令、失败值、断言堆栈见 `r3-mutants/*/`；汇总见 `r3-mutants/summary.json` 与 `r3-failure-values.md`。

变异 A（`hours-before-date`）：把目标构造改回 `new Date(now)`，先设置日程时分再回退目标日期；回退一周仍重设时分。应由纽约 F1 拒绝，实际纽约失败 4 项、Nuuk 和 Scoresbysund 各失败 3 项；三个测试进程均退出 1。

| 时区 | 失败项 | 实际值 | 手算期望 |
| --- | --- | --- | --- |
| America/New_York | F1/spring-query-for-earlier-Monday | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F11/already-ran-same-project | 2026-03-02T08:30:00.000Z | null |
| America/New_York | F11/other-project-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| America/New_York | F11/manual-run-does-not-block | 2026-03-02T08:30:00.000Z | 2026-03-02T07:30:00.000Z |
| Nuuk / Scoresbysund | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |

变异 B（`date-only-rollback`）：保留完整候选的直接构造，只把“回退一周”改为 `slot.setDate(slot.getDate() - 7)`，不重新构造日程时刻。应由纽约 F4 拒绝，实际纽约、Nuuk、Scoresbysund 各失败 2 项，三个测试进程均退出 1。

| 时区 | 失败项 | 实际值 | 手算期望 |
| --- | --- | --- | --- |
| America/New_York | F4/gap-query-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| America/New_York | F4/one-ms-before-normalized-slot | 2026-03-01T08:30:00.000Z | 2026-03-01T07:30:00.000Z |
| Nuuk / Scoresbysund | F12/before-normalized-slot | 2026-03-22T02:30:00.000Z | 2026-03-22T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/2027-before-normalized-slot | 2027-03-21T02:30:00.000Z | 2027-03-21T01:30:00.000Z |

变异 C（`query-clock-round2`）：直接从原 `candidate-round2.patch` 还原 `new Date(now)` 加 `setDate` 再 `setHours` 的第二轮实现。应由新的 Nuuk F12 拒绝，实际纽约 26 项通过，Nuuk 与 Scoresbysund 各失败 7 项，后两组退出 1。各项实际值如下，与第二轮已知坏快照一致。

| 时区 | 失败项 | 实际值 | 手算期望 |
| --- | --- | --- | --- |
| Nuuk / Scoresbysund | F12/sunday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| Nuuk / Scoresbysund | F12/thursday-late-query | 2026-03-29T11:00:00.000Z | 2026-03-28T12:00:00.000Z |
| Nuuk / Scoresbysund | F12/already-ran-Saturday | 2026-03-29T11:00:00.000Z | null |
| Nuuk / Scoresbysund | F12/before-normalized-slot | 2026-03-23T01:30:00.000Z | 2026-03-22T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/next-week-before-slot | 2026-03-30T00:30:00.000Z | 2026-03-29T01:30:00.000Z |
| Nuuk / Scoresbysund | F12/2027-sunday-late-query | 2027-03-28T11:00:00.000Z | 2027-03-27T12:00:00.000Z |
| Nuuk / Scoresbysund | F12/2027-before-normalized-slot | 2027-03-22T01:30:00.000Z | 2027-03-21T01:30:00.000Z |

### 当前日期 E2E、清理异常与证据

2026-11-01 对第三轮候选各运行一次：T-136 的 13 项检查 PASS，退出 0；T-137 的 10 项检查 PASS，退出 0。T-136 的到点日程为 11-03 当地 10:00（15:00Z），提前不触发、到点触发一次、再次查询不重复、关闭后下一周不触发；T-137 的定期复盘在 11-02 当地 09:00（14:00Z）按所选执行者启动，手动复盘和重启后保留设置均通过。摘要分别为 `r3-t136-summary.json`、`r3-t137-summary.json`，原始测试 stdout/stderr 与退出码在同名 `.log` 中；截图和 Electron 日志保留在对应 `r3-*-artifacts/`。

清理发生过一次异常，和产品测试结果分开报告：T-136 已退出 0、输出目录已复制并逐字节核对后，首次 `shutil.rmtree()` 在 `home` 上报 `OSError: [Errno 66] Directory not empty`，运行两份 E2E 的外层编排脚本因此退出 1，T-137 当时尚未启动。没有把这个外层退出码当作产品回归，也没有重跑或覆盖已通过的 T-136；随后用独立命令运行 T-137。

异常详情和当时剩余文件、路径匹配进程检查保存在 `r3-t136-cleanup-anomaly.json`；当时未发现命令行引用该夹具路径的进程，确切写入原因未确认。首次删除已移除部分目录，所以留下的是“剩余现场”，不冒称完整原夹具。剩余 93 个文件、2,797,970 字节保存在 `r3-t136-cleanup-remains/`，在复制与逐字节核对后清理原测试目录 `/private/tmp/t136-nm7m0cmw`，当前清理结果和清单见 `r3-t136-cleanup.json`。T-137 成功夹具 `/private/tmp/t137-t9fgcssm` 正常清理，清单见 `r3-t137-cleanup.json`。没有为此修改产品或测试夹具实现，没有忽略或删除清理失败证据。

日期测试仅使用内存 SQLite；预期失败源码现场保留：

- 基线：`/private/tmp/t223-r3-baseline-5e_dxin6`。
- 第二轮已知坏实现：`/private/tmp/t223-r3-round2-umx9lk03`。
- 变异 A：`/private/tmp/t223-r3-hours-before-date-al0i5geq`。
- 变异 B：`/private/tmp/t223-r3-date-only-rollback-9om0wvq7`。
- 变异 C：`/private/tmp/t223-r3-query-clock-mutant-bn3veljc`。

成功的补丁应用检查夹具已清理。前两轮证据保持原样；第一轮 `history` 探针未重跑。没有连接或启动 Herdr、hc default core，没有写用户全局配置或调用真实供应商模型；E2E 沿用现有本地 scripted Messages 服务。

### 每条验收当前状态

| 条目 | 当前状态 | 依据 |
| --- | --- | --- |
| 原票面修前纽约红态 | PASS | 第三轮固定基线仍由 F1、F4 等断言拒绝，原始输出独立留存 |
| 原票面修后春季值、目标跳过日、秋季重复、普通日、月末、年末 | PASS | 纽约原 26 项完全保留并全部通过 |
| 规则与依据写入注释和 README | PASS | 按数字日历日期直接构造，无查询时分中间值；UTC(t) 歧义规则不变 |
| F12 测试前清单 | PASS | `FAILURE-MODES.md` 末尾第三轮部分，先于新测试与产品修复 |
| 第二轮候选新回归的真实红态 | PASS | 应用原冻结补丁，两个午夜跳过时区各失败 7 项，包括正常周六去重 |
| Nuuk 两个指定深夜查询及已运行去重 | PASS | 候选均取周六 12:00Z；已运行返回 null |
| Nuuk 缺失时刻、未到点回上周、下周普通情况 | PASS | 三种时刻的手算与写死期望见上表，全绿 |
| 原 F1–F11 全部保留 | PASS | 原 26 项 cases 与第二轮数组直接比较一致；F1–F11 都通过 |
| 每组显式 TZ、错误 TZ 拒绝 | PASS | 三组分进程显式设置；不匹配断言的负例退出 1 |
| 基线全部实际结果如实记录 | PASS | 纽约失败 6 项；Nuuk、Scoresbysund 各失败 2 项，不上调为通过 |
| 三个指定变异 | PASS | A 被 F1、B 被 F4、C 被 Nuuk F12 断言拒绝，失败值已列 |
| 当前日期 T-136 E2E | PASS | 13 项检查，进程退出 0；清理异常另存，不混作产品失败或隐藏 |
| 当前日期 T-137 E2E | PASS | 10 项检查，进程退出 0 |
| 成功夹具清理与失败现场保留 | PASS | 原成功夹具已清理；T-136 剩余异常现场及全部预期失败源码副本保留 |
| git diff --check | PASS | `r3-diff-check.log`，退出 0 |
| project-map status | PASS | `r3-project-map-status.log`，Problems 0 / Stale living docs 0 |
| `candidate-round3.patch` 含新增文件、能应用到基线 | PASS | 13,820 字节；检查、应用均退出 0，三份候选文件逐字节一致 |
| 原票面独立审查无未处理阻塞意见 | INCOMPLETE | 本轮已修主控指出的阻塞行为，但新冻结候选仍需主控独立复验；不替主控宣布关闭 |
| 不改地图/存储/去重，不 commit/push | PASS | `r3-git-status.log` 仅三份候选文件，HEAD 不变 |
| 中文报告只追加第三轮 | PASS | 前两轮 24,513 字节完整保留，追加后直接核对前缀一致 |

### 本轮命令与复跑

工作目录：`/Users/luckye/Documents/Code/a2a-worktrees/T-223`。下表的 `E` 表示 `/Users/luckye/Documents/Code/a2a-worktrees/T-223-evidence`，`ZONE` 逐一取三个组名。所有新报告独占创建，复跑须换新的输出文件或目录，不覆盖本轮或前两轮证据。

| 顺序 | 命令 / 操作 | 结果与产物 |
| --- | --- | --- |
| 1 | `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` | 本轮开始，退出 0，Problems 0 / Stale 0 |
| 2 | `TMPDIR=/private/tmp python3 "$E/r3_run.py" round2 --output "$E/r3-round2-red"` | 导出固定基线并应用第二轮补丁；纽约退出 0，其余各退出 1；外层脚本检查到预期红态后退出 0 |
| 3 | `TMPDIR=/private/tmp python3 "$E/r3_run.py" baseline --output "$E/r3-baseline"` | 三组测试均退出 1，完整值见各组 JSON/log；外层脚本确认预期基线红态后退出 0 |
| 4 | `TMPDIR=/private/tmp python3 "$E/r3_run.py" candidate --output "$E/r3-green"` | 三组测试均退出 0，50/50 通过；外层脚本退出 0 |
| 5 | `TMPDIR=/private/tmp python3 "$E/r3_mutants.py" --output "$E/r3-mutants"` | A、B、C 都被指定断言拒绝；三组原始输出分目录；外层脚本退出 0 |
| 6 | `TMPDIR=/private/tmp TZ=America/New_York node workbench/tests/test_t223_retrospective_due.ts . "$E/r3-wrong-tz-should-not-exist.json" America/Nuuk` | 不匹配 TZ，预期退出 1；`r3-wrong-tz.log`，没有生成 JSON |
| 7 | `TMPDIR=/private/tmp python3 workbench/tests/test_t136_retrospective_e2e.py --summary "$E/r3-t136-summary.json"` | 退出 0；`r3-t136.log`；后续首次清理失败另记，并未覆盖该结果 |
| 8 | `TMPDIR=/private/tmp git diff --check` | `r3-diff-check.log`，退出 0 |
| 9 | `TMPDIR=/private/tmp python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` | `r3-project-map-status.log`，退出 0 |
| 10 | `TMPDIR=/private/tmp git status --short` | `r3-git-status.log`，退出 0 |
| 11 | `TMPDIR=/private/tmp git diff --binary HEAD` 的 stdout 接上 `TMPDIR=/private/tmp git diff --no-index --binary -- /dev/null workbench/tests/test_t223_retrospective_due.ts` 的 stdout | 新建 `candidate-round3.patch`，后一个命令退出 1 表示新文件差异；没有暂存或修改 index |
| 12 | 在本轮自己的隔离基线文件目录中执行 `git apply --check "$E/candidate-round3.patch"`，然后 `git apply "$E/candidate-round3.patch"` | 两次退出 0；三份文件直接逐字节比较相同，`r3-patch-check.log` |
| 13 | `TMPDIR=/private/tmp python3 workbench/tests/test_t137_reflect_e2e.py --summary "$E/r3-t137-summary.json"` | 退出 0；`r3-t137.log`；成功夹具正常清理 |

每组测试的底层可直接复跑命令为：`TMPDIR=/private/tmp TZ="$ZONE" node workbench/tests/test_t223_retrospective_due.ts PRODUCT NEW_OUTPUT.json "$ZONE"`。`r3_run.py` 保存了每次完整 argv、真实源码路径、Node 版本、TZ、TMPDIR、用例输入、实际值、期望与堆栈；其快照来自固定完整基线或原第二轮补丁，无供应商依赖。请用第 2、3 条重放旧行为，第 4 条验证当前候选，第 5 条重做三个变异，并使用新的输出路径。测试入口新增必传的 ZONE，前两轮旧命令应针对其各自冻结快照使用，本节命令用于当前第三轮测试入口。

清理过程使用 `shutil.copytree` 保留测试 `out/`、逐字节比较文件后 `shutil.rmtree`；T-136 异常后另用 `ps -axo pid,ppid,command` 仅筛选本次 fixture 路径核对进程，将剩余目录复制至新证据目录、核对文件数和字节、逐字节比较后再清理。没有操作其他任务的测试目录。所有这些本地证据操作均以 `TMPDIR=/private/tmp` 执行。

第三轮审查应使用 `candidate-round3.patch`；前两轮补丁不覆盖。候选源码、README、新测试和追加报告均检查为 UTF-8、无 BOM、LF、无替换字符。本轮元数据见 `r3-run.json`；保留的清理异常不影响 50 项日历测试与两份真实 E2E 的通过结论，也不补称第三轮独立审查已通过。
