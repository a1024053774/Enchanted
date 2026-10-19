# T-093 正常登录 profile：交付结果

2026-10-17；task T-093，attempt a1，worker s16-t093，ready_rev 1。
受管 session 67f986cc-92e4-4089-9c22-802a1143b645，原生 session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
工具 codex-cli 0.163.0，模型配置 gpt-6.1-sol / xhigh；配置不证明实际供应商 tier。

**整票 INCOMPLETE：第三轮独审的旧候选 NO_GO 已保留；本轮恢复白名单局部红绿通过，新候选 T-096 原生七场、后续独审／门禁尚未完成。** 最新交接为 [请求 20](REVIEW-REQUEST-T093-20.md)，依据主控 #129 延续 #125 的保守裁定。真实模型回合仍不跑。

## 主控 #139：r21 两场的 renderer 就绪判定

**整票 INCOMPLETE，诊断为 runner 缺陷。** 主控在 0be3d3ff2 上回传 r21 的 tracer／three／no-argv／version／no-session 五场 PASS、cleanup=true；本轮不重跑这五场。isolation 和 empty-reopen 的 KeyError: 'launch' 来自 runner 过早接受初始化 DOM 帧，不是“未恢复窗格可以没有身份”的合同。T-096 裁定 B 要求 worker 未恢复但保留窗格身份；主控缺 argv 同样须保留身份并显示未恢复。第三窗口合法空集则是 panes=[]，不是三个无身份占位格。

只读对照 [r21-two-case-diagnosis-22.json](r21-two-case-diagnosis-22.json)：isolation 的三个 DOM pane（构思、执行、worker）都没有 launch；snapshot 中分别是 restore_argv_missing／restored／restore_managed_attempt_requires_reclaim。empty-reopen 的构思 DOM 已就绪，执行与 worker 尚无 launch；其 window-2 的 observer-protocol 原件第 2 次 inspect 已出现三格完整身份。runner 却缓存第一次的 second，后续循环仍从旧帧查找。r18b 同名两场的 after-view 均已有三格完整 DOM 身份，包括两个只读的失败窗格。app、renderer、driver、run_restart.py 在 57c3bfb63 与 0be3d3ff2 间逐字相同，没有产品 UI 改动。

根因是 driver 在返回 IPC 回复前已更新 latestSnapshots，随后 inspect 又把该 map 的值附到早先读取的 DOM 上；snapshot 已到达不代表 React 已提交 DOM。原 inspect_window 只检查格数及 snapshot 存在，因而把这种混合帧当成就绪。修复只收紧 evidence/T-096/run_restart.py 的 inspect_window：DOM 身份及 input_enabled 必须与同格 snapshot 对齐，否则继续原有的有界等待。4 秒、64 次 observer RPC 预算、全部下游业务断言和归档核对均未改，没有改成忽略无 launch 的格，也未从 snapshot 补造 DOM 观察。该 runner 的最小修复依据主控 #139 明确授权；不改 r18b/r21 运行原件或任何旧 fixture。

[红态](renderer-readiness-red-22.json) 用 git show 导出的 r18b 旧候选 runner，配合同名旧／新原件的最小只读观察输入，命中两场原始未完成帧和身份／状态／持续占位反例。没有导入整个 runner 或启动 CLI／helper／GUI／模型。[绿态](renderer-readiness-green-22.json) 同一 24 项通过：r18b 两个已渲染正例、r21 后续完整帧继续接受；缺身份、错绑定、状态不同仍不接受；持续占位仍在原期限超时；已保存空窗规则及失败窗格只读断言不放宽。只证明 runner 逻辑，不能替两场原生重跑背书。本轮依“不调用模型”没有新开模型审查。

isolation 的 cleanup=false 是独立未决问题：只读清单当前显示源与归档差异仅为 state.sqlite3（499712／479232 字节）和 WAL（0／4120032 字节）；其他文件数／目录数／链接及目标文字一致。没有足够证据确定复制时何者变化，不能把当前差异推断成 root cause，也不把归档检查改成忽略 SQLite。原测试目录与外置副本不改不删、13 PID 已退出只引用主控核对；本轮没有发信号或重新查询 PID。新两场仍须严格 cleanup=true，否则保留新现场并停止。

只重跑两场的命令和新标签见 [请求 22](REVIEW-REQUEST-T093-22.md)。产品源码及 app 与 0be3d3ff2 相同；原五场 PASS 仍绑定原候选。最终 native 验收、独审及门禁尚未完成；不将离线绿态上调成整票 PASS。

## 主控 #132：helper 失败诊断（基线 19c297315）

**整票 INCOMPLETE。** r20 七场仅由主控完成 tracer／three 两场 PASS、cleanup=true；no-argv 在初始化被中断，后四场未跑。本轮没有重跑，旧候选两场不替新候选背书。原始 fixture／T-096 外置输出／日志保留，独立审查报告原文不改。只读诊断摘要 [r20-no-argv-diagnosis-21.json](r20-no-argv-diagnosis-21.json) 的根因仍 unknown：事件 105 是 helper 输出 JSON 解析失败，缺少当次输出和退出信息，内存压力只有相关迹象，不能补称因果。

processInfo 在原异常上附带 helper 已捕获的 stdout／stderr、退出码／信号、killed、spawn 错误码、根 PID／helper PID、单调耗时。daemon 追加 diagnostics.process_query，原回复和 request_rejected 事件同时保留。解析／执行异常仍返回 orchestration_failed；Refusal 类型／代码和原 details 不改。元数据未知时明确 null，执行失败不伪造 exit=0。身份未知仍立即停止，无重试、回落、缓存成功或终端放行；不新增其他日志文件，helper 本身仍不读 auth／argv／环境。

[红态](helper-diagnostics-red-21-02.json)：基线真实入口通过给定边界收到空／截断 JSON、退出 0 但 killed=true 的空输出、非零退出、SIGKILL、超时终止、EPERM、坏 schema／row，9 项均以诊断缺失的业务断言失败，健康项通过。[绿态](helper-diagnostics-green-21-02.json)：同一 10 场全通过，实际 daemon handler、Panes 和 SQLite；每失败请求仅一次 helper，返回与持久事件相等，精确保留 nonce／输出／退出信息及给定单调耗时，零释放／终端写入。没有执行真实 helper、daemon/socket、CLI、auth 或模型；这不是内存压力复现或根因修复证明。

局部回归 observer 11 项、alias 2 项、T-096 恢复合同（三种身份模式和原反例）、T-091 IPC 19 项通过。恢复白名单及完整 argv／版本／session／leader、OS／网络／转发／门禁均未改。新七场标签已在 [请求 20](REVIEW-REQUEST-T093-20.md) 改为 t093-r21-*，output 仍固定外置 T-096 下；何时运行由用户决定，worker 不启动。新候选独审、原生七场和唯一门禁仍待完成。

限定独立审查 [HELPER-DIAGNOSTICS-REVIEW-21.md](HELPER-DIAGNOSTICS-REVIEW-21.md) 对 a4fdee0b8ebf7b60ec26ceea32515ee0ef694832 给出 PASS（仅 L0/L1）：15 个新输入通过，10 类失败在旧基线上均被同一诊断缺失业务断言拒绝，无导入／环境错误；实际 daemon 回复与重开 SQLite 后的事件一致。原错误对象／类型／代码、单次调用、停止／生命周期结果保持。首轮审查夹具跨 VM 原型比较的假红保留，修正临时夹具后另写 run-02。最终归档提交只加报告／文本和清单，运行源码与测试与受审版本逐字相同。真实 helper、OS／socket、原生七场仍未运行，用户决定重跑时机；此局部 PASS 不替整票独审或门禁。

下文均保留为各旧候选及阶段的历史记录。

## 第三轮 P1 后：恢复白名单

[independent-review-03.md](independent-review-03.md) 与 REVIEW-OUTSIDE-04.sh 原文保留。审查在 788d75f4a 观察到实际 claudeLaunch 生成的正常登录记录仅缺 authentication 就执行版本／PTY 并记为已恢复。worker 用同一 reviewer 探针、精确 788d75f4a 源码在新目录复现：[restore-whitelist-red-20.json](restore-whitelist-red-20.json) 中 cli_calls=pty_calls=1，pane_restored。原案例／oracle 不变，只迁移 scratch／依赖 URL 和合成输入路径，未覆盖旧 reviewer 现场。

当前 recover 默认拒绝，仅正面识别现有 T-096 假 API 主控合同才进入原 argv／task／版本／session／规范身份核对。依据来自 fd5c93e6e 及当前 claudeLaunch：role_card_revision=T-078-2/P1、公开假 token、规范 http://127.0.0.1:显式端口 origin、规范 /private/tmp 隔离 HOME／config、zsh 等同时成立；authentication 可缺省或为假 API 类别，不接受其他类别、额外真实 API/OAuth key 或 NODE_OPTIONS。它是既存认证 profile 的机械识别，不新建策略引擎或恢复生命周期。

正常登录 auth、role revision、audit/preflight、hook 授权、process log、私有 HOME/config 前缀、已知 trace loader、正常登录以 exec 开头的 shell 命令任一标记存在，优先拒绝为 normal_login_restore_requires_protected_start；不能靠删除 authentication 降级。不能确认的记录为 restore_record_unrecognized，两者都保留未恢复，在任何 CLI／PTY／auth 读取之前结束。worker 的 reclaim 拒绝、历史 launch、完整 argv、版本／session、规范执行路径和实际 leader 核对不放宽。

第一次白名单候选 116985ec9 的局部限定审查仍为 FAIL，原文保留在 [RESTORE-ALLOWLIST-REVIEW-20-01.md](RESTORE-ALLOWLIST-REVIEW-20-01.md)。独立 29 场中，正常登录仅残留 shell 的 exec 形式仍被恢复；[原始结果摘要](restore-independent-red-20-01.json) 与 [扩展合同红态](restore-contract-shell-red-20.json) 都保留版本／PTY 到达的业务失败。该候选不能放行。后续修正补上此标记，且正面要求 fake P1 的四项 shell argv 与“完整命令后回到 zsh”的既有形式；缺失／未知 shell 也默认拒绝。只识别形式，不执行或从记录恢复 shell 命令，真正恢复仍使用原 argv 的逐项核对。

[restore-contract-green-20-05.json](restore-contract-green-20-05.json) 保存 30 个 profile 观察：11 个完整／缺字段／部分正常登录、15 个无法识别、2 个合法无 auth 的旧假 API＋1 个显式假 API、1 个 worker。拒绝项均零版本／PTY；三模式各 22 个命名不变量通过，不冒称 66 场原生测试。两个旧记录正例未删，补齐历史 launcher 确实保存的 P1 元数据及 shell 形式；显式假 API 是新增正例。恢复旧单字段 guard、分别删角色版本／假 token／loopback URL 依据、截实际 argv、删身份一致性、固定 leader 及历史 worker 坏实现均被业务断言拒绝。

唯一针对性复核对 1db51d21d 仍报 FAIL：[RESTORE-ALLOWLIST-REVIEW-20-02.md](RESTORE-ALLOWLIST-REVIEW-20-02.md) 原文保留。19 场中仅“未知命令保留合法前后缀”绕过了形式检查，见 [原结果](restore-independent-red-20-02.json)。最终修正删除首尾猜测，要求记录中的完整 shell 命令逐字等于对原 argv 逐项引用后的既有 fake 命令；该纯字段核对先于旧 PID 探测和所有 CLI／PTY／auth 边界。原 argv 校验仍由 resumeArgv 负责，缺 argv 仍返回 restore_argv_missing，版本／session 等原诊断不绕过。

[扩展合同红态](restore-contract-command-red-20.json) 在 1db51d21d 以未知 shell 到达版本／PTY 的业务断言失败；最终 green-20-05 拒绝此新输入。另把审查者原脚本原字复制为 REVIEWER-SHELL-PROBE-20.mjs，仅迁移输出根，worker 重放同一 19 项 oracle：[旧候选 18/19](shell-oracle-worker-red-20.json)、[修正后 19/19](shell-oracle-worker-green-20.json)，均含实际 claudeLaunch 成对生成及新 nonce／中文／引号。此为 worker 重放独立设计的 oracle，**不是新的独立审查通过**；两份 FAIL 报告保留，最终候选仍须主控复审，不再追加本地审查循环。

[旧 reviewer 探针绿态](reviewer-replay-green-20.json) 和 green-20-03 等只证明首次白名单候选，不替本次 shell 修正背书。其 fake 子例写的是 synthetic recorded original argv，未保留真实 launcher 的 shell 形式，当前不再把它算合法 P1 正例；探针原文和输入不改写。最终两类 fake 正例由上述实际恢复合同及使用实际 claudeLaunch 成对生成记录的限定独立复核重新核对。

本轮仅改 panes.ts 的恢复准入和 test_t096_restore.mjs；T-091 IPC 19 项、T-096 daemon 7 项局部回归在完整命令修正后再次通过（regression-20-03）。网络 profile／转发器／事实脚本／processSnapshot 与其余调用点不改，第三轮其余 PASS 仍只覆盖原报告范围。旧 r18b 七场与局部替身不能替新恢复准入背书；必须按请求 20 以新候选重跑七场，output 固定在外置盘 T-096 下，逐屏批准，模型／fake POST 预算 0。

下文请求 19 的结果均保留为旧候选历史，不把第三轮 NO_GO 上调。

## 主控 #127 的外部结果与独立事实复核

[r18-os-and-chain11-summary-19-02.json](r18-os-and-chain11-summary-19-02.json) 保存原始路径、四项生产／测试编译、八场完整运行／预定失败、两份真实 V 收据及 none 的逻辑转发记录和上游收据。生产出站固定 443；测试为同函数生成的 18443，其他权限不变。每场 cleanup=[]、fixture_removed=true、writer 逐项确认；主失败均符合预定，凭据扫描 0、真实 CLI／真实上游／真实 auth 读取／真实模型 0。8 场 HOME 清单差异均为 0，但 pass_condition=false，依据用户裁定 A，仍以 OS 禁写和反例为条件。

T096-REGRESSION-16.sh 原先错误地把 output 指向外置盘 T-093，第一场在 mounted_external_output_required 处退出、未启动窗格。**实际通过的七场由执行主控直接调用原 run_restart.py**，只把 output 改到 T-096，以 t093-r18b-* 为标签；其余 mode、panes、fault、check-close／empty、版本 2.1.302、等待 600 秒及逐屏批准沿原合同。现在脚本仅修正该路径；[旧脚本红态](t096-wrapper-red-19.json)／[修正绿态](t096-wrapper-green-19.json) 用系统 Bash 的给定 Git／mount／exec 核对七种完整 argv，没有再启动真实 runner。不能把主控的直接运行写成修正后脚本的原生运行。

[t096-business-recheck-19-06.json](t096-business-recheck-19-06.json) 是 worker 独立于原 runner 的只读事实重算，不是第三轮独立审查：读取每场 run.json、保存的原生 argv／processInfo／恢复事件／窗口 JSON／task，以及停止归档的最终布局。所有历史记录与 worker attempt 比较均成立；model_turns=fake_posts=0、cleanup_complete=true。原件清单为 [t096-readonly-inputs-19.json](t096-readonly-inputs-19.json)，14 份 T-096 原件保持只读和未跟踪，不纳入本 worker 的路径外提交。

| 原生场次 | 逐场业务观察 | 结果 |
| --- | --- | --- |
| tracer | ideation 同 session、完整事件／内核 argv、规范前台身份与历史 nonce；历史 launch 不变；显式关闭持久化 | PASS（15 项原记录检查） |
| three | 两主控独立恢复；worker 未恢复、无成功事件、receiver 未重启，attempt 不变 | PASS（26 项） |
| no-argv | restore_argv_missing；未恢复／只读、无成功事件 | PASS（9 项） |
| version | restore_version_mismatch；未恢复／只读、无成功事件 | PASS（9 项） |
| no-session | restore_session_missing；未恢复／只读、无成功事件 | PASS（9 项） |
| isolation | ideation 缺 argv 拒绝；executor 继续完整恢复；worker 与 attempt 不变 | PASS（20 项） |
| empty-reopen | 两主控恢复后显式关闭全部；saved=true、panes／keys=[]，无重新授权／task 改动；最终归档开窗集为空 | PASS（31 项） |

同一事实核对还拒绝七个仅改内存观察的反例：缩短内核 argv、改 attempt、改故障码、删历史 nonce、空窗增加 key、空窗后改 task、归档出现额外 open 事件；原件从未改写。它们验证事实核对器，不声称重跑了故障或修改了产品。

为核对最终布局，仅复制已停止的合成 fixture 的 DB＋WAL 到一次性私有目录，在副本以 mode=rw、PRAGMA query_only=ON 查询窗格开关事件，显式关闭后整目录删除；不打开原件作 SQLite 写入、不 checkpoint 原件、不读 auth 表。[SQLite 文档](https://www.sqlite.org/wal.html#the_wal_file) 说明 WAL 属于持久状态。自建探针发现本机 immutable 读法看不到仅在 WAL 的事务（readonly-WAL-probe-19），临时副本读法通过（readonly-WAL-clone-probe-19）；native -02／-03 和 -04 的工具取样／读取错误均保留说明，不能算原生回归失败。最终 -06 七场全部通过，源文件尺寸／mtime 保持不变；这是读取方法修正，未放宽业务断言。

本轮补跑的局部回归：T-091 IPC 19／版本 8、T-078 runtime 11／relay 22、observer 11／alias 2 均 PASS。它们使用给定进程／PTY／Electron 边界；实际 C 单层 profile 中的 libproc 正例来自 r18 完整链，真实原生多窗格／恢复来自上述七场，不能把局部测试扩大成所有 T-078 原生材料已回放。

以下请求 18 及更早段落保留为各阶段的历史记录；其中“待运行／当前／最新”均只属于当时版本。
最新交接为 [请求 18](REVIEW-REQUEST-T093-18.md)。主控 #126 回传 7bba61000 的生产 443 profile compile PASS，primary／green 在 U bind 阶段以 errno 13 失败；主控确认本机 IPNExtension/Tailscale 已占用 *:443。旧失败摘要 [os-r17-failure-summary-18.json](os-r17-failure-summary-18.json) 保留，不把 errno 13 自身外推为占用的独立证明；worker 没有查询或操作该服务。
当前生产入口仍明确固定 443；无模型链默认 18443，可显式配置，生产和测试均调用同一 prepare／policies，只有 port 参数不同。preflight／结束事实报告实际端口；OS 仍不按主机限制，主机锁定仍由应用完成，无 fallback。U 的关闭收据移入 finally，绑定失败也提供零／部分监听关闭数，主错误不被关闭错误覆盖。C 仍须核对完整收据及 ESRCH，V 仍拒绝端口不符／未关闭／错误拥有者。局部红绿与反例见请求 18；当前候选的新 OS 链和原生七场尚未运行，整票 INCOMPLETE。
限定独立审查 [PORT-STARTUP-REVIEW-18.md](PORT-STARTUP-REVIEW-18.md) 对 e5b8329e4 报 INCOMPLETE，L0/L1 局部 PASS、无 finding。新端口 39524／新 nonce 验证生产入口固定 443、同函数仅换端口、Bash 参数、U 零／部分监听及关闭错误、C 严格收据与 ESRCH、应用层主机锁；硬写 443、跳过 close、EPERM 当退出、删主机检查均被独立业务断言拒绝。最终归档仅加报告／摘要和清单，运行源码／测试／脚本未变；OS／完整链／native7／真实 V 入口未运行，不上调整票状态。
不修改 ticket 验收框，不把 Git 提交当作 Gate submit 或 integration 收据。

最新交接为 [第二轮独立审查请求 15](REVIEW-REQUEST-T093-15.md)。主控 #117 已回传 chain-08 counts／V 单场 PASS；它与 chain-07 的其余五场、rehearsal-04 的预期结果均符合要求，但分别绑定下文列出的两个候选，不存在新候选六场统一重跑的记录。T-096 跨票恢复检查仍未完成。以下各“当前／最新”文字均保留为其对应阶段的历史记录。

最新交接改为 [修订候选请求 16](REVIEW-REQUEST-T093-16.md)：第二轮审查报告 independent-review-02.md 保持原文；主控 #121/#122 修订 F 为 OS 仅限 TCP 443、应用层锁主机，**OS 层不再按主机限制**。main 已合入，恢复运行时身份及新网络逻辑的局部检查通过；新 OS 与 T-096 原生七场仍 INCOMPLETE，旧链路 PASS 不替本候选背书。
此前组合阻塞为 **NO_GO**：普通 daemon 直接恢复正常登录记录时未保证原 R/F/D/C 权限上下文，给定边界已复现，见 ISSUE-NORMAL-LOGIN-RESTORE-16.md。
一次针对性独立复核 [NETWORK-RESTORE-REVIEW-02.md](NETWORK-RESTORE-REVIEW-02.md) 已关闭 8771ba58d 的 Bash 脚本问题，但以全新 SQLite／native session 独立确认同一正常登录恢复 P1，结论 FAIL。缺 session 的对照仍会先执行版本命令，因此不能靠清理通常成功来保证安全。该历史检查只使用给定 subprocess／PTY 边界，没有运行真实 CLI／OS，也没有声称观察到实际越权写入。67ffe60ad 只归档报告和状态。

主控 #125 的范围裁定现已落实：正常登录主控记录不在 recover 续接，先返回 `normal_login_restore_requires_protected_start`，状态“未恢复”，提示“请经正常登录入口重新启动”。这是一项已知限制；恢复完整 R/F/D/C 生命周期须另票。假 API 与合法旧记录继续按 T-096 恢复，原历史记录不变。[NORMAL-RESTORE-17.md](NORMAL-RESTORE-17.md) 对应 8771ba58d 的独立探针红态、同探针绿态、实际恢复合同和删拒绝检查变异。正常登录版本／PTY 均为 0，假 API 正例恢复；T-091 IPC 19 项与 T-096 daemon 7 场局部回归通过。当前并非整票 PASS；请求 16 已更新为新输出名和最终冻结 SHA 变量，供主控在沙箱外执行。
限定独立审查 [NORMAL-RESTORE-REVIEW-17.md](NORMAL-RESTORE-REVIEW-17.md) 对 91cd22d52 的 #125 局部合同给出 PASS，新 SQLite／nonce 输入验证零正常登录边界、明确未恢复／重启提示、历史与 attempt 不变、假 API／legacy 正例及原身份拒绝；同一信号拒绝 8771ba58d。最终归档提交只加入报告／摘要和文本状态，不改变产品或测试；新 OS／原生七场仍 INCOMPLETE。

更新：独立审查 01 对第一次冻结候选 1d4c58b4a 给出 **NO_GO（验收文件缺口）**，报告原文保留。
下文首次交付的 PASS 均是当时运行证据，不提升为新候选的独立审查通过。当前仅修正验收输入与审查驱动的失败保存，产品源码未改；新外部复验与新独立审查仍待完成，见末节。

最新状态（主控 #79）：用户裁定 A 改了 HOME 条件。清单差异已不作通过条件，但所有父／辅助进程的 OS 禁写尚未完成，父子 profile 兼容性必须先实测。当前仍 INCOMPLETE；当前工作快照不是 A 已落地的验收候选，最新入口为 REVIEW-REQUEST-T093-03.md。下面的旧版本状态与“产品未改”说明仅对应各自历史阶段。

再更新（主控 #82）：父进程拒写成立，嵌套 C 已以 exit 71 实测失败。当前改为单层重设计，转发层的上游网络权限边界待明确授权，整票 INCOMPLETE。最新请求为 REVIEW-REQUEST-T093-04.md；不再重复嵌套探针。

当前状态（主控 #83）：F 网络边界已明确，授权阻点已解决。新增平级 profile 边界探针，等待主控在沙箱外实测新组合；产品隔离／转发生命周期尚未改造，整票 INCOMPLETE。最新入口为 REVIEW-REQUEST-T093-05.md，精确命令脚本为 PROBE-PARALLEL-01.sh。初次探针只读审查指出两处 P1，原文保留，已通过权限码数据反例和跨 exec 计时／删计时变异修正。另有上游 URL 配置解析的单行产品修正，纯解析红绿见 upstream-config-red-01.json／upstream-config-green-01.json。本轮未执行新 OS 沙箱探针、读 auth、查询 Security 服务、启动供应商 CLI 或模型。

最新状态（主控 #84）：[parallel-profile-01.json](parallel-profile-01.json) 中各 OS 边界均成立，只有 U 后清单收尾失败，原件仍为 INCOMPLETE。现已去掉该 Node→Python 回 exec，在同一 Python 进程采后清单后再确认关闭；旧 profile() 规则未改。产品已接入独立 R 准备、F 转发、D 清单／清理与单层 C；完整新链和五项变异待沙箱外运行，整票仍 INCOMPLETE。当前交接为 REVIEW-REQUEST-T093-06.md／EVIDENCE-RECHECK-03.sh。以上“尚未改造”文字属于此前快照。

## 变更与版本

起点 main 为 61786370428c3ec5f894ea60acccf2695d54c2dc。
正常登录仍经过 controller_start、既有 UserPromptSubmit／PermissionRequest／Stop 及同一转交路径。
新增隔离 HOME 的 auth-only 副本、固定版本与生成状态、本地先记后转的转发器、只读事实命令。
转发记录不保存认证头或正文；终端公开字节对凭据变体脱敏，OSC/DCS 负载不公开。
未修改 acceptance、gates、地图或全局配置。

| 版本 | 本轮证据边界 |
| --- | --- |
| 2b6af7ff4260a6a6cc09f63285b75ec8b1b80bbf | probe-10 代码；主控 #72 回传 PASS，供应商 CLI 2.1.302 只连本地假服务 |
| ff625c3718696cf31a7e9fd0d68e84bd2b0442b7 | 首个产品候选，独立工具审查 FAIL：OSC/DCS 负载可泄漏凭据，保留失败结论 |
| fbc84483ed1efd14783131e2fc2a8e55eb5c3774 | 修复控制负载泄漏及夹具多行 paste；新测试拒绝旧候选 |
| 3b2172beba0427fb6eba69024536e0a7812bf7cf | product-chain-03 沙箱外 PASS，完整 daemon/PTY/hook/Stop 和实际 HOME 清单 |

3b2172beb 之后产品源码及全链脚本、C/Python 假 CLI 未改变；只补转发测试的可选原件导出、证据和交付文档。
最终审查对象为包含本结果与审查请求的冻结提交，完整 SHA 由 `T-093 FROZEN <sha>` 交接；差异核对见 freeze-checks-01.json。

## Acceptance 对应证据

| 条件 | 证据与观察 | 状态与边界 |
| --- | --- | --- |
| 红态：main 无正常登录入口，旧入口拒绝非假 API | [profile-red-01.json](profile-red-01.json)：source_equals_main=true；正常登录认证／sandbox／版本合同三项失败，HTTPS 真实地址被旧假 API 入口拒绝；同一构造合同 [profile-green-01.json](profile-green-01.json) 4 项通过 | PASS（有效合同红态）；原红态摘要 INCOMPLETE 和 rc 1 保留，不改写成绿态 |
| 绿态：假上游走完整链、原件对账、隔离根删除、真实 HOME 无差异 | [product-chain-03.json](product-chain-03.json)：controller_start、真实 PTY、实际进程身份、原生 hook／inbox／Stop，唯一哨兵转交一次，反馈完成；received=forwarded=ledger_requests=model_requests=独立上游=2，outcomes=2；隔离根及夹具删除；[实际 HOME 摘要](product-chain-03.host-home.json) 5554→5554，差异 0 | PASS，主控 #73 沙箱外 rc 0。daemon 用合成源 HOME，另核对主控实际 HOME；未启动供应商 CLI，真实模型／真实上游 0 |
| 反例：启动参数混入真实 HOME 路径被标出 | [forwarder-green-03.json](forwarder-green-03.json) 的 counterexamples.home_references：指定 HOME 前缀插入 argv，报告 launch.argv[1]、1 次；禁用引用检查的变异被拒 | PASS，合成路径反例；不把路径引用等同实际读写 |
| 反例：凭据进入证据被扫描命中 | 同报告的 credential_injections：原值／JSON／URL／base64 去重后的各变体均命中（本次 3 个唯一变体，各 1）；临时泄漏文件随后删除；保留证据 4 文件扫描命中 0 | PASS，只用随机合成值；未把反例凭据原值留进证据 |
| 反例：漏记一条被对账抓住 | product-chain-03 真实转发日志删序号 2 后对账失败；另有可复数的 [missing-row 原件](forwarder-original-01/missing-row/requests.jsonl) 与 [事实命令读回](forwarder-recount-01.json)：入口及独立上游 2，原件请求 1，counts_match=false | PASS；模拟丢记录，保留原始完整版本及损坏副本，不覆盖真实通过记录 |
| 凭据不进证据或 Git | product-chain-03 结束时扫描 state 的 10 个文件，命中 0；probe-10 真实凭据只在内存／隔离根，扫描 0、隔离根已删除；新保留转发原件扫描 0，当前 Git index 对本次合成值／变体扫描 0；新增路径无 auth 副本，只有脚本与小型文本证据 | PASS（所列来源与扫描范围）；没有重读真实 auth 做全 Git 历史扫描，不将合成值检查冒称真实凭据全历史检查 |
| 地图 0 problems | freeze-checks-01.json 保存最终 status 输出；未修改地图 | PASS，0 problems、0 stale living docs |

product-chain-03 在运行时读原始 requests.jsonl 并经事实命令重数；该临时夹具已整体删除，因此其原件没有保留。
为便于独立复数，另运行同一生产转发器，保存 [forwarder-original-01/requests.jsonl](forwarder-original-01/requests.jsonl)：两条请求、两条结果，400 后 200，两个独立上游收据，原值／认证头／正文均不入记录。
它是**另一轮转发测试**，不是 product-chain-03 的原件；[forwarder-recount-01.json](forwarder-recount-01.json) 用同一个只读事实入口分别重数完整与漏记副本。
这些四个小文件由事实命令作为输入读取，按 T-088 留仓库；没有将 sqlite、二进制或整套夹具入库。

## probe-10 三条必须保留的边界

1. 供应商 CLI 的通过依赖隔离配置中新建的 `hasCompletedOnboarding` 和唯一当前 cwd 的项目信任状态。这两个是 **2.1.302 内部状态**；正式模式固定该版本，升级须重新核对，不能静默复用。没有从真实 .claude.json 复制状态，也没有自动业务按键。
2. onboarding 预检会直连 `api.anthropic.com/api/hello` 与 `platform.claude.com/v1/oauth/hello`，两个 hello 候选不经过 BASE_URL。正式模式必须准备完成状态，CLI／子进程只允许本地转发端口与精确 daemon Unix socket；官方地址直连被阻断。事实报告单列可见预检迹象；`preflight_observed=false` 仅表示没识别到相应终端输出，不能证明零网络尝试，不能把转发计数外推为全部网络尝试。正例预检字符串与隐藏预检的变异均有检查。
3. probe-10 收到 **2 个** POST /v1/messages（10594／10574 字节），都携带复制的 bearer、假上游都回 400。按主控结论，说明 400 后发生重试；每次 HTTP 接收独立计数，失败与重试都不能合并。转发器自己不重试、不跟随重定向。

以上来源为主控 #72 与 [probe-10.json](probe-10.json)，真实上游 0，凭据扫描 0，实际 HOME 5554→5554、无差异，隔离根删除。
产品全链使用编译的确定性假 CLI，不能取代供应商登录／路由事实；probe-10 也不能替代本次产品 hook／Stop 的实跑。

## 检查、失败保留与复现

- [counterfactuals-04.json](counterfactuals-04.json)：未改对照及 7 种错误候选均按预期区分，含修复前 OSC/DCS 泄漏候选。
- [private-files-green-01.json](private-files-green-01.json)：合成文件 5 项，auth-only、metadata、符号链接与过期凭据。
- [paste-fixture-01.json](paste-fixture-01.json)：实际 C 夹具修复前把多行 paste 拆成两次，修复后一次完整提交。
- [fixture-version-regression-01.json](fixture-version-regression-01.json)：既有版本核对 8 项通过，原缺陷与删除核对的变异均被拒。
- [PRODUCT-REVIEW-01.md](PRODUCT-REVIEW-01.md) 保留旧候选 FAIL；控制负载修复的新反例通过，不补称旧审查通过。首次 counterfactuals-01 的测试解析问题及先前探针失败保留，不覆盖。

只读重数（可在当前沙箱运行，不读 auth、不启动 CLI）：

```sh
node workbench/src/claudeLoginCheck.ts evidence/2026-10-16-batch16/T-093/forwarder-original-01
node workbench/src/claudeLoginCheck.ts evidence/2026-10-16-batch16/T-093/forwarder-original-01/missing-row
```

复现局部检查须选全新输出与原件目录：

```sh
node workbench/tests/test_t093_forwarder.ts /private/tmp/新的摘要.json /private/tmp/新的原件目录
python3 workbench/tests/test_t093_counterfactuals.py /private/tmp/新的反事实.json
```

第一次冻结前，完整链已由主控 #73 执行，rc 0；当时没有新增必须在沙箱外运行的检查。本次审查修正后的外部复验另见末节。
若独立 reviewer 需要复验，必须由主控另选新输出，后台服务脱离调用者进程组：

```sh
python3 workbench/tests/run_t093_login_chain.py --output evidence/2026-10-16-batch16/T-093/product-chain-04.json
```

真实 HOME 清单范围是 .claude、.claude.json、.claude.json.backup、Library/Keychains；只读元数据，不比较 atime，不读正文、不跟随链接、不用校验值，其余 HOME 路径显式排除。
其他会话可能并发写入，所有差异都报告、不推断因果、不自动忽略；本次完整链实际差异为 0。
事实命令只报告事实，不批准或拒绝模型回合；凭据扫描保留结束时的范围和时间，不冒称新扫描。
本票没有运行真实模型回合，合入后仍等用户另说开工；没有可靠性、吞吐或成本收益主张。

冻结后由执行主控安排新的只读 reviewer 与唯一门禁；本结果不代替最终审查、submit 或 integration。

## 独立审查 01 后的验收修正

主控 #77 转交 [independent-review-01.md](independent-review-01.md)，要求修正两处验收证据。该报告未改字，旧 NO_GO 原样保留；没有据此声称产品行为存在缺陷。
代码／驱动修正候选为 c34d71a975b59a0db8c1e97bb40c0f7a94e629d1；相对第一次冻结，workbench/src、完整链脚本及假 CLI 都没有变化。

| 问题 | 红态与修正 | 当前证据和边界 |
| --- | --- | --- |
| 生产凭据变体列表为空后，候选检查跳过全部注入，仅由清理 ENOENT 退出 | [counterfactuals-05-red.json](counterfactuals-05-red.json) 复现：expected_business_assertion 未观察到、fixture_missing_error=true。现在输入由测试自己的原值、JSON、URL、base64、无填充 base64、base64url 构造；检查列表非空、文件确实创建且内容吻合、正命中及每项均执行；公开字节的禁止值也来自测试输入，不用被测枚举器／扫描器作答案 | [forwarder-green-04.json](forwarder-green-04.json) 对照通过；[counterfactuals-07.json](counterfactuals-07.json) 12 项通过。清空生产枚举器命中 `credential injection must be detected`；空场景、跳过循环、取消写入分别命中非空／执行／文件存在的指定 AssertionError，均无 ENOENT |
| 首条请求不记账的原始失败被审查驱动清理断言盖住 | 原审查外置 omit-first-request.stderr 只留下 `private HOME cleanup must finish`，没有结果 JSON；原业务断言保持 INCOMPLETE。新建 EVIDENCE-RECHECK-02.sh，旧审查脚本 01／02 不动。生成驱动保留首个 failure；清理等待明确不观察已记录的 boundaryFailure；清理异常独立写 cleanup_failures，移除清理断言覆盖主失败的路径 | [evidence-recheck-local-02.json](evidence-recheck-local-02.json)：实际生成驱动在 setup 前强制业务与清理双失败，旧式未捕获清理异常会遮盖主失败并被拒；修正版同时保留 primary_business_probe 与 secondary_cleanup_probe。此为 L1 驱动回归，未启动 PTY/auth/ps；真实首条漏记的完整链尚未复跑，INCOMPLETE |

本轮没有修改 reviewer 的 independent-review-01.md 或 REVIEW-OUTSIDE-01／02.sh。新脚本由 worker 派生，修正不代替新的独立审查。
新的反事实还要求具体业务断言，不再仅因存在 AssertionError 或退出非零就记作“清空变体”已被拒绝。首次红态和旧摘要都保留。

已完成的本地命令（输出路径均为首次创建）：

```sh
node workbench/tests/test_t093_forwarder.ts evidence/2026-10-16-batch16/T-093/forwarder-green-04.json
python3 workbench/tests/test_t093_counterfactuals.py evidence/2026-10-16-batch16/T-093/counterfactuals-07.json
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-02.sh /Users/luckye/Documents/Code/a2a-wt-t093 c34d71a975b59a0db8c1e97bb40c0f7a94e629d1 --check-only
```

--check-only 的两个失败优先级进程、三种生成代码语法检查均通过；它不运行真实 PTY、auth helper、ps 或模型，不冒称外部完整链证据。
完整沙箱外命令由主控对**新冻结提交**执行；第二个参数换成最后交接的完整 SHA，省略 --check-only：

```sh
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-02.sh /Users/luckye/Documents/Code/a2a-wt-t093 FULL_FROZEN_SHA
```

脚本自动创建新的 /private/tmp/t093-evidence-02-* 输出，核对 HEAD 与给定 SHA，一次性导出该版本 workbench，不改仓库或全局配置；后台进程脱离调用者进程组。
它先验证失败优先级，再跑未改对照、独立反例对照，最后跑首条漏记、HOME 漏报、空凭据枚举器、计数恒一致四种生产单处变异；空枚举器另跑候选自己的完成检查。
读取 SUMMARY.json 时，首条漏记必须以 independent_upstream_assertion 为主失败；cleanup_failures 与外层 cleanup.json 分开检查。不得用 ENOENT、超时或另一清理错误替代业务拒绝。
真实 HOME 仍只比较四个既定范围的元数据，所有差异保留；凭据只用合成输入，隔离根和夹具按本轮登记收尾，真实 CLI／真实 auth／真实上游／真实模型均为 0。
尚未执行这条完整命令；当前整票 INCOMPLETE，等待该复验结果和新冻结候选的独立审查。新的审查入口见 REVIEW-REQUEST-T093-02.md。

## 用户裁定 A 后：清单仅报告、父层保护事实待定

来源是用户主控 #79、main c06a73179 的 T-093“裁定”节及 20261018T004018Z-ideation-answer-001：验收改为 OS 强制禁写真实 HOME 加一个拒写反例；清单差异照实报告，不作通过条件。worker 不改受限的项目地图或旧审查原文。

已完成的确定部分：生产 facts 的 inventory 标注 pass_condition=false 与裁定来源；完整链检查继续要求差异数据存在，但不要求空列表；外层返回码保留 child 结果，有差异不再改为失败，child 失败也不放行。复验摘要仍保存原始 home_unchanged 信息，但不以它决定结果。扫描、计数、preflight、清理和身份等其他断言没有放宽。

[inventory-policy-red-01.json](inventory-policy-red-01.json) 在旧逻辑上复现“child=0、有差异仍退出 2”；[inventory-policy-green-01.json](inventory-policy-green-01.json) 的四组 child 成功／失败和有／无差异组合均符合新裁定，前后差异元数据完整保留，旧零差异门槛被拒。边界是 L1 分类，元数据和 child 结果由测试提供，不是 OS 拒写证据。

尚未完成的是所有应用进程的 OS guard。逐进程现状与目标 profile、实际 HOME 与合成认证源 HOME 的区别、输出／FD 边界，以及决定性 SDK 兼容性未知均列在 [HOME-GUARD-A-PLAN.md](HOME-GUARD-A-PLAN.md)。当前不能把只限制 CLI 的旧 C profile 说成父进程和全部 helper 已被保护。

先由主控在沙箱外运行小探针（不要覆盖已存在输出）：

```sh
python3 -I -S -B workbench/tests/probe_t093_parent_sandbox.py --output /private/tmp/t093-parent-profile-01.json --source-revision FULL_FROZEN_SHA
```

它在任何应用工作前同 PID exec H，所有实际 helper 继承 H，记录真实 HOME 唯一新文件拒写及文件未出现，并验证更严格子 profile 在 H 后代中是否真能生效。
删规则变异只在合成 HOME 中做，实际 HOME 规则保留；要求真实独占创建、立即删除及指定业务断言失败，创建／删除记录入证据。这个选择避免主动移除真实 HOME 的保护；它不证明实际 HOME 去掉规则后会写入成功。
清单 helper 也在 H 中，仅记录四范围元数据差异，差异不决定通过；采集失败仍保持 INCOMPLETE。

本地 [parent-probe-safety-02.json](parent-probe-safety-02.json) 仅证明合成文件的独占创建／删除、既有文件保护和未禁写情况下的业务拒绝，实际 HOME 尝试 0，OS profile 执行 0。探针语法已检查，未在 worker 沙箱里运行实际沙箱／ps／CLI，也未读 auth、请求升级或跑模型。

若 sandbox-exec 不能在已有 H 的子进程里施加现有 C/R，必须保持 INCOMPLETE 回主控处理，不能移除 CLI 的网络或 Security 限制来冒充成功。
因此之前 EVIDENCE-RECHECK-02 的完整模式现在直接停止，防止无父层保护时对 A 给出 PASS；旧审查 01／02 脚本和全部旧报告保持原文。新小探针的输出回来后，才能完成全进程保护实现和真实链复验。

## 单层重设计：父层拒写已成立，转发权限待裁定

主控 #82 回传 probe rc 2／INCOMPLETE；原件 [parent-profile-01.json](parent-profile-01.json) 已读回留存。
父 PID 60365 在 H 下独占创建真实 HOME 新文件被 errno 1 拒绝，created=false、absent_after=true；两个 inventory helper 继承 H。
子进程 60700 请求第二层 C 失败，exit 71、Operation not permitted、无实际 child 结果；C 不可列为已生效。清单 5555→5555、无差异、pass_condition=false；临时根删除、清理无错误，auth／CLI／模型／网络均 0。

用户已授权凭据复制单独移到业务 profile 之前／之外，且只精确读一次。后续设计不使用嵌套 profile，也不在 C 内重读原始凭据。
但若包括转发器的所有进程都共用一个只允许本地端口 P 的 profile，现有 http/https.request 无法连接真实上游，另端口 U 的假上游也被禁止。
把 F 移为独立受保护树并给予上游网络，是新的额外边界；不能从凭据准备例外自动推导其授权。

[SINGLE-PROFILE-DESIGN-01.md](SINGLE-PROFILE-DESIGN-01.md) 列明最小建议：R 精确凭据准备，C 单层业务树，另一个平级 F 负责先记后转／上游网络；所有阶段仍禁写 HOME，F/C 禁 Security，CLI 不增加直连上游能力。
本设计尚待明确批准，产品未按它修改；[请求 04](REVIEW-REQUEST-T093-04.md) 将该决定交主控／构思主控。
本轮没有新的必须沙箱外运行的命令，不以进一步 probe 代替权限裁定；原审查报告不改。

## 产品平级 profile 候选 06：实现完成，外验待运行

主控 #84 的旧外验确认：C/F/U/S/M/CLI 子进程禁写真实 HOME、F 越界出站／监听被拒、C 直连假上游被拒、F/U fork 与 Security 被拒、本地配置正例及合成删规则变异均成立。U_closed 已保存，但后清单未得，因此保留原 rc 2、primary_failure=null 及两项 cleanup_failures；不提升为 PASS。主控事后 ps 无残留的转述与 JSON 的观察范围分开。

U 现在用同一个 Python 进程完成前清单、假服务与后清单，后清单成功后才确认 closed；没有改变旧探针 profile() 的 AST。局部测试先重建提前确认的变异，再证明 U_closed_must_include_post_inventory 能拒绝它。JSON ready/closed/stop 在内容完整后原子发布。

产品入口 claudeLoginSession.py 在链外精确读一次原始 auth，只复制 OAuth，生成唯一隔离 HOME 与最小版本绑定状态；启动平级 F/D 后同 PID exec C 中的原 daemon。C 及 hook/Stop 的控制路径保持原样；版本、status、PTY、事实子进程均继承 C。F 的唯一地址／端口由 URL＋显式固定 IPv4 配置，禁 DNS／fallback／其他出站／Security／fork；D 无网络／Security／fork，只收四范围目录/stat，原始清单留在私有根。HOME 禁写覆盖整个 OS 账号 HOME，不用 HOME 环境变量替代，也没有 repo/state/roles 的 HOME 写入例外。

并发 start 的准备会话采用一次性独占消费，落后者不能取得或清理胜者资源。D 区分正常结束、主动取消和根进程失联，对本次登记的 PID/组核对后清理，未确认就保留 INCOMPLETE。C 管理 tmp 与 CLI 私有根分开，结束后的事实命令不应重建已删除的隔离根。当前事实 schema 为 2，原件位置是 forwarder/journal/requests.jsonl。

凭据元数据字段的额外缺口有独立局部红绿：journal-red-01.json 中方法／数值暴露 2 个合成值，journal-green-01.json 为 0 且 JSON 可解析。修正在 F 的写盘边界，不落认证头或请求体。该检查没有监听或请求上游。

局部通过证据：cleanup-local-05.json（U 关闭、提前确认变异、一次合成读取、路径边界、D 正常／取消清理及身份丢失时不发信号；D 的信号为模拟）、once-local-03.json（并发只消费一次、不清理胜者）、facts-local-03.json（四种清单差异／漏记组合不自动授予模型许可）、launch-local-05.json（原 hook/Stop 与单层启动构造）、url-local-03.json（配置解析）、private-files-local-02.json（OAuth 范围／链接／有效期）、oracles-local-02.json（Mach 明确拒绝及跨 exec 截止）。这些不替代新产品 OS 绿态。

最终局部快照补为 cleanup-local-07.json、once-local-05.json、facts-local-05.json、private-files-local-03.json：原始 auth 前的短 D 基线、一次性消费与输入前事实均已接入；新增显式 --preflight 事实模式。局部测试模拟基线子进程／服务计数，未执行新的 OS profile。实际全链必须由主控复验；不据此升级状态。

inventory-race-red-01／green-01 另复现并修正目录在 stat 后、枚举前消失的收尾风险；明确记录 missing／vanished_before_enumeration，保留已见元数据。PermissionError 仍传播，未放宽观测失败。它不证明原 U 一定是这个原因。

完整外验脚本已经准备，命令及逐进程 profile 表在 REVIEW-REQUEST-T093-06.md。绿态使用随机 prompt／inbox 哨兵、真实 PTY/daemon/native hook/Stop、编译假 CLI、独立受保护假上游。逐条对账 F 原件与独立 U 收据；覆盖原三个反例、八个真实 HOME 拒写路径、合成缺失规则的实际创建／立即删除、F 越界连接及 C 绕过 F。五项变异分别破坏路径报告、扫描、计数、首条记账与注入列表，要求各自业务断言失败；清理另列。所有反例只用本地假上游。

probe-10 三条边界仍保留：两个内部状态只对 2.1.302 有事实支持，换版本须重核；onboarding 的两个 hello 直连官方域名，不经过 BASE_URL，必须避免触发并报告终端／私有 debug 的可见信号；400 后的每次重试都算新请求。沉默的被拒网络尝试未测量，不能用转发原件冒称全网络审计。

本候选没有运行真实供应商 CLI、读取真实登录、连接真实接口或产生模型回合。完整新产品 OS 运行、真实域名 DNS/TLS 和独立验收均未取得；不使用旧 PASS、局部模拟或进程标签冒称这些结论。全部原审查与失败保持原文，Git／提交仅冻结候选，不代替受管交付门禁。

## 候选 06 的独立复核与修正

冻结 1e556ce716220b6c1ff3200a0a5407166d8938c6 的新只读复核返回 FAIL，原文保存在
[PRODUCT-PARALLEL-REVIEW-01.md](PRODUCT-PARALLEL-REVIEW-01.md)，没有改写旧审查报告。
复核发现两个可达问题：正式普通 Python 命令可能在挂 profile 前写真实 HOME 的字节码缓存；
D 的意外失败路径只发 TERM，没有确认 C 组退出就可能删除私有根、给出成功清理收据。

入口现在先禁止字节码写入，正式命令统一使用并核对 `-I -S -B`。不支持普通 Python 启动；
解释器的 site／环境启动早于脚本检查，不能把脚本检查当作任意解释器启动的 OS 防护。
D 在意外失败时将 C 根组加入现有的身份核对、KILL、退出确认；明确取消仍保留负责报告的 C 进程。
若 C 组退出未确认，保留原始 PermissionError、单列清理错误并保留私有根，不写成功删除收据。
没有扩大 profile 权限或真实 HOME 写入例外。

同一 [test_t093_review_regressions.py](../../../workbench/tests/test_t093_review_regressions.py)
在旧冻结源码上得到四项预定业务失败，在修正源码上通过：冷缓存禁止写入、缺失启动标志拒绝、
C 忽略 TERM 时仍确认退出、C 仍存活时拒绝成功清理。对照为 review-regressions-red-02.json 与
review-regressions-green-03.json；整个检查缓存写入被拦截、进程信号被模拟，没有真实 auth、网络或 OS profile。
旧源码从 Git 原文读入 /private/tmp，不回退或修改工作树。复现命令：

```sh
python3 -I -S -B workbench/tests/test_t093_review_regressions.py /private/tmp/t093-review-regressions-new.json
```

review-regressions-green-01／02 保留为失败诊断：最初测试在关闭字节码标志后才读取测试源码，
把测试自身加载 _bootlocale 的缓存尝试也纳入了被测入口。最终测试在拦截前准备代码对象，再运行入口；
red-02 用同一最终测试重新拒绝旧实现，未靠删除失败或仅绿态掩盖该问题。debug-01 也原样保留。

相关局部复验 cleanup-local-08、once-local-06、facts-local-06、private-files-local-04、launch-local-07 均通过。
这些仅证明局部逻辑；本候选完整 OS 绿态、五项变异和修正后的 U 收尾仍未在沙箱外执行。
外验命令、每个进程的 profile 及预期业务失败见 REVIEW-REQUEST-T093-06.md；当前整票仍为 INCOMPLETE。

最终局部汇总为 freeze-checks-10.json：43 个脚本／源码语法检查、UTF-8、diff、修改范围和旧 profile AST 核对通过，地图 0 problems／0 stale。
freeze-checks-09.json 保留文档范围检查的错误基线诊断；10 改用上次冻结版本比较，本次没有改动 README 正常登录节以外的内容。

## 主控 #92：原探针通过、产品 Node 路径红态

[parallel-profile-02.json](parallel-profile-02.json) 是候选 47286b7bda7d6497a1c62a067308b18ea3fc1f7a 的外部 PASS：
U 同进程收后清单及关闭已确认，cleanup_failures=[]，collection_complete=true，临时根已删除。
这份原件与旧失败 parallel-profile-01.json 同时保留，不覆盖或把旧失败改称通过。

同一候选六个产品场景均在 prepared_services 后退出 1，未生成结果 JSON。
六份日志中 Node 26.5.0 都在 realpathSync → lstat /Users/luckye 时遇到 EPERM，未进入主模块；
五项变异的预定业务断言均未到达，核对器 FileNotFoundError 也不是业务拒绝。
只读日志摘要为 product-chain-04-startup-red.json；主控事后核对无残留进程和 HOME 新文件，worker 未执行外部 ps。

本次选择用户授权的 (a)，新增 home_read_barrier：保留原 file-read* 屏障和既有源码／可执行文件内容例外，
只用 literal 给这些允许路径的祖先目录增加 file-read-metadata，含真实 HOME；不对整个 HOME 子树开放元数据。
C、F 和外部事实 V 共用，D 规则不动。HOME 的所有写入仍被禁止；网络、fork、Security 等边界均未放宽。

新反例在完整链实际 C／F 下观察 HOME／源码祖先元数据与入口 realpath 正例，同时要求源码根公开 AGENTS.md
的正文读取被拒、读取字节为 0，其祖先目录也不能枚举。只用既有公开文件，不读 auth／用户配置，不写真实 HOME。
独立结果核对器新增相同外部条件，保留原六场状态、计数、扫描、清理和身份断言。

漏检原因：本地检查没有施加 OS profile；原 PROBE-PARALLEL 的 C 和模拟 CLI 是 Python，
F 的 Node 没有产品 F 的 HOME 内容屏障，因此没有发生受限 Node 的源码祖先路径解析。
原探针 PASS 的证明范围是它实际检查的边界和收尾，不能证明产品 Node 可启动；新检查放入实际产品链。

metadata-local-red-01 用旧冻结源码命中缺少祖先元数据规则；metadata-local-green-01 的三项局部检查通过。
其中还验证记录器在合成 HOME 无屏障时会读取一个公开哨兵字节、报告读取成功，并被业务断言拒绝，未把“被拒”写死。
这些仅证明构造／记录器与外部 V 共用规则；worker 没有运行 OS profile，实际元数据放行及正文拒绝仍待外验。
局部复验 cleanup-local-09、review-regressions-green-04、once-local-07、facts-local-07 通过。

新完整命令见 REVIEW-REQUEST-T093-07.md；使用新的 chain-05 路径，先 none，成功才继续五项变异与独立核对。
整票 INCOMPLETE；没有真实供应商 CLI／真实 auth／真实上游／模型回合，没有新的独立验收通过结论。

元数据候选 0a52043f86e5384efae943cbafe859ccb535ec14 的只读审查原文为 METADATA-REVIEW-01.md：
INCOMPLETE，未发现本次边界内的新违约；纯内存对照拒绝正文可读、读取一字节却声称拒绝、ENOENT、目录可枚举和入口未解析五种坏记录。
审查不替代 OS 执行。产品源码随后未变；另补 run_t093_facts_entry.py 供主控验证实际外部 V 入口，
同 PID 准备无认证小输入后进入真正 --stage facts，不嵌套 profile、不留无保护监督进程。
该脚本只做语法检查，未在 worker 中执行；命令、预期计数与保留输入的范围已补在交接请求 07。

## 主控 #94：V 入口通过、R Git 阶段失败

候选 2d4eba04b42ae7dd83f0f190ff99a08aabb9a0b4 的外部 V 已实际通过，原件 external-facts-05.json：
rc 0、两次请求重数一致、fixture_nonce 非空。本轮产品源码未变，保留该入口事实，不提升为完整链通过。
完整 none 原件 product-chain-05-setup-red.json 仍为 INCOMPLETE；其后五场按停止条件未跑。

只读检查定位最新根 /private/tmp/t093-chain-_7290n4q，没有端口／session／audit，只到初始角色与合成认证源，
故失败范围是三个 Git 检查。创建哨兵到结果落盘为 15.236 秒，符合原来的 15 秒超时；相同全索引操作用无认证独立哨兵本地耗时 19.325 秒、正常返回 1。
setup-05-inspection.json 保留目录元数据及测量；未读取认证正文。原异常／stderr 已丢弃，不能恢复哪一条原命令确切超时，超时结论保留为有证据支持的推断。

现在只有完整索引扫描使用 90 秒、有界且只执行一次；原扫描范围、返回码要求和其他断言不变。
R 结果新增 setup_stage、原异常类型／脱敏消息／errno 或 timeout／栈位置，以及最近 Git 的原输出摘要、用时、返回码和回收状态。
诊断先脱敏再截断、写盘前再扫，保留原主失败，清理异常单列。超时持有者终止并回收本次独立 Git 组；部分 stderr 即使回收失败也保留。
R 失败删除新生成的 source-home/.claude，保留其他现场及真实的未完成状态。

setup-diagnostics-red-04 用旧驱动拒绝五项要求；setup-diagnostics-green-04 对当前驱动通过，
覆盖超时回收、90 秒单次扫描、raw／JSON／URL／base64 脱敏、主失败不被清理盖住、实际 main 到 Git 阶段的上下文。
进程及信号为模拟，不代替实际 G 和完整链复验。局部修正过程中 red-02 的回收错误覆盖问题和旧摘要均原样保留。

七个历史根仍有合成认证源，见 retained-fixtures-05.json；不原样归档凭据，选择在保留结果／清单后整根删除。
新 cleanup_t093_retained_fixture.py 只接受已知任务结构、当前 UID、确认已清理的私有 HOME 和已消失的记录 PID／组；未知或活动现场拒绝。
它不读认证正文，只删除依赖链接本身，不沿链接删除实际依赖；初版单次 X 禁 HOME 写入、网络／Security／fork，审查修正后的停机核对与当前 X 权限见下段。
retained-structure-local-01 的初版不识别变异源码副本，结果保留；02 只读识别全部七根，但进程探测为模拟，未实际删除。
retained-cleanup-local-02 的五个合成场景通过；实际清理收据仍待主控执行，不声称已删。

新沙箱外命令、七根逐项清理及 chain-06 复验见 REVIEW-REQUEST-T093-08.md。所有旧结果和审查原文不改。
地图与局部检查见新的 freeze 摘要；没有真实模型／供应商 CLI／真实认证／真实上游回合，整票 INCOMPLETE。

驱动冻结 28276275d96e97d3ac861600530831a5f2d84f91 的只读审查为 FAIL，原文 SETUP-REVIEW-01.md：
R/G 异常与脱敏反例未发现新增问题，但初始目录也可能仍由 R/G 使用，不能仅凭形态删除。
修正后清理入口只接受 retained-cleanup-scope-05.json 中本 worktree 的七根；每个根都必须取得当前 R/G 停机核对，列表缺失、不完整、匹配到进程时拒绝。
以一条 /bin/ps 子进程做已授权的只读核对，只有任务 PID／组／状态进入收据，完整参数不落盘；X 为此允许 fork，子进程继承禁 HOME 写入／网络／Security，产品 F/U/D 的 fork 禁令不动。
收据把核对范围绑定具体根与 worktree，原有已启动服务的 PID／组和 D 清理收据仍逐项要求。
cleanup-quiescence-red-01 在旧冻结源码复现活动初始根被删除；green-01 的同一断言拒绝删除，并核对合成的相对 R、G、空匹配／不完整进程列表。
retained-cleanup-local-03 继续通过五个合成清理场景；这些进程核对为模拟，当前仍没有实际删除七根或取得完整链 OS 绿态，也没有新的独立验收通过结论。

## 主控 #97：清理 PermissionError

请求 08 的七根清理实际都返回 PermissionError／INCOMPLETE，原结果缺少路径和 errno；完整链 -06 没有继续运行。
cleanup-05-inspection.json 保留七份原结果和只读元数据：495 项均无 0000、异主、flags 或特殊文件，七根 0700、UID 501 与 worker 相同，ls -ldeO 未见 ACL。
认证正文未读，保留根未改动。/bin/ps 为 root-owned 4755，/usr/bin/pgrep 为无 setuid/setgid 的 0755。
初始目录也失败，指向共同的受保护 ps 启动；原次错误位置尚未恢复，不能仅凭模式推断当作实捕异常。

默认清理观察器改为非特权 pgrep，限定当前 UID，只收 PID；不复制二进制、不 chmod，也不放宽 X 或产品 profile。
对照 Python 仅睡眠并携带 R/G 标记，不运行实际 R/G；查询须看到它，终止回收并确认组消失后再查真实 R/G。
看不到对照、非预期退出码、输出不合法或回收未确认均拒绝删除；对照 exec 前即设 20 秒硬期限。

失败会记录具体 operation／path／errno，或无文件目标时的 PID；包含可取得的 mode／uid／flags／类型。
遍历错误显式上报，rmtree 回调记录完整路径与原始 os_filename，根缺失核对的权限错误不冒称删除成功，次要错误不覆盖主错误。
新增 --inspect-only 不删除；同一 X 下会单独记录旧 ps 的执行错误，然后用新观察器核对。
只处理既有七个固定根，permission_changes=[]；无需也没有实施 chmod。

局部 cleanup-errors-red-03 在旧冻结版本上六项失败，green-03 通过六项诊断；FIFO 用合成文件验证不打开。
cleanup-observer-red-01 拒绝旧观察器，cleanup-quiescence-green-05 用模拟结果核对 R/G 正对照及失败／不可见对照拒绝；retained-cleanup-local-06 通过含只检查不删除的六个合成场景。
这些不证明新观察器在 X 下已运行。本次仍没有读取真实认证、启动供应商 CLI／真实上游／模型，也没有删除现有七根。
先执行 REVIEW-REQUEST-T093-09.md 的一根只检查命令，成功后才逐根清理、继续请求 08 的 chain-06。整票 INCOMPLETE。

清理实现冻结 d355efac68c74ca8af7fe9bd8fea5a98f1968e9c 的只读审查为 INCOMPLETE，原文 CLEANUP-OBSERVER-REVIEW-01.md：
13 个纯内存反例未发现本次范围内的已证实违约，但没有新 X／观察器／实际删除证据。
它指出原错误单元测试主要直接调用 helper；随后补 cleanup-cli-red-01／green-01，实际调用 main 和独占 JSON writer，只模拟失败操作／bootstrap。
旧实现的最终失败收据缺少 operation/path/errno，被同一业务断言拒绝；当前文件错误与观察器错误两个最终 JSON 均具备准确字段。
这仍是 L1 模拟，不能声称已复现真实受保护 exec 或实际文件权限；清理实现自审查后未变。地图与最终局部状态见 freeze-checks-16.json。

## 主控 #98／#100：先保留主失败，再交清理拥有者

**本候选 INCOMPLETE。** 主控已确认旧七根全部删除成功，inspect-only 的旧 ps 在 X 下直接捕获 PermissionError、errno 1、/bin/ps、4755；新观察器实际通过。
原件摘要与七份清理结果保存在 chain-06-cleanup-red.json。随后候选 bc87c71fc 的 none 在 prepared_services 后遭 ENOTEMPTY，未写 JSON；后五场未跑。
新根 /private/tmp/t093-chain-e189ndt0 只剩 source-home（含合成认证）。worker 仅列元数据，不读认证正文、不删除它。

根因是测试 C 保留了对合成认证源的拒读拒写，却试图删除其父根；删除异常又覆盖了已捕获的业务失败。
主控 #100 同意这条判断并要求独立清理拥有者。原业务错误已丢失，不能从收尾错误推断它是什么。
新流程先持久化原错误的类型／消息／code／errno／path／stack，后续清理错误另列；结果采用独占首次发布、拥有者核对后的原子更新和 fsync，检查点摘要另存 events。
R 的 Git 终止／生成认证目录删除之前也先保存原异常，修正同一类先清理后留证据的问题。

独立长期 D 先执行原 metadata_service，再等待 C 的清理许可；许可必须能读回同一候选／夹具的 cleanup_pending 检查点。
测试 D 只增加本次合成 source-home 的 file-write-unlink，可枚举目录，普通文件正文仍拒读；用 open 反例记录被拒及 0 字节。
C/F 与真实 HOME、网络、Security、fork 边界均不变。原始基线 helper 仍用未扩展 D，结果另列 D_baseline 的完整规则。
D 删合成源并提交带所见检查点序号的收据后退出。C 再确认 U 关闭、daemon 关闭、F/D/U/S/M/G 组与登记子进程退出，最后同步删剩余根。
无法确认写入者就不删根；ENOTEMPTY 等删除错误记录为次要清理失败，不能取代原主失败。报告 PID 最后由外部 V 确认退出。
正式产品不删除用户认证源；首轮 de956c2de 只修改测试／清理／核对与文档，产品 src 未改变。随后审查指出产品准备函数内部同样先清理后报告，修正见下段。

局部红绿为 chain-publication-red-02／green-04：同一检查在 bc87 的真实旧清理尾部命中 primary_JSON_must_exist_before_any_cleanup，当前发布器通过主失败、ENOTEMPTY、存活写入者、次要收尾错误与已有证据不覆盖五项检查。
setup-publication-red-01／green-02 对 R 命中 R_primary_JSON_must_exist_before_source_cleanup，修复后同时核对先落盘再终止 Git。
chain-cleanup-oracle-green-01 用独立给定的收据拒绝活动写入者、主失败丢失、源未删、正文可读、先删源、无历史与报告仍在运行七种反例。
cleanup-quiescence-green-07 增加 C 的活动／正对照；retained-cleanup-local-07 拒绝 source-only 多余项并验证固定结构删除。
这些均为本地合成文件与模拟进程，只证明局部逻辑，不证明 OS 权限或完整链已通过。

主控 #100 明确 Codex 会话本身是一层 sandbox，不能在其中嵌套本次 profile；此前本地可用性检查 exit 71，后续升级被拒，本轮不再尝试。
按其要求交付沙箱外 REHEARSE-CHAIN-01.sh：先让同一原 R/G/C 链在两次 hook／Stop 后主动抛 rehearsal_primary_probe，核对主失败和完整清理，再跑绿态。
两场及独立核对全部符合预期后才运行正式六场；新命令、实际进程 profile 表和停止条件见 REVIEW-REQUEST-T093-10.md。
唯一新残留用 CLEANUP-CHAIN-06.sh 清理，精确范围在 retained-cleanup-scope-06.json；不读认证正文、不 chmod，R/G/C 未停或形态不符均拒绝。
所有旧审查报告保持原文，旧 PASS 不替本候选的 OS 演练／六场复验背书。真实供应商 CLI、真实 auth、真实上游与模型本轮均未运行。

首轮冻结 de956c2de 的只读审查为 FAIL，原文 CLEANUP-PUBLICATION-REVIEW-01.md 保留不改。
它在准备函数内部复现“清理先于原异常落盘”，并证明 V 只信任退出布尔值，活动组／子进程也能通过。
产品 prepare 现要求调用方提供失败发布者，在内部清理前发布，清理异常另报，最后仍抛原异常；真实入口只保存类型／errno，主失败与清理用不可覆盖的独立 JSON，测试入口保存完整脱敏摘要。
C/F/D/G/V 的既有 OS 权限规则未变，测试 D 的合成源 unlink 例外仍按上文单列。不是对准备错误的忽略或成功降级。
V 现把组／子进程身份与原登记记录绑定，并独立用信号 0 核对每个 PID／组；只有 ESRCH 可判已退出，权限错误或仍存活都拒绝。
prepare-failure-red-03 在旧产品源码上拒绝原异常落盘顺序及覆盖；green-03 覆盖实际 prepare＋测试发布器和真实 R main 的类型收据／次要清理错误。
chain-cleanup-oracle-red-03 拒绝旧核对器，green-04 的 12 项检查包括谎报退出、身份错配及漏子进程。
两项均是无 auth／无 OS 执行的合成检查；新沙箱外演练、固定残留删除与正式六场仍待主控，整票保持 INCOMPLETE。

修正实现冻结 965560422036ae4382036a9e68758abe0fd74baf 的一次限定复核为 INCOMPLETE，原文 CLEANUP-PUBLICATION-REVIEW-02.md。
审查者独立执行 prepare 3 项与 oracle 12 项合成检查均通过，认定前两项 P1 的 L1 缺口已关闭；实际 OS 边界仍未测。
原始小报告另存 prepare-review-green-01.json、oracle-review-green-01.json。实现自该冻结后未改；后续只补文本证据。
按请求 10 先清理 e189ndt0，再做同 profile 的两场演练，通过独立核对后才做正式六场；旧候选通过不沿用。


## 主控 #103：pane_release 的 not-ok 回复被断言丢弃

**INCOMPLETE。** 候选 4533ebeb7 的固定残留清理 rc 0／PASS，e189ndt0 已删除；原件 cleanup-07.json。
同候选 primary 演练 rc 2，主失败 chain_operation_failed，失败位置为 turns 的 pane_release 布尔断言，并未到 rehearsal_primary_probe。
边界全部通过，请求 0；主失败先落盘，source HOME／隔离 HOME／夹具删除及写入者退出已确认，cleanup_failures=[]。
原结果摘要与检查点为 rehearsal-01-primary-summary.json、rehearsal-01-primary.events.jsonl。绿态、正式六场均未跑。

旧断言丢弃了 daemon.error／details，event store 又随夹具删除，不能恢复实际拒绝码。
当前 worktree 的 release 检查初始 unknown／无 active、failed，再执行 processInfo 的前台身份核对；没有 T-096 的屏幕就绪条件。
其中 /bin/ps 与之前 X 下被拒的 setuid 程序相同，是待验证嫌疑，不能写成已确认的本轮原因。
没有据此改产品、全局配置或 OS profile，也没有自动重试、放行状态或绕过身份核对。

测试调用现在把 command／实际 error／details 写入 error_summary.daemon_response，message 也保留实际返回码；pane_release 保存前后 status 和返回值。
同样处理 controller_start、pane_dispatch 与 daemon_stop 的 not-ok，清理错误仍为次要；全部内容经既有凭据脱敏与独立扫描后落盘。
daemon-rejection-red-01／green-01 对实际 release 代码块的三种合成回复复现并修复错误丢失，green 验证 details 的合成凭据被脱敏；chain-publication-green-05 的五项主失败／清理检查通过。
这些仅证明 L1 回复留证，不证明本轮真实 daemon 拒绝原因。当前只修复诊断，业务拒绝根因待下一次真实回复，不宣称整链已修好。
请求 11 给出 rehearsal-02-primary 命令；若错误仍为 pane_release_rejected，回传结构化 error／details 和前后状态，停止绿态及正式六场。

诊断实现冻结 d594057a9672e2b7441ca17c4e8632296927f1b4 的只读审查对 L1 留证范围给出 PASS，原文 DAEMON-ERROR-REVIEW-01.md。
审查者独立重跑新旧 release 代码块，并以新 nonce 拒绝码、不同状态、含合成凭据的详情核对清理前发布；原件以 daemon-rejection-review-* 和 publication-review-green-01 保存。
PASS 不覆盖真实 daemon 拒绝原因或 OS 链路。产品／权限／release 条件未改，整票 INCOMPLETE；请求 11 仍需主控先运行新的 primary。

## 主控 #105：方案 b 替换 setuid ps

**INCOMPLETE：修复已实现，OS primary 待执行。** 主控在 6f6e2820b 实际取得 pane_release_rejected，daemon.error=orchestration_failed、details=Error: spawn EPERM；before／after 无 active、queue、writing 或 draft。
旧 release 的第 688 行调用 processInfo，第 398 行唯一 spawn 是 /bin/ps -axo pid=,ppid=,pgid=,tpgid=,comm=；本机 stat 确认 04755，原始回复摘要为 rehearsal-02-primary-summary.json。
结合此前受保护 ps 的实捕拒绝，已定位该 setuid 查询启动；不再把它写成队列或屏幕问题。

选择主控准许的 b：Panes.processInfo 统一改由 /usr/bin/python3 -I -S -B processSnapshot.py 查询 macOS libproc。
helper 在原 C 中继承全部禁令，只遍历本 PTY 后代，不读参数／环境／认证、不全机枚举、不启动子进程。
SDK sys/proc_info.h 的 136 字节 ABI、关键偏移和退出标记均通过静态编译对照；函数语义核对本机 libproc.h 与 Apple 官方开源 libproc.c。
查询保留原 PID／PGID／TTY 前台组／可执行路径条件，复核出生时间／身份变化；权限拒绝／短数据／截断／坏树都拒绝，僵尸和已知退出不作活 leader。
这是多次只读内核查询，不宣称原子快照或后续存活保证；原有 hook／Stop 身份重查继续执行。
没有分离 daemon、增加 CLI 权限或 fallback；所有 OS profile、auth 复制、网络、Security、fork 与门禁源文件保持不变。

REALITY GATE: INCOMPLETE。observed 为真实 spawn EPERM、唯一 ps 调用和 04755；measured 为 SDK ABI 编译通过；inferred 为去掉 setuid exec 可消除已定位的启动障碍。
material unknown 是同一 C 下实际 libproc 查询是否可读以及整链是否成功，不能用模拟结果替代。
最小 Tracer bullet 保留在真实 release／原生 hook／Stop 生产路径，新 primary 同时作为查询权限与两次转交探针；执行主控按请求 12 在沙箱外跑，错误或清理不符即停。

process-observer-red-02 在旧产品上由同一当前测试拒绝 setuid ps；green-04 的 11 场（含随机 PID）通过。
process-snapshot-green-03 的 23 项合成缓冲／树及 ABI 编译通过；ignored-denial 变异命中明确业务断言，见 process-snapshot-mutant-01。
受影响旧 pane 测试首轮失败不是新查询导致：旧产品＋旧测试也重现 writes.then 缺字段，原件 conflict-panes-parent-01；补齐当前 fixture 字段、保留原断言后 conflict-panes-green-02 四项通过。
新观察留证导致旧提取测试包含 TS 注解，parser-red-03 的 Unexpected token 保留；修正提取范围后 daemon-rejection-green-04 三项与 chain-publication-green-06 五项通过。
这些均无真实 libproc／ps／pgrep 查询、OS profile、认证、网络或模型执行。

完整链现在导出实际 release 的 foreground_process_query，独立 V 要求其 observer 方法、PTY root 与内核前台身份匹配假 CLI。
primary-03 的命令和停止条件见 REVIEW-REQUEST-T093-12.md；只有主动失败及完整清理均符合预期，才跑 green／V 和正式六场。

首轮查询实现冻结 3fca92984443d0954f1fda8fbe0ba68230c66dcc 的只读审查为 FAIL，原文 PROCESS-OBSERVER-REVIEW-01.md。
审查者对 native/observer/rejection/publication 的 42 项 L1 检查通过，但指出合法假 API alias 会因 argv[0] 与内核可执行路径不同而误拒。
实际 Claude 启动边界现于原版本校验后、PTY 启动前保存规范 executable_path，Codex 使用原来已规范化的路径；保留实际 argv，不在查询时重新解析 alias。
process-alias-red-02 在首轮冻结上命中 valid_alias_must_keep_foreground_identity；green-02 的真实 start/release＋模拟执行／PTY／内核返回通过 alias 与不同目标反例。
process-alias-mutant-01 将目标改为每次 query 再解析 alias，启动后 alias 改指的其他程序因而被误认；同一反例拒绝了这种错误修法。
version-boundary-green-01 的原版本／并发断言与 conflict-panes-green-03 的原四项业务断言继续通过。新增版本夹具只提供 realpath 的 IO 边界，未削弱版本比较。
首次 alias 夹具用了不符合旧假 API 合同的根前缀，被 isolated_controller_root_required 拒绝、无 JSON；修正为该入口既有 t078-2 前缀后，使用同一最终夹具重新取得红绿，未改产品边界。
以上仍不证明真实 C 的 libproc 权限或完整链成功；新 primary 命令不变，等待主控执行。

实现冻结 7a5adebfcda47b10f28b8c51ecfc49dd7a490720 的一次限定复核为 INCOMPLETE，原文 PROCESS-OBSERVER-REVIEW-02.md。
审查者独立跑 alias 2 项、observer 11 项、version 8 项及其变异检查，认定前一 P1 的 L1 缺口已关闭，无新增阻断项。
小原件另存 alias-review-green-01、observer-review-green-02、version-review-green-01。实现此后未改，最终只补文本证据。
真实 C 下 libproc 与完整 primary／green／六场仍未执行，不能把局部结论上调；主控按请求 12 先跑 primary-03。

## 主控 #111：提示正文与完整派发信封混淆

**INCOMPLETE。** cb1208a0f 的真实 C/libproc 身份已通过，独立上游和原件均为两条请求，认证匹配、状态 400／200、收尾完整；primary 因旧 prompt_matches_fixture=false 而未到主动失败，green 未跑。
rehearsal-03-primary-summary.json 保存原错误和实际前台记录；不改其状态。

根因在旧 U oracle：它把 messages[0].content 与未包装的 fixture.prompt 比较。
规范 native-cli-orchestration:88、125 及既有 T-078 固定字节合同要求派发有“⟦主控 #序号⟧”。store.register 生成标记＋换行，drain 逐字粘贴，假 CLI 只移除终端包装并把原内容作为 user message。
原请求正文没有保留，不补称直接读回；数据流、hook 接受记录、真实 dispatch 局部检查和字节数共同定位：原轮两条 body 都为 247 字节，完整信封的默认 JSON 也是 247，未包装版本为 218。
没有修改假 CLI、编码、system 或产品文本来迎合旧 oracle。

现在 R 按外部规范和随机输入、fresh DB 的 #1 独立生成 expected_request_body，既不读取生产 dispatch 返回值来设预期，也不复制上游输出。
C 先核对第一条序号／完整文本，U 对整个解码 JSON 精确相等；字段、数组位置、数量、role 和 content 都不能忽略。
JSON 表达编码或缩进可不同，content 的内部空白、CRLF／LF、末尾换行、Unicode 字符不归一化；额外 system／消息／键均拒绝。
U 只公开结构标志、类型和长度，不写头、正文或凭据；原认证／计数／顺序／清理断言保留，错误分类改为明确的 managed_request_body_must_match_exactly。
upstream-prompt-red-02 在旧真实 Handler 上拒绝合同正例，green-02 的 13 项通过；内容单项与包含两种错误修法均被同一测试拒绝。
managed-prompt-green-01 的实际 dispatch/store/PTY sink 四项通过，精确字节与独立预期一致。均为 L1，未启动真实网络、CLI、auth 或模型。

共享影响按主控要求扩大到全部调用点审计，完整 13 个当前直接调用及 T-096 恢复入口列在请求 13；本轮产品 src 相对 cb1208a0f 没有修改。
T-091 的六 IPC／paneKey、sender、iframe／跨窗隔离、独立身份序号与输出游标等 11 项及两种旧候选反例通过；版本合同 8 项与变异通过。
T-078 runtime 11 项与 controller relay 22 项通过；它们的 liveness 是 spy，不冒称真实进程边界。原件以 t091-*／t078-*regression 保存。

只读核对 exec/t096@d61876fe29916ccf577da7b9b912cf305d9fdd9d 后确认跨票集成前置项：恢复入口直接用旧 record，而旧记录没有 T-093 新规范身份元数据；T-096 纯测试仍提供 ps 文本替身。
已写 ISSUE-T096-INTEGRATION.md，交执行主控在受管集成候选处理；不能删旧记录正例、改变原 argv、绕过版本／session 或固定 leader 成功。
没有改另一票的 attempt／文件，当前分支也没有 T-096 实现，故该回归未跑；其纯合同与原生重启命令、材料和审批边界已写入请求 13。
在新 primary／green／六场和跨票恢复回归完成前，不给出全 pane 非退化或集成 GO。旧审查原文与既有失败全部保留。

实现冻结 ed2e57d0ad43c533612549db90132761f684feab 的限定独立审查为 INCOMPLETE，原文 MANAGED-PROMPT-REVIEW-01.md。
审查者独立运行上游精确结构 13 项、实际 dispatch/store→PTY 四项、T-091 IPC 11 项及其历史反例；内容单项／包含两种变异被业务断言拒绝。
未发现 oracle 独立性或认证／计数／清理断言弱化；仅更正请求 13 的 T-096 方法标签为 recover(daemon) 内 openPanes 循环，不修改受审运行代码。
新 OS primary04／green04／六场及跨票恢复仍待执行，保持 INCOMPLETE。地图终检 0 problems、0 stale；冻结核对见 freeze-checks-26.json。

## 主控 #116：上游端点关闭与进程退出之间的查询窗口

**INCOMPLETE。** 079842e8b 的 primary04 达到预定主动失败，两条完整 JSON 均匹配、清理完整；green04 及其独立核对通过。正式 chain-07 的 none 通过、五个变异的主失败均符合预期；counts 的次要清理错误使六场独立核对保持 INCOMPLETE。
原独立结论为 chain-07-check.json、rehearsal-04-check.json；chain-07-validation-summary.json 保留阶段、原错误及后续 writer 确认，原临时结果不覆盖。

counts 已读到 U/closed.json，随后 signal 0 查询组时得到 EPERM；旧 gone 立即抛出，记为 upstream_shutdown_unconfirmed。最终同一谓词又以 ESRCH 确认 U 组消失。
U 的关闭收据写在 server_close 之后、进程返回之前；counts 变异只改对账返回值，不改请求和关闭路径。定位为端点关闭到进程退出确认之间的时序窗口，未采集 EPERM 的具体内核来源，不把它当退出证据。
测试链 gone 现在在原期限内把 EPERM 保持为未确认，只有 ESRCH 才通过；D 与全部 writer 屏障同样处理。关闭收据、5000ms 退出期限、主失败先落盘及删除前退出证明均保留。

upstream-shutdown-red-02 在旧真实回调上拒绝提前失败；green-01 的七种时序通过。将 EPERM 当退出的变异被业务断言拒绝，持续 EPERM、存活、缺收据、其他错误仍失败。
V 新增显式 --counts-only，用原有全部每场断言核对这一场，默认六场要求不变；十项局部检查包括权限未知和活 writer 拒绝。另有发布五项、独立清理十二项及精确 JSON 十三项回归通过。
以上仅 L1，不运行实际进程／profile、auth、CLI、网络或模型。首轮测试提取器的 parser 错误单列 harness-01，不计业务红态。
按主控要求仅交 chain-08-counts 与 counts-check 两条沙箱外命令，见 REVIEW-REQUEST-T093-14.md；实际复验和既有 T-096 跨票集成仍为 INCOMPLETE。

首轮冻结 74b7db2bd 的独立审查为 FAIL，原文 UPSTREAM-SHUTDOWN-REVIEW-01.md。审查者用最终 group／child 的 ESRCH→ESRCH→EPERM 时序复现：明细未确认但 all_exited 仍 true，可能放行删除。
修复让汇总同时约束已采集的全部 groups/children.exited；任一最终未确认行均禁止删除，不增加等待或权限。独立原件摘要 shutdown-independent-red-01、命令 upstream-shutdown-review-01-commands 保留。
审查者的实际 D／writer 回调夹具已成为 test_t093_writer_exit.mjs；writer-exit-red-01 在首轮冻结有两项业务失败，green-01 同样七项全部通过。新 OS counts／V 仍未运行。

实现冻结 ae54aac378d7e646b8677e1763cf604ef8a182c4 的一次限定复核为 INCOMPLETE，原文 UPSTREAM-SHUTDOWN-REVIEW-02.md；审查者以原独立时序七项确认原 P1 的 L1 缺口关闭。
仅删 group 条件、仅删 child 条件的两个变异都被最终未确认时禁止删除的业务断言拒绝。摘要 shutdown-independent-review-green-01.json、原命令 upstream-shutdown-review-02-commands.json 保留。
受审实现此后未改，最终仅补文本证据；地图终检 0 problems、0 stale。实际 counts／V 和 T-096 跨票检查仍为 INCOMPLETE，不宣布整票通过。

## 主控 #117：三组证据清单与第二轮独立审查交接

**整票 INCOMPLETE；所列无模型场景的预期结果已取得。** 主控 #117 对 fb39d14f14588bb2634f110b2a5a13d6187b4513 的 counts 回传 rc 2，主失败 missing_raw_request_must_be_detected，cleanup_failures=[]、fixture_removed=true；V 的 counts-only 核对 rc 0／PASS，cases 1。
原件读回与主控结果一致，最终 groups／children 全部 exited=true，隔离根与合成源已删除。真实供应商 CLI、真实 auth、真实上游、真实模型均为 0。此状态覆盖上段当时“counts／V 未运行”的历史记录，不改写旧失败。

摘要为 [chain-07](chain-07-summary-15.json)、[chain-08](chain-08-summary-15.json)、[rehearsal-04](rehearsal-04-summary-15.json)，原路径／字节数／候选／checkpoint 清单为 VALIDATION-MANIFEST-15.json，独立 V 原文保留为各自 check.json。
chain-07 原核对仍 INCOMPLETE，counts 的旧清理错误仍在；chain-08 只补新候选 counts 的证据，不将两代结果篡改成同一代 V PASS。原临时报告未删除，未复制 auth、整个夹具、sqlite 或二进制，也没有虚构外置盘归档。

### 079842e8b 到 fb39d14f1 的准确差异

git diff 确认产品 workbench/src、app、hooks 和依赖配置完全未变，故正常登录、profile、转发器、事实逻辑、Panes.processInfo/libproc 均为相同产品代码。
测试链的变化限定在 finally 收尾：gone 的 EPERM 保持未确认、原期限内仅 ESRCH 确认；最终 all_exited 另须满足每条 groups/children.exited。后一项来自独立审查发现，不可省略成“整个区间只改 gone”。
此外，独立 V 增加显式 --counts-only，仅改本次选择集合、沿用全部每场断言，默认仍须六场；新增相应时序／范围测试、README 与文本证据。finally 之前的触发、注入和业务断言未改。
这不是新产品版本的六场通过证明；最终文档冻结与 fb39d14f1 的产品及运行测试代码也保持相同，具体差异与状态记录在 freeze-checks-30.json。

| 场景 | 原实跑与结论 | 对新候选仍成立的部分／未重跑边界 |
| --- | --- | --- |
| none | chain-07／079842e8b，rc 0，V pass=true；2 请求、400→200、原件对账、两次 hook／Stop、哨兵一次、清理完整 | 产品、假 CLI、独立 U 和正常业务断言均未变，仍是同一产品行为的有效实跑证据；chain-08 也走过这些正常阶段再触发计数反例。没有把 none 标为 fb39 的新全场实跑 |
| home-references-empty | chain-07／079842e8b，home_path_injection_must_be_reported；V pass=true、清理完整 | HOME 引用函数、argv 注入及其精确断言未变，仍证明忽略 HOME 引用会被抓住；该早失败路径的新收尾没有单独 OS 重跑 |
| scanner-zero | chain-07／079842e8b，credential_injection_must_be_detected；V pass=true、清理完整 | 扫描器、六变体及实际注入／命中断言未变，仍证明扫描恒零会被业务断言拒绝；不扩大为真实凭据全 Git 历史检查，也不称新早失败收尾实跑 |
| drop-first-record | chain-07／079842e8b，forwarder_record_count_must_match_upstream；V pass=true、清理完整 | F record 注入点、独立 U 收据和计数断言未变，仍证明首条漏记被对账抓住；finally 之外的比较没有放宽，新早失败收尾未单跑 |
| empty-credential-cases | chain-07／079842e8b，credential_injection_cases_must_not_be_empty；V pass=true、清理完整 | 空集合前置业务断言及全部注入必须执行的断言未变，仍证明不是靠 ENOENT 退出；新早失败收尾仅有原实跑、局部新时序和共同收尾代码证据，不冒称已重跑 |
| counts-always-match | chain-07 旧主失败正确但有清理错误，原 V pass=false；chain-08／fb39d14f1 同主失败、清理完整、V pass=true | 以新一场关闭该收尾缺口；仍只接受 ESRCH，最终每条退出明细须确认。旧失败保留，不用新结果覆盖旧候选状态 |

rehearsal-04 的 primary／green 与 V PASS 继续绑定 079842e8b。主失败先落盘、完整派发 JSON、hook／Stop 和产品不变量未变；新 finally 的变化另由 chain-08 OS 实跑及 UPSTREAM-SHUTDOWN-REVIEW-02 的局部时序／删条件变异证明。没有重跑新候选两场演练。
独立审查应核对上述证据延续范围，不能只看组合场景均符合预期就宣布同一新版本全套通过。下一步由主控安排新的只读第二轮审查；本轮只整理既有文本，不再启动链路、OS 查询、auth 或模型。

## 主控 #121/#122：端口规则、应用主机锁定与恢复身份修复

**整票 INCOMPLETE；局部检查通过，真实模型仍为 0。** 第二轮独立审查为 INCOMPLETE，independent-review-02.md、REVIEW-OUTSIDE-03.sh 均按原字保留。主控在沙箱外编译实际 F：127.0.0.1 通过，203.0.113.31 报 host must be * or localhost；原件摘要 profile-compile-review02-red.json 保留。
worker 合并因 ORIG_HEAD.lock 写共享 Git 目录被沙箱拒绝，未申请升级；主控执行 MERGE-MAIN-16.sh 并代为提交，合并头为 64c6456de2b7c0111628defce442d999a26734db，双亲含旧 T-093 与 main 0e92f78ec（T-096 fd5c93e6e）。无冲突。MERGE-BLOCKED-16.md 是此前暂停记录；本段覆盖其“尚未合并”状态。

主控 #121 修订其网络裁定，构思主控在 #122 确认没有超出 T-092 决定。F 的 OS 规则现在为 remote tcp4 "*:443"，**OS 层不再按主机限制**。应用捕获配置 hostname，在 transport 前拒绝目标漂移，lookup 再核对 hostname 并只返回配置 IPv4；入站 Host 被剔除，不跟随重定向。非配置目标拒绝记录为 upstream_host_mismatch；原件仍先写 request 并 fsync，失败／重试仍逐条计数。
prepare 在读取原始 auth 或启动服务前拒绝非 443；本地假链固定 HTTP 127.0.0.1:443，若占用或权限不足报 INCOMPLETE，不换端口、不重用别人的 listener、不申请 root。C、D、HOME、Security、fork、Unix socket、门禁规则未放宽。preflight／结束事实新增 network_boundary 三字段，明确 OS 主机过滤为 false，不能当作全网络审计。
forwarder-host-red-02 在旧实际 handler 的两种非配置目标时序命中业务拒绝，green-02 五项通过；分别去掉 transport 前和 lookup 校验的变异都被 non_configured_host_must_not_connect 拒绝。测试只用 supplied transport，不向 127.0.0.2 或假主机联网。端口最终 green-02 五项为纯构造／prepare 校验，含显式 0；旧 or 会将 0 当默认端口，port-zero-red-01 复现，现只对未声明端口的 HTTPS 默认 443。**这些不证明本机编译或 OS 拒连已通过**。
network-fact-red-01 因缺少新边界字段被业务断言拒绝，green-02 验证实际 preflight；没有把事实字段常量当 OS 执行证明。旧记录与回归仍保留。

恢复红态在合并原源码上复现：版本／session／给定内核身份均合法，缺 executable_path 的旧记录仍报 restore_process_missing。最终同信号红态 t096-restore-red-03 没有早期 PTY 替身的 kill 缺字段干扰；red-01/02 仍保留，不丢弃失败。
修复在原版本与 native session 核对后、PTY spawn 前建立 realpathSync(argv[0])，已有规范身份不同则 restore_executable_changed。只给运行时 record 副本补字段，历史启动记录不变、原 argv 完整，leader 仍来自实际 processInfo，未改版本／session 条件或 worker 归属。
test_t096_restore 的两个旧记录正例、已有身份匹配、身份改变拒绝均通过；保留历史 worker 误恢复反例、实际 PTY argv 缩短变异，新增删除身份校验／伪造 leader 变异均命中业务断言。测试给定 subprocess／PTY／clock／realpath 边界，真实 SQLite/native 文件；不是原生恢复实跑。
合并后的 T-091 IPC（含空布局）19 项、版本 8 项、observer 11 项、alias 2 项、T-078 runtime 11 项／relay 22 项、T-096 daemon 7 项／进程 probe 11 项／argv 材料 5 项通过；均注明边界替身，未执行真实进程查询或 Electron。

新 OS 入口为 T093-OS-16.sh：先只编译，再 primary／green／V 与正式六场。新链实际 F 负例检查非 443 端口，应用目标反例在 C 内用真实 handler＋传输替身验证；两个层次分别留证。旧 probe_t093_parallel_profiles.py 的 standalone 入口与旧 OS 结果属于原 localhost/端口方案，不作为新 F 权限证明。
T096-REGRESSION-16.sh 提供 tracer、three、missing-argv、version-mismatch、missing-session、isolation、empty-reopen；仅主控沙箱外运行，初始化仍逐屏批准，脚本不自动按键／登录或预置内部状态。任何失败保留现场，交主控按裁定重开 T-096，worker 不自行修改另一票验收或自动重试。
本轮没有真实 auth 读取、真实供应商 CLI、实际 OS profile、真实上游或模型回合。合并／修复局部通过不等于七场原生恢复或新网络权限已验收。报告复制遇旧同名文件时独占创建拒绝，旧件未覆盖，新件改用 r16 名称，见 evidence-copy-collision-16.json。

首轮限定审查 e1177a02d 为 FAIL，原文 NETWORK-RESTORE-REVIEW-01.md：网络与恢复身份的限定检查未发现违约，但交接 verify-six 在系统 Bash 3.2 因空 flags 数组而不能启动 V。现只改位置参数转发，实际 Bash＋exec 哨兵的七分支红绿为 outside-wrapper-red-01／green-01；没有把 shell 失败算作 V 业务拒绝。
审查结束后 worker 追加实际 recover 的正常登录标记输入，复现另一个组合问题：普通 daemon 可直接派生正常登录记录的 CLI，未恢复原 R/F/D/C 上下文。给定边界失败为 normal-restore-boundary-01，未真实启动 CLI／OS，没有实际 HOME 写入或泄漏主张。
见 ISSUE-NORMAL-LOGIN-RESTORE-16.md，已交主控按 #122 重开 T-096 并裁定本票是否先明确拒绝该恢复；未自行实现完整恢复设计。该路径 NO_GO，当前不能给整体集成 GO；原七场假 API 回归不能覆盖它。网络／规范身份修复和脚本修正的其他验证继续按各自范围报告。
