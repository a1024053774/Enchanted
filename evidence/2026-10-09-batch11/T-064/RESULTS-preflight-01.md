# T-064 工作台角色权限设置：批准门槛交接

状态：**BLOCKED（待执行主控批准上游接入并确认免确认默认/生效时点；尚未实现）**。

依据主控 #22、[brief](../brief-T-064.md)、T-064 ready_rev 1 和 spec 第 1 节。fork `a2a` 基线 `7a3a13249e562bf2d7f9ff4cb024f39b13d62434`；a2a 开工版本 `883b9ae2ea337c293318076faf6ec1a16785aac5`。没有 fork 改动或提交，未 push。

必须先批准的文件、行号、最小改动、已核对的调用者与五种失败方式处理计划，见 [needs-decision-01.md](needs-decision-01.md)。blocking 收件箱条目：`20261010T064912Z-worker:t064-issue-001`。

brief 明确要求：“开始改这些文件前先停下，列出文件、行号和最小改动，等我批准。”共享免确认 matcher 仅接收工具名；要落实受管身份与活跃 turn 条件，还需要凭据与 provider 调用点的最小接入。Claude full-access 会跳过 canUseTool；已检查现有 SDK 类型，发现按 MCP server 收紧的现成接口，但未进行实际协议探针。没有自行扩大默认权限或改变运行模式。

| 验收项 | 本轮事实 |
| --- | --- |
| 红态 | 新增功能合同的 expected-red：通过真实 Vite SSR resolver 加载实际设置导航，没有“角色权限”；assertion 退出 1。原输出、完整命令、环境覆盖和 fork 版本保存在 [navigation-red01.json](navigation-red01.json)。未把导航探针称为完整 UI/MCP 验收 |
| 五个角色显示、自定义、恢复默认 | 未实现、未运行；ticket checkbox 保持未勾选 |
| 真实 MCP tools/list、调用与新旧凭据冻结 | 未运行，旧 T-058 通过结论不替本票背书 |
| 免确认正反例 | 未运行；默认值与显式自定义如何共存、免确认是否随凭据冻结，已提交主控确认 |
| 核心结构底线 | 尚未改产品，未新增 dismiss/关闭 blocking 开关；不能据此宣称新设置已通过反例 |
| 用户输入与可读变更记录 | 未实现；计划采用同库同事务，不在设置成功后另行补记 |
| 既有套件、fmt、lint、typecheck | 本轮仅文档/证据；未运行产品检查，没有把未运行写成通过 |
| 截图与外观判断 | 未生成，未判断；没有启动浏览器或桌面应用 |
| 独立审查 | 未运行、未消耗允许的一次审查；没有产品候选可冻结 |

重放命令：

```sh
python3 evidence/2026-10-09-batch11/T-064/run-preflight-01.py red02
```

每次须换新 label，原证据以独占创建保存。脚本返回产品断言的真实退出码；`red01` 是 1，原因是所要求的页面缺失，未出现导入或夹具失败。使用 Bun 1.4.2、Node 24.13.1，Bun 只经 fork `a2a/scripts/bun`，独立外置盘 slot 为 `s11-t064-preflight`；Vite 为 middlewareMode，没有监听端口，并在 finally 关闭。

没有启动服务/provider、没有模型 turn、没有认证副本、没有读写 `~/.codex` / `~/.claude`、没有操作正式工作台或 Herdr、没有构建或写共享 dist。保留既有 `.grok/` 和主控持续追加日志。本轮新增文件仅在 T-064 证据目录，并只追加本票 Resolution，保持 open、待主控关闭。

下一步：执行主控确认 [上游清单与口径](needs-decision-01.md) 后继续本票 Tracer bullet。此交接不是完成实现、验收或关闭 ticket。最终 project-map 状态和编码/差异检查保存于 `delivery-checks-01.json`。
