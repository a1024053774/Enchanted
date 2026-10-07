# T-035 交付记录（2026-10-07）

交付状态：**PASS，仅限 T-035 的五项验收**。ticket 保持 `open`，**待主控关闭**；完整 M1 为 **INCOMPLETE**。独立只读审查为 [PASS](acceptance-review.md)。全仓检查存在失败，不能写成全仓通过。

fork 分支 `a2a`，冻结提交 `7cb0ac0a3d5232e90ab2db1fb7eb9ee696d1af73`，基线 `0b1740fd4e385baf389095e5cfa16dd67adcd3b4`，均为本地提交。a2a 的证据提交号绑定最终 `T-035 DONE` 回执；未 push。

范围与截止点：从读取任务书、接入点核实开始，到准确冻结产物的正例、反例、独立审查及最终清理完成。主控 Claude Code（`wF:pM`）；实现与实时观察由 Codex worker（`wF:pW`）完成。独立审查在冻结后另开 fresh context；没有将实现者的观察或 worker 自审称为独立 monitor。

## 五项验收

| 条件 | 结论 | 命令、结果与证据 |
| --- | --- | --- |
| 独立核心与上游清单 | PASS | `packages/a2a-gates` 持有自己的 SQLite、追加事件与任务级操作锁；所有门禁状态变更在该核心。独立审查核对了 CLI/HTTP/MCP 的汇合点。[改动清单](upstream-file-manifest.json)、[接入点核实](接入点.md) |
| 真实 worker 显式交付 | PASS | [create-3](create-3.json)、[dispatch-3](dispatch-3.json)、[status-7](status-7.json) 含完整 argv、退出码与原始 JSON。Codex 经 app-server 完成同内容分页夹具；原生两次 `a2a_submit` 的调用/返回保存在 [原始 rollout](rollout-2026-10-07T16-00-01-01a117f3-8284-73c3-a699-cef596238531.jsonl) 与 [配对摘录](frozen-submit-calls-and-results.json) |
| 独立验收、CAS 与回收 | PASS | [verify-3](verify-3.json) 在新 detached worktree 运行冻结 oracle，12/12 PASS；[integrate-3](integrate-3.json) 持久化意图后执行 `git update-ref` CAS；[Git 独立读回](frozen-integration-readback.json) 确认目标提交；[reclaim-3](reclaim-3.json) 与 [原生归档读回](frozen-primary-native-archived.json) 确认 stopped/archived |
| 任务窗口可见 | PASS（功能） | 原生桌面截图：[claimed](frozen-claimed.png)、[submitted](frozen-submitted.png)、[verified](frozen-verified.png)、[accepted](frozen-accepted.png)、[回收后](frozen-reclaimed.png)。沿用 Synara 的 Badge、主题和字号 token；外观判断由用户负责 |
| 反例不推进 | PASS | 错 session 的 `stale_session` 事件先于 submitted：[事件](frozen-events-before-integrate.json)。[真实不交付会话](frozen-no-submit-native-observe-1.json) 已 completed/idle，门禁 [仍 claimed](no-submit-status-3.json)；[verify](no-submit-verify-3.json)、[integrate](no-submit-integrate-3.json) 分别以 exit 1 拒绝，[引用不变](frozen-no-submit-ref-readback.json) |

最终正例身份：task=`pagination-frozen`，attempt=`ba8c5fe3-fc32-48ca-afce-eeb6fdb582bd`，session_id=`5d49298b-38ea-4105-8008-f76f87621abd`，fence=1，spec_rev=1，Synara thread=`5f582def-0aa2-44fb-a9a4-968fac583e74`。worker HEAD、候选与集成引用均为 `fd0b69579c5c8f8f2d0f97c33f51a3783226aca1`。规格版本为本次任务书、T-035 与 `synara-m1-2026-10-07`；锁、身份与 CAS 语义来源为任务书指定的三份冻结规格。

## 红态、版本绑定与模型配置

- 实现前，真实隔离 Synara `/health` 为 200，`POST /api/a2a` 为 404：[契约红态](contract-red.json)。这是新行为缺失的红态，未将环境失败当业务红态。
- 冻结分页 oracle 对原始 starter 返回 exit 1，12 项中 10 项业务断言失败：[结果](oracle-known-bad.json)、[精确命令与退出码](oracle-known-bad-command.json)。oracle 预期答案未改。
- 第一轮使用 `approval-required`，原生请求进入审批等待；未批准。依 [主控决定](controller-decision-01.md) 正常中断、门禁回收后清理。[原生审批](native-runtime-observe-1.json)、[中断](old-turn-interrupt.json)、[回收](old-attempt-reclaim-2.json)、[清理](old-runtime-cleanup.json) 保留。其外置盘 overlay 与未使用预备包装器的问题也没有计为合格模型证据。
- 第二轮闭环虽通过，但独立审查发现其实际加载 bundle 缺少冻结候选的工具集合注册行：[不相等记录](candidate-runtime-binding.json)、[唯一差异](candidate-runtime-bundle.diff)。该轮 `*-2` 与早期无前缀截图只作为历史证据，不给当前候选背书。
- 从冻结 `7cb0ac0` 重建后，用新 home、新隔离 Git 夹具重新取得完整正例与反例。实际 backend argv、产物 mtime 先于原生运行、保留的旧基线字段均在 [绑定记录](frozen-runtime-binding-before-rebuild.json)；审查者独立比较 [加载产物](frozen-loaded-server-bundle.mjs.gz) 与冻结源码重建产物，7,034,921 字节完全相同：[最终绑定](frozen-runtime-binding.json)。比较完整字节，没有计算指纹。
- `runtime.json.fork` 保留 session 开始时的基线 `0b1740f`，不是最终运行版本；新增 `runtime_candidate` 明确标记 `7cb0ac0`，未隐去旧字段。
- Worker 使用 gpt-6.1-sol、xhigh、Synara `options.fastMode=true`；没有外部 Codex 包装器。[原生 turn](frozen-turn-context.json)、[原生设置](frozen-native-settings.json) 读回 `never` / `danger-full-access` 与 `service_tier=priority`。[实际 argv 与 /tmp homes](frozen-native-launch.json) 保留。只证明运行配置；没有证明供应商计费、性能或成本收益。

## 检查与复现

所有 Bun/Node 命令均经 fork 的 `./a2a/scripts/bun`，`A2A_SYNARA_SLOT=t035`，构建工具链与缓存仍在外置盘。隔离桌面与 server 的启动脚本位于本证据目录；它们在缓存入口之后显式设置运行 home，避免只改 `--home-dir` 却把 Codex overlay 留在外置盘实例目录。

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| `run build:desktop`；冻结提交 `run --cwd apps/server build` | PASS；桌面实际运行及精确 bundle 绑定已核对 | [冻结构建](frozen-server-build.log)、[重建复验](frozen-server-build-verify.log)、绑定记录 |
| `run typecheck` | PASS，8 workspace | [日志](typecheck.log) |
| `run lint` | PASS，既有 warnings 保留 | [日志](lint.log) |
| `run fmt:check` | NO_GO，exit 1；最后只剩范围外、原有未跟踪 `.grok/settings.json` | [最终日志](fmt-check-final.log)；原文件未动 |
| `run test` | NO_GO，exit 1；server 7856 PASS、1 失败、27 跳过，其余 workspace 通过 | [完整日志](workspace-test.log) |
| 上述失败用例单独复核 | PASS，1 项通过、435 跳过；未证明失败根因或已修复 | [日志](provider-replay-focused.log) |
| 独立 CLI/Git 核对 | PASS，17/17；审查者另行重跑 | [脚本](check-frozen-live.py)、[结果](check-frozen-live-result.json) |
| 项目地图 status | PASS，0 problem、0 stale living doc；T-035 仍 open/claimed | [输出](project-map-status-final.txt) |

全仓失败位于 `ProviderCommandReactor.test.ts:7200`：`replays quarantined thread work beyond a pinned global cursor after restart`，`session.lastError` 为 null。该源码及测试相对基线没有 diff；单例通过不替代全仓失败结论。没有改其断言或扩大到上游修复。

记录里的 `argv` 可重放。完整启动：准备新的 /tmp home（仅 auth.json、指定信任与两条 allow 规则），更新本目录 `runtime.json` 的隔离根，再经入口运行 `desktop-launch.mjs` 与 `dev:web`。操作使用 `gate-call.py <唯一证据名> '<JSON 请求>'`；它只从隔离根读取本机实例凭据，不写入命令证据。Live 核对命令为 `python3 .../T-035/check-frozen-live.py`，要求该次实例仍运行；本次实例已清理，不能将清理后的连接失败当新的业务红态。

## 清理、证据与交接

[最终清理](runtime-cleanup-frozen.json) 确认只退出本次桌面/backend、只停止自己创建的 web 进程组；本次 source home、overlay 及临时用户字节基线副本已删除。用户 `auth.json`、`config.toml` 在本次运行前后逐字节相同。没有安装 worker hook，也没有改用户级配置。证据目录 [没有 auth.json 或用户凭据内容](credential-copy-check.json)。

完整夹具 Git repo、worktree、oracle 快照以 [归档](frozen-fixture-and-worktrees.tar.gz) 保存，没有登记 gitlink；[门禁 DB](gate-state-frozen-final.sqlite3)、[原生 DB](synara-state-frozen-final.sqlite)、原始 rollout、追加事件和失败记录均保留。原始 submit 摘录的不足保留，另加配对调用/返回摘录；未覆盖异常结果。角色、CLI、Herdr、skill 源路径与版本见 [版本记录](versions-and-roles.json)。

下一步由主控关闭 T-035、同步地图，并处理全仓失败及范围外格式文件的归属。主控创建的 `controller-decision-01.md` 原样留存，待主控提交。T-036 / 完整 M1 的交付、恢复、编排场景、完整 CLI 契约、多 agent 层级、人工介入记录与切换没有在本次取得通过结论。
