# T-064 最终交接

状态：**PASS（worker 执行结论，限本票批准范围；决定 02 的真实 provider 补证已完成。唯一独立审查的历史结论仍为 INCOMPLETE，未追审，补证交主控自审；保持 open，待主控关闭）**。

依据主控 #22/#23/#24、ready_rev 1、[brief](../brief-T-064.md)、[决定 01](controller-decision-01.md)、[决定 02](controller-decision-02.md)。最终 fork **`49cae984f22924de006e0f8358cb447eb881aaf6`**，基线 `7a3a13249e562bf2d7f9ff4cb024f39b13d62434`。原实现 `0bf4bb2ca`、默认模式修复 `7c04fb3fe`、stop 组合修复 `49cae984f` 均保留；决定 02 后未改生产代码，补证固定在该提交，未 push。

## 已完成

工作台设置“角色权限”有五角色、六种 a2a 能力、工具免确认、恢复默认、可读变更。新凭据冻结能力/免确认，旧凭据不变；无免确认自定义沿用 provider 原模式，显式空集合保留。每次成功保存/恢复由 A2AGates 同一 SQLite 事务写配置、action/settings-page 用户输入和追加审计；每角色 revision CAS。

Tracer bullet 贯穿配置、签发、真实 HTTP/MCP/SQLite 与 UI。Deep modules：业务定义/存储在 gates rolePermissions，删原能力重导出；无平行门禁、策略引擎、重试、双写或降级。Ubiquitous language 沿用现有五角色、能力、凭据、用户输入。

| 范围 | 最终证据与实际边界 |
| --- | --- |
| 父红态 | navigation-red01：真实导航缺页、断言退出 1；http-contract-red03 为未挂载 API 的补充 503，不把静态目录缺失当产品缺陷 |
| 五角色、变更、冻结 | [final27-entry/oracle.json](final27-entry/oracle.json)：最终提交真实 owner HTTP/MCP，手写默认集合、新旧 token、实际 status/raise 成功与 submit 拒绝、空集合、恢复、未知保存值/签发拒绝、并发 CAS、dismiss/blocking 底线、逐条原子审计均通过 |
| UI | [final24b-ui-oracle.json](final24b-ui-oracle.json) 和五角色/custom/reset 截图：真实设置页保存/恢复并读回服务器；运行版本 7c04，之后只改 server a2a stop 投影，UI 源码未变。外观由用户判断，未自行判美观 |
| 默认反例、普通会话 | ordinary-raw15/ordinary-and-audit-14：真实普通签发维持父六种通用能力，MCP 无 a2a 工具、活跃调用拒绝；最终默认/普通 Auto 不设置 Claude override，见 default-policy-red20/green21 |
| provider 决策逻辑 | Codex manager 原审批入口、Claude adapter 的 canUseTool/批准事件与失效/闲置/退休/Plan/错 server/未勾选反例通过。原生传输和活跃事实受控，不能据此称真实 provider 进程完整闭环通过 |
| Claude 实际控制协议 | claude-protocol-probe-02：SDK 0.3.259 + 实际 CLI 2.1.296 接受 synara mode 收紧/清除，0 用户消息/模型 turn；仅证明 API 可用 |
| Codex 真实权限边界 | [codex-good53-real/runtime-events.json](codex-good53-real/runtime-events.json)：实际 app-server、approval-required、真实活跃 worker turn；checked raise 完成并有核心问题行，unchecked submit 发出 mcpServer/elicitation/request，保持未批准。实际进程的坏候选被同一 contract46 断言退出 1 拒绝；最终对照共 2 个 turn，加保留的首次两次，累计 4/4 |
| Claude 真实权限边界 | [claude-good40-real/runtime-events.json](claude-good40-real/runtime-events.json)：实际 CLI 2.1.296 经 Synara ClaudeAdapter + SDK 0.3.259，full-access 下显式 override 仍让 unchecked submit 发出 canUseTool/request，checked raise 完成并落核心问题行。坏候选同一断言退出 1；模型输入来自本机假 Messages API，只证明权限边界，不证明模型行为 |
| 事务崩溃 | crash-transaction-06：真实隔离 CLI 在 role 行写入、输入未插入时 SIGTERM，重启后三者全回滚 |
| 已知坏实现 | parent-native09：父 manager 被 6 个业务断言拒绝；input-mutant09：省略 saveInput 被审计断言拒绝；default-policy-red20：无自定义的 4 个 override 断言失败；stop-unit-red29：修复前 stop 投影被新增断言拒绝 |
| stop 组合 | cap-composition-final22-active：真实 MCP 给构思主控增加 operate 后从 unknown_inbox_entry 变 ideation_required（红）；[cap-composition-final27-active-green.json](cap-composition-final27-active-green.json)：相同缺失条目输入前后均到达 unknown_inbox_entry，stop 权限未被新增能力遮蔽；计时、ACK、目标、身份与中断门禁仍在原核心 |
| 最终检查 | types26、fmt-check26、lint26 通过；server26 369/369；gates23 19/19（gates 文件随后未改）；最终原有 35 项编排/交付/恢复在 final28 原始 command/trace。检查的 dirty 内容与最终 49cae 提交相同，版本与 dirty 状态已记录 |

## 独立审查与主控决定

唯一一次 fresh-context 审查目标为 `0bf4bb2ca` + a2a `10718bd2c77b375c3b5fdde3930ba75109400d7e`；[结论](acceptance-review-19.md) **INCOMPLETE**。审查确认 HTTP/MCP/SQLite、UI、原子性和反事实；未重现实现违反，指出 provider 边界缺口：实际 CLI 控制方法可用，不证明实际 Codex/Claude 进程发出并消费 permission request/tool turn。没有拿旧结论替修复版背书，没有第二次审查。

上报 `20261010T073006Z-worker:t064-issue-001`；[最小选项](provider-boundary-needs-decision-22.md) 原样保留。决定 02（a2a `1997a974d5d55b71cc1d89c2b38e02802ec4206e`）批准最多 4 个隔离 Codex turn 和真实 Claude CLI + 本机假 Messages API，并接受两项修复 diff。依此补齐以下证据，没有第二次独立审查；旧审查未改判，新增部分由执行主控自审。

审查后实施者另发现并修复两项本票范围内回归，均保留红态：
1. Claude 原候选对默认/普通会话也收紧 MCP，影响 Auto。现在只对显式免确认集合设置 override，默认说明按会话模式/已有授权，4 项红态转绿，含 default-auto。
2. caller 按能力优先选 executor，加入 operate 会遮蔽 stop。stop 工具按其已验证 requiredCapability 投影窄 stop 授权，未改核心 stop 条件；实际 MCP 红绿和旧 tools.ts 反事实均保留。

## 决定 02 的实际进程补证

Tracer bullet 继续使用真实应用层：设置 API 保存 → 实际 provider 签发/冻结 → 原生 CLI 工具调用 → Synara 权限决策 → 真实 MCP → 核心问题记录或待批准请求。场景固定为 worker 两种能力、仅勾 `a2a_raise`，不勾 `a2a_submit`。原生进程和活跃事实未替换；stop 的额外调用者运行事实另明确标为受控。

| 场景 | 同一外部合同断言 | 原始输入、事件与结果 |
| --- | --- | --- |
| Codex 好候选 | PASS，退出 0 | [contract55](codex-good53-contract55.json)、[native events](codex-good53-real/runtime-events.json)、[核心记录](codex-good53-real/gateway-core-records.json)、[实际 native home](codex-good53-real/actual-native-home.json) |
| Codex 已知坏候选 | NO_GO，退出 1：checked raise 未执行 | [contract55](codex-bad54-contract55.json)、[原始断言失败](codex-bad54-contract55.log)、[native events](codex-bad54-real/runtime-events.json)、[实际 native home](codex-bad54-real/actual-native-home.json) |
| Claude 好候选 | PASS，退出 0 | [contract46](claude-good40-contract46.json)、[native events](claude-good40-real/runtime-events.json)、[核心记录](claude-good40-real/gateway-core-records.json) |
| Claude 已知坏候选 | NO_GO，退出 1：checked raise 未执行 | [contract46](claude-bad41-contract46.json)、[原始断言失败](claude-bad41-contract46.log)、[native events](claude-bad41-real/runtime-events.json) |

[provider-contract-46.py](provider-contract-46.py) 不读驱动 verdict，四次使用同一断言：checked 工具实际返回成功、问题行绑定同一 thread/turn、没有 checked 待批准请求、唯一的 pending 是 unchecked 工具且同一活跃 turn。已知坏实现只在隔离证据进程用 Bun loader 把勾选判断改为一律 prompt，生产 checkout 未改，也未增加第二套产品 API。驱动识别负例的 NO_GO 不是验收通过；相同外部断言的退出 1 才是坏实现被拒证据。

Claude 最小协议探针在 claude-probe36 确认真实 CLI 接受 localhost API、执行 checked raise 并发出 unchecked 权限请求，记录见 [protocol-probe-oracle](claude-probe36-real/protocol-probe-oracle.json)。当次驱动因 live SQLite 锁退出 1，没有把整次运行写成 PASS；后续通过真实 SQL owner 导出事件，不替换 canUseTool、SDK query、MCP 或进程。两份最终原生 init 的 apiKeySource 都为 ANTHROPIC_API_KEY，配置目录在 /tmp，假 key 与 API 由夹具提供，没有读取/复制用户 Claude 凭据或使用真实 Claude 模型。真实 CLI 的 permissions override 与请求流成立；不证明假模型会自行选择正确工具。

Codex CLI 固定 0.162.0、gpt-6.1-sol、显式 Fast、check_for_update_on_startup=false，approval-required。来源 home 只复制 auth.json，夹具信任根及 git add/commit 规则由脚本创建，无 hook。最终两次的实际 CODEX_HOME 也由 CLI 启动器核对为 /tmp 下的 Synara native overlay，不只核对认证来源目录；来源和 native home 均已整目录删除。Fast 是请求参数，供应商实际 tier 未核实。预算 [codex-turn-budget-42.jsonl](codex-turn-budget-42.jsonl) 已预留并实际使用 4/4，四份 journal 各一个 turn.started，没有额外模型 turn。未发送 accept/acceptForSession；pending 请求保持未批准，随后以 owned interruption 结束实际进程，再走 reclaim。初次两次及准备失败见 [执行回执](real-run-receipts-48.json)，最终两次见 [cleanup-final-native-56](cleanup-final-native-56.json)，完整 argv/版本/输入/清理在各场景记录中。

原 codex-good44/bad45 的权限结果成立，但 Synara 自动创建的实际 CODEX_HOME 在外置盘，与决定 02 的 /tmp 位置要求不完全一致。归档检查时发现后保留原证据、上报 `20261010T085249Z-worker:t064-issue-001`，清理旧 native overlay，用剩余两次预算修正夹具并重跑。见 [isolation-correction-53](isolation-correction-53.md)、[cleanup-native-home-52](cleanup-native-home-52.json)。未改生产适配器；旧隔离位置缺项未被隐藏，也未以旧两次单独宣称严格隔离通过。

实际入口的重放命令为 `python3 evidence/2026-10-09-batch11/T-064/real-provider-33.py <新编号> <codex|claudeAgent> <good|checked-prompts>`；好 Codex 的 stop 记录另设 T064_STOP_RECORD=1。Codex 本次预算已用尽，驱动拒绝第五次，再运行须另获批准。只重读已有机械证据：`python3 evidence/2026-10-09-batch11/T-064/provider-contract-46.py evidence/2026-10-09-batch11/T-064/<编号>-real`。后者好候选退出 0，坏候选退出 1，无模型调用。所有新证据绑定 fork 49cae；原有 types/fmt/lint、369+19 和 35 项场景不因证据文档变化重复运行。

## 失败方式、范围与限制

并发同角色：一个 200/一个 409，不覆盖、不记伪成功。中途退出：配置/输入/审计同事务回滚。未知能力：拒绝新保存；保留已存原值、停止签发，CAS 恢复把原值写 before。全能力去掉：新目录为空、调用拒绝。运行中变更：旧凭据不动，新签发才生效。

上游仅获批 8 文件：settingsNavigation、settings route、Services/Layers 的 SessionRegistry/Credentials、Codex manager、ClaudeAdapter；其它在 gates/contracts/server a2a/web a2a 内。未改 computerToolPermission、OpenCode、ACP、Devin、Cursor、Grok、Droid、sessionLease、用户 CLI 权限配置、AGENTS/CONTEXT/地图。免确认仅 Codex/Claude，页面已明示。

**被用户授予 stop 的其他角色，其 stop 在核心记录中按 ideation 地址、真实 thread 记录**。实际例见 [stop-address-record](codex-good44-real/stop-address-record.json) 和 [MCP 回执](codex-good44-real/stop-mcp.json)：executor 凭据明确包含 a2a:stop，真实 caller thread 为 3a1babfb-b29b-4eff-ac21-ede8303b05b3；满足原 2 分钟、无 ACK 等条件后核心事件 actor 为 ideation，details.thread 为被中断的真实 worker f032bf4c-116c-4e37-b57f-9e523514b27d。这里核心事件的 thread 是目标，调用者 thread/turn 仍由网关凭据绑定、传入核心，但没有另复制到该事件字段。额外 executor 的活跃运行事实受控，目标是真实 Codex CLI；没有为 stop 增加模型 turn。字段差异已上报 `20261010T084028Z-worker:t064-issue-001`，未改核心条件。

另发现原生 interrupted 与最终 completed 投影分歧，见 [原始关联记录](terminal-projection-observation-47.json)、[范围外上报](terminal-projection-issue-47.md)，收件箱 `20261010T084341Z-worker:t064-issue-001`。本票权限合同取自中断前的 MCP 结果和请求，stop 地址取自核心事件；不宣称整个中断终态链路正确。没有修改未批准的 ProviderRuntimeIngestion/ProviderCommandReactor，交主控另审。

真实 HTTP/MCP/SQLite/UI 和两种 provider 的工具权限边界均有证据；闲置、普通、失效等其余逻辑反例仍使用已标明的受控测试。无桌面构建/发布、整仓测试或用户外观验收。仅操作自建隔离实例、外置盘缓存；未读写正式工作台数据或停用户 Herdr。只提交本票文件、自己追加的问题和 Resolution，保留他人 dirty 日志及 .grok/。

## 原始失败与重放

原 gate 报告在 RESULTS-preflight-01，首候选报告在 RESULTS-candidate-01。类型/配置打包、ISO Z、导览、普通闲置、UI 未等 web-ready 的准备失败保留；不是产品红态。cap-composition 首轮比较了两个闲置拒绝，不能证明组合性质；随后先重建活跃状态，保存真正业务红态，绿态独立断言缺失条目应到达 entry 校验，未把“同样拒绝”当通过。

每次换新 label/root/output 编号；start-server-03 + settings-entry-05 为真实 API，start-web-10 + run-ui-11 为实际 UI；cap-composition-probe-25 另传新结果名；各检查 argv/exit 在 JSON，固定编号脚本不得覆盖原输出。共享原日志的尾部空白使 staged-diff-check-18 为 2，未改写原日志，不写通过；源码 fmt/diff 检查通过。

决定 02 的准备失败、驱动定位/锁/回收/生命周期误用均见 [preparation-failures-48](preparation-failures-48.md)，不冒充产品红态，不覆盖旧日志或结果。补证前 RESULTS 保存在 RESULTS-before-provider-48.md；原 INCOMPLETE 和原问题均保留。

隔离 SQLite/Git/control 现场在 retained-fixtures-16、retained-final-fixtures-30、[retained-real-fixtures-52](retained-real-fixtures-52.tar.gz) 与 [retained-final-native-56](retained-final-native-56.tar.gz) 归档；排除 token、auth、浏览器 profile 与 native 下载缓存，应用数据和 Git 原目录保留，不登记 gitlink。首次 62 MB 归档未删，移到自建外置盘目录，位置与原因见 cleanup-native-home-52；该旧归档也排除了 auth/token。新启动服务均已停止，/tmp provider/source/native home 及旧外置盘 native overlay 已删除，见 cleanup-real-49、cleanup-native-home-52 与 cleanup-final-native-56。[最终机械检查](delivery-final-audit-57.json) 核对 4/4 实际 turn、两份真实 native 路径、凭据来源链接、配置和完整 home 删除；不是第二次独立审查。Herdr 交付两仓库已提交版本 + DONE 行，无门禁 submit/attempt/session/fence，绑定 ready_rev 1、主控 #22/#23/#24、决定 01/02 和完整代码版本。待主控自审补证并关闭本票。
