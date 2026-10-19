STATUS: INCOMPLETE

TARGET: `630291ca7a07086d231e38a15fe1f1c9e6411bf0`，起点 `61786370428c3ec5f894ea60acccf2695d54c2dc`；仓库 `/Users/luckye/Documents/Code/a2a-wt-t093`，分支 `exec/t093`。

2026-10-18，执行主控 #119 派发的第二轮独立审查。task T-093 / attempt a1 / ready_rev 1；请求中的 session 为 `67f986cc-92e4-4089-9c22-802a1143b645`。这些是交付绑定信息，不声称本轮重新验证了 fence 或取得门禁收据。无作者或第一轮 reviewer 会话历史，未开子 agent。

**第一轮两项验收缺口已取得修复证据；本候选仍不能给出无条件 PASS。** 非 loopback 上游的 F profile 生成了本票历史编译器曾拒绝的数值主机语法，须先执行无联网编译对照；T-096 恢复与新身份字段的跨票问题也仍开放。没有本轮外部回传时，不把这两个边界猜成通过。本报告不修复实现、不提交、不集成，也不批准真实模型开工。

EVIDENCE:

审查依据先从最新 main 的 T-093、T-092 六项用户决定和裁定 A 重建，再读请求 15、RESULTS、PROBE 系列和第一轮报告。使用 `git show`、基线到冻结候选的 `git diff` 阅读原文；作者结果和旧审查仅作定位与待核实材料。应用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、document-writing。审查期间候选 HEAD 未变化；受控文件没有修改。

目标是验证隔离登录、调用计数、HOME 禁写、凭据保护和共享进程身份查询，并检验完成条件能否拒绝明显错误实现。非目标是实现、登录刷新、真实供应商 CLI/模型运行、跨票合并或门禁操作。Ubiquitous language 沿用 task、attempt、启动记录、原生会话与事实命令；不把终端 idle 或作者 PASS 当验收。

独立合同如下：只复制现有登录凭据到隔离 HOME，结束删除整个隔离根；本地转发层逐条先记后转，失败及重试分别计数；事实脚本报告路径引用、清单变化、计数及凭据命中，不代用户放行。裁定 A 用 OS 禁写及拒写反例替代“清单无差异”通过条件，差异仍须报告。真实模型复核最多 3 回合，且本票合入后仍等用户另说开工。本轮真实凭据读取、供应商 CLI、真实上游及模型调用均为 0。

| 审查项 | 判定与独立证据 |
| --- | --- |
| main 红态、候选构造入口 | PASS。将 main 源码用 `git archive` 导出，把同一当前构造检查放入副本：main rc 1，三条正常登录合同失败，原假 API 仍拒 HTTPS；候选同一检查 rc 0、4 项通过。main 的 `source_equals_main=true`。首次 main 副本缺 effect 依赖的环境失败保留，不算红态；补上已有依赖链接后才取得上述业务红态。 |
| 第一轮空凭据变体缺口 | PASS。`test_t093_forwarder.ts:16` 起独立构造六种输入，不从生产 `credentialVariants` 取输入。文件创建、读回、命中、全部执行均有断言；空场景另有明确前置断言。本轮清空生产枚举器的单处变异以 `credential injection must be detected` 失败，rc 1，无 ENOENT。独立随机原值/编码检查对照 rc 0，坏实现 rc 2。 |
| 第一轮首条漏记被清理覆盖 | PASS，限实际到达的场景。直接读 `/private/tmp/t093-chain-07-drop.json`：上游两次，request 原件只有序号 2，首条收据 `recorded_before_receipt=false`；主失败为 `forwarder_record_count_must_match_upstream`，cleanup=[]、fixture_removed=true。checkpoint 的 cleanup_pending 和最终 complete 都保留该主失败。不是凭非零退出认定变异有效。 |
| HOME 裁定 A | PASS，限已实跑 profile、进程与本地配置。逐个 profile/实际拒写及合成 HOME 删规则对照见下文；清单 `pass_condition=false`。不推广为沙箱外准备阶段或系统服务不会写。 |
| 网络边界 | 本地配置 PASS；非 loopback 上游 INCOMPLETE。源码固定 F 监听端口及唯一 peer，C 只有 F TCP 和本次 Unix socket；原件有两项 EPERM 拒连及额外监听拒绝。非 loopback profile 的语法阻点尚待本轮 OS 编译对照。 |
| 凭据来源和泄漏 | PASS，限静态路径、probe-10 摘要及扫描范围。原始 auth 在 R 精确读取一次；完整假链 real_auth_reads=0。候选范围 43 个提交的 `git log -p` 五类 token 特征命中 0；未读取真实 token 作精确历史匹配。 |
| 计数和重试 | PASS，限本地假上游。两条独立收据与 request 序号 1/2、outcome 400/200 对齐；U 在接收时读取 journal。新转发器对照保留原件并独立重数；漏记第二次请求的单处变异被先记后转断言拒绝。 |
| 全 pane 进程查询 | 当前候选的查询/身份边界 PASS；全生命周期非退化 INCOMPLETE。查询错误传播、非法快照拒绝、身份条件和 alias 边界通过；T-091/T-078 局部回归通过。T-096 旧记录恢复兼容性未解决，原生窗口/恢复实跑未完成。 |
| probe-10 披露 | PASS。RESULTS:59 起的三条边界及末段更新保留版本内部状态、官方直连预检、400 后重试；没有把无可见文字或 F 计数写成全网络审计。 |
| 地图 | PASS。本轮开始及交付前 status 均 rc 0，0 problems、0 stale。 |

HOME 与进程绑定：

`claudeLoginSession.py:91` 的 C/F/D 公共规则禁写 OS 账号真实 HOME；root/state/repo/audit 必须位于 HOME 外。F/D 平级独立施加 profile，C 只施加一层，PTY、zsh、CLI、clang、version/auth status、hook/inbox、事实子进程及 libproc helper 继承 C。没有嵌套 sandbox 或无保护 ps fallback。对额外 FD 的关闭在进入业务 profile 前完成。

| 进程/阶段 | 实际保护及本轮核对 |
| --- | --- |
| R、脱离引导 | 业务沙箱外的有界准备：参数/FD、临时目录、一次原始 auth 读取及 exec。不是受 C 保护的长期监督进程。不能宣称所有时刻、所有进程绝对都已禁写。 |
| D_baseline | 在原始 auth 读取前，以独立 D profile 采四范围目录/stat；禁网络、Security、fork、HOME 写。chain-07 none PID 71232；chain-08 counts PID 85016。 |
| C 及后代 | chain-07 none 根/报告者 PID 70843；chain-08 counts 84944。登记表含 PTY、版本、hook/inbox、clang、事实与 libproc 子进程。继承结论来自实际启动路径及 OS 继承，不只来自 `C inherited` 标签。 |
| F Python→Node | 同一 F profile 跨 exec，禁 HOME 写、fork、Security；仅 forwarder 目录可写。两场 F PID 分别 71253、85027。 |
| 长期 D | 两场 PID 71247、85021。真实产品不删除原始用户 auth；测试 D 仅可删除本次合成 source-home，并在读取已持久化主失败 checkpoint 后删除。 |
| U、S、M | 各自独立 profile 保留真实 HOME 禁写；U 只监听两个明确测试端口、无出站。S/M 只有合成 HOME 的 deny 差异。 |
| G0/G1/G2、V | Git 检查为独立 G，无 HOME 写、网络或 Security。V 自己施加保护并查询退出，不沿用 C 的自报。原 V 输出的存在证明历史核对结果，不等同本轮重新查询历史 PID。 |

none 与新 counts 各有八次独占新建真实 HOME 文件的尝试：C 父、CLI、F Node、F Python、D、U、S、M，全部 EPERM/未创建；D 再核对八个路径均不存在。S 的合成 HOME 尝试被拒；M 只去掉合成 HOME 禁写后成功创建、删除并确认不存在，命中 `home_write_must_be_denied`；真实 HOME 禁令始终保留。本轮没有为了变异去掉真实 HOME 禁令或尝试无保护写用户 HOME。

这证明所跑进程及其 profile 下这些写操作确实被 OS 拒绝，合成对照的检查能拒绝漏规则；不能证明 R、Security 服务或用户其他会话没有写入，也不能据此前后清单做因果归属。清单范围 .claude、.claude.json、.claude.json.backup、Library/Keychains；只读目录/stat，不读正文、不跟随链接、不比 atime/校验值。差异仅为事实，不再作通过条件。C/F 的祖先元数据例外不允许 HOME 目录枚举或 AGENTS.md 正文读取，原件中的两项读取拒绝仍为 EPERM。

网络与计数：

本地证据中 F→配置 U 实际收发两次；F→另一活跃 U 端口为 EPERM，CLI→配置 U 为 EPERM，F 另起监听端口也为 EPERM。F 的 Node 请求显式使用配置 URL、固定 IPv4 lookup、URL 端口；无自动 DNS、轮换 peer、重定向或重试。C 的 TCP 例外只到 F；G/D/V 无网络，U 无出站。两个拒连反例证明本地配置下不能绕过，不能替非 loopback/TLS 补证。

`claudeForwarder.ts:67` 检查原件 inode/dev、写完并 fsync；`:78` 先写 request，`:103` 后发上游。journal 失败返回失败并停止继续转发，outcome 失败留下 journal_failure。U 的接收代码独立读取 ledger，期望由外部任务合同、随机 prompt 和 fresh DB 的 #1 派发标记构造，对整个 JSON 精确比较；不从生产 dispatch 返回值或上游输出复制答案。

本轮另跑生产转发器，保存 `/private/tmp/t093-review02-latest/forwarder-raw/requests.jsonl`，独立重数 request=[1,2]、outcome=[400,200]，与独立上游 2 次相符。raw/missing-row 为小型元数据原件，不含正文或认证头；扫描为 0。它是本轮独立转发实验，不冒充历史整链的 journal。

凭据：

`claudeLoginSession.py:175` 在受保护 baseline 后仅调用一次 `read_auth`；显式选择 file 或 macos-keychain，失败不枚举、切源或重试。钥匙串路径是 `claudeLoginFiles.py:83` 的精确服务 `Claude Code-credentials`、`-w` 和指定 login.keychain-db，结果只捕获在内存，复制 claudeAiOauth 到 0600 私有文件。F/C 之后读取的是隔离副本，不是再次读取原件。

“沙箱外读取”须准确理解为 R 位于 C/F/D 业务沙箱之外；security 命令本身仍套专用只读、无网络、禁 fork profile，不是完全无沙箱的 security。probe-10 摘要支持原登录被识别、携复制 bearer 的两个本地 POST、扫描 0、私有根已删除；本轮没有再运行真实 auth 验证。Keychain 服务自己更新 WAL 不在 CLI 进程禁写证明之内。

历史扫描精确命令为 `git log --format='commit %H' -p 617863704..630291ca7a07086d231e38a15fe1f1c9e6411bf0`；只在内存匹配 Anthropic OAuth access、refresh、API key、JWT 和长 bearer 五类特征，43 个提交命中 0。结果只保存类别/计数/位置，不输出疑似值。它不证明未知格式/编码或真实 token 原值从未出现；结束时扫描也不证明所有中间时刻。没有读取 auth.json、.credentials.json 或钥匙串数据库正文来扩大扫描。

Panes.processInfo 与共享调用：

当前 `panes.ts:402` 的 exec 有 5 秒/4 MiB 上限，exec 拒绝、JSON 解析失败及 schema/树错误都传播；没有将异常吞成空列表。helper 用 libproc 读取本 PTY 后代，无全机 ps、argv、环境或认证读取；权限错误/短数据/截断/重复树/身份变化退出非零，已知退出/僵尸不当活 leader。出生时间用于防止查询中 PID 复用；查询不是原子快照或未来存活保证。

leader 仍要求 PID=PGID=TTY 前台组、内核路径等于启动前保存的 `executable_path`，保留原 argv；不是查询时再解析 alias。版本检查仍先于身份捕获与 PTY 启动。复核了 daemon 的反馈、窗口 assertCurrent、pane_process_info，以及 pane 的反馈、用户放行、中断前后、初始化 release、screenKey、主控 caller 两次、worker caller、readThread 共 13 处调用。原有会话/spec/attempt/fence 与 Stop 前后重查未放宽。

本轮在 archive 副本实际通过：observer 11 项、native buffer/tree/SDK ABI 23 项、alias 2 项、T-091 IPC 11 项及其历史反例、T-091 版本 8 项、T-078 runtime 11 项、relay 22 项、conflict panes 4 项。IPC 的六类请求、sender+paneKey、独立凭据/sequence/cursor、iframe/跨窗/错 task/旧 launch 拒绝保留。T-078 的队列、输入记录、Stop、一次转交和失败隔离保留。这些的 Electron/PTY/进程 IO 为替身；实际 C/libproc 的证据来自历史 rehearsal/chain 原件，不能称本轮原生窗口与所有生命周期均重跑。

T-096：独立读取 `ef8bcd32db2dd801fb648506dc4f2409b63fa745:workbench/src/panes.ts:206`、`:243`、`:265`，恢复仍复用旧 record 并调用 processInfo，没有建立新规范身份。合法旧记录缺 executable_path 时，当前比较必得不到 leader。本轮给实际 processInfo 合法进程行及缺字段旧记录，结果命中 `valid_kernel_identity_must_match`，rc 2；同一边界有该字段则 rc 0。此为输入反例，不是第四个实现变异，也不冒充完整 T-096 重启。本分支没有恢复实现，所以不能自行改另一票，也不能声称已通过跨票恢复。

probe-10 三条披露：RESULTS 保留 2.1.302 的 hasCompletedOnboarding 与唯一当前 cwd 信任内部字段；两个官方 hello 候选绕过 BASE_URL；两个 POST 均回 400，按主控结论存在重试。`preflight_observed=false` 只表示终端/私有 debug 未识别迹象，沉默的被拒尝试未测量。本轮只核对摘要及实现约束，未读真实 CLI 终端原文、未复跑供应商 CLI。

证据延续判断：

直接读回清单 21 个原始 JSON/checkpoint/V 文件，字节数均与清单一致，无校验值；独立重数请求/结果、核对主失败、清理和每条 writer 明细。没有靠 summary 的 PASS 代替原件。历史 PID 不在本轮重新 signal 查询，避免把 PID 复用后的结果冒充当时存活。汇总保存于 `original-evidence-audit.json`。

| 场次 | 原候选/观察 | 对当前候选可支持的结论 |
| --- | --- | --- |
| rehearsal-04 primary/green/check | 079842e8b；primary 达预定失败，green 通过，V PASS/2 场 | 完整派发 JSON、hook/Stop、libproc、两条请求和主失败先落盘的产品事实有效；新 finally 未对这两场单独重跑。 |
| chain-07 none/home/scanner/drop/empty | 079842e8b；none 通过，四个反例均命中指定业务断言、清理完整，V 对各场 pass=true | 产品、触发、注入和业务断言未变，继续支持相同行为；不等同新版本早失败收尾已逐场 OS 重跑。 |
| chain-07 counts | 同上；主失败正确，但 cleanup 有 upstream_shutdown_unconfirmed，原 V 该场 false、整体 INCOMPLETE | 旧失败保留，不能追认该场完整通过。 |
| chain-08 counts/check | fb39d14f1；主失败 missing_raw_request_must_be_detected，cleanup=[]，每条 writer 已确认，V PASS/1 场 | 新共同收尾在该真实路径取得证据，不替代六场或两场演练统一重跑。 |

`git diff 079842e8b fb39d14f1 -- workbench/src workbench/app workbench/hooks workbench/package.json workbench/package-lock.json` 为空。测试执行路径有两处实质收尾变更：gone 遇 EPERM 保持未确认并在原期限内等 ESRCH；all_exited 还要约束最终 groups/children 每条 exited。V 的 counts-only 仅选择单场，未改默认六场的全部要求；另有相关时序/选择测试。fb39d14f1→630291c 的产品与 tests 差异均为空，workbench 只有 README 文本变化。

因此旧业务场次不会因这两处收尾改动全部失效；它们支持的是不变的产品及前置断言，变化部分由 chain-08 和本轮七项 writer 时序、七项 shutdown、十二项 cleanup oracle 等局部检查补证。没有同一新候选的六场总通过收据，不制造组合 V PASS。非 loopback profile 本来就未被这些 localhost 场次覆盖，不能凭版本相同弥补。

FINDINGS:

- 已确认的跨票集成不兼容仍开放：当前 `workbench/src/panes.ts:416` 需要 executable_path；T-096 上述恢复入口直接使用旧记录。恢复拥有者须在原版本校验之后、启动 PTY 之前建立运行时规范身份，保留不可变历史记录和完整 argv；已有身份不得忽略目标一致性。不允许删旧记录正例、固定 leader 成功或绕过版本/session。此项阻止“全 pane 非退化/集成 GO”，不是本分支已经执行失败的 T-096 整链收据。
- 本轮未确认新的异常吞并、fallback、平行 API 或身份放宽。结构扫描对基线→候选 src 定位 47 个标记后逐项按真实 caller、所有权和可达错误判断；标记数不是验收数。转发边界把记账/传输失败转固定错误与 journal_failure，私有 auth helper 的宽捕获非零退出以防泄露，生命周期清理失败留下缺事实/失败事件，不构造成功事实。`inet_pton` 的 OSError 仅用于区分域名与 IPv4 字面量，没有回退地址。ClaudeLogin、转发器、libproc helper 分别承载实际生命周期/HTTP/OS 边界，属于 Deep modules；没有新增无保护查询或第二套门禁。

COUNTEREXAMPLE:

一次性副本来自 `git archive`，位于 `/private/tmp/t093-review02-latest`；未建 worktree、未提交，依赖只链接既有 node_modules。每个实现变异只改一个生产位置，先跑相同信号的未改候选。三个变异均取得业务拒绝，退出非零没有被直接当作证据。

| 单处变异 | 相同信号的候选 | 实际坏实现结果 |
| --- | --- | --- |
| `panes.ts` 将 observer exec 的拒绝吞掉，合成 schema 正确的空 rows | 独立 observer 信号 rc 0，随机合法 PID/组/路径匹配，EPERM 必传播 | rc 2，`observer_permission_error_must_propagate`。证明实际 processInfo 的错误传播；无 OS 故障注入。 |
| `credentialVariants` 入口直接返回 [] | 独立六种编码检查 rc 0；候选自己的 forwarder 检查 rc 0 | 独立检查 rc 2，`independent_credential_injection_must_be_detected`；候选检查 rc 1，`credential injection must be detected`，未出现 ENOENT。 |
| `ClaudeForwarder.record` 跳过 sequence>1 的 request，仍转发 | 同一 forwarder 检查 rc 0，U 先 400 后 200，两次均先记账 | rc 1，第二次 U 接收时 `durable record must precede upstream receipt`。未超时，没有清理断言覆盖。 |

精确命令（输出须另选新文件名；已有原件不可覆盖）：

```sh
node /private/tmp/t093-review02-latest/observer-independent.ts /private/tmp/t093-review02-latest/candidate /private/tmp/新的-observer-control.json
node /private/tmp/t093-review02-latest/observer-independent.ts /private/tmp/t093-review02-latest/swallow-observer /private/tmp/新的-observer-mutant.json
node /private/tmp/t093-review02-latest/credential-independent.mjs /private/tmp/t093-review02-latest/candidate /private/tmp/新的-credential-control.json
node /private/tmp/t093-review02-latest/credential-independent.mjs /private/tmp/t093-review02-latest/empty-variants /private/tmp/新的-credential-mutant.json
node /private/tmp/t093-review02-latest/candidate/workbench/tests/test_t093_forwarder.ts /private/tmp/新的-forwarder-control.json
node /private/tmp/t093-review02-latest/empty-variants/workbench/tests/test_t093_forwarder.ts /private/tmp/新的-empty-mutant.json
node /private/tmp/t093-review02-latest/omit-retry/workbench/tests/test_t093_forwarder.ts /private/tmp/新的-retry-mutant.json
```

坏 forwarder 的原始 stderr 为两个独立断言，保存在 forwarder-empty.stderr、forwarder-retry.stderr；这两个坏运行没有最终 JSON，不能补称它们的清理已由最终 JSON 证明。该限制不影响其中已直接观察到的明确业务拒绝。三个变异的命令/退出/对照摘要另见 independent-mutations.json、forwarder-mutations.json。

LIMITATIONS:

1. **非 loopback F profile 必须优先核实。** `claudeLoginSession.py:102` 把非 127.0.0.1 地址原样设为 peer，`:110` 生成 `(remote tcp4 "数值IPv4:端口")`。本轮实际调用候选 policies 的纯函数输入 203.0.113.31，得到 `(allow network-outbound (remote tcp4 "203.0.113.31:443"))`。同票 profile-compile-red-04.json 曾记录数值主机编译失败、诊断 `host must be * or localhost in network address`；当前所有 OS 绿态只用 localhost。它是明确的语法风险，不是实际出网或模型额度问题。本轮未调用 OS 编译器重测该 profile，故暂不把推断写成新复现的 NO_GO，也绝不能把“F 可连接真实配置上游”写成 PASS。
2. 上述对照已写入 `REVIEW-OUTSIDE-03.sh profile-compile`：直接导入冻结候选的 policies，分别编译 localhost 和文档用途的非 loopback IPv4；不应用 profile、无 DNS/网络/auth/CLI。若后者编译失败，即为可达产品阻断，应判 NO_GO；修复应在 profile 构造层，用经 OS 证明可编译且仍精确限制 peer/port 的单一路径，不放宽为任意地址，也不回退无沙箱。此模式本轮仅做 bash -n 和嵌入 Python 语法检查，尚无执行结果。
3. T-096 两票受管集成候选及原生恢复回归未执行；本分支缺恢复实现。脚本 t096-restore/daemon/probe 要求主控另行提供已经建立的集成候选及完整 SHA，不替主控创建合并或授权运行。T-091/T-078 的原生窗口和 captured-screen/hook 生命周期仍未全部重跑。T-078 empty/newline 以及需要原材料的 startup/epochs 入口也已写入脚本；缺材料不算通过。
4. 若主控需要当前冻结候选的新 OS 补证，脚本提供 none、primary/green、drop-first-record、empty-credential-cases 等单场入口，以及 verify-six/rehearsal/counts。先 none 对照通过再做变异；反例 rc 2 仅在预定 primary、cleanup=[]、fixture_removed=true 和独立 V 都符合时才算有效拒绝。每次脚本 exec 到单个入口，不保留无保护长期监督进程。不得把旧候选结果传给新候选 V。
5. 真实 DNS/TLS、模型回复、真实登录刷新行为没有新运行证据；本轮不需要也不允许用真实模型补这些检查。保留原 probe-10 的版本与观测限制。

主控首条无凭据对照命令：

```sh
bash evidence/2026-10-16-batch16/T-093/REVIEW-OUTSIDE-03.sh profile-compile /Users/luckye/Documents/Code/a2a-wt-t093
```

局部检查原件、命令与范围都保存在 `/private/tmp/t093-review02-latest`：local-checks.json（15 个入口均 rc 0）、conflict-panes-command.json、forwarder-retained-command.json、launch-main-red02-command.json、history-scan.json、structural-markers.json、version-continuity.json、original-evidence-audit.json、outside-script-check.json、project-map-final.*。首次 archive 多带了不存在的 tsconfig 路径而退出 128，未提取候选；identity.json 记载该环境错误，随后只导出所需目录。未覆盖旧运行证据。仓库仅新增本报告及指定沙箱外脚本，中文 UTF-8，无 BOM；没有 commit/checkout/reset/stash/push/submit/集成、全局配置写入或升级请求。

RULE:

第一轮的同源答案/空注入与清理覆盖失败类别，当前由独立编码输入、执行计数和持久化主失败 checkpoint 的真实入口检查捕获。新发现的非 loopback 风险说明 localhost 正例不能证明配置地址分支；完成检查应在不读 auth、不联网的准备阶段，对实际生成的非 loopback F profile 做编译正例，并保留原精确 peer/port 拒连合同。这应是可执行检查，不需要再加一条纯文字提醒。T-096 的检查由恢复拥有者在受管集成候选运行，保留旧记录和原身份拒绝条件。本审查未改这些实现或验收文件。

T-093 REVIEW INCOMPLETE
