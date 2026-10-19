# T-093 修订网络边界与 main 恢复兼容交接 16

此请求已由 [请求 18](REVIEW-REQUEST-T093-18.md) 取代。主控 #126 在 7bba61000 上取得 compile PASS；primary／green 因 U 无法监听 443 而失败，后续未跑。以下保留为当时的命令与判断条件，不在新候选上继续使用 r17 输出名或要求本地 443 空闲。

**INCOMPLETE：主控 #125 的正常登录恢复拒绝已落实，网络／规范身份修正及局部红绿完成；新 OS profile／无模型链、T-096 原生七场尚未执行。**
原组合阻点 [普通 daemon 恢复正常登录记录的 profile 缺口](ISSUE-NORMAL-LOGIN-RESTORE-16.md) 已由主控 #125 收窄处理：正常登录记录在任何 CLI 命令前标为“未恢复”，返回 normal_login_restore_requires_protected_start 并提示经正常登录入口重启；不重建 R/F/D/C、不扩大 T-096。独立旧探针红态、同探针绿态、零版本／PTY 与历史不变／假 API 正例见 [NORMAL-RESTORE-17.md](NORMAL-RESTORE-17.md)。下面七场仍只核对假 API 的原生恢复。
候选绑定最后 `T-093 FROZEN <完整 SHA>`。本次基线为主控完成的合并 64c6456de2b7c0111628defce442d999a26734db，包含 main 0e92f78ec6824265cdfcbb9387ba4b454d7eee7f（含 T-096 fd5c93e6e）；无冲突。task T-093 / attempt a1；worker s16-t093，session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
不 push、不 rebase、不改门禁／地图或验收状态；Git 冻结不代替 submit、验收或集成。本票不启动真实模型，仍须用户合入后另说开工。
首轮限定审查 [NETWORK-RESTORE-REVIEW-01.md](NETWORK-RESTORE-REVIEW-01.md) 对 e1177a02d 报 FAIL，确认交接脚本在 Bash 3.2 的 verify-six 空数组错误。现改用位置参数；outside-wrapper-red-01／green-01 用实际系统 Bash、exec 参数哨兵验证七分支，不调用 Python／OS profile，V 六场要求未变。
一次针对性复核 [NETWORK-RESTORE-REVIEW-02.md](NETWORK-RESTORE-REVIEW-02.md) 对 8771ba58d 报 FAIL：原 Bash P2 已关闭，独立确认正常登录恢复 P1。报告原文不改。此次按 #125 新裁定修正该入口拒绝；不沿用旧审查作为新修正通过证据。
冻结前检查见 freeze-checks-34.json，独立审查后归档见 freeze-checks-35.json；freeze-checks-33.json 保留旧 NO_GO。地图为 0 problems／0 stale，主控第二轮审查原件不改；不补称新 OS 或原生恢复已运行，尚无 submit／验收／集成收据。
新限定独立审查 [NORMAL-RESTORE-REVIEW-17.md](NORMAL-RESTORE-REVIEW-17.md) 对代码候选 91cd22d523af28ab9a13631d6919635be430ba34 的 #125 合同给出 PASS，无 finding；独立新输入验证正常登录零版本／PTY、明确未恢复、历史不变与假 API／legacy 恢复正例，旧 8771ba58d 被业务断言拒绝。最终归档候选与它的产品／测试相同。下面所有命令的 candidate 必须填本轮末行完整冻结 SHA，输出已换成 r17／chain-10；先编译与 primary，再逐项继续，不覆盖旧结果。

## 事实、授权与边界变化

第二轮独立审查 [independent-review-02.md](independent-review-02.md) 和 [REVIEW-OUTSIDE-03.sh](REVIEW-OUTSIDE-03.sh) 按原字保留。主控实际编译旧 F：127.0.0.1 成功，203.0.113.31 失败，报 host must be * or localhost；摘要 [profile-compile-review02-red.json](profile-compile-review02-red.json)。这是确实阻断真实上游的编译红态，不是 mock 推断。
主控 #121 修订其 #17 裁定，构思主控在 #122 确认符合 T-092 决定：**OS 层不再按主机限制**。F 的 OS 出站仅允许 `remote tcp4 "*:443"`；主机锁定由应用完成，其他端口仍禁，C 仍只能访问 F 的本地端口及指定 Unix socket。不能继续宣称 OS 只准配置的主机。
prepare 在 auth 读取、服务启动前拒绝非 443 上游。测试仍用 HTTP 明文 loopback，但端口固定 443；生产 HTTPS 的 TLS 按配置 hostname 校验证书，应用只返回配置 IPv4，不做 DNS／fallback／地址轮换。F 的监听端口 P 和记录目录规则、HOME 禁写／读取屏障、Security／fork 禁令不变。

## 产品修正与反例

claudeForwarder.ts 在构造时捕获配置 hostname，先记 request 并 fsync；transport 前发现目标漂移则记录 `upstream_host_mismatch` 并拒绝。lookup 也核对 hostname，再只给 pinned IPv4；入站 Host 过滤及不跟随重定向的原行为保留。
两个检查各有实际作用：IP 字面量会跳过 Node lookup，因此 transport 前也须拦截；lookup 的错误也须作为固定业务类别写 outcome，不能静默放过。类内部字段固定为配置值，不允许请求选择主机。
[forwarder-host-red-02.json](forwarder-host-red-02.json) 是同一真实 handler／给定 transport 的五场检查跑旧产品；[green-02](forwarder-host-green-02.json) 验证配置目标、忽略入站 Host、拒绝非配置 IP、拒绝非配置 lookup 名、不跟随 302。分别删 transport 前／lookup 校验的 [变异](forwarder-host-mutant-01.json)、[变异](forwarder-lookup-mutant-01.json) 均命中 `non_configured_host_must_not_connect`。没有对 127.0.0.2 或假域名发网络请求。
[端口红态](forwarder-port-red-01.json)／[最终绿态](forwarder-port-green-02.json) 只证明真实 policy 构造与提前拒绝非 443（包括显式 0）；**不证明 macOS 编译／权限执行**。显式 0 曾被旧 `or` 默认成 443，边界红态 port-zero-red-01 保留，现只给未声明的 HTTPS 端口默认 443。OS 负例由下方同 profile 实跑，F 连一个活跃的非 443 本地端口必须 EPERM；该事实现在叫 non_443_port，不再用旧名字暗示按主机隔离。
preflight／结束事实新增 network_boundary：os_host_filter=false、os_remote_ports=[443]、application_host_lock=true。缺字段的 [业务红态](network-fact-red-01.json) 与 [实际 preflight 绿态](network-fact-green-02.json) 保留；这些是策略描述，不是逐连接网络审计。

## T-096 恢复兼容

合并后的恢复仍用旧 record，和 processInfo 所需 executable_path 不兼容。同一实际 recover／SQLite／native 文件夹具给定合法版本、session 和内核 JSON，旧源码报 restore_process_missing，见 [red-03](t096-restore-red-03.json)。早期 red-01/02 另有 PTY 替身缺 kill 的次要错误，保留原件，最终 red-03 已补齐该 IO 边界，不能用它遮盖根因。
panes.ts 在原 argv／task／版本／native session 核对之后、PTY spawn 之前 realpathSync(argv[0])；已有 executable_path 时要求一致。只有 runtimeRecord 副本新增规范路径，历史 launch record 和完整 argv 不动，原 resume 选择器规则不变。leader 仍来自实际 processInfo，无固定 leader，也没有跳过版本／session。
test_t096_restore.mjs 保留两个合法旧记录正例，另跑已有身份匹配／改变；核对顺序 version→canonical→spawn、历史记录不变、原 argv 逐字段、旧 worker 不恢复／attempt 不变、失败兄弟隔离与最终空布局。subprocess 提供 libproc JSON，virtual realpath 提供别名目标，PTY／clock 为给定边界，不调用真实内核或 CLI。
最终 [t096-restore-final-01.json](t096-restore-final-01.json) 保存三类身份模式；历史 worker 反例、实际 PTY argv 被缩短、身份校验删除、恢复 leader 被硬设为 1 均被业务断言拒绝。它不是原生重启回归，不能替代下方七场。
合并后 T-091 IPC 19 项（含明确空布局与重复重开）、版本 8 项、observer 11 项、alias 2 项、T-078 runtime 11／relay 22、T-096 daemon 7／进程 probe 11／argv 材料 5 的局部回归通过。小原件均在本目录；无真实进程查询／Electron。
若下方 T-096 原生回归失败或 INCOMPLETE，保留现场，交主控按 #122 裁定重开 T-096；本 worker 不自行改另一票的验收、自动重试或绕过初始化。

## 保持的四条底线

- 用户裁定 A：真实 HOME 全目录 OS 禁写；独占新建不存在路径的实际拒写及 D 再确认不存在仍是新链必验项，清单差异仅报告、pass_condition=false。合成 HOME 删规则变异必须真的创建、删除且被业务断言拒绝；不去掉真实 HOME 禁令。R 的有界准备／一次精确 auth 读取例外、C/F/D/G/U/S/M/V 的 profile 身份及关闭 FD 规则不变。
- probe-10：2.1.302 内部 onboarding／唯一 cwd trust 状态换版本须重核；两个官方 hello 候选绕过 BASE_URL，必须避免触发并报告可见迹象，沉默的被拒尝试未测量；400 后重试逐条计数。转发原件不等于全网络审计。
- 全 pane libproc：13 个现有直接调用及 T-096 recover 仍走同一个查询；规范可执行路径、PID/PGID/TTY 与出生时间复核不变。T-091/T-078 窗口、队列、hook/Stop、版本／身份合同未放宽，详请求 13；本次只在恢复边界补运行身份。
- 请求先记后转、失败／重试分别计数，三原反例、空变体、首条漏记及恒一致计数变异不变。主失败先发布，清理错误单列；收据＋原期限内 ESRCH、最终每条 writer 确认才删除；凭据／正文不进证据、Git 或终端。

旧 chain-07/08、rehearsal-04 只绑定旧产品；新 F 权限、事实字段和 main 组合不能沿用它们的通过。旧 standalone parallel probe 也仍是原 localhost 权限方案，不能替新 F 作 OS 证明。

## 主控沙箱外：先编译，再新无模型链

每步独立调用，输出均须不存在，不覆盖旧结果。设置实际冻结 SHA：

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本次完整冻结SHA
osrun="$repo/evidence/2026-10-16-batch16/T-093/T093-OS-16.sh"
bash "$osrun" compile "$repo" "$candidate" /private/tmp/t093-r17-compile-01.json
```

要求 rc 0／PASS，loopback 和 203.0.113.31 都能编译，报告 OS_host_filter=false、仅出站 443。此命令只调用编译器，不应用 sandbox、不联网、不读 auth；任一不符即停。

```sh
bash "$osrun" primary "$repo" "$candidate" /private/tmp/t093-r17-primary-01.json
```

期望 rc 2／INCOMPLETE，但 primary 恰为 rehearsal_primary_probe、两次 U 收据／精确 JSON、应用主机负例、OS 非 443 拒连及 CLI 直连 U 拒绝全部成立；cleanup=[]、fixture_removed=true、最终 writer 每行确认。其他失败即停。
U 独占监听本地 443，若被占用或权限不足，会报 fake_upstream_listener_unavailable 及 errno；不换端口、不复用别人 listener、不申请 root。所有请求只在实际 U 成功绑定、写本场 ready 后才会发出。

```sh
bash "$osrun" green "$repo" "$candidate" /private/tmp/t093-r17-green-01.json
bash "$osrun" verify-rehearsal "$repo" "$candidate" /private/tmp/t093-r17-rehearsal-check-01.json /private/tmp/t093-r17-primary-01.json /private/tmp/t093-r17-green-01.json
```

两项均须 rc 0／PASS 后再逐场运行正式六场；每场须核对预定主失败及完整清理，失败不同即停，不连续盲跑：

```sh
bash "$osrun" none "$repo" "$candidate" /private/tmp/t093-chain-10-none.json
bash "$osrun" home-references-empty "$repo" "$candidate" /private/tmp/t093-chain-10-home.json
bash "$osrun" scanner-zero "$repo" "$candidate" /private/tmp/t093-chain-10-scanner.json
bash "$osrun" counts-always-match "$repo" "$candidate" /private/tmp/t093-chain-10-counts.json
bash "$osrun" drop-first-record "$repo" "$candidate" /private/tmp/t093-chain-10-drop.json
bash "$osrun" empty-credential-cases "$repo" "$candidate" /private/tmp/t093-chain-10-empty.json
bash "$osrun" verify-six "$repo" "$candidate" /private/tmp/t093-chain-10-check.json /private/tmp/t093-chain-10-none.json /private/tmp/t093-chain-10-home.json /private/tmp/t093-chain-10-scanner.json /private/tmp/t093-chain-10-counts.json /private/tmp/t093-chain-10-drop.json /private/tmp/t093-chain-10-empty.json
```

none 为 rc 0／PASS；其余 rc 2、预定主失败依次为 home_path_injection_must_be_reported、credential_injection_must_be_detected、missing_raw_request_must_be_detected、forwarder_record_count_must_match_upstream、credential_injection_cases_must_not_be_empty；每场清理完整，V 为 rc 0／PASS。JSON 与同名 events 全保留。

## 主控沙箱外：T-096 七场

仅使用本次冻结、全新标签和外置盘输出。沿用原 T-096 初始化流程，每个原始屏幕单独 capture／批准／key；trust 后另批 startup-ready，原六键／空队列放行规则不变。下面命令本身不批准 Enter、信任或登录，不预置 onboarding/trust 状态；同一时刻最多一个 Electron，模型／POST 预算 0。
`cli` 填已核对的真实 2.1.302 规范路径，`approval` 填本次运行授权位置。先 tracer，完整通过再 three／四个故障／empty-reopen；任何失败停止并交主控重开 T-096。

```sh
resume="$repo/evidence/2026-10-16-batch16/T-093/T096-REGRESSION-16.sh"
cli=/已核对的Claude_Code_2.1.302可执行文件绝对路径
approval=主控本次运行授权位置
bash "$resume" tracer "$repo" "$candidate" "$cli" "$approval" t093-r17-tracer-01
bash "$resume" three "$repo" "$candidate" "$cli" "$approval" t093-r17-three-01
bash "$resume" missing-argv "$repo" "$candidate" "$cli" "$approval" t093-r17-no-argv-01
bash "$resume" version-mismatch "$repo" "$candidate" "$cli" "$approval" t093-r17-version-01
bash "$resume" missing-session "$repo" "$candidate" "$cli" "$approval" t093-r17-no-session-01
bash "$resume" isolation "$repo" "$candidate" "$cli" "$approval" t093-r17-isolation-01
bash "$resume" empty-reopen "$repo" "$candidate" "$cli" "$approval" t093-r17-empty-reopen-01
```

原件写 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-093/<label>`，盘未挂载报错，不回退。沿用的 runner 会在 evidence/T-096 写本次新 label 的 run/archive 文本摘要，不覆盖旧标签／attempt；由主控运行和收取这些原件。
要求实际 argv 逐字段相同、同原生 session／历史 nonce、版本相符、失败兄弟隔离、worker 未恢复／attempt 不变、无模型／fake_posts=0、cleanup_complete=true。empty-reopen 还须第三个真实窗口保持空 DOM／pane keys／saved=true 且 panes=[]，不能新增 worker 或凭据。
具体逐屏命令及预算沿用 [T-096 RUN-RESTART](../T-096/RUN-RESTART.md)；缺批准、超时或退出不明只保留 INCOMPLETE，不补按键或重复退出，不把旧 T-096 PASS 当本次回归通过。
