# T-112 / a1 交付记录

状态：**INCOMPLETE**。角色设置和派发覆盖已实现，本地合同检查 PASS；真实 reviewer 的副本外路径保护与坏配置对照已 PASS，完整 daemon + CLI + Electron 验收待 NATIVE-06。

首个交付已由主控提交：`44f163011434d6509974c48e4051437feb3acc73`；#39 修订为 `ee5bf995734d27701b8c3dd91511324bef9d2ed5`，#40 数据库读取修订为 `3ebbc9a3bbff48eb01ae2e606cac51a03c9f1a99`，#42 诊断为 `ee1fce36d5e757d1ae664b11696bdfe9d13a3cb4`，#44 真实会话探针为 `d60c3ea06a73e8ac6af790b8ad703b23ba387e36`，分支 `exec/t112`。#46 启动顺序修订已由主控提交为 `5695229777f01f5685f89e0a24cd1cb809ee8476`。该修复已由主控提交为 `8a6d3f6fed955f2ec1e196a1c3afae55e7e420fd`。#50 的完整原生接线已由主控提交为 `859ce7048ac263759c0c187874fc563290477ecd`；#51 的检索修订已由主控提交为 `21389ed18f823ec37a34e09fff176ecf60ac9859`；本轮 #52 的 worker 启动夹具修复待 COMMIT-10 提交；未改产品权限、候选写入或原生工具回执的要求。不调用模型、不 push、不改全局 CLI 配置、不走 submit；尾注继续由会话钩子生成。

## #52 worker 首轮启动夹具修复

- outside-native-05.json 保留：检索、baseline high 拒绝、changed-effort reviewer good/bad 已通过；factory 在等待原生身份时失败。该失败中的 pane_release 已成功返回 busy，且发生在身份等待之前，因此不是旧的“先等身份再放行”循环。worker 假 API 的 user/title 请求数均为 0、api_errors 为空；终端尾部含 Trust and continue，随后为空输入框。这与首轮 Enter 被信任提示消耗相符，不能冒充首轮回合已运行。
- start() 原来只信任夹具祖先 root；现改为每例自己创建的具体 Git repo，沿用 T-108 Codex 夹具的精确信任配置，供其 linked worktree 解析仓库信任。只修改 /private/tmp 隔离 CODEX_HOME；不改产品权限，不写用户配置，不额外按键、不重发首轮输入。
- factory、ui-settings、override 继续共用同一个 launch()：前台领导进程核对 → pane_release 一次 → 等本地 API 收到 user 首轮 → 保存模型/强度及请求序号 → 核对非空原生身份及同一领导进程 → 匹配原生 Stop。保存放行前的进程信息、隔离配置、放行回执和首轮请求选择，即使后续身份等待失败也保留已到达阶段。未放宽身份或 API 断言；不支持 effort 的启动失败分支不变。
- 针对性检查 PASS：CHECK-WORKER-STARTUP-10.py 执行真实 start() 源码直到 daemon 边界，分别检查三个用例只配置其明确的 Git repo 信任。修前三个用例均不满足（worker-startup-trust-red-01.json），修后全部满足（worker-startup-trust-green-01.json）。这是夹具配置回归，不代表真实 CLI 首轮已通过；仍须 NATIVE-06 取得首轮 API、同进程原生身份与 Stop。
- 本轮仅改上述 runner、针对性检查及本票报告/脚本；T-108 与 IPC 产品路径未变，保留最近 rev7 的 PASS，不重复执行。地图仍为稀疏 checkout 原有 8 个缺失链接、0 stale，见 project-map-rev10-final.txt。全票状态维持 INCOMPLETE，待完整原生运行与主控独立审查。

## #51 检索移除 ripgrep 依赖

- outside-native-04.json 在第一步因沙箱外 PATH 没有 rg 而失败，尚未执行原生用例。这是设置失败，不算业务红态；旧结果保留。
- SEARCH-REPO-08.py 改用 git grep -n -E，保持三组查询、大小写规则和排除项；ERE 使用普通分组和逐行的点号表达原正则含义。范围为当前稀疏 worktree 中存在的受控文件，包含隐藏路径，排除 Git 元数据、node_modules、evidence 和 package-lock.json；不搜索未受控文件。search-rev9-01.json 保存实际 argv、cwd、退出码和完整输出，没有安装工具或创建包装/链接。
- 针对性验证 **PASS**：PATH=/usr/bin:/bin 下修前缺少 rg 的失败已复现（search-path-red-01.json），修后同一路径约束下命令退出 0（search-path-green-01.json）。三组结果分别为 51、7、10 行；忽略排序、开头 ./ 与单文件查询新增的文件名前缀后，行号和正文均与修前原文完全相同（search-parity-rev9-01.json）。首轮比较器未处理该文件名前缀而报 INCOMPLETE，原摘要保留，未改写成 PASS。
- 本轮只修改本票证据目录中的检索脚本、报告和重跑脚本，不改产品或其余原生验收步骤；T-108 / IPC 最近有效回归仍为 rev7 的 PASS，不重复执行。完整原生验收及随后独立审查仍未完成。

## #50 完整原生验收接线

- **真实权限结论 PASS**：outside-reviewer-diag-04.json 绑定 8a6d3f6fe，classification=old_profile_probe_was_not_the_real_reviewer_sandbox。起点和候选的两个 good 都先成功写入候选副本，保护文件均保持 unchanged；两个 bad 仅额外放开父目录，保护文件均被写入且被同一 oracle 判为不通过。每例均取得完整 argv、原生身份、解析后权限、调用参数与匹配的原生工具回执，API 为本地无凭据夹具。按主控 #50，旧 :workspace 探针的安全疑点解除，无须上报权限 issue；该结果不冒充 Electron 和其余派发场景的通过证据。
- 完整 runner 移除 codex sandbox 子命令，直接复用已通过的 run_reviewer_case，以候选设置 low 各运行一次 good 和 bad。候选副本必须写成功；good 必须保护父目录，bad 必须实际越界并被 oracle 拒绝；两例清理都须确认结束再进入后续派发。任一 reviewer 清理不明，整个临时根目录保留且结果为 INCOMPLETE。为让诊断与完整 runner 单向复用同一探针，将原样 Git 解包函数移到 t112_archive.py，避免相互导入；test_t112_archive.py 仅调整导入，原拒绝断言未改。原关闭后 SQLite 合同检查保留，完整权限验收不再通过该合同的 PTY 替身。
- 完整入口继续实际启动后台与交互 CLI，核对出厂 gpt-6.1-sol/high/普通速度、真实 Electron 表单保存 low 后的下一次 worker 派发、覆盖优先级、原生 Stop、启动身份和完整 argv。覆盖对照先保存 t112-saved-unselected-model/medium/Fast=false，再覆盖 gpt-6.1-sol/xhigh/Fast=true，避免模型字段相同而不能区分来源。不支持的 effort 必须保留原值出现在 argv 与 CLI 报错中，产生非零退出的 launch_failed，且不能悄悄发起另一个假 API 回合。
- 完整入口的假 API 与诊断一样记录线程错误并在 join 后纳入最终状态，避免并行标题失败被遗漏；只记录夹具模型调用数 0，系统级供应商出站监测仍为未实施，不以本地计数替代独立出站证明。
- **全仓检索已记录并检查**：search-rev8-01.json 保存 3 条 rg 命令及完整原文，第一条扫描当前稀疏 checkout 的全部可读源码/配置/文档（排除 .git、依赖、历史 evidence 和 lockfile），共 51 行匹配。当前受管启动路径只保留 Codex 身份核对、字段形状、供应商推断、交付事实/尾注身份比对，未发现固定模型/强度的拒绝。PI/OMP/Grok 的旧 provider 合同枚举属于尚未启用的其他 CLI，不是 Codex/Claude 入口门禁。launch-worker 的 choices 仅用于方向和 default/fast tier；model/effort 没有 choices。README 的 xhigh 只剩覆盖示例；五角色卡均写默认见设置可改。AGENTS.md:67 的固定说法保持未改，仍由主控转交。完整 NATIVE-04 会再运行相同脚本，把原文收入本次原生摘要，检索记录本身不自动作语义通过判定。
- 本轮 archive 红绿与越界拒绝回归 PASS（baseline-extraction-rev8-01.json），真实捕获请求回放 PASS（request-replay-rev8-01.json），Python 3.9.6 语法/模块加载、Electron driver 语法、zsh 脚本与 diff 检查 PASS（native-rev8-static-01.json）。Electron 摘要会保留真实进程入口、表单保存前后值与库读回；worker 即使中途失败，也先保留启动记录，避免清理后丢失完整 argv。T-108 与 IPC 源码、产品源码均未改，最近回归仍为 t108-rev7-01.json / ipc-rev7-01.json PASS。本轮不引用无效的冻结审查作通过依据，完整原生运行后由执行主控另开独立审查。

## #48 真实请求格式与工具协议修复

以下为 #48 交付时的协议修复记录；其中待验的 reviewer 权限已由 #50 的真实对照解决。

- outside-reviewer-diag-03.json 已收到真实 API 请求，首轮身份等待问题已越过；失败是夹具把工具声明当作顶层 tools。原结果保留，不算沙箱业务红态。对照 T-108 的流式夹具后，又用本机固定 0.162.1、隔离无凭据 home、真实交互 CLI 和 loopback API 直接捕获请求；request-capture-02.json 保存完整 argv、配置与请求原文。实际声明在 input 中 type=additional_tools 的 tools 数组里，包含命名空间 custom 工具；其 description 中声明内层 shell 函数及参数。现在只解析这份实际声明，不补猜测工具、不回退到旧顶层格式；工具名、内层函数名、命令/目录/等待参数名都随声明取值。
- 原生 CLI 还会并发发送 thread_source=thread_title 的独立请求，带有标题 JSON schema。按 client_metadata 的 x-codex-turn-metadata 分流，标题返回合法 JSON 文本，不消耗根回合的工具调用或原生回执。code-mode-protocol-01.json 保留首次误把标题当回执的预检失败；修后 code-mode-protocol-02.json 与使用精确输出断言的 code-mode-protocol-final-03.json 均 PASS：真实 CLI 执行带随机标记的纯文本 JavaScript 调用，后续 user 请求送回同一 call_id 的 custom_tool_call_output。它只证明原生协议往返，未执行 shell，也不证明文件权限。
- request-replay-red-01.json 用真实捕获请求通过修前实际 HTTP Handler，记录 HTTP 500；修后同一请求回放 PASS（request-replay-final-05.json）。另验证标题请求不发工具、同时改名外层工具/内层函数/三个参数时输出随之改变、删除声明时明确拒绝。reviewer-stream-final-04.json PASS，缺失输入增量与保留 call_id 却改写输入的变异仍被拒绝。协议构造统一到同票 t112_native_api.py；完整 native runner 也按同一元数据区分标题和根请求，避免标题污染模型/effort 计数。
- 所有 POST 在 JSON 解析和工具选择前保存原文；诊断结果保留请求原文、请求来源、完整声明、原生调用和回执。退出时先 join 假 API 处理线程，再记录最终请求/错误计数，避免失败摘要仍显示旧计数；线程结束后仍断言 api_errors 为空，迟到的协议错误也不能进入成功分类。候选副本写入成功、保护文件边界、原生日志匹配和权限参数断言均未放宽。原生权限归因仍待 REVIEWER-DIAG-04，不改产品权限。
- 首次本地捕获因沙箱禁止 ps 而设置失败，未取得请求；收尾等待超时后保留了唯一夹具 /private/tmp/t112-request-capture-ejczqfcb，见 request-capture-failed-01.json。COMMIT-07 先运行 CLEAN-CAPTURE-01.py：仅核对含该唯一目录的固定 CLI 及其后代，按身份停止后直接删除目录；遇到不符身份则报错保留。后续捕获已改用自己尚未回收的 Popen 子进程身份收尾，成功记录均确认进程回收与夹具删除，不用广泛 tmp 清理。
- 本轮 T-108 与 IPC 回归均 PASS，见 t108-rev7-01.json、ipc-rev7-01.json；未修改这两项测试。本轮 T-108 明确记录的 444 个已结束合同夹具已直接删除，见 completed-fixtures-cleanup-rev7-01.json，未匹配或删除其他临时根目录。代码仍未取得真实 reviewer shell 的候选写入与权限回执，不宣称安全问题已归因或全票通过。

独立协议核查仍为 INCOMPLETE，见 protocol-independent-review-rev7-01.md：审查期间新增静态检查摘要导致其冻结快照被判失效，未形成对当前候选有效的审查结论。实际 reviewer 权限仍须外部运行，不将局部协议结果上调为全票通过。

## #46 启动顺序修复

- outside-reviewer-diag-02.json 的 baseline-good 已有真实 0.162.1 领导进程，前台进程组正确，但 api_requests=0、candidate 文件不存在。脚本要求先取得 native_session 才 release，首轮输入因此没有放行。生产 Panes.release 本来只要求前台 CLI 领导进程且未失败；探针加的前置条件超过了生产入口，会在会话首轮才落盘的生命周期中形成循环等待。此为 #46 当时的判断；后续 #48 的真实请求已确认放行后能够进入首轮，权限结论仍未知。
- 修为先核对前台领导进程并保存 pre-release.json，再调用真实 release，随后仍须拿到非空 native_session，并断言领导进程未变，才发布 identity.json。父进程同时等待身份文件和原生工具回执，避免工具先完成时抢读尚未写入的身份文件。同票 run_t112_native.py 也有相同前置等待，已按同一顺序修正；未修改生产 Panes.release。
- 旧结果没有 sessions 清单，夹具按此前授权清理，无法事后补查。新结果保存放行前、取得身份后的 sessions 清单，以及收尾后的整个隔离 CODEX_HOME 文件清单和 JSONL 首行，便于区分目录尚不存在、文件位置不同与定位器未绑定。GET 路径和 POST 数量分别记录，启动失败时也保存 launch、阶段文件和 home 清单。
- 新启动回归执行实际 driver 源码，只提供 daemon/process/FS 边界：reviewer-startup-red-02.json 记录修前一直等待身份且没有 release；reviewer-startup-green-01.json PASS，验证放行后取得身份、无领导进程不放行、放行后无身份不通过、领导进程变化不发布身份。首轮 reviewer-startup-red-01.json 是 VM 测试环境缺少 URL 的设置失败，保留但不算缺陷红态。该回归不作为原生 CLI 或沙箱证据。
- 候选副本必须写成功、匹配原生工具回执、持久化调用参数比对、解析后权限与 argv 检查均保留。原生权限归因仍为 INCOMPLETE；后续 REVIEWER-DIAG-03 在请求解析阶段失败，当前待 REVIEWER-DIAG-04。

## #42 / #44 权限调查：已由 #50 的真实边界对照归因

REALITY GATE: PASS（权限归因）。#50 的真实 good/bad 对照确认问题是旧 profile 探针，见本报告开头；以下保留此前调查过程。产品权限未扩大，原断言未放宽。

- **observed**：outside-native-03.json 的数据库读取通过；随后 profile 探针 exit=0，protected.txt 被写，原断言失败。该探针选择 --permission-profile :workspace，实际 reviewer 构造器选择 --sandbox workspace-write，两者并不相同。
- **measured**：reviewer-metadata-01.json 从起点 e3102389e 和候选 3ebbc9a3b 的实际 Panes.createReview 构造器分别取得完整启动记录。起点 effort=xhigh，候选按设置为 low；二者的沙箱均为 workspace-write，network_access=false、network_proxy=false、exclude_slash_tmp=true、exclude_tmpdir_env_var=true 均保持一致。该检查提供 PTY 替身，仅执行真实 CLI 版本探测，不声称运行了真实 reviewer 会话。
- **measured**：同一证据保存了两个已装 CLI 的 --version、--help、sandbox --help 原文。产品路径绑定 0.162.1，探针也是 0.162.1；把候选的 reviewer 启动器改传已装 0.163.0，启动前被原版本门禁以 codex_version_mismatch 拒绝。未放宽版本门禁；外层 Herdr/Codex 会话版本不等于本工作台的受管 CLI 版本。
- **inferred**：OpenAI Docs 的 [Permissions](https://learn.chatgpt.com/docs/permissions) 说明 profile 不与旧 sandbox 配置组合，内置 :workspace 允许写系统临时目录；[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)说明旧 exclude_slash_tmp/exclude_tmpdir_env_var 控制临时目录可写范围。因此旧 profile 探针不能直接代表 reviewer 的旧式沙箱。protected.txt 位于 /private/tmp 下，文档差异足以解释此次异常，但尚未证明本机运行效果。
- **measured**：outside-reviewer-diag-01.json 中，两个旧 profile 探针均越界写入；其余 6 个探针均 exit=2，CLI 要求 --permission-profile，不接受单用 sandbox_mode 来解析旧沙箱。候选写入没有发生，不能把这些设置失败解释为边界保护。此前尝试用 sandbox 子命令模拟旧沙箱的路径已从诊断代码移除。
- **此前 PROBE**：REVIEWER-DIAG-04 已在沙箱外 PASS。它用生产 serve 的现有 createGates 参数取得同一个 Panes 实例，调用真实 createReview、真实 PTY 和完整原始 argv，使用原 hooks、后台与身份校验，不提供 PTY 替身。测试只分配隔离 task/review 对象来验证启动边界，不冒充 claim/submit/独立审查验收。起点与候选各执行原配置、仅在隔离 home 增加父目录 writable_roots 的坏配置，共 4 个真实 CLI 会话。
- **独立观测**：本地 Responses API 根据 CLI 实际声明的工具返回一次 shell 调用，先写 candidate-probe.txt，再写父目录 protected.txt，每次使用随机内容标记。只有候选写成功才接纳本次边界观测；工具输出须在后续 API 请求中携带匹配 call_id，并在原生日志中持久化。持久化的调用参数/工作目录必须与发出的调用一致；完整 argv 的目录、approval、sandbox、网络/tmp 与 hooks 逐项校验，解析后的网络/tmp 策略也必须符合请求。保存进程身份、turn_context.sandbox_policy、工具回执与收尾后的文件读回值。坏配置必须实际写入保护文件且被同一业务 oracle 判为失败。API 在工具回执后等待收尾，不生成审查结论或触发另一张任务的交付过程。
- **停止条件**：若起点和候选的真实 reviewer 都越界写入，则上报涉及权限的 blocking issue，交主控转用户；若仅候选越界则修本票回归；若两者真实 reviewer 均保护成功且坏配置对照被拒绝，再把原生 runner 的旧 profile 探针换成同一真实会话路径。该停止条件现已由 #50 的第三种结果解决；完整 runner 将用同一路径重证。

早期协议预检 reviewer-stream-02.json 曾 PASS，但其手工工具声明未覆盖真实请求结构；本轮真实请求回放与原生纯文本调用补足该缺口，均不作为原生沙箱证据。真实会话的首次运行在 #46 的放行前身份等待处失败，第二次在 #48 的请求解析处失败，修后仍待外部权限运行。诊断脚本只写自己创建的临时夹具，身份绑定地收尾自有进程；清理未确认则保留现场并维持 INCOMPLETE。本轮原生结果将写 outside-reviewer-diag-04.json，旧失败摘要保留。脚本仅配置无凭据的 loopback 假 API，不请求真实模型，也不生成截图；没有系统级出站监测，因此 vendor_egress_observed 记为 null，不能把本地请求计数当作零出站请求的独立证明。

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

reviewer 保持 T-076 的 workspace-write 候选副本参数、独立 home、网络/tmp 限制与无 worker Git hook 环境。模型/强度设置不参与权限参数构造；outside-reviewer-diag-04.json 已以真实 good/bad 对照证明候选副本外的该文件写入边界；完整 runner 将再次验证。Herdr 期 launch-worker 保留默认值，移除 effort choices。

Tracer bullet：设置表单 → IPC → SQLite → 派发 → argv。Deep modules：复用现有 store、门禁和启动器。Ubiquitous language：沿用现有五个角色名。

## 本轮检查

| 检查 | 结果与摘要 |
| --- | --- |
| 实际 Git 快照解包 | PASS，baseline-extraction-final-03.json；本轮复验 baseline-extraction-rev3-01.json 也 PASS：保留 26 个真实 hook 链接，内部相对链接/硬链接成功，12 类非法输入写入前拒绝；恢复旧“拒绝全部链接”行为会失败。 |
| Claude 默认值红态 | controller-defaults-red-01.json：修前将 Codex 默认送给 Claude 的错误被独立默认值断言拒绝。 |
| 角色设置与 argv | PASS，execution-rev2-final-07.json：五角色默认、SQLite 重开、覆盖优先级、角色隔离、权限字段拒绝、reviewer 原参数、实际 zsh 退出码及启动失败事件。 |
| 已知坏变异 | PASS，mutants-rev2-05.json：旧 Claude 枚举、错误优先级、reviewer 误用 worker、固定 worker 门禁、惰性字符串掩盖启动失败均被拒绝。 |
| Claude 启动构造 | PASS，claude-profile-rev2-02.json：默认 Haiku/low、覆盖 Opus/high/Fast 及原权限参数，原隔离/钩子/版本/地址拒绝检查保留。 |
| IPC 合同 | PASS，ipc-rev2-06.json；本轮复验 ipc-rev7-01.json 也 PASS；保留原拒绝检查及新增设置 channel 的 iframe、未知窗口、非法字段拒绝。 |
| 构建 | PASS，build-rev2-final-03.json；临时构建目录已清理。 |
| T-108 回归 | PASS，t108-rev2-04.json；本轮复验 t108-rev7-01.json 也 PASS，未修改该测试。 |
| 已关闭夹具跨运行时读取 | PASS，closed-fixture-green-01.json；相同 Node 合同生产者、Python 消费者，3 条边界检查。修前在相同查询处失败，见 closed-fixture-red-01.json。 |
| reviewer 假 API 工具流预检 | PASS，reviewer-stream-final-04.json、request-replay-final-05.json；以实际 0.162.1 请求声明为输入，拒绝缺失增量/改写调用变异。code-mode-protocol-final-03.json 取得真实 CLI 纯文本工具回执，仅协议证据，非原生权限证据。 |
| 原生 high 红态 | PASS，outside-native-02.json 的 baseline_high / baseline_real_dispatch_high_refused，真实 daemon 门禁返回 worker_executor_mismatch。 |
| 原生全链路 | INCOMPLETE，outside-native-01.json 在解包前置条件失败；02 在已关闭夹具查询处失败；03 查询通过但 reviewer 权限探针失败；outside-reviewer-diag-01.json 的旧式模拟在 CLI 参数解析阶段失败；reviewer-diag-02 在首轮放行前身份等待处失败，API 请求数为 0。reviewer-diag-03 进入 API 后因错误的顶层 tools 假设失败。reviewer-diag-04 的原生权限 good/bad 对照已 PASS；native-04 在首步检索因缺少 rg 失败；native-05 通过检索、baseline 和 reviewer 后在 factory 首轮失败，后续待 native-06。 |
| reviewer 首轮启动顺序 | PASS，reviewer-startup-green-01.json；修前红态见 reviewer-startup-red-02.json。实际 driver 源码执行，边界由测试提供，非原生权限证据。 |
| 地图检查 | INCOMPLETE：稀疏 checkout 原有 8 个缺失文件链接问题，0 stale；本轮结果见 project-map-rev10-final.txt。 |

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
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-10.sh
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-06.sh
```

先提交再运行，使 source_head/code_revision 绑定完整提交。NATIVE-06 依次运行全仓检索、真实 baseline high 红态、changed-effort reviewer good/bad、出厂 worker、真实 Electron 设置后派发、主控覆盖与 CLI 不支持值反例；结果写 outside-native-06.json，旧结果不覆盖。只使用本地无凭据假 API，Electron 必须从内置盘运行。可用 T112_ELECTRON_DIST 指向内置盘上现有 Electron dist；默认是主控仓库的内置盘 Electron。构建和依赖测试副本在本票临时根目录/内置盘构建目录，spawn-helper 执行位只改私有副本；结束后直接清理已确认退出的自有夹具，不归档到外置盘。

## 已交接事项

- AGENTS.md:67、69 的固定模型/强度说法由执行主控转交构思主控；worker 未修改治理文件。
- 真实 reviewer 的该副本外路径写入边界已 PASS，网络/tmp 解析后配置亦核对；未另外运行网络连通性或每一种路径的写入探针，不扩大该单一路径观测的结论。
- 首轮独立冻结审查 independent-review-01.md 原结论 FAIL 保留。其 runner exit-1 和 shell 源码断言问题已修；后继候选尚待执行主控的新会话独立审查，不引用旧审查作通过依据。
- 全仓检索与 CLI 帮助原文仍在 search-final-02.json、cli-help-01.json 等原摘要中。当前模型/effort 不作固定值门禁；其他供应商的旧 provider 合同不在本票新增运行时范围。
- T-110 接线边界未扩大：renderer.tsx 原第 10–11 行 import、第 48 行 bridge 类型、第 570 行组件；main.ts 新增独立 settings IPC，preload.ts 增加一个 bridge 方法；sidebar.ts、原通知区块和原样式文件未改。
