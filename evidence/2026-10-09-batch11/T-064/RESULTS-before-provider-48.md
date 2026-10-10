# T-064 最终交接

状态：**INCOMPLETE（唯一一次独立审查缺真实 provider 权限请求证据；两项范围内回归已修复，未追审；保持 open，待主控关闭）**。

依据主控 #22/#23、ready_rev 1、[brief](../brief-T-064.md)、[决定 01](controller-decision-01.md)。最终 fork **`49cae984f22924de006e0f8358cb447eb881aaf6`**，基线 `7a3a13249e562bf2d7f9ff4cb024f39b13d62434`。原实现 `0bf4bb2ca`、默认模式修复 `7c04fb3fe`、stop 组合修复 `49cae984f` 均保留，未 push。

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
| 事务崩溃 | crash-transaction-06：真实隔离 CLI 在 role 行写入、输入未插入时 SIGTERM，重启后三者全回滚 |
| 已知坏实现 | parent-native09：父 manager 被 6 个业务断言拒绝；input-mutant09：省略 saveInput 被审计断言拒绝；default-policy-red20：无自定义的 4 个 override 断言失败；stop-unit-red29：修复前 stop 投影被新增断言拒绝 |
| stop 组合 | cap-composition-final22-active：真实 MCP 给构思主控增加 operate 后从 unknown_inbox_entry 变 ideation_required（红）；[cap-composition-final27-active-green.json](cap-composition-final27-active-green.json)：相同缺失条目输入前后均到达 unknown_inbox_entry，stop 权限未被新增能力遮蔽；计时、ACK、目标、身份与中断门禁仍在原核心 |
| 最终检查 | types26、fmt-check26、lint26 通过；server26 369/369；gates23 19/19（gates 文件随后未改）；最终原有 35 项编排/交付/恢复在 final28 原始 command/trace。检查的 dirty 内容与最终 49cae 提交相同，版本与 dirty 状态已记录 |

## 独立审查与待决定

唯一一次 fresh-context 审查目标为 `0bf4bb2ca` + a2a `10718bd2c77b375c3b5fdde3930ba75109400d7e`；[结论](acceptance-review-19.md) **INCOMPLETE**。审查确认 HTTP/MCP/SQLite、UI、原子性和反事实；未重现实现违反，指出 provider 边界缺口：实际 CLI 控制方法可用，不证明实际 Codex/Claude 进程发出并消费 permission request/tool turn。没有拿旧结论替修复版背书，没有第二次审查。

上报 `20261010T073006Z-worker:t064-issue-001`；[最小选项](provider-boundary-needs-decision-22.md)：主控确认无真实模型的实际 CLI + 本机模型 API 夹具入口，或批准少量真实工具 turn 的认证来源/模型/预算，或接受 INCOMPLETE 并切后续验证。未擅自读用户权限配置/Claude 凭据或消耗模型。

审查后实施者另发现并修复两项本票范围内回归，均保留红态：
1. Claude 原候选对默认/普通会话也收紧 MCP，影响 Auto。现在只对显式免确认集合设置 override，默认说明按会话模式/已有授权，4 项红态转绿，含 default-auto。
2. caller 按能力优先选 executor，加入 operate 会遮蔽 stop。stop 工具按其已验证 requiredCapability 投影窄 stop 授权，未改核心 stop 条件；实际 MCP 红绿和旧 tools.ts 反事实均保留。

## 失败方式、范围与限制

并发同角色：一个 200/一个 409，不覆盖、不记伪成功。中途退出：配置/输入/审计同事务回滚。未知能力：拒绝新保存；保留已存原值、停止签发，CAS 恢复把原值写 before。全能力去掉：新目录为空、调用拒绝。运行中变更：旧凭据不动，新签发才生效。

上游仅获批 8 文件：settingsNavigation、settings route、Services/Layers 的 SessionRegistry/Credentials、Codex manager、ClaudeAdapter；其它在 gates/contracts/server a2a/web a2a 内。未改 computerToolPermission、OpenCode、ACP、Devin、Cursor、Grok、Droid、sessionLease、用户 CLI 权限配置、AGENTS/CONTEXT/地图。免确认仅 Codex/Claude，页面已明示。

真实 HTTP/MCP/SQLite/UI 与 CLI 控制进程成立；provider 运行事实/原生 I/O 在免确认逻辑测试中受控。无新真实模型 turn、认证副本、桌面构建/发布、整仓测试或用户外观验收。仅操作自建隔离实例、外置盘缓存；未读写正式工作台数据或停用户 Herdr。只提交本票文件和 Resolution，保留他人 dirty 日志及 .grok/。

## 原始失败与重放

原 gate 报告在 RESULTS-preflight-01，首候选报告在 RESULTS-candidate-01。类型/配置打包、ISO Z、导览、普通闲置、UI 未等 web-ready 的准备失败保留；不是产品红态。cap-composition 首轮比较了两个闲置拒绝，不能证明组合性质；随后先重建活跃状态，保存真正业务红态，绿态独立断言缺失条目应到达 entry 校验，未把“同样拒绝”当通过。

每次换新 label/root/output 编号；start-server-03 + settings-entry-05 为真实 API，start-web-10 + run-ui-11 为实际 UI；cap-composition-probe-25 另传新结果名；各检查 argv/exit 在 JSON，固定编号脚本不得覆盖原输出。共享原日志的尾部空白使 staged-diff-check-18 为 2，未改写原日志，不写通过；源码 fmt/diff 检查通过。

隔离 SQLite/Git/control 现场在 retained-fixtures-16 与 retained-final-fixtures-30 归档；排除 token、auth、浏览器 profile，原目录保留，不登记 gitlink。Herdr 交付两仓库提交 + DONE 行，无门禁 submit/attempt/session/fence，绑定 ready_rev 1、主控 #22/#23、决定 01 和完整代码版本。待主控审修复 diff 与补齐真实 provider 边界后关闭。
