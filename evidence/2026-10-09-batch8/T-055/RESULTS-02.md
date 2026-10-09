# T-055：真实 Codex 权限提示后的交接

状态：**BLOCKED**。依照 [主控决定 01](controller-decision-01.md)，真实验证出现 provider 权限提示后已保存现场并停止；没有批准请求，没有修改 `computerToolPermission.ts`，没有切换权限模式。ticket 保持 open，待主控决定与关闭。原 [首轮范围阻塞报告](RESULTS.md) 保留。

未验收的 fork 候选：`13ec64ce6b6b19b913fe69bfc71dbf49c0f54bb0`，分支 `a2a`，父修订 `6efac8432d7ae37e74b76e42d4e9fd3004d9a0e2`。依据 T-055 `ready_rev: 1`。这是保存实现现场的本地提交，不是验收通过或集成结论，未 push。

## 主控需要决定

2026-10-09 10:42:16.758 UTC，真实 Codex 发出：

```text
Allow the synara MCP server to run tool "a2a_raise"?
```

请求 id：`c98aec9d-21f8-474b-aedd-ae03df765d27`。上报参数逐字为标题“oracle 漏了空页”、正文“分页夹具没有覆盖最后一页为空的情况。”、`blocking=true`、`refs=[]`。`tool.started` 后为 `approval.requested`，pending interaction 的 `decision` 与 `responseCommandId` 都为 null。没有 issue 记录落库。

完整现场见 [permission-stop-01.json](permission-stop-01.json)、[原生快照](real-observation-02.json)、[原始 rollout](real-rollout.jsonl)。原始 rollout 副本按 spec 只留本地，由本目录 .gitignore 排除，不进 Git；权限现场的结构化快照进入版本控制。没有发送 approval.respond、answer_issue 或第二条模型输入。

已核对的权限路径：

- `codexAppServerManager.ts:4503` 的普通网关自动批准分支要求有效运行身份、活跃 turn、default interaction，以及 `autoApproveSynaraTools=true` 或 full-access，最后还要求 `isSynaraGatewayToolName` 命中目录。
- `computerToolPermission.ts:247` 的目录只有 `a2a_submit`，没有 `a2a_raise`；该文件未改。
- 本次验收显式选择 `runtimeMode=approval-required`；`ProviderCommandReactor.ts:2256` 的自动批准标记来自活跃 group coordinator 配置，不是普通受管 worker 的默认授权。因此不能断言“只改工具名目录便能消除本次提示”。没有尝试改目录或授予标记来绕过停止条件。

最小选项是授权下一次隔离验收对这一工具逐次人工批准，保留原权限策略。若要求普通受管 worker 自主通过此提示，则需要构思主控先取得用户对权限变更的授权，再明确工具目录与授权标记的范围。worker 未选择其中任何一项。

## 红态、实现与实际读回

| 项目 | 本次证据与边界 |
| --- | --- |
| 父修订真实入口红态 | [red-entry-01.json](red-entry-01.json)：真实应用层、SQLite、HTTP/MCP 路由和线程凭据；`tools/list` 成功但无 `a2a_raise`。拟用面板路径未挂载，落到静态资源兜底返回 503。脚本以合同缺失断言 exit 1，不是连接失败 |
| 工具注册正例 | [real-tools-list.json](real-tools-list.json)：当前线程凭据的实际工具列表含 `a2a_raise`；真实 worker 已调用该名字，但停在 provider 批准前。不能将此写成上报成功 |
| 面板 HTTP 接口 | [real-panel-empty.json](real-panel-empty.json)：实际接口返回 ok，records/issues/user_inputs 均为空。未取得有问题内容的面板截图 |
| 门禁业务状态 | [real-status-stopped.json](real-status-stopped.json) 的完整 task 与 [dispatch 回执](real-dispatch.json) 完全相等，仍 claimed；attempt、fence/spec_rev=1、candidate、verification、integration 未改变 |
| 真实 worker | 仅一次真实 turn，gpt-6.1-sol / xhigh，经 Codex app-server 0.162.0，实际权限请求已保存。未完成上报或接收答复，真实 Codex 闭环 INCOMPLETE |
| 类型与格式 | gates、server、web 类型检查及指定九个文件的格式化命令均 exit 0。类型检查早于最终提交，不能替代最终候选的完整检查。fork 提交前 diff --check 通过 |
| 未运行 | 同脚本完整绿态、成功存储/重启/反例/答复/去重/重放、CLI 链读取、界面发送/截图、交付 8/恢复 9/编排 18/membership/T-044 场景、fmt:check、lint、完成检查点的 fresh-context 独立审查。全部 Acceptance 保持未勾选；停止条件解除后再执行一次最终候选审查 |

保存的实现经过 MCP 定义与注册、核心追加表、HTTP/CLI 读取、原生用户消息发送、任务窗口会话旁的 IssuePanel。输入与派生人工介入由门禁核心同事务写入，面板派发前登记 message id，消息记录器据此跳过重复 message 输入。**这些是实现内容，不是已取得的行为通过证据。** 没有按正则或关键词判断内容含义。

上游接入清单只有获批的 `apps/server/src/agentGateway/Layers/AgentGateway.ts` 两处：import 与工具列表注册。其余八个文件在任务书允许的四个目录内。完整清单、差异见 [partial-candidate.json](partial-candidate.json)、[partial-candidate.diff](partial-candidate.diff)。没有改变共享 dist 或依赖目录，没有增加运行依赖。

Tracer bullet 的状态写入集中在门禁核心，Deep modules 的接口仍由核心隐藏持久化；Ubiquitous language 使用既有 task、attempt、thread、用户输入与人工介入术语，没有第二套门禁业务状态。

## 隔离、失败与收尾

- 外置盘隔离目录 `instances/t055-red-03`、`t055-green-02`；使用产品完整服务层和 createEffectServer，未用替身工具或 provider 冒充真实 Codex。全部 provider 初始关闭，只在本次隔离 green-02 中启用 Codex。
- [codex-isolation.json](codex-isolation.json)：`/tmp` 下的新 CODEX_HOME 仅复制 auth.json，只信任核对过的新夹具根（所有 worktree 都在该根内），只有 git add、git commit 两条 allow 规则，无 hook。固定实际二进制版本 0.162.0，argv 带 service_tier="fast" 与 check_for_update_on_startup=false。请求中的 fastMode/Fast 设置不证明实际供应商 tier；原生 thread/settings 读回为 priority，未声明计费或性能收益。
- 首次使用 Node 直接执行源码因 extensionless import 失败；第二次 Bun 启动缺 Open 服务；两份原日志分别保留在 server-red-01.log、server-red-02.log。补齐实际启动依赖后 red-03 就绪。两次属于夹具启动失败，不计合同红态。
- 准备时依据旧报告检查 0.161.0，实际读到 0.162.0，断言失败；其后固定当前版本。一次只读收尾探针遇到控制结果文件写入中的 JSON Extra data；未改产品，重新读取新凭据时成功。失败摘要见 [setup-failures-02.txt](setup-failures-02.txt)。
- 所有本次启动进程使用 start_new_session；停止前核对命令，再仅向自己的实例发送 SIGTERM。服务/provider 已退出，未批准 pending request；停止记录见 stop-green-01.json、stop-permission-01.json。
- 原始 rollout 保存后，已删除整个认证 home；隔离服务根无 auth.json。用户 config/rules 的 size、mtime、mode 与 herdr status 原始输出前后完全相等，见 [cleanup-real.json](cleanup-real.json)、user-before-real.json、user-after-real.json。未操作正式工作台目录、用户配置或用户 Herdr。
- 测试 Git repo/worktree、门禁 SQLite 与原生数据库归档为 retained-green-02.tar.gz、retained-red-03.tar.gz，不登记 gitlink。归档不含认证 home、secrets 或 endpoint。其他 worker/主控的 dirty 文件与 fork `.grok/` 保留。

## 重放入口

在父修订、外置盘挂载时，使用新的 label，避免覆盖既有失败与场景：

```sh
python3 evidence/2026-10-09-batch8/T-055/start-server.py NEW_RED_LABEL
# 待该新隔离目录 ready.json 出现后：
python3 evidence/2026-10-09-batch8/T-055/red-entry.py /Volumes/WD-Elements/dev-cache/synara/instances/t055-NEW_RED_LABEL NEW_RED_RESULT
```

真实权限探针由 start-server.py 与 prepare-real.py 复现；它会消耗一次真实 turn，需要先取得上述主控决定再运行。启动 argv、非秘密环境、原始输出在 server-*-launch.json 与 server-*.log；检查的精确 argv 在各 *.command.json。继续执行时须从保存的未验收候选出发，不能沿用本次局部读回作为完整通过结论。
