# T-044 交接（2026-10-09）

**BLOCKED，等待主控决定回收验收方式；不得关闭 ticket 或采用此候选切换工作台。** 最终 fork 候选 `808156d63ef8e265a0e2c017fae7851e50a51019`，基线 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`，分支 `a2a`，未 push。HTTP/UI 与两次审查分别绑定早期候选 `c4c1aff2b`、`839a1e97c`；不把它们的局部通过移用为最终候选的完整通过。

## 主控需要决定

任务书要求隔离 dev 实例关闭全部 provider，同时要求全程通过门禁回收后截图。实际 create → dispatch → attach 成功，但原生 turn 启动后会进入明确的 `session.status=error`。既有 T-037 `readManagedThread` 保护将它拒绝为 `run_external_unknown`，不能执行 stop/archive。因此没有回收后的真实淡化截图，也没有把 membership 手动改为已结束。

冻结候选上的完整请求/身份见 `reclaim-frozen.jsonl`，首次实测见 `reclaim-01.jsonl`。最小选项：

1. 保持 T-037 回收语义，批准改变隔离验收配置，使用不调用模型的受控原生 provider 夹具取得可运行、空闲、停止和归档事实，再验证门禁与界面。
2. 批准扩大恢复范围，使“原生会话报错、且已核对没有运行实例/活跃 turn/待批准”的会话可以回收；这涉及已验收的保护条件，须重新取得红态与反例。

本 worker 未自行选择、启用 provider、修改回收保护或修改等待期限。还存在下列冻结候选上的测试失败和界面加载未知，不能只解决截图条件便宣布完成。

## 已实现

- `create` 自动建立任务窗口条目，新增可选 title，省略时用 task id；`dispatch` 创建的 thread 自动归入 worker。
- `attach` 接收 task、role、ModelSelection、runtimeMode 和 UTF-8 指令文件路径，创建普通 Synara local thread 并发送指令。它不建立交付 attempt，只记录 attached 事件；该事件不绑定当前 worker attempt。
- attach 的持久身份与回收位于门禁核心；worker 按 attempt 回收，普通会话按 thread 回收，拒绝同时提供两种身份。成功回收后写入 endedAt，保留成员，界面用既有 Badge 标“已结束”并淡化。这条成功路径尚无完整实测证据。
- 自动归属和人工修正共用任务操作锁，人工修正继续用 revision CAS。门禁状态没有转移到 membership 或上游 ProjectTask/HubWorkItem。
- 已修复审查发现的历史记账问题：attachment 结束事实与完成事件同事务提交；membership 写失败后重复 reclaim 按已持久事实修复归属；人工删除/重加时从 attachment/attempt 派生结束标记。合法旧 worker 缺少新增 `reclaimed_at` 时，从其 append-only reclaimed 事件取结束时间。该旧格式支持有独立反例，不是推测性兼容分支。

Tracer bullet 为公开 HTTP → 同一核心 → 原生 orchestration → 独立 membership → 任务窗口；Deep modules 的状态写入责任仍在门禁核心；Ubiquitous language 沿用现有 task、attempt、thread。没有增加运行依赖、MCP create/dispatch/attach 工具或第二套业务状态。界面仅复用现有栏、Badge 和字号，没有新建通用组件。

## 验收证据与限制

| 条件 | 结果 | 证据 |
| --- | --- | --- |
| 缺失实现的红态 | PASS（新合同红态） | `red-02/trace.jsonl`、`red-02/scenario-source.py`：真实 HTTP create 成功但 membership 不存在，attach 被 schema 拒绝；`red-cli-attach.json` 是 CLI 不支持 role 的原始输出 |
| 自动 create/dispatch/attach | PASS（HTTP、存储与原生消息创建） | `window-frozen/trace.jsonl`、`fixture.json`；provider 关闭，不证明实际模型执行 |
| 输入变化 | PASS（早期候选 HTTP 与原生持久字段） | `sentinel-frozen/trace.jsonl`、`native-model-readback.json`：monitor/sentinel 与 reviewer 的模型、参数、project/runtimeMode/envMode 经原生 projection 读回；不证明实际 provider 执行。指令仍是同一固定输入，缺少变化后的原生指令读回 |
| attach 不能交付/推进业务状态 | PASS（实际 MCP handler 内部身份检查）；真实活跃会话认证链 INCOMPLETE | `submit-counterexample-frozen.log`：用 reviewer caller 与有效 worker task/attempt/session/fence/spec_rev/commit，经实际 `a2aSubmitTool.handler` 拒绝；10 个变更命令均拒绝，任务前后相同。caller/turn 活跃断言由夹具提供，不是真实 provider/Gateway 认证实测 |
| 回收与淡化历史 | BLOCKED | `reclaim-frozen.jsonl`：error 会话被既有门禁保护拒绝；未伪造 endedAt、未取得淡化截图 |
| T-038 membership 场景 | PASS（HTTP） | `membership-frozen.jsonl`、`membership-boundaries-frozen.json`：两任务、worker/reviewer、旧 revision、未知项目/thread、重复成员、跨项目、门禁 project 不匹配、OPTIONS/origin；外部持锁时人工保存返回 operation_busy，读回不变。CAS 起始 revision 来自先前 GET，不再假设 create 后为 0 |
| 35 项首轮 | PASS（运行期间候选有变化，不能为最终提交背书） | `orchestration-01/` 18/18，`delivery-recovery-01/` 17/17 |
| 18 项冻结候选 | NO_GO，17/18 | `orchestration-frozen/command.json`、`trace.json`；自动成功后的幂等 reclaim 用例在 submit 收到 operation_busy，原因未确定 |
| 17 项 c4 冻结候选 | PASS，17/17 | `delivery-recovery-frozen/` |
| 18 项 839 候选 | PASS，18/18 | `orchestration-final/`；不覆盖后续的旧格式字段修复 |
| 35 项最终候选 | NO_GO，34/35；1 项夹具 INCOMPLETE | `last-orchestration/`：17/18，首项读取 native store 时缺少 thread，KeyError，trace 分类 fixture-error；`last-delivery-recovery/`：17/17。最终两组顺序运行，没有改变断言或期限，未把夹具失败归因到产品或上游 |
| fmt / lint / typecheck | PASS（最终提交） | `fmt-last.*`、`lint-last.*`、`check-last.*`；lint 868 warnings、0 errors |
| attachment 历史记账与回放 | PASS（最终 CLI/Git/SQLite；native 边界受控） | `lifecycle-event-red`、`lifecycle-readd-red` 在业务断言失败；`event-last`、`membership-last`、`legacy-worker-last` 通过。`lifecycle-proof.ts` 注入真实 SQLite 事件/归属写失败，检查完成事件恰一次、回滚、重复 reclaim 修复与业务状态不变 |
| 旧 worker 格式 | PASS（独立旧格式字段反例） | `legacy-worker-red.log` 原样保存已回收 worker 时丢标记；`legacy-worker-last.log` 原样保存及删除/重加均保留标记。旧格式由隔离记录去除新增字段复现，真实 provider 生命周期不在此证明内 |
| 现有 a2a 服务测试 | NO_GO | `core-and-service-01.log`：11 项中 10 通过、1 失败；`service-focused-frozen.log` 单例复跑仍失败，等待 accepted 时实际 verifying，随后 fixture dispose 导致 database is not open 的未处理 rejection。未定位到候选或上游，未改测试 |
| 任务窗口截图 | INCOMPLETE（最终候选）；较早截图是有效的局部观察 | `ui-active-02.png/json` 显示实际任务、worker、reviewer 和原生指令；冻结候选 `ui-active-frozen-failure.png/json` 停在 Loading projects/会话不可用，没有修改 SQLite 来处理加载问题 |
| fresh-context 独立审查 | NO_GO（历史候选）；最终候选未取得独立通过 | `acceptance-review-01.md` 一次 fresh-context 审查为 FAIL；同一审查者一次定向复核 `acceptance-review-02.md` 仍为 FAIL。已按红态修复其旧 worker 发现、补充 membership 故障证据，但没有再做第三轮审查；不声称审查已通过 |

未运行完整 workspace suite；受管回收边界已经需要主控决定，局部测试也有未解决失败。没有通过结论、实际 tier、真实 provider 运行、模型理解、真实 Gateway caller 认证、Electron 原生窗口或生产使用的声明。

## 过程与保留

- 首次 red-01 与 green-01 的 HTTP 请求早于 dev 就绪，连接拒绝属于环境失败，不能算合同红/绿；其 git 场景与 `environment-failure.json` 保留，异常全文仅存在本轮工具输出，没有另存完整 traceback 文件。
- `ui-active-01` 在 Vite 就绪前连接拒绝；run-check 与截图同名 JSON 冲突的失败原样保留，后续命令元数据改用 `.command.json`，没有覆盖旧文件。
- 范围偏离：正式工作台 status 执行了两次。这个入口读取了任务书禁止访问目录内的 `workbench-process.json` 身份元数据，报 PID 身份改变（`formal-status-readonly.json` 保存一次复核输出）。没有直接访问正式会话数据库/profile/endpoint 凭据，也没有启动、停止、重启或写入正式实例；此只读越界不应写成完全遵守目录禁读。之后未再访问正式目录。
- 未运行改写 `apps/*/dist` 的构建命令，未改依赖布局、T-045 worktree、Herdr 或用户 Codex home。先前 dev 的 contracts watch 按既有 dev 命令构建 packages/contracts/dist，不冒充桌面构建或原生 Electron 验收。
- 所有 app provider 关闭；隔离环境、启动 argv、进程身份与停止记录见 `start-*.json`、`dry-run-*.log`、`stop-*.json`。后台实例使用 start_new_session，后续清理核对完整子进程树。
- `provenance.json` 记录版本、规则来源、主控提供的 s5-t044 启动 argv 和 wF:p18（未另行 live 核对）。本 worker 的受管 attempt/session/fence 未提供，保持未知；不把配置当作供应商实际 tier 证明。审查是获分配的 collaboration 子 agent，不是 app provider turn；实际供应商 tier 未验证。skill 源快照在 `skill-sources/`。
- `native-readback-fixture-failure.json` 是读取 HTTP 记录中 null input 的探针错误，修正探针后读回成功；不计产品红态。`host-observation.json` 仅记录负载/内存实测，未据此宣布失败原因。
- 所有自建 dev 服务已停止，5817/7777 无监听；外置盘夹具与旧现场保留。完整隔离 Git repo/worktree 归档在 retained-fixtures 系列文件中，没有登记 gitlink。

## 复现

外置盘挂载，fork checkout 为冻结提交，启动本目录 `start.py NEW_LABEL`；只在 health 的 startupReady 和 Vite 端口均就绪后运行。场景标签必须全新，避免覆盖旧证据。

```sh
python3 evidence/2026-10-09-batch5/T-044/window-scenario.py NEW_LABEL green
python3 evidence/2026-10-09-batch5/T-044/reclaim-scenario.py NEW_RECLAIM_LABEL evidence/2026-10-09-batch5/T-044/NEW_LABEL/fixture.json
python3 evidence/2026-10-09-batch5/T-044/run-check.py NEW_SUBMIT_LABEL /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch5/T-044/submit-counterexample.ts /absolute/path/fixture.json
```

35 项命令、源码副本、环境和输出分别保存在两组 `*-frozen/command.json`。归属场景使用 `membership-scenario.py LABEL http://127.0.0.1:5817 /absolute/path/membership-fixture.json`，后者引用单独创建的测试项目，不操作截图任务的 membership。截图脚本 `shoot.mjs LABEL /absolute/path/fixture.json active` 只读取并导航，没有响应替换或手动编辑归属。
