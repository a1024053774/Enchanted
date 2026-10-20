# T-112 / a1 交付记录

状态：**INCOMPLETE**。角色设置和派发覆盖已实现，本地合同检查 PASS；真实 daemon + CLI + 本地假 API + Electron + 原生沙箱验证仍待主控重跑。

首个交付已由主控提交：`44f163011434d6509974c48e4051437feb3acc73`；#39 修订为 `ee5bf995734d27701b8c3dd91511324bef9d2ed5`，#40 数据库读取修订为 `3ebbc9a3bbff48eb01ae2e606cac51a03c9f1a99`，分支 `exec/t112`。本轮处理主控 #42 要求的 reviewer 权限调查，尚待 COMMIT-04 提交诊断脚本；尚未修改原生 runner 的沙箱探针或断言。不调用模型、不 push、不改全局 CLI 配置、不走 submit；尾注继续由会话钩子生成。

## #42 权限调查：尚未解除

REALITY GATE: INCOMPLETE。目标是区分本票引入的权限回归、起点已有问题与探针构造错误。未扩大 reviewer 权限，未改原断言，不能以文档推断替代原生边界验证。

- **observed**：outside-native-03.json 的数据库读取通过；随后 profile 探针 exit=0，protected.txt 被写，原断言失败。该探针选择 --permission-profile :workspace，实际 reviewer 构造器选择 --sandbox workspace-write，两者并不相同。
- **measured**：reviewer-metadata-01.json 从起点 e3102389e 和候选 3ebbc9a3b 的实际 Panes.createReview 构造器分别取得完整启动记录。起点 effort=xhigh，候选按设置为 low；二者的沙箱均为 workspace-write，network_access=false、network_proxy=false、exclude_slash_tmp=true、exclude_tmpdir_env_var=true 均保持一致。该检查提供 PTY 替身，仅执行真实 CLI 版本探测，不声称运行了真实 reviewer 会话。
- **measured**：同一证据保存了两个已装 CLI 的 --version、--help、sandbox --help 原文。产品路径绑定 0.162.1，探针也是 0.162.1；把候选的 reviewer 启动器改传已装 0.163.0，启动前被原版本门禁以 codex_version_mismatch 拒绝。未放宽版本门禁；外层 Herdr/Codex 会话版本不等于本工作台的受管 CLI 版本。
- **inferred**：OpenAI Docs 的 [Permissions](https://learn.chatgpt.com/docs/permissions) 说明 profile 不与旧 sandbox 配置组合，内置 :workspace 允许写系统临时目录；[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)说明旧 exclude_slash_tmp/exclude_tmpdir_env_var 控制临时目录可写范围。因此旧 profile 探针不能直接代表 reviewer 的旧式沙箱。protected.txt 位于 /private/tmp 下，文档差异足以解释此次异常，但尚未证明本机运行效果。
- **unknown / PROBE**：需在沙箱外运行 REVIEWER-DIAG-01。脚本用隔离 Git 快照、依赖和 home 对照起点与候选，每版分别执行旧 profile 探针、按记录 sandbox_mode 选择的旧式探针、故意增加父目录 writable_roots 的坏配置；另保存 0.163.0 二进制的旧式探针对照。每次同时读回候选与保护文件，要求坏配置确实写入保护文件且被原业务断言拒绝；候选目录都不能写时只算设置失败。
- **停止条件**：若起点和候选的旧式探针都越界写入，则上报涉及权限的 blocking issue，交主控转用户；若仅候选越界则修本票回归；若两者旧式探针均保护成功且旧 profile 探针越界，再修原生 runner 的探针构造，并保留坏配置反例。当前尚未确认属于哪一种，不提前下安全结论。

当前沙箱内执行 codex sandbox 会报 sandbox_apply: Operation not permitted；因此只做了无需应用 seatbelt 的元数据对照。诊断脚本只写自己创建的临时夹具，完成后删除，不启动模型或连接供应商。结果将写 outside-reviewer-diag-01.json，旧失败摘要保留。

## 本轮修复

- **关闭后的 SQLite 夹具**：outside-native-02.json 已取得真实 high 派发红态，随后在 reviewer 合同夹具查询时失败。已用相同 Node 生产者和 Python 3.9.6 / SQLite 3.54.0 复现：数据库存在，连接已关闭，WAL/SHM 已移除，普通 mode=ro 查询仍报 unable to open database file；并非目录清理或路径错误。只对这个已结束的夹具改用 mode=ro&immutable=1，查询前要求数据库存在且没有 WAL/SHM，查询后显式关闭连接。正在运行的 daemon 数据库继续普通只读查询，不使用 immutable、不重试、不改为可写连接。依据：[SQLite 的只读 WAL 条件](https://sqlite.org/wal.html#read_only_databases)。红绿摘要分别为 closed-fixture-red-01.json 与 closed-fixture-green-01.json；同一信号先失败后通过，另验证缺失数据库不被创建、活跃 WAL 被拒绝。
- **安全解包**：outside-native-01.json 是设置阶段失败，cases/checks 为空，不能算业务红态。已核对起点 e3102389e 的 `git archive`：workbench/hooks 下有 26 个受控符号链接，目标均为同目录 hook.py，没有硬链接。新逻辑先校验完整成员与链接图，再写文件；保留内部符号链接与硬链接，拒绝绝对路径、成员路径穿越、越界/缺失目标、循环链接、链接父目录写入、重复成员和特殊文件。起点与候选均按 Git 快照处理，不把链接解引用成普通文件。
- **Claude 默认值**：按主控 #39 的范围内裁定，worker/reviewer/monitor 出厂为 Codex `gpt-6.1-sol / high / Fast=false`；ideation/executor 沿用现有 Claude 入口 `claude-haiku-5-5 / low / Fast=false`。已有显式设置保留；覆盖 > 设置 > 对应角色出厂值。Claude 只接收 --model、--effort 和 settings.fastMode，不接收 Codex 配置参数。未增加 Codex 主控或 monitor 运行时。
- **临时夹具**：已删除额外的旧清理脚本；完成的本地夹具直接删除，仅保留文本摘要。原生 runner 也会在本次进程收尾完成后删除自己的临时目录，失败的终端尾部诊断保存进 JSON；若进程清理未确认，则保留仍在使用的目录并明确报告。
- **T-108**：主控已确认上次临时根目录消失来自其磁盘清理操作，不是产品缺陷。旧失败 t108-final-02.json 保留；本轮按要求重新执行，结果见 t108-rev2-04.json。

## 功能与权限

五角色设置写入 a2a 自己的 SQLite 追加式事件。dispatch 和 run --wait-seconds 支持 --model、--effort、--fast true|false；controller_prepare/start 也支持覆盖。完整 argv 和请求模型/强度/tier 一致记录，不把请求配置当供应商实际执行层级。

worker_executor_mismatch 保留 Codex 身份检查，删除固定模型名单与 xhigh 检查。旧 Claude 合同不再按 effort 枚举拒绝。未知非空取值交给 CLI；会话建立前的非零退出记录 launch_failed，不被后续 zsh 掩盖。

reviewer 保持 T-076 的 workspace-write 候选副本沙箱：原审查 worktree 只读，独立 home，网络/tmp 限制与无 worker Git hook 环境不变。模型/强度设置不改变权限。Herdr 期 launch-worker 保留默认值，移除 effort choices。

Tracer bullet：设置表单 → IPC → SQLite → 派发 → argv。Deep modules：复用现有 store、门禁和启动器。Ubiquitous language：沿用现有五个角色名。

## 本轮检查

| 检查 | 结果与摘要 |
| --- | --- |
| 实际 Git 快照解包 | PASS，baseline-extraction-final-03.json；本轮复验 baseline-extraction-rev3-01.json 也 PASS：保留 26 个真实 hook 链接，内部相对链接/硬链接成功，12 类非法输入写入前拒绝；恢复旧“拒绝全部链接”行为会失败。 |
| Claude 默认值红态 | controller-defaults-red-01.json：修前将 Codex 默认送给 Claude 的错误被独立默认值断言拒绝。 |
| 角色设置与 argv | PASS，execution-rev2-final-07.json：五角色默认、SQLite 重开、覆盖优先级、角色隔离、权限字段拒绝、reviewer 原参数、实际 zsh 退出码及启动失败事件。 |
| 已知坏变异 | PASS，mutants-rev2-05.json：旧 Claude 枚举、错误优先级、reviewer 误用 worker、固定 worker 门禁、惰性字符串掩盖启动失败均被拒绝。 |
| Claude 启动构造 | PASS，claude-profile-rev2-02.json：默认 Haiku/low、覆盖 Opus/high/Fast 及原权限参数，原隔离/钩子/版本/地址拒绝检查保留。 |
| IPC 合同 | PASS，ipc-rev2-06.json；保留原拒绝检查及新增设置 channel 的 iframe、未知窗口、非法字段拒绝。 |
| 构建 | PASS，build-rev2-final-03.json；临时构建目录已清理。 |
| T-108 回归 | PASS，t108-rev2-04.json；未修改该测试。 |
| 已关闭夹具跨运行时读取 | PASS，closed-fixture-green-01.json；相同 Node 合同生产者、Python 消费者，3 条边界检查。修前在相同查询处失败，见 closed-fixture-red-01.json。 |
| 原生 high 红态 | PASS，outside-native-02.json 的 baseline_high / baseline_real_dispatch_high_refused，真实 daemon 门禁返回 worker_executor_mismatch。 |
| 原生全链路 | INCOMPLETE，outside-native-01.json 在解包前置条件失败；02 在已关闭夹具查询处失败；03 查询通过但 reviewer 权限探针失败，正在按 #42 调查。尚无原生绿态。 |
| 地图检查 | INCOMPLETE：稀疏 checkout 原有 8 个缺失文件链接问题，0 stale；本轮结果见 project-map-rev4-final.txt。 |

```sh
python3 -B workbench/tests/test_t112_archive.py --summary evidence/2026-10-20-batch18/T-112/baseline-extraction-final-03.json
node workbench/tests/test_t112_execution.mjs evidence/2026-10-20-batch18/T-112/execution-rev2-final-07.json
python3 -B workbench/tests/test_t112_counterfactuals.py --summary evidence/2026-10-20-batch18/T-112/mutants-rev2-05.json
node workbench/tests/test_t093_launch_profile.ts evidence/2026-10-20-batch18/T-112/claude-profile-rev2-02.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-20-batch18/T-112/ipc-rev2-06.json
node workbench/tests/test_t108_questions.mjs evidence/2026-10-20-batch18/T-112/t108-rev2-04.json
python3 -B workbench/tests/test_t112_closed_fixture.py --summary evidence/2026-10-20-batch18/T-112/closed-fixture-green-01.json
```

这些摘要路径已存在，不可覆盖；需要重跑时另取文件名。用完的本票旧夹具已按主控 #39 清理，见 completed-fixtures-cleanup-02.json；其他任务和仍运行的进程目录不在清理范围。

## 主控重跑命令

```sh
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-04.sh
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-REVIEWER-DIAG-01.sh
```

先提交再运行，使 code_revision 绑定完整提交。本次先运行独立权限诊断，不重跑尚未修正的全链路探针；结果写 outside-reviewer-diag-01.json，不覆盖 native-01、02、03。诊断不需要 Electron 或 API。待原生边界归因完成后，按结论修复或上报，再提供全链路重跑脚本。仅在私有依赖副本修改 spawn-helper 执行位，无需挂载外置盘。

## 已交接事项

- AGENTS.md:67、69 的固定模型/强度说法由执行主控转交构思主控；worker 未修改治理文件。
- 原生 reviewer 的网络/tmp/原 worktree 边界仍须外部实际验证，不能用合同测试代替。
- 首轮独立冻结审查 independent-review-01.md 原结论 FAIL 保留。其 runner exit-1 和 shell 源码断言问题已修；后继候选尚待执行主控的新会话独立审查，不引用旧审查作通过依据。
- 全仓检索与 CLI 帮助原文仍在 search-final-02.json、cli-help-01.json 等原摘要中。当前模型/effort 不作固定值门禁；其他供应商的旧 provider 合同不在本票新增运行时范围。
- T-110 接线边界未扩大：renderer.tsx 原第 10–11 行 import、第 48 行 bridge 类型、第 570 行组件；main.ts 新增独立 settings IPC，preload.ts 增加一个 bridge 方法；sidebar.ts、原通知区块和原样式文件未改。
