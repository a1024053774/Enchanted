# T-064 工作台角色权限设置

状态：**INCOMPLETE（实现与机械验收通过，等待唯一一次独立审查；保持 open，待主控关闭）**。

依据主控 #22/#23、T-064 ready_rev 1、[brief](../brief-T-064.md) 与 [决定 01](controller-decision-01.md)。fork 基线 `7a3a13249e562bf2d7f9ff4cb024f39b13d62434`，冻结源码 **`0bf4bb2cab2216f567df2d4fb1729bee3cac6fe9`**。未 push，未操作正式工作台。原 BLOCKED 报告保存在 [RESULTS-preflight-01.md](RESULTS-preflight-01.md)，原红态和失败现场保留。

## 行为与证据

工作台设置新增“角色权限”：五角色、六种 a2a 能力、工具免确认、恢复该角色默认和最近变更。能力与免确认在签发时冻结，旧 token 不变。能力与免确认可以分别自定义；无免确认自定义沿用 T-055/T-058 语义，显式空集合不会回退。默认仍是原预设。

Tracer bullet 已贯穿同库配置、A2AGates 写入入口、HTTP、签发、实际 MCP 与设置页。Deep modules：业务定义/存储在 gates 的 rolePermissions，原浅层能力重导出模块删除；没有另写门禁、策略引擎、重试、双写或兼容路径。Ubiquitous language 沿用现有五角色、能力、凭据和用户输入。

| 验收项 | 实际证据 |
| --- | --- |
| 先红后绿 | `navigation-red01.json`：父导航经真实 Vite resolver 加载，没有“角色权限”，合同断言退出 1。`http-contract-red03.json` 的缺 API 落入静态路由、返回 503 是补充现象，不把静态目录缺失当产品缺陷。`http-contract-final11.json`：相同 API 合同在冻结源码通过 |
| 五角色默认 | [final11-entry/oracle.json](final11-entry/oracle.json)：实际 HTTP/MCP 目录逐项对照 spec 第 1 节手写预期，executor 17、ideation 8、worker 2、reviewer/monitor 各 1。浏览器逐角色对照六个能力开关，见 [final13-ui-oracle.json](final13-ui-oracle.json) |
| 自定义与冻结 | HTTP 保存 worker 为 raise/read，旧 MCP token 仍有 submit/raise，新 token 有 events/issues/raise/status；实际 status/raise 成功，submit 返回 capability_denied。空 monitor 新 token 无工具，旧 token 不变；恢复后新 token 回到默认。原请求和回执在 `final11-entry/http-*.json` |
| 免确认正反例 | 实际 Codex manager 原生审批入口、实际 Claude adapter 的 canUseTool/批准事件；覆盖勾选、未勾选、空集合、普通/失效身份、非活跃/过期 turn、退休、其他 server、Plan、stopping、默认 full-access/已有 grant。只控制原生传输/流，不把它说成新模型成功。`server10.log` 含相关测试及既有 T-055/T-061 反例 |
| Claude 协议 | [claude-protocol-probe-02.json](claude-protocol-probe-02.json)：SDK 0.3.259、真实 CLI 2.1.296 在 bypassPermissions 中接受对 synara 的 default 收紧和清除；没有用户消息或模型 turn。失败不加 fallback，适配器沿原启动失败清理路径退出 |
| 结构底线 | 新签发 executor 的实际 MCP disposition：dismiss 返回 user_required，关闭 blocking 返回 blocking_requires_user；设置页没有这两项开关。见原 HTTP/MCP 回执及截图 |
| 输入与审计 | [ordinary-and-audit-14.json](ordinary-and-audit-14.json)：9 次成功 HTTP 变更 + 2 次实际 UI 保存/恢复，11 条 action/settings-page 输入与 11 条追加变更逐条对应，核对 actor、时间、前后值和 input_id；冲突/失败不记伪成功 |
| 普通会话反例 | 真实签发仍是父修订六种通用能力，实际 MCP 不列出 a2a；活跃普通会话调用 raise 返回 capability_denied。见 [ordinary-raw15.json](ordinary-raw15.json) |
| 已知坏实现 | `parent-native09.log`：加载父 Codex manager 时，6 条业务断言失败（勾选 disposition 不放行，未勾选/普通/失效身份的 raise 被放行）；`input-mutant09.log`：省略输入写入被 action/audit 断言拒绝。当前相同测试通过 |
| 真实中断 | [crash-transaction-06.json](crash-transaction-06.json)：隔离 CLI 已写 role 行、尚未插入输入时，核对 PID/argv 后 SIGTERM；重启实际核心，配置、输入和审计全部回滚至默认 revision 0 |
| 产品检查 | 全 workspace typecheck、fmt:check、lint（880 warning、0 error）、migrations:check 通过；服务端相关 365/365、gates 19/19。`types10`、`fmt-check10`、`lint09`、`migrations12`、`server10`、`gates10` 有完整命令/原日志。前几项运行时是 dirty 候选树，其内容与随后冻结提交相同，不声称当时已干净提交 |
| 原有端到端 | 冻结提交下编排 18/18、交付/恢复 17/17，共 35/35；[编排命令](final12-orchestration/command.json)、[交付恢复命令](final12-delivery-recovery/command.json) 与各自 trace 保存原始输出和完整版本 |
| UI | 实际设置入口保存/恢复并读回服务端；[overview14.png](overview14.png)、[audit14.png](audit14.png)、五个 `final13-ui-角色.png` 和 custom/reset 截图作证。复用 SettingsRow/Section、Switch、Button、SegmentedControl 和字体 token。外观由用户判断，本报告不判“美观通过” |
| 独立审查 | 待对冻结源码及本票证据提交进行唯一一次 fresh-context 只读审查；不读 RESULTS、Resolution、inbox 正文、旧审查 |

## 五种失败方式

- 两窗口同时改：真实 HTTP 并发使用同一 monitor revision，恰好一个 200、一个 409；只新增一条输入与变更，不覆盖先保存者。
- 改到一半退出：真实事务中断后配置、输入、审计全回滚，原数据库与中断标记保留。
- 未知能力：新请求拒绝；已存异常可读回、签发拒绝，不悄悄取默认；CAS 恢复把原值保存在 before。
- 全能力去掉：显式空数组保存，新 tools/list 为空，调用拒绝；与无自定义区分。
- 运行中变更：旧凭据的能力/免确认不改，重新签发才用新集合；界面提示“新会话（重新签发凭据）后生效”。

## 范围与局限

上游仅改获批 8 个文件：settingsNavigation.ts、_chat.settings.tsx、Services/Layers 的 AgentGatewaySessionRegistry.ts 和 AgentGatewayCredentials.ts、codexAppServerManager.ts、provider/Layers/ClaudeAdapter.ts。其它源码/测试在 gates/contracts/server a2a/web a2a 内。未改 computerToolPermission.ts、OpenCode、ACP、Devin、Cursor、Grok、Droid 或 sessionLease.ts。

免确认仅对 Codex/Claude 生效，页面已明示，其它 provider 不新增免确认。没有新模型 turn；MCP、HTTP、SQLite 和浏览器是真实应用依赖，provider 活跃状态及传输在权限测试中受控；CLI 控制协议是实际进程。不扩大为生产、全 provider 或真实模型完整闭环。未做桌面构建、打包、发布、整仓测试或用户外观验收。

准备失败保留：types04 设置组件属性、types09 测试 finalizer/null 类型；counterfactual-07/08 配置打包失败不是业务红态，09 才是有效红态；green05 的 Python 3.9 ISO Z 解析错误在 final11 修正夹具后完整复验；final11 UI 被 Import projects 导览挡住，失败截图与原脚本保留，final13 只关闭自己的导览后通过。普通首轮未建立活跃 turn、拒绝结果不同；原 HTTP 未即时保存，后续单独诊断回执明确标为新请求（caller_turn_inactive），15 建立活跃状态并保存完整回执后通过。没有把准备失败当产品缺陷或覆盖现场。

## 重放与隔离

新 label 启动 `start-server-03.py LABEL http://localhost:8088`；串行跑 `settings-entry-05.py LABEL`、`start-web-10.py LABEL`、`run-ui-11.py LABEL NEW_UI_LABEL`。各检查 argv 在对应 JSON；反事实 config 09 用 `T064_COUNTERFACTUAL=parent-native` 或 `missing-input`。固定编号脚本复跑必须换输出编号/隔离根，不能覆盖原证据。

Bun/Node 只经 fork a2a/scripts/bun，缓存与隔离实例在外置盘。没有认证副本、没有用户 Claude/Codex 权限配置或正式工作台数据操作，没有停止用户进程。自建服务经身份核对后停止；retained-fixtures-16.tar.gz 保留 SQLite、控制输入/输出与完整测试 Git 现场，排除 token、浏览器 profile、隔离 HOME，原目录仍保留，不登记 gitlink。主控持续日志与 .grok/ 不提交。

Herdr 交付两仓库提交与 DONE 行，不走门禁 submit，无本票 attempt/session/fence；执行绑定 ready_rev 1、主控 #22/#23、决定 01 与完整 fork 版本。
