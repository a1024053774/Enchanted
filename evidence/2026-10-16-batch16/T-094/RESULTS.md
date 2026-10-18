# T-094-1：启动失败诊断（2026-10-17）

状态：INCOMPLETE。busy-02 已复核为 10 次真实启动全部成功，且每次 start 前有至少 1500ms 稳定采样。按 main `c06a73179` 中的用户裁定与主控 #78，两个获准修订的验收文件已改为检查行为，新候选 14 个用例全部通过；旧 `617863704` 的稳定窗口和超时 argv 检查为红，错误版本变异体也为红。但旧 `617863704` 已正确实现启动时读取版本，其修订后的版本检查实际通过，无法满足“这一项旧实现也必须失败”的字面要求，交主控裁定，不制造无关失败。独立审查和本轮原件归档仍待完成。

绑定：task T-094 / attempt a1 / worker s16-t094；启动记录 `launch-efca9e180a594c2e98ec594874eaf253`；session `1f06c59c-a447-47e4-8075-9a7571db35d3`；规格 T-094 ready_rev 1；基线 `61786370428c3ec5f894ea60acccf2695d54c2dc`。任务书未给 fence、门禁 state 或 submit 参数，worker 不推测这些身份。

## 诊断与改动

真实 red-01 由执行主控运行，Herdr client/server 均为 0.9.4，Codex CLI 0.163.0。5 次逻辑启动、5 次真实 agent start、0 个模型回合；前三次成功，后两次失败。5 个自建 pane 均由探针关闭；主控确认隔离 CODEX_HOME 已删除。原件位置见 `red-01.archive.json`，精简结果见 `red-01-summary.json`。

两次失败分别为 `wF:p5A` / `launch-6f6f69df7f824b8ab594c41704e4fff5` 和 `wF:p5B` / `launch-c995dbfe0426468bb726f8edc6d1114b`。Herdr 返回 `agent_pane_busy`，start 调用耗时分别为 0.01128 秒与 0.01114 秒。这两次失败不是 30 秒等待超时。原启动记录丢失了这一错误身份，只有 CalledProcessError 字符串。

red-01 紧邻 start 前的 process-info 报告 shell 独占前台组；再前一条仍有 `kiro-cli init zsh post --rcfile zprofile`。当时尚不能判断后续占用者。后续 busy-01 已捕获 conda 初始化，具体更正见主控 #62 一节；本票不再以 Git 提示符解释这两次失败。

[Herdr v0.9.4 的 start_agent](https://github.com/herdrdev/herdr/blob/v0.9.4/src/app/agents.rs) 既检查终端 agent 状态，也重新检查 shell 是否可用；[CLI 就绪等待](https://github.com/herdrdev/herdr/blob/v0.9.4/src/cli/agent.rs) 区分 busy、超时、名称丢失和首屏阻断。这些是源码事实；red-01 无法反推命中了 server 内哪一个 TargetBusy 分支。本票不改 Herdr、不改 zsh，也不增加启动重试或时限。

`scripts/launch-worker` 现将失败命令、退出码、stdout、stderr、错误码、失败阶段和完整 start argv 写入启动记录。start 失败后，只读观察本次 pane 的进程和 agent 注册状态，分别记录 `outcome=started_unregistered`、`started_not_ready`、`started_unconfirmed` 或 `unknown`；未启动的明确拒绝记录 `not_started`。查询失败保留诊断，不将未知注册状态当作名称缺失。

按主控 #57 的修订，入口不关闭失败 pane：记录 `pane_disposition=retained_for_controller` 和 pane id，交主控处置。复现探针仍会关闭自己创建的 pane。半成功保留 `phase=failed` 的拒收语义，同时带独立 outcome；不会被现有提交尾注入口当作成功启动。未改动范围外的启动记录校验器、acceptance/、地图、全局配置或 Herdr server。

### agent_pane_busy 的当前处理与依据

入口在调用 start 前要求 shell 独占前台组的采样持续稳定 1500 毫秒，目标采样启动间隔为 100 毫秒；任一采样出现子进程或其他不满足条件的状态就重新计算稳定窗口。shell 检查总期限仍为 30 秒，不随重计时延长。通过后只调用一次 `herdr agent start`。收到 `agent_pane_busy` 后仍保存诊断、报错退出、保留 pane，不重试；这保留了稳定窗口误判时的明确失败路径。

稳定窗口是主控 #63 明确选择的就绪判据，不是初始化完成证明。初始化中途若空闲超过窗口，或子进程只在采样之间运行，仍可能误判；README 已写明。Herdr CLI 自己的就绪处理仍由原版本负责，探针记录的一次 CLI 调用不等于只有一次 server 内部请求。

### 主控 #60：把首次前台采样提升到错误身份

复用收到 busy 后紧接着的第一次 `herdr pane process-info`，不新增查询或轮询。校对 pane 身份后，将采样时刻、前台进程组、各进程的 PID / name / argv 写入 `busy_foreground`，同时附在 `error` 字符串和终端错误摘要末尾。原始 Herdr stderr 保持原样。argv 缺失时保留 null，不推测命令；查询失败仍留在 observations，不伪造占用者。该采样发生在 CLI 返回 busy 后，不能冒充 server 做出拒绝判断的同一时刻。

新增合同测试把带随机独立参数的 `git status` 进程放入边界夹具，核对 argv 出现在记录错误和终端报错中，并核对 start 后只有一次 process-info、接着原有 agent get；没有再次 start 或关闭 pane。修复前在 `264e6df66970b419398e27ee7d2ff9235cca006b` 上因缺少 `busy_foreground` 取得合同红态；修复后全部 7 个边界场景通过。记录见 `busy-contract-red-01.txt`、`busy-contract-green-01.txt`、`busy-contract-summary-01.json`。这是诊断合同证据，夹具中的 Git 不是对真实根因的发现。

本轮还通过未修改的旧验收场景 `test_delayed_shell_then_commit` 和 `test_agent_start_failure_is_not_retried`，结果分别见 `busy-existing-shell-01.txt`、`busy-existing-start-01.txt`。本轮完整命令输出与夹具暂存在 `/tmp/t094-busy-details-01`，由下述复现脚本一并归档，不覆盖前轮证据。

主控运行 `sh evidence/2026-10-16-batch16/T-094/outside-busy.sh`：默认在同一稀疏 worktree 独立启动 8 次，也可传 `<新label> <5～10>`。沿用隔离 CODEX_HOME、只到首屏、0 个模型回合和每次 finally 只关闭自建 pane 的探针；原件直接写外置盘。busy 记录必须把前台采样放进 error 和终端 stderr，否则探针报诊断不完整。每次 argv 会打印到主控日志，清单生成在本目录。

busy-01 数据已回传，8 次中 6 次成功、2 次失败；捕获的是 conda 初始化，先前的 Git 提示符假说不成立。该修订应用于本报告的当前解释，不改写历史原始日志。

## 主控 #62：初始化间隙的提前放行

原件：`busy-01/run.json`、每次 `herdr.jsonl` 和 `identity/records/launches.jsonl`，精简数据见 `busy-01-summary.json`，归档清单为 `busy-01.archive.json`。共 8 次 start、0 个模型回合，8 个自建 pane 都由探针关闭。

| 次数 | pane / launch | 放行时最后一个进程快照 | busy 后第一次采样 |
| --- | --- | --- | --- |
| 1 | `wF:p5J` / `launch-835b22996eb8413b82176914c752ee37` | pgid = shell PID 81538，只有 PID 81538 的 `-zsh` | 同组出现 `/opt/miniconda3/bin/conda shell.zsh hook` 及 zsh 子进程 |
| 4 | `wF:p5N` / `launch-c279b01084c04d06a5a5fc3881c0993d` | pgid = shell PID 82933，只有 PID 82933 的 `-zsh` | 同组出现 `conda shell.posix activate base` 及 zsh 子进程链 |

只读核对 `/Users/luckye/.zshrc:129–142`，其中第 131 行调用 `/opt/miniconda3/bin/conda shell.zsh hook`，第 133 行 eval 初始化输出；与运行采样相符。触发者属于用户的 shell 初始化配置，本票不修改它。启动器的责任是核对初始化完成，不能把“用户配置触发”当成放弃编排修复的理由。

提前放行位置精确如下（`96456ceac`）：

- `scripts/launch-worker:137–142` 已完整要求 shell PID 有效、前台 pgid 等于 shell PID、前台进程数组长度为 1、唯一 PID 就是 shell、进程名属于 shell。
- `scripts/launch-worker:143` 见到第一次符合条件的快照便 `break`，随即第 145–148 行调用 start。30 秒只是检查失败时的截止期限，不是初始化完成证明。
- busy-01 在这个 break 前确实只有 shell，随后初始化继续派生 conda。问题不是“把存在子进程的同一份快照误判成空闲”，而是“一次无子进程的快照不能证明以后不再派生初始化子进程”。

受控红态：`python3 -B scripts/test_launch_worker_failure.py --report /tmp/t094-init-gap-details-01/red.json LaunchFailure.test_initializer_gap_is_not_initialization_complete -v`。夹具时序由测试独立指定为“首次 shell 独占 → conda 子进程 → 初始化完成”，在完成之前启动会被拒绝。当前代码在首次快照后调用 start，返回 `agent_pane_busy`，测试失败，见 `init-gap-red-01.txt` / `init-gap-red-summary-01.json`。完整边界套件本轮结果为 8 项中原有 7 项通过、新红态 1 项失败，见 `init-gap-suite-red-01.txt`，不能称为全绿，也不能据此集成。完整原件暂存 `/tmp/t094-init-gap-details-01`，等待后续主控归档。

主控 #63 已否决 shell 执行回执，原因是会写入用户真实 shell 的历史并显示在 pane 中。本票没有实现、也不会运行该回执方案。主控选择稳定窗口并接受其不能证明初始化完成的局限，执行方式见下一节。

## 主控 #63：稳定窗口实现与验证

取值：1500 毫秒采用主控建议区间的上限，接受每次至少约 1.5 秒预启动检查的代价，拒绝本轮要求模拟的 200 毫秒初始化间隙；100 毫秒为目标采样启动间隔，查询本身超过该间隔时不堆叠调用。这是经主控选择的参数，不宣称从对照实验得出了最优值，也不声称所有初始化间隙都短于它。

`scripts/launch-worker` 保留现有 shell / pgid / 子进程检查，以单进程 `time.monotonic()` 计算稳定窗口和总期限。不合格采样清空稳定起点，30 秒截止点始终不变。成功采样后再次核对截止点，防止查询跨越期限后放行。启动记录增加 `shell_ready_policy={stable_ms:1500,sample_interval_ms:100,timeout_ms:30000}`。超时不再查询或启动 agent：将最后一次成功采样的完整前台信息写入 `shell_foreground`、`error` 和 stderr；若从未成功采样则为 null。保留 pane，仍不改 `.zshrc`、Herdr 或全局配置。

两个受控场景经过真实 launch-worker 命令入口，Herdr / Codex 是显式替身，不连接真实服务、没有模型回合：

- 初始化间隙：前 200 毫秒只有 shell，200～1000 毫秒出现前台 conda 子进程，随后 shell 独占。旧候选提前调用 start 并被拒绝；新候选等待最终稳定段至少 1500 毫秒才调用一次 start，测试同时检查计时重置。
- 持续占用：每次采样都有前台子进程，30 秒期限内没有 start；到期记录最后 argv（含每次独立生成的参数），错误记录和终端输出都必须包含它，pane 留给主控。新候选通过实时时限与 argv 断言。

正式反事实命令：`python3 -B scripts/test_launch_worker_failure.py --launcher evidence/2026-10-16-batch16/T-094/launch-worker.pre-stable --report /tmp/t094-stable-details-01/red-02.json LaunchFailure.test_initializer_gap_is_not_initialization_complete LaunchFailure.test_persistent_child_times_out_with_last_argv -v`，旧候选为 `b7b7472b7031241cac733443cee8934afd2e24c9` 的原脚本。两项均红：提前启动、缺少最后前台 argv，见 `stable-contract-red-02.txt`。

正式绿态命令：`python3 -B scripts/test_launch_worker_failure.py --report /tmp/t094-stable-details-01/green-02.json -v`，9 项全部通过，用时 56.459 秒，见 `stable-contract-green-02.txt`。完整原件与既有初始化间隙红态由 `outside-busy-02.sh` 归档，当前仍在 `/tmp/t094-stable-details-01` 和 `/tmp/t094-init-gap-details-01`；仓库只留文本摘要。

首轮夹具曾跨子进程比较 monotonic 值。本机 Python 3.9.6 的观测显示每个进程的数值起点不同，导致模拟子进程阶段没有出现；该轮 `stable-contract-red-01.txt` / `stable-contract-green-01.txt` 保留，但不作为 200 毫秒场景的通过证据。已改用跨进程 Unix 时间并重新取得上述同夹具红绿对照；产品内部计时一直使用同一进程的单调时钟。探针的跨 CLI 时间记录也改成 Unix 纳秒。时钟观测见 `stable-clock-probe-01.txt`。

交付检查：Python / 内嵌代理与 shell 脚本语法通过，文本为 UTF-8、无 BOM、LF。完整 diff 的空白检查指出 `stable-clock-probe-01.txt` 首行原始 Python 版本输出自带尾随空格；为保留原件未清洗。排除这一原始输出文件后，其余变更的 `git diff --check` 通过；不将完整空白检查记作通过。

真实复现：主控已运行 `outside-busy-02.sh`，标签 `busy-02`，测试实现为 `acf747d948be03df6ea91bb852bdfa545e938ee0`。worker 复核原始 JSONL、CLI 调用时间及每次 close：10 次独立首屏启动均 rc 0，每次 start 前最后一段 shell 独占采样至少 1500 毫秒，10 个自建 pane 的 close 均 rc 0，0 个模型回合。见 `busy-02-summary.json` 与 `busy-02.archive.json`。这是本轮真实复现结果，不作为长期可靠性或收益改善的证明。

### 原有验收冲突及范围外问题

- 旧 `test_launcher_shell_ready_e2e.py` 写死恰好 5 次 process-info，历史失败保留在 `stable-legacy-delayed-01.txt`。主控 #78 获用户授权后已修订该断言，见下一节；其余既有用例与断言保留。
- 旧 `test_herdr_traceability_e2e.py` 固定期待 CLI 版本 0.162.1，历史失败保留在 `stable-trailers-01.txt`。主控 #78 获用户授权后已改为独立观察启动时版本输出；未伪装真实 CLI 版本。
- 根 README 的既有“原生门禁入口”段落仍指向 Synara fork，与 `acceptance/entry/a2a_gates.py` 实际转交本仓库 workbench CLI 的事实不符。本轮仅按授权新增启动器稳定窗口与局限说明；门禁文档更正超出本票范围，留给主控另行处理。

## 主控 #78：仅修订获准的两个验收断言

授权来源：用户裁定见 main `c06a73179:.project-map/tickets/T-094-launch-worker-intermittent-start-failure.md` 的“裁定”节及 `20261018T004018Z-ideation-answer-001`。本轮 acceptance/ 只修改 `test_launcher_shell_ready_e2e.py` 和 `test_herdr_traceability_e2e.py`，没有修改生产启动器或其他 acceptance 文件。

稳定窗口断言：保留原有 unknown 状态、前台子进程、不同 pgid、shell PID 被其他程序替换的夹具输入；新增独立 Unix 纳秒事件记录，检查初始化子进程确实出现、start 前最后一段连续采样全部只有 shell 且持续至少 1500ms。保留 split / process-info / start 的顺序与单次 start 约束，去掉精确查询次数。另加持续前台子进程的超时用例，核对独立随机 argv 同时出现在启动记录错误和终端报错里；原有超时、挂起查询、错误、身份不符和不重试断言不变。

版本断言：边界记录器转交启动器实际发起的同一次 `codex --version`，独立保存其返回码和 stdout，再与 prepared 启动记录的 `cli_version`、提交尾注中的 A2A-Tool 分别比较。预期值不从启动记录本身取得，也不固定某个版本号。原有固定假 CLI 输出 0.162.1 仍是夹具输入，真实 CLI 输出本轮为 0.163.0，两者都经实际调用回执核对。启动器从起点就会执行 --version，本轮没有为此改生产路径。

没有放宽其他断言：`revised-assertion-scope-01.json` 保存 AST 核对结果；两个目标以外的原方法保持一致，稳定窗口测试中从 managed_env 开始的全部原断言保持一致，提交尾注核对仅改变 A2A-Tool 预期来源，剩余方法体保持一致。

统一重放命令：`python3 -B evidence/2026-10-16-batch16/T-094/run-revised-acceptance.py`。脚本在 /tmp 建立从 `61786370428c3ec5f894ea60acccf2695d54c2dc` 提取的 scripts 副本和错误版本变异体，只运行真实 Git、显式 Herdr 替身和 codex --version，不启动真实 Herdr 或模型。每条确切命令、退出码与耗时见 `revised-acceptance-summary-01.json`；完整 stdout/stderr、夹具和本轮修订测试源码快照在 `/tmp/t094-revised-acceptance-01`。脚本返回 1，状态为 INCOMPLETE，因为下表版本旧实现红态要求未满足。

| 检查 | 旧 617863704 | 新候选 | 解释 |
| --- | --- | --- | --- |
| 初始化子进程与连续 1500ms shell 独占 | 红：仅 72.493ms 就 start | 通过 | 同一修订断言拒绝旧提前放行 |
| 超时报出前台 argv | 红：缺少 shell_foreground | 通过 | 同一修订断言拒绝旧诊断缺失 |
| 启动版本等于实际 --version 输出 | **通过** | 通过 | 旧脚本第 65 行原本就正确读取输出 |
| 实际执行 --version、却把记录版本加上错误后缀 | 变异体红 | 不适用 | 断言因 cli_version 不等于独立回执而拒绝，不是设置或其他错误 |

新候选共 14 个用例全部通过：LauncherContract 7 项（含新超时 argv 用例）、原 Contract 7 项（含提交、amend/rebase/merge、版本、原生身份替换、打分与损坏拒收）。两项旧 shell 红态、版本旧实现正例及错误版本反例共另 4 步，合计 18 步全部保留。用户要求版本旧实现必须红与代码事实不符，本 worker 不擅自把它判红，也不自行将变异体替代认作该要求已获批准；需主控裁定是否接受“旧版本正例 + 错误记录版本反例”的证据组合。

本轮无需沙箱外模型复验。请主控运行 `sh evidence/2026-10-16-batch16/T-094/archive-revised-acceptance.sh`，把完整本地原件归档到外置盘并生成清单；该脚本不会将 INCOMPLETE 上调为 PASS。独立 reviewer 应依据新修订断言、原始回执和已知坏实现结果审查最终候选。

## 主控 #59 回传原件的核对

主控在沙箱外运行 `outside-green.sh`，脚本 rc 0；worker 随后直接读取外置盘上的 `identity/records/launches.jsonl`、`herdr.jsonl` 和 `run.json`，确认启动记录原件与探针保存的快照逐字段一致。核对命令为 `python3 -B evidence/2026-10-16-batch16/T-094/check-recorded-green.py`；结果见 `recorded-green-check-01.txt`，精简数据与原件清单见 `green-01-summary.json`、`unregistered-01-summary.json` 及同名 `*.archive.json`。重放只读核对时加 `--output <不存在的新目录>`，原始记录与已有摘要均保留。

| 原件 | 启动事实 | 记录核对 |
| --- | --- | --- |
| green-01 第 1、3、4、5 次 | rc 0，`phase=started` | 4 次启动成功 |
| green-01 第 2 次 | rc 1，`phase=failed`；`wF:p5D`；`launch-ff2ef727627a415baaf3f278e62515fe` | `error_code=agent_pane_busy`，`outcome=not_started`，原始 stderr 已保存 |
| unregistered-01 | rc 1，`phase=failed`；`wF:p5H`；`launch-431cd36ffa9e44e1a6c9067ac44671af` | `outcome=started_unregistered`；真实 Codex 进程存在，agent 名称缺失；成功启动消费入口拒收 |

green-01 第 2 次的 `herdr_stderr` 包含 `agent target pane wF:p5D is not an available shell`；`error_code` 与原始 Herdr 输出一致。`launch.stderr` 末尾仍有 CalledProcessError 的退出码文本，但同一行前面已打印 `错误=agent_pane_busy，结果=not_started`，完整输出前部也有原始 Herdr JSON；启动记录并非只剩退出码。该次 start CLI 调用耗时 2.02456 秒，仍未达到 30 秒。失败后入口取证捕获到同一前台组中的 `conda shell.posix activate base` 及子 shell，后续探针观察又只剩 zsh。这支持“shell 快照可能处于初始化过渡”的推断，不能证明 Herdr 在确切拒绝时刻命中了哪个检查分支，更不能证明稀疏 Git 提示符是根因。

因此，green-01 不满足“全部启动成功”分支；它提供了“失败时带可读原因”分支的真实证据，失败的那次仍按失败计数。unregistered-01 是明确标注的故障注入：一个真实 `pane run` 启动 Codex，未调用真实 `agent start`；边界返回注入的 `agent_name_not_found`。入口观察到 PID 65114 的 Codex 和缺失的名称，写成独立半成功结果。它证明分类，不是自然出现的名称丢失故障或原始竞态的根因证明。

两组共 6 次逻辑启动、5 次真实 agent start、1 次未命名 Codex 启动、0 个模型回合；每次探针均只关闭自己 split 返回的 pane，6 次 close 均 rc 0。主控确认 wF 没有残留的自建 pane。启动入口本身保留 pane 的行为与主控 #57 的修订一致。

## 验证与限制

- `python3 -B scripts/test_launch_worker_failure.py --launcher evidence/2026-10-16-batch16/T-094/launch-worker.parent --report .../contract-final-red-01.json -v`：旧实现拒绝不了诊断/分类缺陷；失败日志保留。
- `python3 -B scripts/test_launch_worker_failure.py --report .../contract-final-green-01.json -v`：6 个场景全部通过。夹具显式替换 Herdr/Codex，不连接 socket，不证明真实 Herdr 时序。pane id 每次使用新的随机输入；每次仅一次 start；所有场景均断言入口不关闭 pane。
- `python3 -B acceptance/test_launcher_shell_ready_e2e.py --artifacts /tmp/t094-existing-launcher-contract-01`：6 个场景全部通过，用时 70.800 秒，结果见 `existing-contract-01.txt`。验收文件未修改；原始夹具与命令日志已归档，见 `existing-contract-01.archive.json`（15 文件 / 103147 字节）。边界测试完整输出见 `contract-details-01.archive.json`（5 文件 / 178556 字节）；历史摘要中的 pending 路径是归档前的记录，原件没有覆盖。
- `project_map.py status --root .`：主控 #63 结果为 `project-map-status-05.txt`；主控 #78 本轮结果另存 `project-map-status-06.txt`。

历史 `outside-green.sh` / busy-01 原件全部保留。本轮稳定窗口使用 `outside-busy-02.sh` 取得真实证据；后续重放须换用新的 label 和归档目录，避免覆盖历史原件。

按 behavioral-acceptance-review 的独立性要求，最终验收须由主控另开干净只读 reviewer 会话。worker 的测试和诊断不能代替该结论。此前自动关闭方案的日志保留为历史证据，已在 TEST-PLAN.md 标明不适用于修订后的候选。
