# T-093 第二轮独立审查请求 15

**INCOMPLETE：无模型场景的预期结果已取得，等待本次冻结候选的独立审查与门禁；T-096 跨票集成项仍未解决。**
审查对象为最后 `T-093 FROZEN <完整 SHA>`，产品及运行测试代码与 fb39d14f14588bb2634f110b2a5a13d6187b4513 相同，本次仅整理文本证据／清单与文档。
task T-093 / attempt a1，worker s16-t093；session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
基线 main 为 61786370428c3ec5f894ea60acccf2695d54c2dc。不得将此冻结当作 submit、验收、集成或真实模型开工许可。

## 本轮独立审查范围

请在新的只读 session 审查完整 T-093 产品与验收证据，特别检查四项：用户裁定 A 的真实 HOME 禁写；全 pane 的 libproc 查询替换；probe-10 的版本／预检／重试边界；F 和 C 的网络分离。
重建事实与外部 oracle，不以作者 PASS、自带检查数量或旧审查替代判断。保留原独立审查 01 的 NO_GO，以及后续限定审查的 FAIL／INCOMPLETE；它们不是本次完整审查的通过收据。
不可写仓库、改测试、改变断言、动其他 ticket 或门禁。无真实模型回合、真实上游或新增真实 auth 读取；无全局配置写入。需要本机 OS profile 的运行仍由主控执行脚本，reviewer 不申请升级或嵌套 sandbox。

## 最新证据、候选与有效性

入口清单：[VALIDATION-MANIFEST-15.json](VALIDATION-MANIFEST-15.json)。它列出三组共 21 个原始 JSON／checkpoint 文件的路径、字节数、候选与保留位置；没有校验值，不删除原件，没有归档或复制 auth／sqlite／二进制。
[collect-validation-15.py](collect-validation-15.py) 只整理固定文件名的既有报告，不启动业务链或进程查询，不制造新验收结论。summary 的原 status、主失败和版本均保留。

| 组别 | 实跑候选与结果 | 保留文本 |
| --- | --- | --- |
| rehearsal-04 | 079842e8b6808fa95a7e6f2efbd5fce2c8d1e0ac；primary 命中 rehearsal_primary_probe、green rc 0；V PASS、2 场；两条精确 JSON／400→200／完整清理 | [摘要](rehearsal-04-summary-15.json)、[原 V](rehearsal-04-check.json)、清单中的两份 events |
| chain-07 | 同一 079842e8b；none 通过，五变异主失败均正确；counts 有 upstream_shutdown_unconfirmed，原 V 整体仍 INCOMPLETE，其他五项 pass=true | [摘要](chain-07-summary-15.json)、[原 V](chain-07-check.json)、六份 events |
| chain-08 | fb39d14f14588bb2634f110b2a5a13d6187b4513；仅 counts-always-match，rc 2／预定 missing_raw_request_must_be_detected；cleanup=[]、fixture_removed=true，最终退出明细全确认；V rc 0／PASS、1 场 | [摘要](chain-08-summary-15.json)、[原 V](chain-08-counts-check.json)、counts events |

这是两个候选的组合证据，**没有同一新候选六场全重跑的记录**。主控 #117 按要求仅复跑 counts；逐场的延续性分析在 RESULTS 的“主控 #117”节。
079842e8b→fb39d14f1 的产品 src、app、hooks、依赖配置与 profile 未变。测试执行路径实际有两处收尾修改：gone 遇 EPERM 仍未确认并在原期限内等 ESRCH；all_exited 同时约束最终每条 group／child.exited。另有 V 的显式 --counts-only 选择、新局部反例及文档，不能写成整个版本区间只有一行变更。
旧五场的业务触发、注入、断言和产品代码未变，结论仍可用于这些相同行为；它们不是新候选早失败路径收尾已重新实跑的证明。新收尾另有 chain-08 实跑及 [限定复核](UPSTREAM-SHUTDOWN-REVIEW-02.md) 的 D／最终 writer 时序、删 group／child 条件变异。
审查者须独立判断这种跨版本证据边界；不将旧 chain-07 V 改成 PASS，不去掉候选绑定，不把两代结果传给同一 candidate 的 V 冒充全套通过。

## Acceptance 与当前证据

| 合同 | 当前观察与原件 | 审查重点 |
| --- | --- | --- |
| 红态：main 无正常登录入口，旧假 API 拒绝非假配置 | profile-red-01.json 绑定原 main，合同红态；profile-green-01.json 局部正例 | 红态拒绝是否源自业务合同，非环境失败 |
| 正常登录仍经 controller_start／原生 hook／Stop | chain-07 none 与 rehearsal-04；新 counts 也完成两次 hook／Stop 和一次 inbox 哨兵转交后才命中计数反例 | 不替换成旁路启动或合成成功事件；compiled fixture 不是供应商 CLI |
| 计数逐条先记后转，失败与重试均计数 | 各完整运行独立 U 两条 POST /v1/messages，分别 400／200；forwarder_raw_records 两 request、两 outcome；U 在接收时独立读 ledger，确认对应序号已存在 | 摘要中的数组来自原结果保存的解析副本，非仍在磁盘的 journal 原字节；不能冒称已删除夹具中的原文件仍存在 |
| 三个原反例与自带检查有效 | chain-07 home、scanner、drop、empty；none 中六种凭据注入和删序号 2 对账；chain-08 counts | 变异必须命中预定业务断言，不能靠 ENOENT、清理错误或空注入失败 |
| 用户 A 的 OS HOME 禁写 | 下节的实际拒写／独立不存在确认；合成 HOME 删规则变异 | 清单差异不作通过条件，不能因此放宽凭据、计数或清理 |
| 凭据不进证据或 Git | probe-10 扫描 0；产品链只用合成 auth，公开报告与 Git index 对本场合成值扫描 0，私有根／合成源删除 | 未重读真实 auth 做全 Git 历史扫描，不将结束时扫描扩大成所有时刻证明 |
| 地图与独立验收 | 本轮 status 0 problems／0 stale；新完整独立审查、Gate submit／验收／集成尚未完成 | 不以局部审查或 Git 提交替代 |

## 裁定 A：HOME 禁写与每个进程的 profile

依据用户在 main c06a73179 的裁定（主控 #79 转达）：**“OS 沙箱强制禁写真实 HOME，并有一个试图写真实 HOME 被拒的反例；前后清单照实报告，不作通过条件。”**
边界取 OS 账号真实 HOME，不用环境 HOME 代替。所有业务 profile 含 deny file-write* (subpath 真实HOME)，没有 repo/state/roles 位于真实 HOME 的写入例外；运行数据与工作区须在 HOME 之外。
macOS 已实测不允许嵌套 sandbox；C 只挂一层，后代继承，F/D/U 等平级单独挂 profile。

| 实际进程／阶段 | profile 与例外 |
| --- | --- |
| R 准备／精确 auth 读取 | 唯一单列的沙箱外准备阶段：原始 auth 精确读一次，file 或 Claude Code-credentials 指定钥匙串条目二选一，无枚举／fallback；只生成私有隔离副本。产品完整链为合成源，real_auth_reads=0。R 及脱离引导只作有界参数／FD／临时目录准备、exec，未保留无保护长期监督进程 |
| G0／G1／G2 只读 Git 检查 | G，禁写真实 HOME、禁网络、禁 Security；实际 PID 在每场 processes.G 和退出组里 |
| 原始 auth 读取前的清单进程 | D_baseline，禁写真实 HOME／网络／Security／fork，只读批准范围的目录/stat |
| 根 Node 测试驱动／daemon、PTY shell、编译假 CLI、clang、版本命令、hook／inbox／事实子进程、libproc helper | 同一个 C 或 C inherited；真实 PID、父 PID、角色在摘要 processes.C；禁写真实 HOME，有读取屏障；只允许 F 本地端口及本次 daemon Unix socket。保留所需 fork/exec，未给 CLI 外连权限 |
| Python F guards → exec Node F | 独立 F，禁写真实 HOME；只能写 forwarder 目录；禁 fork／Security；网络见下一节 |
| 长期 D／合成源清理拥有者 | 独立 D；四范围目录/stat；测试 D 仅另准本次 synthetic source-home 的 unlink，仍不能读认证正文。D 读回已 fsync 的 cleanup_pending 检查点后才删合成源；产品不删原始用户 auth |
| 假上游 U | 独立 U，禁写真实 HOME、禁 Security／fork／出站，只监听本场两个测试端口（配置上游及负例端口），不向真实接口转发 |
| S／M 写保护对照 | 独立 S／M，均保留真实 HOME 禁写；M 只删除合成 HOME 的禁写规则 |
| 独立结果核对 V | 自己的 V，禁写真实 HOME／网络／Security；signal 0 独立核对原登记组、子进程、报告者退出，不靠作者布尔字段通过 |

PID 级清单在 chain-07 none 和 chain-08 counts 摘要的 processes／writer_exit；其他运行的原路径也在清单。C 后代依 OS 继承和实际登记绑定 profile，不能把“C inherited”字符串单独当 OS 证明。
两场完整事实各有八个真实 HOME 独占新文件尝试：C 父、F Node、F Python、D、U、CLI、S、M，均 errno EPERM、created=false；D 对全部八个路径再确认不存在。不是尝试覆盖已有文件。
S 在合成 HOME 被拒；M 删该合成规则后独占新建成功、立即删除且记录 deleted=true／absent_after=true，并命中 home_write_must_be_denied。该变异证明检查能抓丢失的规则，**没有实际删掉真实 HOME 禁令去写真实 HOME**。
只读清单范围 .claude、.claude.json、.claude.json.backup、Library/Keychains；不读正文、不跟随链接、不比 atime 或校验值。报告 collection_complete、changed／differences 与 attribution；本场 changed=[] 只是观察，pass_condition=false，不推断其他会话写入归属。
C/F 只放行必要祖先的 file-read-metadata 供 Node 解析路径；同 profile 下 AGENTS.md 正文读取及真实 HOME 目录枚举仍 EPERM。不能把这些元数据例外解释为读取其他全局配置的许可。

## 转发层网络边界

源码入口：workbench/src/claudeLoginSession.py 的 policies／enter_cli／start_services，claudeForwarder.ts 与 claudeForwarderService.ts。F 是 C 的平级受保护进程，脱离调用者进程组，不嵌套 profile。
F 只监听所配本地 P，只出站到配置 upstream_url 的端口＋显式 upstream-address IPv4；HTTP 假上游必须是匹配的 127.0.0.1。真实配置可指向 api.anthropic.com:443，但无默认值、不写死 fallback、不自行查询 DNS／轮换地址；HTTPS 仍按 URL 主机名验 TLS。
F 先写原件并 fsync 再转上游，不保存认证头或请求正文；自身不重试／重定向，journal 写入失败停止转发。
C 的 TCP 只到 F 的 P，不能绕过 F；Unix IPC 仅本次 control.sock。D／G／V 无网络，U 无出站。
实际反例：F 连未配置端口 EPERM、额外监听 EPERM、写 forwarder 外路径 EPERM、fork EPERM；CLI 直连配置上游 EPERM。F→所配假 U 实际收发两次证明正例，相关收据和代码在摘要中。
没有真实接口流量、真实 DNS/TLS 验证或模型回合，不能由本地 HTTP 绿态外推这些结论。

## probe-10 的三条保留边界

1. [probe-10.json](probe-10.json)／[PROBE-10.md](PROBE-10.md) 只证明 2.1.302 的真实登录副本被识别、采用自定义地址且带复制的 bearer。走通依赖新建 hasCompletedOnboarding 与唯一当前 cwd 的 projects[路径].hasTrustDialogAccepted；均为内部状态，固定该版本，换版本重新核对。未复制用户 .claude.json，也没有自动业务按键。
2. onboarding 静态预检的两个 hello 候选直连 api.anthropic.com/api/hello、platform.claude.com/v1/oauth/hello，不经过 BASE_URL。正式启动须生成完成状态，事实检查 generated／state_intact 和终端／私有 debug 的可见预检迹象，C 禁止直连。preflight_observed=false **不能证明零连接尝试**；沉默的被拒尝试未测量，不把 F 接收计数冒充全部网络审计。
3. probe-10 两个 POST 都回 400，主控据此确认重试边界；每次请求（含失败／重试）单独计数。产品无模型全链另用 400→200 两次，F 不自行重试，不按一次输入合并计数。

## Panes.processInfo 的全 pane 产品变更

这是 T-093 全部产品差异的一部分，不能因本轮只改测试而漏审。旧 release spawn /bin/ps（本机 04755）在 C 下 EPERM；按主控 #105 的方案 b，统一改为 `/usr/bin/python3 -I -S -B processSnapshot.py PTY_PID`，helper 与原调用进程同 profile，5 秒／4 MiB 有界。
helper 通过系统 libproc 的 proc_listpids(PROC_PPID_ONLY)、proc_pidinfo、proc_pidpath 只遍历本 PTY 后代；不读 argv／环境／auth，不枚举全机，不另启动子进程。SDK ABI、出生时间／父子／组／TTY／路径复核、短数据／截断／权限错误／坏树拒绝均须审查；没有无保护 ps fallback。
leader 仍须 PID=PGID=TTY 前台组，内核路径等于启动边界捕获的 executable_path。实际 argv 不改；版本检查之后、PTY 之前确定规范路径，不在每次 query 重解析 alias。查询是多次内核读取，不宣称原子快照或未来存活保证。
真实 C/libproc 已由 rehearsal-04、chain-07 与 chain-08 达到；权限拒绝、身份替换和 alias 改指反例则是独立给定 native 缓冲／exec 边界的 L1 证据，不能把它们称为真实内核故障注入。

直接调用影响：daemon.ts 的 settleInboxFeedback、window assertCurrent、pane_process_info；panes.ts 的 sendGateFeedback、releaseByUser、interruptThread 前后两次、release、screenKey、caller/controller 两次、caller/worker、readThread，共 13 处。准确位置、业务及 T-078 补充回归在 [请求 13](REVIEW-REQUEST-T093-13.md)。
T-091 六 IPC（snapshot/input/composition-start/release-queue/focus-observation/output）、sender＋paneKey、独立凭据／sequence／cursor、iframe／跨窗／旧 launch 拒绝合同未变；IPC 11 项及历史反例、版本 8 项、T-078 runtime 11／relay 22 项通过，原件 t091-*regression、t078-*regression。它们的 Electron／进程 IO 边界是替身，不替代原生窗口和生命周期实跑。

T-096 集成风险仍开放：[ISSUE-T096-INTEGRATION.md](ISSUE-T096-INTEGRATION.md)。本分支没有恢复实现；原 d61876f 和本轮只读核对的 exec/t096@ef8bcd32db2dd801fb648506dc4f2409b63fa745 都在 recover(daemon) 中直接复用旧 record，缺 executable_path 时会被新 comparator 误拒。
集成拥有者须在原版本校验之后、恢复 PTY 之前建立运行时规范身份，保持不可变旧记录／完整原 argv，已有身份字段不得绕过目标一致性；更新测试的 ps 文本 IO 替身而保留旧记录、版本／session、缺 argv、兄弟隔离、worker 不恢复及原变异。不得固定 leader 为成功或改另一票 attempt 来绕过。
这阻塞跨票集成通过结论，不能以 T-093 假 CLI 绿态或 T-096 旧 PASS 关闭。本轮没有重跑原生 T-091／T-096，不宣布全 pane 非退化。

## 只读复核与停止条件

纯合成复核可用新输出运行；不读 auth、不启动服务／CLI／OS 进程查询：

```sh
node workbench/tests/test_t093_upstream_shutdown.ts /private/tmp/t093-r15-shutdown.json
node workbench/tests/test_t093_writer_exit.mjs /private/tmp/t093-r15-writer-exit.json
python3 -B workbench/tests/test_t093_counts_result_selection.py /private/tmp/t093-r15-selection.json
python3 -B workbench/tests/test_t093_upstream_prompt.py /private/tmp/t093-r15-prompt.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /private/tmp/t093-r15-t091-ipc.json
node --experimental-vm-modules workbench/tests/test_t091_claude_version.mjs /private/tmp/t093-r15-t091-version.json
node workbench/tests/test_t078_pane_runtime.ts /private/tmp/t093-r15-t078-runtime
node workbench/tests/test_t078_controller_relay.ts /private/tmp/t093-r15-t078-relay
```

复核须拒绝 EPERM 当退出、最终未确认仍删目录、空凭据变体、恒一致计数、漏记和包含匹配等坏实现；真实关闭仍要求收据＋原期限内 ESRCH、最终每行确认，V 再独立查询。
T-096 只可在两票受管集成候选运行 test_t096_restore.mjs、test_t096_daemon_restart.mjs、test_t096_process_probe.py；纯合同及三格／失败隔离原生重启命令、原材料与逐屏批准边界详请求 13，当前 worktree 不伪造其通过。
若需要重跑本机同 profile 链，交主控使用 EVIDENCE-RECHECK-03.sh／REHEARSE-CHAIN-01.sh 和新路径；只用合成 auth／编译假 CLI／本地假 U。不得启动真实供应商 CLI、读取真实认证或将真实模型作为验收补项。
任何必要事实缺失、跨票恢复未验证或候选变化均报告 INCOMPLETE；存在可复现违约则 NO_GO／FAIL。报告区分本票受限事实结论与整体集成结论，禁止把两者合成无条件 GO。
