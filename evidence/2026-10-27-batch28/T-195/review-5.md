# T-195 独立只读审查（第 5 轮）

## STATUS

**INCOMPLETE**。**R4-F1、R4-F2 的定向关闭复核均为 PASS，本轮没有确认的新发现。** 但冻结候选的完整 CLI e2e 在前 8 项通过后，等待终端 Claude 报会话号超时；本轮不能给出整套运行通过的结论。该停点与 R4 一致，原因仍未知，不据此认定为本轮差异引入的产品缺陷。

TARGET：`/private/tmp/t195-cand5`，完整 HEAD `bf16c21d5a7a155f57b62cde1b55e0c62eab90ad`。仅审 `ed5a63b → bf16c21` 的 3 个文件及 R4 两项关闭情况；不验收 T-194、T-193 或整票发布。实际差异保存为 [candidate.diff](candidate.diff)。

验收依据为 [T-195 ticket](/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-195-copy-native-session-link.md)、本轮 brief、[R4 报告](/private/tmp/t195-review4/REPORT.md)：复制 CLI 自己的当前会话号及对应记录路径；无法确认身份时置灰并说明原因。沿 `native_link` 的 **Tracer bullet** 验证，按 **Deep modules** 检查文件读取层的错误分类职责，用 **Ubiquitous language** 区分受管会话绑定、终端钩子报告与线程号。

## FINDINGS

无本轮确认的、需要修改候选的发现。以下是两项关闭结论及同类路径检查，不是对所有输入的无缺陷保证。

| R4 事项 | 结论 | 证据 |
| --- | --- | --- |
| R4-F1：日期目录预检把祖先目录 EACCES 当成不存在，恢复旧链接 | **PASS，根因层关闭** | 读取职责仍在 `codexRootThreads`；移除预检，直接 `readdirSync`，只跳过 ENOENT，其他错误返回目录路径与原因。真实 daemon/socket 的同一跨月反例在父版本失败、候选通过。 |
| R4-F2：终端 Codex 的事件名写成 `pane_native_session` | **PASS，关闭** | 事实文档现明确受管为 `pane_native_session`、终端为 `shell_native_session`，与实际调用链一致。 |

### R4-F1 的根因与同类路径

[nativeLink.ts:144](/private/tmp/t195-cand5/workbench/src/nativeLink.ts:144) 现在直接读取日期目录；[第 146 行](/private/tmp/t195-cand5/workbench/src/nativeLink.ts:146) 只允许 ENOENT 表示该日期路径缺失。EACCES 等错误在同一读取层转换为 `unreadable`，调用方在 [第 48 行](/private/tmp/t195-cand5/workbench/src/nativeLink.ts:48) 返回不可用及“读不了”原因。文件 stat、打开、读取和不完整首行的既有失败路径仍返回不可确定，没有增加重试、备用身份来源或第二套选择逻辑。

本轮真实 socket 复验的输入是：9 月 30 日启动的 monitor、仍可访问的绑定线程 A、10 月 27 日同工作区的线程 B。可读时因 B 置灰；将 10 月祖先目录设为 000 后，直接枚举得到 EACCES、`existsSync` 为 false，候选仍置灰并说明无法读取；恢复权限后仍因 B 置灰。错误指向扫描先遇到的 `10/01`：该祖先不可搜索时，连这一天是否存在都无法判断，不能直接略过。父版本在相同扰动下返回可用的 A；这是独立于新增“明天目录”夹具的反例和修复对照。

逐项检查本文件其余 I/O 分支后，未确认还有“读取失败被当成没有其他匹配，从而恢复旧链接”的路径：

- 受管 Codex 的目录和候选文件失败均先返回不可确定；最后 `existsSync(file)` 为 false 只会禁用链接，不会选择其他线程。
- agy 在 [第 103 行](/private/tmp/t195-cand5/workbench/src/nativeLink.ts:103) 枚举全部 `.db`；`readDatabase` 的读取失败会在匹配数量判断之前禁用。顶层目录的 `existsSync` 为 false 会得到零匹配并禁用，不会从剩余匹配中选出一个。
- opencode 的库缺失或无法检查时禁用；数据库读取失败也禁用。PTY 报告文件无法检查时取不到 ID，不会回退到按目录猜号。
- Claude 与终端 Codex 的记录定位按已经绑定或报告的精确 ID 查找，没有受管 Codex 那种“排除其他线程失败后确认旧线程”的选择逻辑。它们仍有 `existsSync` 可能把权限错误描述成“找不到”，以及部分 `readdirSync` 错误可能直接使请求失败的边界；这不是本轮新修复，也不等同于本轮所查的旧链接恢复反例。本报告不把这些分支宣称为统一错误文案已通过实测。

### 文档一致性

[事实文档第 8 行](/private/tmp/t195-cand5/findings/2026-10-27-native-session-ids.zh-CN.md:8) 已分别命名两类事件。受管 Codex 的 rollout 收集器在 [panes.ts:1261](/private/tmp/t195-cand5/workbench/src/panes.ts:1261) 写 `pane_native_session`；终端报告经 `terminal_hook`、`noteShellHook()`、`noteNativeReport()`，在 [panes.ts:360](/private/tmp/t195-cand5/workbench/src/panes.ts:360) 写 `shell_native_session`。[README:321](/private/tmp/t195-cand5/workbench/README.md:321) 对受管绑定、终端带进程号的钩子、终端 agy/opencode 禁用及无法确认时置灰的主要描述一致。

## EVIDENCE

### 本轮独立运行

环境为 macOS、Node `v26.5.0`。探针、隔离源码、夹具、日志和报告均位于本审查目录。候选开始与结束 HEAD 相同、受控文件无差异；原有未跟踪 `workbench/node_modules` 保留，见 [开始](candidate-start.json) / [结束](candidate-final.json)。

| 检查 | 结果 | 产物 |
| --- | --- | --- |
| 候选实际 nativeLink 与真实文件权限/格式边界 | **10 PASS / 0 FAIL**，退出 0 | [脚本](probe-io.mjs)、[结果](io.json)、[stderr](io.stderr) |
| 候选真实 daemon、SQLite、`native_link` socket，跨月权限前后对照 | **PASS**，退出 0 | [脚本](probe-socket.mjs)、[结果](socket.json)、[stderr](socket.stderr) |
| 父版本相同 socket 探针 | **预期红态**，退出 1；权限故障时旧号变可用 | [脚本](probe-socket-parent.mjs)、[结果](socket-parent.json)、[stderr](socket-parent.stderr) |
| 冻结 `bf16c21` 的完整真实 CLI e2e | **INCOMPLETE**，退出 1；8 项通过后终端 Claude 等待超时 | [运行脚本](run-frozen-e2e.py)、[摘要](frozen-e2e.json)、[stderr](frozen-e2e.stderr)、[诊断](e2e-diagnostic.json) |
| 差异空白检查 | **PASS**，退出 0 | 命令及以上各项退出码见 [review-runs.json](review-runs.json) |

10 项文件检查覆盖 open EACCES、readdir EACCES、stat ENOENT、read EISDIR、不完整 JSON、启动前不可读旧文件的排除、可读其他工作区及 subagent 的排除，以及跨月第二线程的权限故障前/中/后对照。不存在的日期路径由跨月跨度内的缺失日期和可用绑定正例共同覆盖；没有把“所有错误都置灰”的实现算作通过。

父版本源码仅通过 `git ls-tree` / `git show ed5a63b:<path>` 导出到本目录的 `parent-source/`，没有切换或修改任何候选。复用 R4 两个探针时只改导入路径和候选标签；完整 e2e 使用候选测试的副本，只改 ROOT 与临时目录位置，并传入 `--revision bf16c21` 导出该版本产品源码，没有改业务输入、断言或超时。

复现本轮定向检查需使用新的夹具和输出路径，避免覆盖证据，例如：

```sh
node /private/tmp/t195-review5/probe-io.mjs /private/tmp/t195-review5/io-replay-01 > /private/tmp/t195-review5/io-replay-01.json 2> /private/tmp/t195-review5/io-replay-01.stderr
node /private/tmp/t195-review5/probe-socket.mjs /private/tmp/t195-review5/socket-replay-01 > /private/tmp/t195-review5/socket-replay-01.json 2> /private/tmp/t195-review5/socket-replay-01.stderr
node /private/tmp/t195-review5/probe-socket-parent.mjs /private/tmp/t195-review5/socket-parent-replay-01 > /private/tmp/t195-review5/socket-parent-replay-01.json 2> /private/tmp/t195-review5/socket-parent-replay-01.stderr
python3 /private/tmp/t195-review5/run-frozen-e2e.py --revision bf16c21 --summary /private/tmp/t195-review5/frozen-e2e-replay-01.json > /private/tmp/t195-review5/frozen-e2e-replay-01.stdout 2> /private/tmp/t195-review5/frozen-e2e-replay-01.stderr
```

### 新场景的期望与反事实

[new e2e:388](/private/tmp/t195-cand5/workbench/tests/test_t195_native_link_e2e.py:388) 的场景通过真实权限边界构造不可搜索的日期目录，调用真实 `native_link` socket。期望“不可用且说明读不了”来自 ticket 的“不冒充原生当前会话”要求及 R4 对无法确定身份的错误边界，不是从候选输出生成答案。

`next_day` 是夹具自己创建的输入路径；原因必须包含它。前置可用断言拒绝“永远置灰”；权限扰动后的不可用断言拒绝“永远返回绑定旧号”。“明天”用于命中既有扫描范围，不是以某次输出推导业务期望。隐藏目录为空不意味着查询方能够确认其中为空；本契约要求读取失败时承认未知。本轮另用含真实第二根线程的跨月合成记录复验，避免只依赖这个空目录场景。

只读核对了 brief 指定的四份既有摘要及测试源码，摘录见 [existing-evidence-audit.json](existing-evidence-audit.json)：

- `green-12-v5.json` 与 `green-13-with-t194.json` 均有 16 项 PASS；新场景中正常时可用、扰动后不可用，原因含 EACCES 和日期路径。
- `red-v4-ed5a63b.json` 明确指定父版本，前 15 项通过，在新增断言失败；其 `during` 保存了仍可用的旧绑定。不是启动、依赖或语法失败。
- `mutant-v5-codex-unsearchable-day-skipped.json` 也通过前 15 项，在同一新增断言失败，保存旧号仍可用；变异将 ENOENT 专属跳过改为所有目录读取错误都跳过，确实重现所查失败类。
- 红态与变异摘要的整体状态仍为 INCOMPLETE，不能称整套运行通过；但它们拒绝目标坏行为的证据有效。两份 green 和变异的 `revision` 为 null，不能单凭文件名绑定冻结完整提交；本轮候选与父版本的真实 socket 对照补上了冻结版本的独立证据。
- 真实 CLI 初始 ID/路径的期望仍来自 Claude transcript、Codex `session_meta` 内的 ID 与 cwd；新场景没有调用生产身份选择函数生成期望。文本格式断言本身不证明身份，身份另由原生记录内容核对。

### 本轮完整 e2e 的边界

前 8 项实际通过包括真实 Claude/Codex 的记录 ID 与 cwd、文本字段、受管 Claude `/clear` 后置灰、Codex 注入第二根线程后置灰。Claude 使用本地脚本化模型接口，Codex 使用真实模型。终端阶段 PTY 包含提交的第一句及脚本化回复，但没有 `shell_native_session` 事件；摘要报“超时：Claude 报来会话号”。未确定是 CLI 钩子、审查环境还是其他原因；没有证据足以归因于 Unix socket 沙箱限制。

该次运行没有执行到新增日期目录场景及后续终端断言；本轮其他探针、既有 green 和本次完整 e2e 是不同层次的证据，不能互相改写结果。

按本次功能范围核对 Agent 产品能力轴：

| 能力轴 | 本轮适用与证据边界 |
| --- | --- |
| 编排 / 状态 | 适用：真实启动记录、事件、daemon；不验收调度或崩溃恢复。 |
| 流式 / 异步 | 适用：CLI 钩子和事件；终端报告等待未完成，未证明全部事件时序。 |
| 检索 / 记忆 | N/A：本改动没有 RAG 或模型记忆。 |
| 身份 / 范围 | 适用：当前原生线程、工作区及文件权限；本轮核心检查。 |
| 交互入口 | 适用：真实 socket；本轮无 renderer 改动，未重跑 UI 或系统剪贴板。 |
| 文件 / 媒体 | 适用：真实文件读取、首行 JSON、权限扰动；跨月记录内容为合成输入。 |
| 外部副作用 | N/A：被审功能为读取查询；本轮不验收剪贴板写入或外部发布。 |
| 运维 | N/A：不涉及部署、生产流量或回滚验收。 |

## LIMITATIONS

- 这是冻结差异的定向审查，不是全部 CLI、全部损坏格式、全部并发时序或整票发布验收。没有重跑 renderer 构建、T-104、T-118、T-121；这些未改动范围不以旧结果冒充本轮通过。
- 本轮主要定向证据达到真实本地依赖和 socket 入口；跨月 monitor 与 rollout 为合成记录，没有让真实 Codex 跨月存活。它证明权限扰动下的错误分类，不证明实际事故频率。
- 完整 e2e 的终端 Claude 超时仍是未知项；不能把已有 green 的通过归给本次冻结运行，也不能将同一停点直接定性为本轮新增缺陷。
- 所有自建 daemon 均已停止，socket 与 PID 文件均已消失，见 [cleanup.json](cleanup.json)。隔离 Codex `auth.json` 已删除、内容未输出。测试摘要的 `removed:false` 原样保留：清理后目录中留下重建的插件目录缓存，没有认证文件；未把这个异常改成成功。后续 `pgrep` 返回 3，进程检查不可用，因此没有宣称已用它独立证明所有子进程退出，也未继续删除该缓存。
- 一次只读 Python SQLite 诊断在 daemon 关闭后因普通 `mode=ro` 打开失败，未用作产品红态；改用只读 `immutable=1` 读取已关闭数据库后取得诊断。没有修改数据库。
- 没有修改候选、原仓库、ticket、全局配置或既有证据，没有提交、修复或外部发布。候选原有 `node_modules` 链接保持。报告仅陈述本轮修复关闭与证据边界。
