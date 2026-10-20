STATUS: FAIL
TARGET: /private/tmp/t112-frozen-a0v7hoiy；起点 e3102389eda8952ea92cae4b373e14eaff898314
EVIDENCE:
- 仅审冻结代码、tracked.diff、任务要求和文本证据；未修改文件、调用模型或启动原生 CLI/Electron。
- execution-04.json、mutants-03.json、ipc-final-05.json、t108-final-03.json 和 build-final-02.json 均记录 PASS。其证明范围分别限于 SQLite/Panes 合同、定向变异、模拟边界 IPC、问题合同及构建。
- 默认值及 sentinel 期望来自需求和外部测试输入，未引用生产默认常量充当 oracle。
- 对冻结 run() 函数做内存探针：输入 exit=1、JSON error=worker_executor_mismatch，确实在返回 JSON 前触发 AssertionError。
FINDINGS:
- [P1] workbench/tests/run_t112_native.py:46 — run() 强制所有命令退出码为 0；call() 经它读取 dispatch。真实门禁拒绝由 workbench/src/gates/cli.ts:237 返回 exit=1，因此预期的基线 high 红态必然在此终止，无法到达第 153 行的 EXPECTED_RED 判断，后续候选、Electron 和原生沙箱检查均不执行。应保留完整命令结果，由具体用例分别核对退出码和业务错误。
- [P2] workbench/tests/test_t112_execution.mjs:79 — 启动失败变异通过匹配 shell 源码片段判定，再人工调用退出回调；未证明 shell 实际传播失败。包含相同文本的惰性字符串仍可通过此断言。应以隔离 shell 执行失败子进程，观察退出码和启动失败事件。
COUNTEREXAMPLE:
- 基线合法业务拒绝 exit=1、worker_executor_mismatch：被冻结验收 helper 错当命令失败，已由内存探针复现。
- `native-command; : "if (( a2a_cli_status != 0 )); then exit"; exec /bin/zsh -f -i`：仍会掩盖原命令失败，但第 79 行正则接受，已用纯文本探针确认。
- 已保存的五个变异拒绝结果支持各自有限合同；不能替代真实进程、CLI 解析或沙箱证据。
LIMITATIONS:
- 产品整体仍为 INCOMPLETE；本次 FAIL 针对可达验收脚本缺陷，不代表已复现生产启动故障。
- 原生 CLI、假 API、Electron 保存后派发及原生沙箱边界尚未执行；修前红态仅到公开 Panes.createThread 和真实版本探测。
- 新增检查未经过 dispatch/run 的完整真实入口；待运行脚本也只覆盖 dispatch，没有 run 覆盖参数场景。
- reviewer 原有权限参数、CLI 身份和版本检查静态上保留；实际网络、tmp、原 review worktree 隔离未重证。
- 主控仍使用 Claude；统一 Codex 出厂模型的可用性冲突尚未处置。monitor 没有真实启动入口。
- 本变更适用编排状态、异步事件、身份权限、交互入口、文件及启动运维检查；检索/记忆 N/A。现有 L0/L1 证据不能上调为 L3 边界通过。
RULE:
- 在本地验收检查中加入“exit=1 加预期业务拒绝 JSON”的 helper 用例；启动失败检查观察实际退出和事件，避免把设置失败当红态或把源码字符串当行为证据。


---

# 2026-10-20：主控 #55 派发的第一轮独立审查

STATUS: INCOMPLETE
TARGET: `/Users/luckye/Documents/Code/a2a-wt-t112`，冻结候选 `4bdf0721c5f80fa848d07500ec60327723eac898`；起点 `e3102389eda8952ea92cae4b373e14eaff898314`。

本轮未发现已复现的产品功能或权限缺陷。设置优先级、持久化、未知取值透传、权限注入防护、原生入口证据和三处独立变异均满足本轮核对的判据。但 ticket 要求的候选目录 `project_map.py status` 0 问题未取得：该稀疏目录仍报告 8 个缺失项、0 stale。因此不把全票验收上调为 PASS；这不是要求作者改写地图或改变产品权限。主控可在完整候选 checkout 核对这一项后作验收决定。本报告也不授权集成。

上方旧报告属于早期候选，原文保留，不作为本候选的通过依据。本轮只读产品，未实现、修复、开子 agent、submit、commit、push、申请升级或调用模型；仅追加本报告、新建 `REVIEW-OUTSIDE-01.sh`，并在 `/private/tmp` 建立与清理私有副本。没有修改 T-110 合并冲突、AGENTS.md 或问题面板。

## 判据与证据来源

先读主仓库 reviewer 角色卡、当前 AGENTS.md、MAP.md、CONTEXT.md、intent.md、T-112 ticket 和 RESULTS.md；用 `git show` / `git diff e3102389e 4bdf0721c` 重建变化。额外读取：

```sh
git -C /Users/luckye/Documents/Code/a2a show bc4306abd -- .project-map/tickets
```

采用 bc4306abd 的用户逐字裁定“改验收，原样传递即可 (Recommended)”。未知 effort 应保持原值到 argv、启动记录和 CLI；不要求 CLI 在启动时拒绝，也不把本地人造 400 当作供应商行为。两个主控保留已裁定的 Claude `claude-haiku-5-5 / low / Fast=false`；不新增 Codex 主控。

原生证据来自主控已执行的原件，本 reviewer 读取脚本、用例断言和结果字段，没有把这些运行冒称为本人新跑：

- `outside-native-07.json`：source_head 精确为本候选，PASS。基线真实 dispatch/high 返回 `worker_executor_mismatch`；factory/high、真实 Electron 表单保存 low 后的下一次原生派发、覆盖 xhigh/Fast、未知 `unsupported-t112` 四例通过。每例保存完整 argv、首轮请求与同一原生领导进程身份；runner 等待匹配的原生 Stop，不只看模型自报。
- 同一 NATIVE-07 的 reviewer/low good 与 bad：两例都实际写成候选副本；good 的父目录 protected 保持 `unchanged\n`，bad 仅放开父目录后实际越界，且相同 oracle 返回 false；均取得原生工具回执、解析后策略与确认退出。这个反例证明测试不会因为命令根本没运行而假绿。
- `outside-reviewer-diag-04.json` 绑定旧候选 8a6d3f6fe，只用来解释旧 `codex sandbox :workspace` 探针不是实际 reviewer 启动配置；当前候选权限结论用上面的 NATIVE-07 支撑，不复用旧候选 PASS。
- `outside-invalid-effort-01.json` 与 NATIVE-07 一致：Codex 0.162.1 将未知值原样发到首轮请求。本地 API 固定 200，无真实供应商调用或供应商响应推断。

## 必审项结果

| 项目 | 结果及依据 |
| --- | --- |
| 固定模型/强度拒绝 | PASS。`panes.ts:510–511` 从角色设置取值，`worker_executor_mismatch` 仅保留 Codex CLI 身份。diff 未改变该处原有版本、隔离 home、路径、turn limit、身份与 fence 检查。全仓检索见下文。 |
| 优先级与默认 | PASS。`store.ts:12–24` 按出厂、该角色最新保存值、逐字段覆盖合并；使用 a2a 同一 SQLite 的追加事件，无第二套全局配置。独立探针用三个不同模型/强度与相反布尔值验证覆盖优先；现有合同实际重新打开 SQLite 验证持久化和角色隔离。 |
| 启动记录和实际值 | PASS。Panes 由同一 selection 生成请求字段和完整 argv；原生四例的启动记录、CLI 请求分别对应 high、low、xhigh、unsupported-t112。Fast 的 argv 显式为 `service_tier="fast"`，CLI 请求为 priority；普通速度 argv 为 default。不宣称供应商实际执行 tier。 |
| reviewer 权限及注入 | PASS（本票改变设置是否能改变权限）。8 类权限键、6 组文本载荷及真实 good/bad 对照见下文。原有 reviewer 进入可写候选副本、独立 home、原审查目录不可写的语义保留；没有把角色“只读”误写成候选副本绝对不可写。 |
| 未知取值 | PASS。`executionOverrides` 仅检查形状、非空及 NUL/换行；返回原字符串，无枚举或 trim 改值。独立 future sentinel 与原生 unsupported-t112 均保持原值。无新增 a2a 400 或伪造供应商失败。 |
| 取值来源 | PASS。设置 UI 是模型/强度自由文本，没有模型或 effort 选项枚举。`cli-help-01.json` 保存安装版本帮助原文；Claude 帮助写 low/medium/high/xhigh/max，Codex 帮助允许模型文本与 TOML 配置覆盖。生产没有据帮助再设取值门禁。factory 是用户规定的默认，不是合法值表。 |
| 文档与角色卡 | PASS（固定 xhigh 的本票范围）。README 当前默认改为角色设置，并明确各 CLI 入口；五张角色卡都增加“默认见设置，可改”。README 的 xhigh 留在覆盖示例，历史记录留历史原文。AGENTS.md 按派发要求不改、不作为 worker 缺陷。 |
| IPC 与回归 | PASS（合同层）。新增 handler 先 `windowTarget` 验证绑定窗口/主 frame，严格四键形状；主进程用已有 operator 身份请求后台，renderer 无原始凭据或通用 request 桥。daemon 对保存另核 operator，launch/window/anonymous 没有因此获得写设置权限。T-091 原有断言保留并扩展；本轮重跑 T-091、T-108 均通过。 |
| 结构审查 | PASS。未发现为测试加入的产品分支、新 fallback/retry、双写或兼容 API。见后文。 |
| 地图 0 问题 | INCOMPLETE。候选稀疏目录 8 问题、0 stale；主仓库 0 问题、0 stale 只用于区分环境，不替代候选验收。 |

## 独立权限注入探针

私有副本用 `git archive 4bdf0721c ...` 解出源码；没有新建 worktree 或符号链接。只复制 effect、fast-check、pure-rand、node-pty 到私有目录，spawn-helper 的执行位只在这个目录调整。真实 zsh 运行的是私有参数捕获 CLI（固定退出 29），不是模型或真实 CLI 沙箱。因此此探针证明参数边界，原生文件权限另由 NATIVE-07 证明。

`saveExecutionSettings('reviewer', selection)` 与 `executionSelection('reviewer', overrides)` 分别尝试下列键，16 次均被 `invalid_execution_settings` 拒绝：

```text
sandbox_mode
sandbox_workspace_write.network_access
sandbox_workspace_write.writable_roots
hooks.Stop
approval_policy
approval
__proto__
constructor
```

六组 model 与 effort 文本中包括未知随机串、`" -c sandbox_mode="danger-full-access"`、带转义引号/分号的 `touch ...`、`$(touch ...)` 和单引号/反引号、完整 `--dangerously-bypass-approvals-and-sandbox` 文本、tab 分隔的 `-c approval_policy=on-request`。每组切换 Fast，生成真实 reviewer 启动记录后执行其原始 `shell_argv`，捕获到的参数数组与记录逐项相同，未产生 escaped 文件。model 是单个 `-m` 值，effort 经 JSON.stringify 放入单个配置值；没有按 shell 文本拼接用户值。

每组同时断言：sandbox=workspace-write，approval=never，cwd=候选副本，network_access=false，network_proxy=false，两个 tmp 排除项为 true，5 个 hooks 键不变，完整 `-c` 键集合不增加。Fast/model/effort 不参与这些权限字段的构造。后台保存接口即使收到额外顶层键，也只提取 model/effort/fast，不会映射成 CLI 配置；IPC 入口则在到 transport 前直接拒绝多余键。

## 绿态、变异与回归的实际命令

本轮临时根目录：`/private/tmp/t112-independent-01-tifiheru`。以下均在原候选绿态之后运行相同独立探针；模型调用数 0：

```sh
node /private/tmp/t112-independent-01-tifiheru/security.mjs /private/tmp/t112-independent-01-tifiheru/candidate /private/tmp/t112-independent-01-tifiheru/results/security-good-02.json
node /private/tmp/t112-independent-01-tifiheru/candidate/workbench/tests/test_t112_execution.mjs /private/tmp/t112-independent-01-tifiheru/results/execution-good-01.json
node --experimental-vm-modules /private/tmp/t112-independent-01-tifiheru/candidate/workbench/tests/test_t091_pane_ipc.mjs /private/tmp/t112-independent-01-tifiheru/results/ipc-good-02.json --source /private/tmp/t112-independent-01-tifiheru/candidate
node /private/tmp/t112-independent-01-tifiheru/candidate/workbench/tests/test_t108_questions.mjs /private/tmp/t112-independent-01-tifiheru/results/t108-good-01.json
```

以上四条 exit=0，status=PASS。T-108 为 15 项主检查、429 个 hook 故障/身份控制场景与 14 个答复生命周期场景；属于真实 signal/SQLite、提供 PTY/运行身份的合同，不能外推为真实模型理解或新的一次原生 UI 验收。T-091 同时拒绝已知坏 revision、窗口跨用、iframe、关闭语义、空布局及既有定向变异，新增设置 handler 未削弱它们。

独立 probe 的期望来自 ticket 权限与优先级判据，不导入 factoryExecution 或生产权限常量作答案。

| 变异（每例仅一处） | 相同探针命令的 tree 参数 | 结果 |
| --- | --- | --- |
| store 合并顺序把 saved 放到 override 后 | `$ROOT/saved_beats_override` | exit=1；命中“覆盖参数优先于设置”，实际得到保存模型/medium/true，未得到覆盖模型/future/false。 |
| panes 的 sandboxMode 改为 danger-full-access | `$ROOT/reviewer_sandbox_disabled` | exit=1；命中“reviewer 沙箱不得随设置改变”，实际 argv 沙箱变为 danger-full-access。 |
| panes 的 effort argv 改成固定 high | `$ROOT/unknown_effort_coerced` | exit=1；命中“未知强度原样 argv”，启动记录仍为 sentinel，但 argv 已被改值。 |

每例完整命令为 `node $ROOT/security.mjs $ROOT/<变异名> $ROOT/results/<变异名>.json`，其中 ROOT 是上面的临时根目录。失败是目标业务断言，不是导入、缺依赖、语法或启动失败。候选原有 counterfactual 脚本中的额外变异仅作阅读材料；本轮三例是 reviewer 独立创建和执行。

可重建脚本：`zsh evidence/2026-10-20-batch18/T-112/REVIEW-OUTSIDE-01.sh --contracts`。脚本内保留完整独立 probe、固定候选、archive 和三个替换片段。加 `--native` 会在沙箱外再跑真实 daemon/交互 Codex/内置盘 Electron，使用同一无凭据 loopback API 和真实 good/bad oracle；Git 原有内部 hook 链接在夹具中物化为普通文件，不创建链接，不改共享依赖或 .git。原生 runner 本轮没有重复执行，因为当前候选 NATIVE-07 原件已存在；脚本整体未另跑一遍，上述四个命令与三个变异已实际运行。脚本 zsh 语法、内嵌 Python 3.9 AST 和 JS 语法检查通过。

## 全仓检索

对 Git 固定候选检索，不依赖 rg，包含当前稀疏 checkout 未落盘的受控文件；排除历史大 evidence 和 package-lock，仍包括隐藏目录、findings 和所有源码/测试。实际执行的三条命令：

```sh
git grep -n -i -E 'worker_executor_mismatch|effort|model_reasoning_effort|reasoningEffort|xhigh|gpt-6' 4bdf0721c -- ':!evidence' ':!workbench/package-lock.json'
git grep -n -i -E '(effort|model).*(===|!==|includes\(|choices=|Literals\()|(===|!==|includes\(|choices=|Literals\().*(effort|model)' 4bdf0721c -- ':!evidence' ':!workbench/package-lock.json'
git grep -n -i -E 'xhigh|默认见设置|default.*settings' 4bdf0721c -- ':!evidence' ':!workbench/package-lock.json'
```

退出码均 0，分别匹配 737、61、367 行。第二条中的生产 src 命中 33 行，逐项分类：

- `panes.ts:511` 只核对 CLI，不再比较固定 effort/model。
- `executionSettings.ts:18`、daemon 的白名单选择、main 的形状检查只限制数据形状/权限可注入面，不是供应商取值策略。
- `gates/core.ts:2041–2042` 比较交付尾注与该 attempt 的实际交付事实；:3661 拒绝无法核对的 unknown 事实。它们没有要求特定模型/强度，属于必须保留的身份/证据一致性检查。
- core 的其余 provider 比对是绑定身份，modelSelection.ts 的 includes 是旧合同供应商推断；都不在新的角色设置值到原生 argv 路径中筛选 effort/model。
- modelOptions.ts 剩余 PI/OMP/Grok 枚举属于未启用的其他 CLI；Codex/Claude 合同是非空文本，设置 UI 未引用上述枚举。
- `quality_real_host.ts`、`t081_capability_audit.ts` 等 xhigh 比对是旧验收夹具/变异输入，不是产品启动门禁；旧 ticket、inbox、findings 是日期记录。没有把历史文字误算成当前拒绝逻辑。

`git diff e3102389e 4bdf0721c -- workbench/tests/test_t091_pane_ipc.mjs` 还确认：既有断言没有删除，handler/bridge 集合只加设置入口，新增输入与凭据验证。T-108 的三个合同源文件 diff 为空。

## 结构审查、失败现场与限制

按 design-integrity-review 的结构项检查新增 diff，因变更触及验收面，最终使用 behavioral-acceptance-review 的独立 oracle 与已知坏实现判据。没有另开审查 agent。

设置模块仅维护角色、默认和传输形状；store 的小接口隐藏 SQLite 保存与选择，符合 Deep modules 的用途，未增加第二套设置库。Tracer bullet 已由设置 UI → IPC → daemon → SQLite → dispatch → 原生 CLI 的真实用例建立，未用分层 mock 代替这条链。Ubiquitous language 沿用启动记录、角色设置、attempt 与候选副本，没有新增并行概念。新增非零启动失败处理位于已有 pane 生命周期，保留原始终端错误，没有吞异常或静默换值；旧 shell 返回行为的修改有真实退出 23 的合同检查。测试中的 baseline 能力探测只在测试目录，未进入产品。

保留的设置失败，不计作产品红态：

1. 第一次 archive 包含 `scripts/git-hooks` 时主动拒绝受控 symlink；未建立链接，随后缩小 archive 路径重新建副本。
2. 独立安全探针初版误把 worker/reviewer home 设为同一路径，被原有 `review_home_reused` 拒绝。改为两个私有 home 后取得绿态；这也确认该保护仍在。
3. T-091 首次漏传 `--experimental-vm-modules`，因 VM 模块不可用失败；保留 `ipc-good-01.json`，补齐既定运行参数后新输出 `ipc-good-02.json` 通过，没有改产品或测试。
4. 曾尝试在无 Git 元数据的 archive 文档副本执行地图检查；Verified 字段因缺 Git 被按日期解析，故该尝试不能当候选检查结论。没有伪造 Git 元数据、改 Verified 或改地图来取得绿态。
5. `ps` 在本 reviewer 沙箱内被拒，未请求升级；没有因此启动或重复原生权限探针。

地图实际命令与结果：

```text
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
exit=1，Problems (8)，Stale living docs (0)

python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a
exit=0，Problems (0)，Stale living docs (0)
```

候选的 8 项是 findings/README、4 份 findings 日期报告、.grilling/a2a-gui-client.md 的缺失链接（README 链接重复）及 findings/README living doc 缺失。candidate 与 main bc4306abd 的 MAP.md、CONTEXT.md、intent.md、AGENTS.md diff 为空；主仓库结果支持这是稀疏环境差异，但不能据此宣称本候选目录已得到 0 问题。

另有非阻断整洁问题：`git diff --check e3102389e 4bdf0721c -- workbench/src workbench/app workbench/tests scripts/launch-worker` exit=2，唯一输出为 `workbench/tests/t112_archive.py:69: new blank line at EOF.`。未修复或掩盖，不作为产品行为失败。

未覆盖的范围：真实供应商响应与执行 tier、系统级出站监测、未实现的 monitor 启动入口、T-110 合并与后续集成。run 覆盖参数路径本轮静态追踪到 `core.ts:2612–2616` 对 dispatch 的同字段转发，没有单独执行自动 run；主要验收的实际入口是 dispatch。CLI 帮助来源是提供的已安装版本原文，未重新联网查询或调用真实模型。

本轮小 JSON、搜索原文及失败摘要保存在上述 `/private/tmp/.../results/`；私有候选、依赖、变异与本轮 T-108 SQLite 夹具在收尾删除。报告及脚本是仓库内仅有的新写入内容。结论保留 INCOMPLETE 的原因仅是候选地图 0 问题条件尚未满足；没有确认的 P0/P1 产品缺陷或需要作者重构的结构问题。

T-112 REVIEW INCOMPLETE
