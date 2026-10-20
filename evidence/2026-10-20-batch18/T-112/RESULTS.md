# T-112 / a1 交付记录

状态：**INCOMPLETE**。角色设置和派发覆盖已实现，本地合同检查 PASS；真实 daemon + CLI + 本地假 API + Electron + 原生沙箱验证仍待主控重跑。

首个交付已由主控提交：`44f163011434d6509974c48e4051437feb3acc73`；#39 修订为 `ee5bf995734d27701b8c3dd91511324bef9d2ed5`，#40 数据库读取修订为 `3ebbc9a3bbff48eb01ae2e606cac51a03c9f1a99`，#42 诊断为 `ee1fce36d5e757d1ae664b11696bdfe9d13a3cb4`，#44 真实会话探针为 `d60c3ea06a73e8ac6af790b8ad703b23ba387e36`，分支 `exec/t112`。本轮按 #46 修复探针的首轮启动和身份等待顺序，尚待 COMMIT-06 提交；未改产品权限、候选写入或原生工具回执的要求。不调用模型、不 push、不改全局 CLI 配置、不走 submit；尾注继续由会话钩子生成。

## #46 启动顺序修复

- outside-reviewer-diag-02.json 的 baseline-good 已有真实 0.162.1 领导进程，前台进程组正确，但 api_requests=0、candidate 文件不存在。脚本要求先取得 native_session 才 release，首轮输入因此没有放行。生产 Panes.release 本来只要求前台 CLI 领导进程且未失败；探针加的前置条件超过了生产入口，会在会话首轮才落盘的生命周期中形成循环等待。真实 CLI 的首次落盘时点仍待重跑确认。
- 修为先核对前台领导进程并保存 pre-release.json，再调用真实 release，随后仍须拿到非空 native_session，并断言领导进程未变，才发布 identity.json。父进程同时等待身份文件和原生工具回执，避免工具先完成时抢读尚未写入的身份文件。同票 run_t112_native.py 也有相同前置等待，已按同一顺序修正；未修改生产 Panes.release。
- 旧结果没有 sessions 清单，夹具按此前授权清理，无法事后补查。新结果保存放行前、取得身份后的 sessions 清单，以及收尾后的整个隔离 CODEX_HOME 文件清单和 JSONL 首行，便于区分目录尚不存在、文件位置不同与定位器未绑定。GET 路径和 POST 数量分别记录，启动失败时也保存 launch、阶段文件和 home 清单。
- 新启动回归执行实际 driver 源码，只提供 daemon/process/FS 边界：reviewer-startup-red-02.json 记录修前一直等待身份且没有 release；reviewer-startup-green-01.json PASS，验证放行后取得身份、无领导进程不放行、放行后无身份不通过、领导进程变化不发布身份。首轮 reviewer-startup-red-01.json 是 VM 测试环境缺少 URL 的设置失败，保留但不算缺陷红态。该回归不作为原生 CLI 或沙箱证据。
- 候选副本必须写成功、匹配原生工具回执、持久化调用参数比对、解析后权限与 argv 检查均保留。原生权限归因仍为 INCOMPLETE，待 REVIEWER-DIAG-03；输出写 outside-reviewer-diag-03.json，不覆盖旧结果。

## #42 / #44 权限调查：尚未解除

REALITY GATE: INCOMPLETE。目标是区分本票引入的权限回归、起点已有问题与探针构造错误。未扩大 reviewer 权限，未改原断言，不能以文档推断替代原生边界验证。

- **observed**：outside-native-03.json 的数据库读取通过；随后 profile 探针 exit=0，protected.txt 被写，原断言失败。该探针选择 --permission-profile :workspace，实际 reviewer 构造器选择 --sandbox workspace-write，两者并不相同。
- **measured**：reviewer-metadata-01.json 从起点 e3102389e 和候选 3ebbc9a3b 的实际 Panes.createReview 构造器分别取得完整启动记录。起点 effort=xhigh，候选按设置为 low；二者的沙箱均为 workspace-write，network_access=false、network_proxy=false、exclude_slash_tmp=true、exclude_tmpdir_env_var=true 均保持一致。该检查提供 PTY 替身，仅执行真实 CLI 版本探测，不声称运行了真实 reviewer 会话。
- **measured**：同一证据保存了两个已装 CLI 的 --version、--help、sandbox --help 原文。产品路径绑定 0.162.1，探针也是 0.162.1；把候选的 reviewer 启动器改传已装 0.163.0，启动前被原版本门禁以 codex_version_mismatch 拒绝。未放宽版本门禁；外层 Herdr/Codex 会话版本不等于本工作台的受管 CLI 版本。
- **inferred**：OpenAI Docs 的 [Permissions](https://learn.chatgpt.com/docs/permissions) 说明 profile 不与旧 sandbox 配置组合，内置 :workspace 允许写系统临时目录；[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)说明旧 exclude_slash_tmp/exclude_tmpdir_env_var 控制临时目录可写范围。因此旧 profile 探针不能直接代表 reviewer 的旧式沙箱。protected.txt 位于 /private/tmp 下，文档差异足以解释此次异常，但尚未证明本机运行效果。
- **measured**：outside-reviewer-diag-01.json 中，两个旧 profile 探针均越界写入；其余 6 个探针均 exit=2，CLI 要求 --permission-profile，不接受单用 sandbox_mode 来解析旧沙箱。候选写入没有发生，不能把这些设置失败解释为边界保护。此前尝试用 sandbox 子命令模拟旧沙箱的路径已从诊断代码移除。
- **unknown / PROBE**：当前需在沙箱外运行 REVIEWER-DIAG-03。它用生产 serve 的现有 createGates 参数取得同一个 Panes 实例，调用真实 createReview、真实 PTY 和完整原始 argv，使用原 hooks、后台与身份校验，不提供 PTY 替身。测试只分配隔离 task/review 对象来验证启动边界，不冒充 claim/submit/独立审查验收。起点与候选各执行原配置、仅在隔离 home 增加父目录 writable_roots 的坏配置，共 4 个真实 CLI 会话。
- **独立观测**：本地 Responses API 根据 CLI 实际声明的工具返回一次 shell 调用，先写 candidate-probe.txt，再写父目录 protected.txt，每次使用随机内容标记。只有候选写成功才接纳本次边界观测；工具输出须在后续 API 请求中携带匹配 call_id，并在原生日志中持久化。持久化的调用参数/工作目录必须与发出的调用一致；完整 argv 的目录、approval、sandbox、网络/tmp 与 hooks 逐项校验，解析后的网络/tmp 策略也必须符合请求。保存进程身份、turn_context.sandbox_policy、工具回执与收尾后的文件读回值。坏配置必须实际写入保护文件且被同一业务 oracle 判为失败。API 在工具回执后等待收尾，不生成审查结论或触发另一张任务的交付过程。
- **停止条件**：若起点和候选的真实 reviewer 都越界写入，则上报涉及权限的 blocking issue，交主控转用户；若仅候选越界则修本票回归；若两者真实 reviewer 均保护成功且坏配置对照被拒绝，再把原生 runner 的旧 profile 探针换成同一真实会话路径。当前尚未确认属于哪一种，不提前下安全结论。

本地协议预检 reviewer-stream-02.json PASS，删除参数增量事件，以及保留 call_id 却改写命令的变异都被拒绝；这不作为原生沙箱证据。真实会话的首次运行在 #46 记录的放行前身份等待处失败，修后仍待外部运行。诊断脚本只写自己创建的临时夹具，身份绑定地收尾自有进程；清理未确认则保留现场并维持 INCOMPLETE。原生结果将写 outside-reviewer-diag-03.json，旧失败摘要保留。脚本仅配置无凭据的 loopback 假 API，不请求真实模型，也不生成截图；没有系统级出站监测，因此 vendor_egress_observed 记为 null，不能把本地请求计数当作零出站请求的独立证明。

本轮独立只读检查的状态为 INCOMPLETE，未取得原生证据；指出了策略校验未参与判定、原生调用参数未比对、完整 argv 校验不足及零出站计数缺乏独立观测。前三项已补断言，调用参数变异已本地验证会被拒绝；第四项已撤掉未经测量的零出站计数，并明确上述证据边界。修改后尚未重新做独立验收，不引用该检查作 PASS。

## 本轮修复

- **关闭后的 SQLite 夹具**：outside-native-02.json 已取得真实 high 派发红态，随后在 reviewer 合同夹具查询时失败。已用相同 Node 生产者和 Python 3.9.6 / SQLite 3.54.0 复现：数据库存在，连接已关闭，WAL/SHM 已移除，普通 mode=ro 查询仍报 unable to open database file；并非目录清理或路径错误。只对这个已结束的夹具改用 mode=ro&immutable=1，查询前要求数据库存在且没有 WAL/SHM，查询后显式关闭连接。正在运行的 daemon 数据库继续普通只读查询，不使用 immutable、不重试、不改为可写连接。依据：[SQLite 的只读 WAL 条件](https://sqlite.org/wal.html#read_only_databases)。红绿摘要分别为 closed-fixture-red-01.json 与 closed-fixture-green-01.json；同一信号先失败后通过，另验证缺失数据库不被创建、活跃 WAL 被拒绝。
- **安全解包**：outside-native-01.json 是设置阶段失败，cases/checks 为空，不能算业务红态。已核对起点 e3102389e 的 `git archive`：workbench/hooks 下有 26 个受控符号链接，目标均为同目录 hook.py，没有硬链接。新逻辑先校验完整成员与链接图，再写文件；保留内部符号链接与硬链接，拒绝绝对路径、成员路径穿越、越界/缺失目标、循环链接、链接父目录写入、重复成员和特殊文件。起点与候选均按 Git 快照处理，不把链接解引用成普通文件。
- **Claude 默认值**：按主控 #39 的范围内裁定，worker/reviewer/monitor 出厂为 Codex `gpt-6.1-sol / high / Fast=false`；ideation/executor 沿用现有 Claude 入口 `claude-haiku-5-5 / low / Fast=false`。已有显式设置保留；覆盖 > 设置 > 对应角色出厂值。Claude 只接收 --model、--effort 和 settings.fastMode，不接收 Codex 配置参数。未增加 Codex 主控或 monitor 运行时。
- **临时夹具**：已删除额外的旧清理脚本；完成的本地夹具直接删除，仅保留文本摘要。原生 runner 也会在本次进程收尾完成后删除自己的临时目录，失败的终端尾部诊断保存进 JSON；若进程清理未确认，则保留仍在使用的目录并明确报告。
- **T-108**：主控已确认上次临时根目录消失来自其磁盘清理操作，不是产品缺陷。旧失败 t108-final-02.json 保留；本轮按要求重新执行，结果见 t108-rev2-04.json。

## 功能与权限

五角色设置写入 a2a 自己的 SQLite 追加式事件。dispatch 和 run --wait-seconds 支持 --model、--effort、--fast true|false；controller_prepare/start 也支持覆盖。完整 argv 和请求模型/强度/tier 一致记录，不把请求配置当供应商实际执行层级。

worker_executor_mismatch 保留 Codex 身份检查，删除固定模型名单与 xhigh 检查。旧 Claude 合同不再按 effort 枚举拒绝。未知非空取值交给 CLI；会话建立前的非零退出记录 launch_failed，不被后续 zsh 掩盖。

reviewer 保持 T-076 的 workspace-write 候选副本参数、独立 home、网络/tmp 限制与无 worker Git hook 环境。模型/强度设置不参与权限参数构造；实际只读边界仍待本轮原生验证，不能用参数断言替代。Herdr 期 launch-worker 保留默认值，移除 effort choices。

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
| reviewer 假 API 工具流预检 | PASS，reviewer-stream-02.json；命名空间函数、自定义 exec、shell_command 的命令和工作目录传输，以及缺失参数增量、保留 call_id 却改写命令的变异。仅协议证据，非原生权限证据。 |
| 原生 high 红态 | PASS，outside-native-02.json 的 baseline_high / baseline_real_dispatch_high_refused，真实 daemon 门禁返回 worker_executor_mismatch。 |
| 原生全链路 | INCOMPLETE，outside-native-01.json 在解包前置条件失败；02 在已关闭夹具查询处失败；03 查询通过但 reviewer 权限探针失败；outside-reviewer-diag-01.json 的旧式模拟在 CLI 参数解析阶段失败；reviewer-diag-02 在首轮放行前身份等待处失败，API 请求数为 0。按 #46 修后待 reviewer-diag-03，尚无原生绿态。 |
| reviewer 首轮启动顺序 | PASS，reviewer-startup-green-01.json；修前红态见 reviewer-startup-red-02.json。实际 driver 源码执行，边界由测试提供，非原生权限证据。 |
| 地图检查 | INCOMPLETE：稀疏 checkout 原有 8 个缺失文件链接问题，0 stale；本轮结果见 project-map-rev6-final.txt。 |

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
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-06.sh
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-REVIEWER-DIAG-03.sh
```

先提交再运行，使 code_revision 绑定完整提交。本次先运行真实会话的权限诊断，不重跑尚未修正的全链路权限探针；结果写 outside-reviewer-diag-03.json，不覆盖旧结果。诊断不需要 Electron，仅使用自己绑定的 loopback 假 API，不访问供应商。待原生边界归因完成后，按结论修复或上报，再提供全链路重跑脚本。仅在私有依赖副本修改 spawn-helper 执行位，无需挂载外置盘。

## 已交接事项

- AGENTS.md:67、69 的固定模型/强度说法由执行主控转交构思主控；worker 未修改治理文件。
- 原生 reviewer 的网络/tmp/原 worktree 边界仍须外部实际验证，不能用合同测试代替。
- 首轮独立冻结审查 independent-review-01.md 原结论 FAIL 保留。其 runner exit-1 和 shell 源码断言问题已修；后继候选尚待执行主控的新会话独立审查，不引用旧审查作通过依据。
- 全仓检索与 CLI 帮助原文仍在 search-final-02.json、cli-help-01.json 等原摘要中。当前模型/effort 不作固定值门禁；其他供应商的旧 provider 合同不在本票新增运行时范围。
- T-110 接线边界未扩大：renderer.tsx 原第 10–11 行 import、第 48 行 bridge 类型、第 570 行组件；main.ts 新增独立 settings IPC，preload.ts 增加一个 bridge 方法；sidebar.ts、原通知区块和原样式文件未改。
