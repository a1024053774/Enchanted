# T-141-1 / a1 交付记录

状态：**INCOMPLETE**。RUN-OUTSIDE-05 共 29 场，25 场符合预期（含 T-127 绿态、worker 旧版红态、全部 T-141 红/变异和 T-140/T-131/T-132）；四场的诊断与现场保留。两个 trust 场景是静态 SQLite 读取失败，原始输入单变量复放已确认正确拒绝；两个目录场景被更早的 hook 来源检查正确挡住，旧的后层预期没有实际执行。本轮仅修证据读取、补齐隔离源码的故障注入和等待终态识别，原行为断言与超时不变。RUN-OUTSIDE-06 只跑这四场加 T-127 绿态，真实结果待回传。

工作目录 `/Users/luckye/Documents/Code/a2a-wt-t141`，分支 `exec/t141`，起点 `3f8813b0e`。任务来源为 T-141 ready_rev 1；交付提交号以 `DELIVERED` 消息为准，真实运行脚本另保存当时的完整 Git 版本和工作区状态。未 push、未合并 main。受保护 oracle 中，T-140 仅改获准的隔离信任配置；T-127 另按本轮用户裁定修改四处 worker 期望及四个变异定位，第六轮另补齐同一个 reviewer 运行时变异并识别 paused 等待终态；所有行为断言、检查名及超时保持，详见下文；T-131、T-132 原样。未改地图、ticket、AGENTS.md、CONTEXT.md 或其他 worker 的源码。

## 候选行为

- Claude worker/reviewer 去掉 `--strict-mcp-config`，通过只匹配 `^mcp__` 的原生 PreToolUse hook 允许用户 MCP 工具；删除已被真实 CLI 拒绝的 `permissions.allow: ["mcp__*"]`。保留 `--setting-sources ""`，避免设置文件合并扩大原生工具写入范围；有用户作用域 MCP 时，单独将 `$HOME/.claude.json` 传给原生 `--mcp-config`，不把该文件的其他设置并入会话。Bash 沙箱允许所有域名、Unix socket 与本地连接，保留原生文件工具的目录限制、Git common dir 禁写与原有两条 Git 例外。
- Codex 保留 `-a never`、workspace-write、a2a hook 和角色选择的模型/强度/tier；worker/monitor 不覆盖项目信任；reviewer 仅对一次性审查副本保留 `-c projects={<该副本>={trust_level="untrusted"}}`，防止候选中的 `.codex` 配置、hooks、exec policy 影响独立审查。移除网络代理和 TUI 通知覆盖，显式开放 workspace-write 网络。写入根为当前 workspace、worker 请求目录和项目额外目录，不沿用用户配置中额外的可写根。
- Codex 排除共享 `/tmp` 与原 `$TMPDIR`，worker 的 shell 临时文件放在请求目录的 `.a2a-tmp/`；reviewer/monitor 放在各自一次性工作目录的 `.a2a-tmp/`。新 e2e 同时检查 tempfile 能运行、共享临时根不能写，另设 `shared-temp-writable` 反例；outside-02 的 Codex 原生探针与反例符合要求；新候选仍待外部复跑。
- trusted 目录依据原生 `OSC 7501;state=idle:app=codex` 包及前台领导进程核对放行首条任务；untrusted 只代按不保存信任的 Open restricted，并等待同一个 ready 包；unset 记录 `codex_folder_trust_requested`，不按 Trust and continue。后续 idle 包不代替 Stop 或业务验收。
- worker 角色卡说明原生审批拒绝后用 `issue` 上报、必要时结束回合等主控答复。沿用原有 `answer_issue` 与会话队列，没有新增通信接口或放宽门禁检查串。
- reviewer 门禁只同步启动参数契约；会话/attempt 绑定、候选目录、原生身份、不同于 worker、禁止 resume/fork、写入范围与其余质量串保持原检查。

## 第六轮：四场的实际拒绝层与最小修复

按执行主控要求，先读四场 JSON/完整 log、夹具任务状态/门禁事件/原生 hook 事件与变异源码，再写 `diagnosis-outside-05.md`（实施前假设与证据），之后才改测试。结构化摘录为 `outside05-four-cases-06.json`，原始 `outside05-jYDNPNbR/` 和所有夹具保持原样。该轮代码版本为 `7c58ba11c5dad6c2fef79e0b19ed8da0abd6145e`。

| 场景 | 实际拒绝层 / 失败原因 | 本轮处理与未证明事项 |
| --- | --- | --- |
| t127-no-untrusted | 启动参数门禁 `review_launch_boundary` 已拒绝缺失 trust 的 reviewer；矩阵不是 proof=null，而是读取器报 SQLite OperationalError | 只对已结束、无非空 WAL 的夹具快照使用 `mode=ro&immutable=1`，不做 fallback。原路径及独立单文件副本的普通 ro 均失败，immutable 可读；更底层 SQLite sidecar 原因未证明。原 helper 用真实输入，仅补回 untrusted 即通过同一门禁，证明不是无关 sandbox/身份错误 |
| t127-trusted-copy | 同一启动参数门禁已拒绝候选 trusted；同一静态读取失败 | 同上；helper 先核对实际参数确为 trusted，仅改成 untrusted 后同门禁通过，控制条件没有放宽 |
| t127-folder-runtime-unbound | scanner 已被变异而绑定错误目录会话，但 hook 的 cwd 仍是 review Git worktree、内存 record.worktree 仍是 candidate。UPS/工具/Stop 共 10 次被 `question_origin_unverified` 拒绝，未进入 review_submit，review 仍 running | 是运行时故障注入不完整，让原本想测的后层 `review_native_session_folder` 不可达。补齐同一隔离变异：持久 launch 保存之后，仅伪造 pane 内存 record.worktree，使 scanner 与 hook 来源的假运行时一致。持久记录与 attempt workspace 仍指候选，生产来源检查不改。原有“review 不通过并有指定 native-session-folder 拒绝”的断言保留；真实后层执行待 RUN06 |
| t127-gate-folder-unchecked | 关闭后层目录 guard 仍被上述早层挡住，故超时不能算抓住此变异 | 采用同一完整运行时故障注入，使删除后层 guard 的效果可见。仍要求坏实现真的产生 review.state=passed 且被原行为断言拒绝，才计反例通过；其他早拒/超时保持 INCOMPLETE |

`36fc44914` 到第五轮候选的 workbench/src 没有差异；与 `c113e7120` 的 questions.ts、paneRecovery.ts 也无差异。旧 T-127 变异注释本来就记过更早的 question_origin_unverified。因此有证据说明早层拒绝机制不是本轮 review 参数形状引入的生产回退；没有据此声称已重跑旧版完整端到端，也没有把未到达的后层检查补称为通过。

另一个等待缺口：真实 gate 拒绝 reviewer receipt 后，daemon 的 failReviewProtocol 将 task 设为 paused、review 设为 unknown；“审查结束”的等待谓词原来不接纳 paused。本轮仅增加该终态，240 秒期限不变；之后仍执行同一拒绝断言，普通绿态仍必须 review_passed，不把暂停当作审查通过。

本地证据：`origin-replay-06.json` 对两份真实 Stop hook 复放：原持久记录的来源检查均拒绝；仅伪造内存 worktree 后 envelope 通过，持久 launch 原值不变。这只证明故障注入已覆盖前一层，不证明真实后层审查已完成。`t127-delta-06.json` 的 AST 比较确认所有 check 名称、断言表达式、其他变异与超时均不变，只有该 runtime 变异及 paused 等待终态变化。`t127-oracle-06.json` 的 14 个谓词输入与全部 13 个变异/场景定位、语法检查 PASS。

`outside05-reclassification-06b.json` 用新矩阵重判保存的第五轮输入：T-127 绿态与两个实际 trust 拒绝得到 PASS（仍核对只修 trust 后同门禁通过及进程退出 0），两个旧超时仍 INCOMPLETE，未被粉饰。该文件明确区分 expected_boundary 与 observed_gate_result；早一份 `outside05-reclassification-06.json` 的 refusal_layer 是计划检查层，不能当作旧超时的实测拒绝层。

运行 `zsh evidence/2026-10-23-batch23/T-141/RUN-OUTSIDE-06.sh`，创建新的 outside06-* 目录，恰好 5 场：t127、t127-no-untrusted、t127-trusted-copy、t127-folder-runtime-unbound、t127-gate-folder-unchecked。保留两个目录场景的原断言和原负例分类，不放宽成“任意早拒就通过”。实际能否到达后层及关闭后层后的错误通过，须本轮原生运行验证；如果还有其他层拒绝，继续 INCOMPLETE，不延长超时。

本轮冻结测试候选的一次独立只读 behavioral-acceptance-review 为 INCOMPLETE，报告 `acceptance-review-06.md`：有界检查未发现可达的验收违规，独立用实际 trust 输入及叠加的无关 sandbox 缺陷验证了单变量控制；新目录变异仍缺原生执行证据，不作 PASS 结论。最终本地语法、编码检查及范围记录为 `local-final-06.json`，project-map 状态见 `status-final-06.txt`（0 problems / 0 stale）。

## 第五轮：对齐获准的四处 worker 期望（历史）

执行主控在本会话转述用户 2026-10-23 的逐字选择“改这四条 worker 断言 (Recommended)”，记录为 `20261023T153252Z-executor-report-001`。授权仅把按“worker 强制 untrusted”写的四处改为 worker 沿用用户配置；reviewer 的副本 untrusted、精确目录门禁、候选配置/hooks/exec policy 不影响审查的规则保持。允许旧变异定位到当前源码形状，不改变其坏行为与审查断言，不改其他检查名或超时。本轮没有改生产源码。

| 位置（改前名称） | 改前 | 改后及保留条件 |
| --- | --- | --- |
| `worker_folder_untrusted_in_argv` | 要求 worker argv 含主仓库 `projects=...untrusted` | `worker_trust_not_overridden`：不得有 `projects=` 或 `projects.` 覆盖；worker 使用隔离 home 里预先写好的 demo trusted |
| `user_home_not_rewritten` | 禁止整个 config_after 含 `[projects` | 只禁止新增部分 added 含 `[projects`；原配置必须仍是字节前缀，其他 home 文件逐字节比较、仅允许追加 `[tui]` 等原比对全部保留。因此夹具预先写入的 demo trusted 保留，a2a 不能追加或改写 trust |
| `restricted_answered_before_first_task` | worker 启动事件前三条须为 restricted intent/opened/turn_submitted | `trusted_worker_starts_directly`：事件恰为 `['turn_submitted']`，不经过 restricted；前面的真实 API 首请求等待和 worker_started 检查保留 |
| `project_codex_hooks_not_run` | worker/reviewer 的 project hook 标记一律不得出现 | `reviewer_project_codex_hooks_not_run`：仅放开 worker 部分，任何以 project 开头、以 -reviewer 结束的配置钩子/文件钩子标记仍拒绝；两类 home hooks 仍须实际运行。worker 的项目钩子是否运行如实保留在 markers，不据此要求 reviewer 放行 |

四个旧变异定位：`untrusted-config-missing` 现在删除仅 reviewer 的那条 projects spread；`project-trusted` 将同一 reviewer 覆盖改成 trusted；`session-folder-differs` 的实际命令仍移到审查 Git worktree，并将该命令的 untrusted 根设为主仓库（使用现有 `realpathSync(task.repo)`，原来的 repositoryRoot 已不存在）；`resume-worker-in-argv` 定位到当前带 extraDirectories/mcpConfig 的构造器后，仍只给 reviewer 加 resume worker 会话。其他变异定义原样保留。

`outside-04-summary.json` 与 `t127-red-04-summary.json` 保存真实修前失败：`36fc4491422d9ae3792da4d7a78e5d3014ecd585` 上 T-127 实际 startup 为 `['turn_submitted']`，旧断言拒绝它；同一轮其他 13 场符合预期。原目录 `outside04-SqmEfaks/` 不覆盖，归档归执行主控。

新增 `test_t141_t127_oracle.py` 只测试验收谓词与源码变异入口，不当作原生 CLI 证明。修前 `t127-oracle-red-05.json` 在上述真实 startup 输入上红；改后 `t127-oracle-green-05.json`、扩展的 `t127-oracle-green-05b.json` 在 14 个独立好/坏输入上通过：拒绝 restricted/未送达、两种 projects 覆盖、home 文件改动/非前缀/新 trust、两种 reviewer project 标记，同时允许 worker project 标记。后者另逐一应用全部 9 个 `--mutant` 与 4 个 `--reviewer-case` 的补丁，定位均唯一，Node 语法检查均通过；没有据此声称这些变异已被真实运行抓住。

`t127-authorized-delta-05.json` 用 AST 比较确认：除这四个授权谓词/名称、相关说明和四个变异字符串入口外，其余 Python 节点保持不变，包括审查身份/目录/新会话/untrusted、副本变异执行、写入边界、home hooks、交付集成检查与所有超时。

`RUN-OUTSIDE-05.sh` 创建新 `outside05-*` 目录，共 29 场：原 T-141 全套及 t127/t140/t131/t132；新增本地 oracle 检查、worker 旧版强制 untrusted 的真实红态、全部 T-127 变异入口与四种 reviewer 隔离场景。组合反例覆盖删除 trust 门禁、删除原生目录门禁、丢失 unbound 记录。失效定位、无关前置失败和未到达目标断言均记 INCOMPLETE。restricted-unanswered 还须同时有原生 Open restricted 屏幕与 native_ready_signal_missing，单纯超时不算抓住。`scan-whole-home` 只记录功能与时间，不计入负例或性能收益证明；其余每场按独立预期分类。真实结果待回传，截图不提交。

第五轮冻结候选 `29e4e69b6234cfbbe2107fdee9f5fdc22b845c6f` 经一次独立只读 behavioral-acceptance-review 得到 FAIL（原报告 `acceptance-review-05.md` 保留）：两个 trust 变异原先只匹配通用 `review_launch_boundary`，可能把无关 sandbox/身份/目录失败当作反例通过。

后续修复只收紧证据分类，不改生产门禁或 T-127 的受保护断言：RUN05 从该失败夹具的只读 SQLite 读取 `review_requested` 与 `review_lifecycle_failed` 保存的实际 review、launch、live 输入，保存为新的 trust-input.json；`t141_review_trust_rejection.mjs` 用同一生产 `reviewLaunch` 复放，先确认实际 trust 缺失/改 trusted 且原记录被拒，再仅恢复正确的候选副本 untrusted 参数。只有其余输入不动就能通过同一门禁，才把这次拒绝计为 trust 反例。若还有其他边界错误、找不到输入或复放无法通过，保持 INCOMPLETE。

`reviewer-specific-refusal-05.json` 本地 PASS：两种实际生产 builder 记录的 trust 反例均能通过这项单变量控制；同样的通用错误码再叠加无关 `launch.sandbox=read-only` 后，控制仍被拒、证据为 INCOMPLETE，不能计作 trust 反例。此结果只证明分类控制逻辑；真实失败输入的提取与完整变异执行仍待 RUN05，不把修复写成新候选已通过独立审查。

## 第四轮：仅审查副本保留 untrusted（历史）

执行主控在本会话转述用户 2026-10-23 的逐字裁定“选 A”，来源为 `20261023T141957Z-executor-needs-decision-001` 的 executor report 回复：Codex reviewer 的一次性审查副本保持 untrusted，worker 与 monitor 沿用用户配置。这个例外保住独立审查：副本里由 worker 写入的 `.codex` 配置、hooks、exec policy 不生效。它不把用户 home 改为 untrusted，也不改变 worker/monitor 信任。

实现只在 Codex reviewer argv 增加 `-c projects={<realpath(candidate_workspace)>={trust_level="untrusted"}}`；门禁恢复 T-127 的精确目录核对，缺少这条、指向其他目录、值改成 trusted 均拒绝。写入根、网络、`-a never`、会话身份与门禁其他检查保持原规则。启动沿用已有 Open restricted 处理，不选择保存信任的 Trust and continue。

本地生产 builder → 真实 reviewer 参数门禁：`reviewer-trust-red-04.json` 在修前 `8cf7caf70e5306a82f834b68812cedb494840632` 因缺少审查副本 untrusted 失败（该版本相较 `369d20539` 仅纳入主控证据，workbench 代码未变）；修后 `reviewer-trust-green-04.json` PASS，包含上述三个坏记录以及 worker/monitor 不覆盖信任的核对。`launch-contract-04.json`、`startup-green-05.json` PASS；`runner04-preflight.json` 核对脚本入口与 14 场清单。它们证明启动与门禁契约，不证明真实审查已运行，也不替代候选 `.codex` 钩子不执行的原生证据。

T-127 夹具唯一改动：`workbench/tests/test_t127_codex_home_e2e.py:212-215` 的隔离 CODEX_HOME/config.toml，旧配置只有 fixture provider，新配置在 provider 前加入 `[projects."<repo.resolve()>"]` 与 `trust_level = "trusted"`。该 repo 是测试自行创建的 demo 仓库；不写真实用户 home。依据为本会话执行主控明确授权：“只允许改夹具（在它隔离 CODEX_HOME 里把它创建核对的 demo 仓库标 trusted，同 T-140 裁定），断言、检查名、变异、超时都不动”。`t127-fixture-only-delta.json` 以 AST 核对，除这段 config 内容外所有 Python 节点不变。

执行主控已有原生失败原样留在 `t127-check-01/`，小摘要 `t127-check-01-summary.json`：CLI 0.163.0，worker 处于 Folder access，记录 `codex_folder_trust_requested`。这证明此前未设置信任的前置失败，不能证明本轮 reviewer 行为。

第四轮当时无法仅凭获准配置修改 T-127 变为全绿：它仍要求 worker 经过 restricted 启动事件、worker argv 强制 untrusted，并要求 config.toml 完全没有 `[projects]`；另有 worker 与 reviewer 项目 hooks 一律不运行的断言。前面三项与本轮授权直接冲突，hooks 实际影响尚待原生运行。旧变异的部分源码定位也不再匹配 reviewer-only 的参数形状。我没有改这些断言、检查名、期望、变异或超时，也没有为满足旧断言改回 worker 的信任覆盖。问题已上报 `20261023T151346Z-worker:b23-t141-issue-001`，更早的 startup 断言补充为 `20261023T151642Z-worker:b23-t141-issue-001`；原文分别保存在 `issue-t127-protected-contract.md`、`issue-t127-startup-expectation.md`。本轮用户已授权上述四处对齐，见第五轮；历史问题与失败证据保留。

`RUN-OUTSIDE-04.sh` 创建新 `outside04-*` 目录，跑 T-141 三契约、无模型 MCP 加载探针、真实 e2e 红/绿、四个变异，以及 t127/t140/t131/t132，共 14 场。t127 仍按普通回归要求 PASS，不把前述冲突失败登记为预期成功。脚本只记录完整候选版本与实际结果，不提交截图；大日志/夹具归执行主控按 T-088 归档。

## RUN-OUTSIDE-03 已回传结果

执行主控提交 `8cf7caf70` 纳入 `outside03-Co3TG9Q3/`，其 `candidate.txt` 为 `369d2053980ae5f2460cd2a16c557ac97571e214`，`matrix.json` 为 PASS：三契约、无模型加载探针、green、T-140/T-131/T-132 通过；red 与四个变异均在各自行为断言处失败。green 原生工具结果和服务收据证明用户 MCP 实际调用，两类 CLI 公开 HTTPS curl 成功；Codex 审批拒绝→issue 面板→答复→原 worker 继续、两类 CLI 的写入边界、两个独立审查均完成。T-140 的 Codex monitor 边界也实际走过，因此前文第三轮的 monitor 信任担忧没有在该次运行中复现。它们是上一候选的有效证据，不能替代本轮恢复 reviewer untrusted 后的 RUN-OUTSIDE-04，也没有覆盖 T-127。

## RUN-OUTSIDE-02 结果与第三轮修复

原始目录 `outside02-FMG476aF/` 保留，归档归执行主控；小摘要为 `outside-02-summary.json`，原生工具清单、MCP 错误和 T-140 诊断摘录为 `diagnosis-outside-02.json`。

| 场景 | 实际结果 |
| --- | --- |
| launch / reviewer / startup 三契约 | PASS，候选为 `29c9015ad64c1b3db6c45a8bd2e483e6fab5e193` |
| red / network-closed | 均按预期被 `codex_no_network_denial_in_argv` 拒绝 |
| answer-dropped | 按预期在答复后 worker 未继续的等待处失败 |
| shared-temp-writable | 按预期抓住 `/tmp` 范围外实际写入成功 |
| native-tools-unrestricted | 按预期抓住原生 Write 实际写入 Y 成功 |
| T-131 / T-132 | PASS，原始 oracle 未改 |
| green | INCOMPLETE：原生 MCP 返回 `No such tool available: mcp__t141_user__ping`；此前 Codex issue/答复/继续、两类 CLI 的 shell 探针和 Claude 原生 Write 边界已走到 |
| T-140 | INCOMPLETE：T-D writes 超时；原生 `codex_folder_trust_requested` 指向独立 demo 仓库，产品按裁定没有代按 Trust |

MCP 根因不是工具名或权限拒绝：该 worker 原生 transcript 的直接工具与 deferred 工具清单里都没有 MCP，也没有 pending/failed MCP 服务；隔离 HOME 顶层 `mcpServers.t141_user` 存在，但 `--setting-sources ""` 同时屏蔽 user-scope MCP。针对同一隔离 HOME 的原生命令 `claude --setting-sources '' mcp get t141_user` 返回未找到，`--setting-sources user` 可连接。后者会同时启用用户设置，故不作为产品修复。

本轮在现有启动 builder 中只读检查 `$HOME/.claude.json` 顶层 `mcpServers`；非空时以文件路径传给原生 `--mcp-config`，不复制凭据、不把服务配置或其他用户设置写进 argv。原生解析该文件的 MCP 部分，不合入文件权限、hooks 等设置。没有 MCP 时不加参数。reviewer 门禁仅同步这个可选参数：路径必须是该 launch HOME 的 `.claude.json`，其他位置拒绝；原有边界检查不放宽。此路径支持用户作用域 MCP；项目 `.mcp.json`、局部/插件 MCP 与自定义 `CLAUDE_CONFIG_DIR` 不在本轮已验证范围，README 不宣称它们已加载。

无模型交互探针 `t141_probe_claude_mcp.py` 使用新隔离 HOME、自己创建的 stdio 服务与无输入的原生 CLI。`mcp-native-load-probe-02.json` 为 PASS：负例没有服务请求，显式加载收到 `initialize`、`notifications/initialized`、`tools/list`，原始目录 `/private/tmp/t141-mcp-probe-r938da6t`。它证明加载，不证明工具执行。首轮 `mcp-native-load-probe-01.json` 因 CLI 未在 SIGTERM 后 10 秒内退出而 INCOMPLETE；未跑到正例，不能作加载证据；其子进程最终退出未经核对，原目录保留。探针现在仅对自己新建的进程组发 SIGKILL 并 wait，记录 pid，避免同类清理悬置。

新 e2e 在调用 MCP 前先用原生 `ToolSearch` 精确发现工具，并新增发现成功断言；原来的 `claude_mcp_result_reaches_worker` 仍要求真实非错误工具结果包含 `T141_USER_MCP_OK`，服务 tools/call 收据也仍必须存在，没有改成功期望。新参数契约在修前 `29c9015ad` 红（`mcp-config-red-03.json`）、修后绿（`mcp-config-green-03.json`）；生产 builder → 门禁及外来 MCP 路径反例为 `reviewer-contract-05.json`，原生启动信号为 `startup-green-04.json`。`runner03-preflight.json` 核对脚本进入本仓库且有 13 个不同场景；`t140-fixture-only-delta.json` 用 AST 比较证明除了隔离 config.toml 的内容外，T-140 的所有 Python 节点保持不变。它们不代替本轮完整原生 e2e。

T-140 获准修改的位置是 `workbench/tests/test_t140_extra_dirs_e2e.py:155-158`：旧 config.toml 只有本地 provider；新配置在 provider 前加入 `[projects."<fixture.repo.resolve()>"]` 与 `trust_level="trusted"`，仅指向该测试新建的 demo 仓库，写在自己的隔离 CODEX_HOME。没有改变断言、检查名、期望值或超时。依据为执行主控在本会话逐字裁定：“允许你只改 workbench/tests/test_t140_extra_dirs_e2e.py 的夹具配置——在它自己的隔离 CODEX_HOME 的 config.toml 里把该测试创建并核对过的 demo 仓库标为 trusted；不得改任何断言、检查名、期望值或超时。”

第三轮曾通过 `20261023T140702Z-worker:b23-t141-issue-001` 上报 T-140 reviewer/monitor 的独立目录信任前置（原文 `issue-t140-trust-followup.md`）。本轮 reviewer 以每会话 untrusted 打开，不再需要信任其父目录；monitor 仍沿用用户配置；outside-03 已实测走过 Codex monitor，本轮不扩大其夹具信任。

## RUN-OUTSIDE-01 失败与第二轮修复（历史）

原始结果目录为 `outside-XATDqKD0/`，保持原样，归档由执行主控负责。入仓库的小摘要为 `outside-01-summary.json`；`diagnosis-outside-01.json` 保存只读 SQLite 摘取与 Electron 监听日志。没有把环境或启动失败算作变异被抓住。

| 失败场景 | 已观察的根因 | 本轮修改与验证边界 |
| --- | --- | --- |
| T-131 / T-140 / T-132 Claude worker 不发首个请求 | 信任确认事件后，`worker_startup_unrecognised` 中保存第二个 Settings Warning：`mcp__*` 在 allow 规则中无效。不是信任按键失效；T-132 同一原因 | 删除无效 allow 规则，改用官方支持的 MCP 前缀 hook matcher 与 PreToolUse allow 输出；信任按键和三个 oracle 均不改。本地新增契约在旧实现红、修后绿；真实回归待 RUN-OUTSIDE-02 |
| answer-dropped / shared-temp-writable / native-tools-unrestricted 均停在 native refusal then issue | Codex 还没进入首回合，已记录 `codex_folder_trust_requested`；只信任夹具父目录不能覆盖独立 demo Git 仓库 | 新 e2e 的隔离 home 明确信任已核对的 demo 仓库本身及已创建的 `state/review-copies`，不修改真实用户 home。新启动结果待外部复跑 |
| green 在 project 页前连接拒绝 | 客户端报 `127.0.0.1:65535` 拒绝连接；同一实例的 `electron.log` 公布 DevTools 监听 `127.0.0.1:49154`。当时的请求端口与监听端口不一致，没有 worker 启动 | 新 e2e 使用该实例日志公布的原生监听端口，并记录预分配端口和实际监听地址；不继续查询预分配猜测值。导致原先端口不一致的更下层原因未证明，不归到 MCP 或信任错误 |

MCP hook 使用[Claude 官方 hook 文档](https://code.claude.com/docs/en/hooks#pretooluse-decision-control)的 matcher 与 `hookSpecificOutput.permissionDecision`，原有 signal hook 仍对全部工具记录事件；MCP 授权组仅对 MCP 工具运行，Bash/Read/Edit/Write 不会匹配。reviewer 参数门禁逐项核对该组，扩大到全部工具或删掉此组均被本地反例拒绝。它不是放行 Settings Warning 的补按键路径。

本轮本地证据：`launch-mcp-rule-red-02.json` 在修改生产代码前拒绝 `0a71ffc1a` 候选的旧无效规则；`launch-mcp-rule-green-02.json` 核对 MCP matcher 的正反例并执行原生 hook JSON 命令；`reviewer-contract-04.json` 核对新启动记录及 MCP matcher 放宽/缺失反例；`startup-green-03.json` 保持三类启动处理与后续 idle 不代替 Stop；`runner02-preflight.json` 核对新脚本工作目录与 12 个不同场景。Python/zsh 语法与 diff 检查通过。它们不替代真实 CLI 的 MCP 调用与回归。

用户裁定由执行主控在本会话转述，引用 `20261023T125315Z-ideation-answer-001`：MCP 选 A，放开用户 MCP；硬边界只对原生文件工具与 shell 成立，MCP 写入不在边界内；门禁路径检查照旧。**用户 MCP 服务的写入权限不由 Bash 文件沙箱限制**，README 已明确，不宣称 MCP 写入也被限制在 worktree。

未改 `claudeLaunch.ts`：其中 strict MCP 参数属于旧的隔离 controller 入口；本任务明确针对 worker/reviewer，实际路径在 `panes.ts`。

## 已取得的证据

| 检查 | 结果与范围 | 文件 |
| --- | --- | --- |
| 新启动契约修前 | 预期红态：Claude 仍禁止用户 MCP | `launch-red.json` |
| 同一启动契约候选 | PASS；执行 Claude 参数生成器并核对 Codex 启动源约束，不是原生权限证明 | `launch-green-02.json` |
| 真实生产启动记录 → 真实 reviewer 参数门禁 | PASS；两类 CLI 的合法记录通过，扩大写入根、改审批策略、注入 Git 配置、错配工作目录均拒绝 | `reviewer-contract-03.json` |
| trusted 初次放行修前反事实 | 预期红态：起点源码不能按原生 ready 包放行 | `startup-red-01.json` |
| 初次放行候选与独立屏幕样本 | PASS；分包、仅一次放行、后续 idle 不替代 Stop；其他 app、普通文本、进程身份不明、已停止均不放行；外部 untrusted/unset 屏幕只选 restricted/不选 Trust | `startup-green-02.json` |
| 主控沙箱外三种目录信任探针 | 已观察 trusted 有 ready 包；untrusted/unset 停在各自对话框，没有首回合前 SessionStart；零模型调用。原始摘要的 INCOMPLETE 状态保留 | `probe-codex-start-01/*.json`、`outside-startup-facts.json` |
| 原生 untrusted 选项后续探针 | PASS（仅启动信号）：等屏幕安静再选 Open restricted 后收到 ready 包；零模型调用 | `restricted-startup-facts-02.json` |
| 主控沙箱外目录信任继承三变体 | PASS 仅指独立观察符合三种期望；CLI 0.163.0，无模型、无代按信任。原始摘要的 INCOMPLETE 保留，不当作整票 PASS | `probe-trust-inheritance-01/facts.json`、同目录原始脚本与摘要 |
| IPC 与起点比较 | PASS 仅指“不更差”：起点与候选同样在过期的 handler 名单断言失败；两者都不是 IPC 绿态 | `ipc-comparison.json` |
| RUN-OUTSIDE 工作目录修复 | 修前从仓库父目录运行，修后正确进入本 worktree，且先核对测试入口存在；只执行脚本前缀 | `runner-root-red.json`、`runner-root-green.json` |
| Python / zsh 语法、diff 空白检查 | PASS；不代替真实运行 | 下方重现命令 |

第一轮 reviewer 契约夹具因继承 a2a Git hook 而初始化失败，保留 `reviewer-contract-01.json`；夹具改为初始化时禁用该夹具 Git hooks 后重跑通过。首轮 untrusted 探针过早按 Enter，没有取得 ready 包，保留 `restricted-startup-facts.json`；按生产入口已有的安静等待规则修正探针后取得后续观察。它们均不算业务红态。

本地重现（输出换成未存在的新路径）：

```sh
node workbench/tests/test_t141_launch_contract.mjs <新摘要>
node workbench/tests/test_t141_reviewer_contract.mjs <新摘要>
node workbench/tests/test_t141_startup_signal.mjs <新摘要> [源码根目录]
python3 -B workbench/tests/test_t141_t127_oracle.py --summary <新摘要>
python3 -B workbench/tests/t141_probe_codex_start.py --trust untrusted --open-restricted --summary <新摘要>
python3 -B workbench/tests/t141_probe_claude_mcp.py --summary <新摘要>
PYTHONPYCACHEPREFIX=/tmp/t141-pycache python3 -m py_compile workbench/tests/test_t141_loosened_limits_e2e.py workbench/tests/t141_probe_codex_start.py
zsh -n evidence/2026-10-23-batch23/T-141/RUN-OUTSIDE-01.sh
zsh -n evidence/2026-10-23-batch23/T-141/RUN-OUTSIDE-06.sh
git diff --check
```

修前启动信号测试的源码由 `git archive 3f8813b0e workbench/src workbench/roles workbench/terminal workbench/hooks` 解到独立 `/tmp` 根，再链接现有 `workbench/node_modules` 和 `package.json`；该根作为测试第二参数，不修改当前候选。

## 待运行的真实入口与局限

下一轮运行 `zsh evidence/2026-10-23-batch23/T-141/RUN-OUTSIDE-06.sh`，创建新的 `outside06-*` 证据目录，只跑第六轮列出的五场。第五轮的其他 25 场已符合预期，本轮没有生产源码改动，不重复运行全套；两个目录场景的故障注入修复尚无原生运行结果。脚本仍要求在指定行为断言处抓住坏实现，环境失败、超时或无关早拒均不计通过。历轮结果均保留。

新 e2e 使用真实后台、真实门禁、真实 Electron 和已安装的交互 Claude/Codex CLI；Messages/Responses 由本地脚本接口驱动，**不证明模型会自发理解或选择 issue 工作流**。它实际驱动原生审批拒绝，再驱动 issue，并核对问题面板、主控接口答复和 worker 继续交付；不以 answer_registered 事件替代送达。

只读 behavioral-acceptance-review 针对冻结候选 `bf3d00a82` 给出 FAIL：外部脚本多退一级目录、e2e 缺原生文件工具调用。原报告保留在 `acceptance-review-01.md`。后续修复脚本路径，补 Claude 原生 Write 的额外目录成功与范围外拒绝、CLI 工具结果和测试进程实际文件读回；shell 探针的结果也由测试进程读回文件核对。新增 `native-tools-unrestricted` 反例。脚本目录已取得独立红绿，原生 Write 用例与反例已在 outside-02 真实抓住边界与放宽变异；没有把这些修复当作新候选独立审查通过。

MCP 放在测试专用 `$HOME/.claude.json` 的顶层 `mcpServers`，属于用户作用域配置；服务的 tools/call 收据与 CLI 工具结果共同证明调用。Codex 使用 `/tmp` 下的隔离 home，仅有夹具 provider、已核对 demo 仓库与 `state/review-copies` 的 trust 和两条 git allow 规则；使用无凭据的本地接口，故没有复制 auth.json，结束会删除整个隔离 Codex home。未写真实 `~/.claude`、`~/.codex`。

| 任务卡条件 | 当前结论 |
| --- | --- |
| Claude / Codex 公开地址 curl 成功 | outside-05 green PASS。仅公开 HTTPS，其他协议未验证 |
| 用户 MCP 可调用 | outside-05 green 的原生工具结果与服务回执 PASS |
| 原生审批拒绝 → issue 面板 → 主控答复 → 原 worker 继续 | outside-05 green PASS，丢答复变异被指定行为检查抓住 |
| 原生文件与 shell 越界拒绝、额外目录可写 | outside-05 green 与 T-140 PASS，放宽变异均被指定行为检查抓住 |
| 完整 argv、reviewer 不因新参数被拒 | outside-05 green 与 T-127 绿态 PASS；T-127 剩余四个隔离场景见第六轮 |
| 原始版本红态、至少两个变异 | outside-05 red 与 T-141 四个变异全部按各自行为检查失败 |
| T-127 / T-140 / T-131 / T-132 回归 | outside-05 的四个绿态回归均 PASS；剩余四个隔离场景按第六轮诊断处理，目标五场待 outside-06 |

临时目录：outside-02 的 Codex 原生共享临时根拒绝和 tempfile 可用符合要求，`shared-temp-writable` 被实际 `/tmp` 写入抓住。Claude 保留 CLI 原生的每用户临时目录：[官方沙箱文档](https://code.claude.com/docs/en/sandboxing#temporary-directories)说明其用于 sandbox shell 临时文件，T-122 既有探针也记录强行禁止会破坏 shell；本票不在没有独立原生证据时改写该机制。影响是原生 CLI 必需的临时区仍属例外，不能宣称只可写 worktree/请求目录/额外目录这三类路径。新测试分别记录 `/tmp`、原 `$TMPDIR`、实际 shell TMPDIR 与 tempfile 的结果；outside-02 green 中 Claude 的 `/tmp` 与原 `$TMPDIR` 写入均 false、实际 shell TMPDIR 为 `/tmp/claude-501`、tempfile true；新候选仍待复跑，不把历史探针当新候选通过。

执行主控补充了 Codex CLI 0.163.0 的三种无模型原生观察，脚本与摘要原样保存于 `probe-trust-inheritance-01/`：

| 已配置的信任与新目录结构 | 实际观察 |
| --- | --- |
| 信任主仓库，Git worktree 放到另处 `state/worktrees/demo/T-1` | 继承主仓库信任，直接进入输入框，出现原生 ready 包 |
| 信任 `state/review-copies`，在其下创建非 Git 目录 `r-1` | 继承祖先信任，直接进入输入框，出现原生 ready 包 |
| 信任父目录，在其下新建独立 Git 仓库 | 不继承父目录信任，出现 Trust this folder?，没有 ready 包 |

这些是原生信任继承事实。按本轮裁定，产品 reviewer 不能因此继承已信任祖先而加载候选配置；每个审查副本显式设为 untrusted，由后台选择不保存信任的 Open restricted。worker worktree 继续继承项目仓库信任；worker/monitor 尚无适用信任时上报，等用户自己处理，a2a 不代按 Trust and continue，不写 `~/.codex`。这组三变体只证明当前 CLI 的信任继承，不证明网络、工具权限或完整 e2e。原始摘要仍为 INCOMPLETE，观察事实单独汇总，不改原始状态。

inbox `20261023T125143Z-worker:b23-t141-issue-001` 的 T-140 夹具信任担忧已由 outside-02 实际确认：Codex 正确停在未设置信任处。本轮仅按新裁定修复 demo 的夹具配置，未改产品信任处理。

Codex 无额外目录的 monitor 继续使用原有 read-only 模式；本票真实网络验收针对 worker/reviewer，不宣称此 monitor 网络已放开。原始夹具、截图和大日志由执行主控依 T-088 归档；本 worker 未删除已有现场。session 开始及提交前 project-map status 为 0 problems / 0 stale。

## 留给构思主控同步的治理文字

本 checkout 的 `AGENTS.md` 共 109 行，全文检索没有“worker 沙箱关网络”或“Codex untrusted”原文，不能给出不存在的行号。请构思主控核对其规范源；本 worker 未改该文件。

- `AGENTS.md:33`：“权限只在工作台内：角色卡、任务卡路径加门禁检查、每会话的 CLI 启动参数、收件箱命令行四层（T-071）。a2a 系统不写 `~/.claude`、`~/.codex` 等全局配置，钩子与权限只经每会话的启动参数传入。”该约束保持；unset 信任由用户自己处理。
- `AGENTS.md:36`：“真实 Codex 验收使用 /tmp 下的隔离 CODEX_HOME：只复制 auth.json；只信任已核对的夹具根目录；只复现用户规则中的 `git add`、`git commit` 两条 allow prefix_rule；hook 只在主控逐次批准后安装。”本次无凭据的脚本接口不需要 auth 副本。
- 关网络与单 socket 原文实际在 `.project-map/tickets/T-075-tracer-bullet-daemon-gate-pane.md:52`：“worker 的每会话启动参数只放行编排后台那一个 Unix socket，网络保持关闭”；第 59 行：“开 Codex 托管网络代理，域名名单留空，只放行后台 socket”；第 131 行记录 A2 未验证成、改走 B。它们是日期记录，由构思主控核对 T-141 后应怎样索引，worker 不改。
- `workbench/README.md`“用户的 Codex home”一节已明确 worker/monitor 继承用户配置、仅审查副本保持 untrusted，理由是候选的 `.codex` 配置、hooks、exec policy 不能影响审查独立；MCP 写入不属于原生文件与 Bash 沙箱边界也已写入该 README。门禁路径检查没有因此放宽。
