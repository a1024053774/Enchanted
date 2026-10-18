STATUS: FAIL
TARGET: 788d75f4a75a861a7beb23f3f0ac97a6ecc70938；产品运行版本 57c3bfb634b6908be968fcb88090293ed5d4dd65；起点 617863704，合入 main 0e92f78ec 的提交为 64c6456de。
RELEASE: NO_GO

第三轮独立审查，2026-10-19。只读，没有实现、修复、子 agent、模型调用、真实凭据读取、升级请求、提交或门禁操作。审查结论由最新 main 的 T-093、T-092 六点决定、用户裁定 A 和本次派发的三项裁定重建；作者 RESULTS、请求和事实脚本仅用于定位。

FINDINGS:

**[P1] `workbench/src/panes.ts:245`：正常登录恢复的识别只依赖一个可缺失字段，缺字段即进入普通恢复路径。**

当前检查为 `record.authentication !== "isolated normal login"`。正常登录记录缺少 `authentication` 时，其他明确标记仍在：`role_card_revision="T-093/normal-login/2.1.302"`、`login_audit_directory`、`login_preflight_file`、正常登录的 env 和 shell 命令。恢复入口没有校验这些记录是否确实属于允许恢复的假 API 合同，也没有拒绝无法识别的认证类别。`store.ts:41` 保存 JSON，`:48` 直接反序列化；缺字段不会在存储边界被拒绝。

独立探针通过实际 `Panes.recover`、真实 SQLite 和原生会话文件运行，只替代 subprocess、PTY 和进程查询边界。完整标记正常登录为版本调用 0、PTY 0、`normal_login_restore_requires_protected_start`；缺认证字段的正常登录为版本调用 **1**、PTY **1**，产生 **`pane_restored`**，错误为空。假 API 与无认证字段的合法旧假 API 正例均正常恢复，全部历史 launch 未改写。

为排除手造记录形状导致的误报，另用冻结候选的实际 `claudeLaunch` 生成正常登录记录；补上首启阶段保存的版本和规范执行路径，再仅删除认证字段并加入无产品含义的观察标签。相同结果：`cli_calls=1`、`pty_calls=1`、恢复成功。没有执行 `/usr/bin/true` 或供应商 CLI；调用次数来自边界 spy。此证据证明恢复合同被绕过，不宣称观察到真实 HOME 写入或凭据泄漏。

复现：

```sh
node /private/tmp/t093-r03-uj4pu1e0/generate-normal-record.mjs
node --experimental-vm-modules /private/tmp/t093-r03-uj4pu1e0/restore-independent.mjs \
  /private/tmp/t093-r03-uj4pu1e0/candidate/workbench/src/panes.ts \
  /private/tmp/t093-r03-uj4pu1e0/out/另选全新结果.json \
  /private/tmp/t093-r03-uj4pu1e0/out/generated-normal-record.json
```

第一条已运行，已有独占输出，不应原样重复覆盖；复跑恢复探针只需第二条。原件 `restore-independent.json`、`restore-generated-valid-session.json` 均退出 2，明确违反“正常登录在任何 CLI 前拒绝”。中间 `restore-generated-input.json` 因合成 native metadata 的 cwd 不匹配而在版本之后拒绝，保留为工具诊断，不冒充完整恢复正例；修正夹具后才取得上述完整反例。

最小修正归恢复入口：在任何 CLI 执行之前，可靠地区分正常登录、可恢复假 API 和无法识别的记录；缺一条字段不能把正常登录降为普通恢复。保留合法旧假 API 正例，不靠一律拒绝旧记录、删除正例、固定 leader 或放宽版本/session 达成。候选的 `test_t096_restore.mjs:102` 只给两个正常登录样本加完整认证字段，当前全绿不能覆盖本反例；须补缺字段输入，并在版本和 PTY 两边界断言 0。本 reviewer 未实施修正。

EVIDENCE:

## 按合同逐项核对

| 必审项 | 判断与独立依据 |
| --- | --- |
| 第二轮非 loopback 编译问题 | **PASS，旧阻点关闭。** 直接读取 `/private/tmp/t093-r18-compile-01.json` 四个编译结果：生产 443、测试 18443，127.0.0.1 与文档 IPv4 输入均编译成功、diagnostic 为空。原 profile 只有 `remote tcp4 "*:端口"`。源码 `claudeLoginSession.py:92–123` 为同一生成器，没有测试端口分支；`:453` 生产显式固定 443。局部 10 项另验证随机测试端口、非 443/显式 0 拒绝与仅端口差异。 |
| 应用主机锁、重定向、Host、DNS | **PASS，限所审边界。** `claudeForwarder.ts:98–110` 剔除 Host，使用构造时保存的 URL/hostname/IPv4；传输前拒绝主机漂移，lookup 再核对主机并只返回给定 IPv4。没有系统 DNS 回落、重定向处理或自行重试。实际 handler 的五项 supplied-transport 检查通过：正常、Host 篡改、目标漂移、lookup 错主机、302 不追随；去掉预连接检查的变异在业务断言失败。真实 DNS/TLS/官方接口未测试。 |
| OS 非允许端口拒绝与 HOME | **PASS，限原件覆盖。** 八场实际 F 的其他活端口均 `EPERM`；测试出站仅 18443，生产 profile 编译仅 443。C 直达 U、F 另起 listener/fork/越界写均有拒绝记录。实际 HOME 独占创建被拒、未创建，D 核对探针路径不存在；合成 HOME 删禁令对照验证检查有效。**OS 层不再按主机限制。** HOME 前后清单仅报告，八场差异为 0 不参与通过条件，`pass_condition=false`。 |
| 正常登录不恢复 | **NO_GO。** 完整认证字段的两种正常登录记录确实在版本/PTY 前拒绝，即使 session 缺失也为 0；单字段缺失反例仍执行 CLI 并成功恢复，见 P1。第二轮 P1 只关闭了完整字段路径，未完全关闭。 |
| 恢复运行时身份 | **PASS，独立于上述认证分类缺陷。** `panes.ts:262–280` 保留版本与原生会话核对，再用完整 argv[0] 的 realpath 建立运行时副本，随后启动 PTY。已有规范身份不同则拒绝；历史不写回。实际局部合同的两个 legacy 正例、匹配/改变身份、完整实际 shell argv、实际观察 leader、worker 不恢复和 attempt 不变均通过。七场原生材料另核对内核 argv 与进程事实。没有把新记录的原生场次冒称缺 executable_path 的旧记录正例。 |
| libproc 影响全部 pane | **PASS，所列回归范围。** 逐项审阅 14 个调用点，包括 recover、反馈、用户放行、中断前后、release、screenKey、主控 hook/Stop 两次、worker caller/readThread、daemon 反馈/window/pane_process_info。`processInfo` 的 exec、解析、schema、重复树及脱离根的行均失败传播；leader 仍要求 PID=PGID=TTY 前台组且执行路径等于首启/恢复前捕获的规范路径。helper 的出生秒/微秒、父/组/前台组在前后及最终遍历重查，权限错误、短数据、截断与身份变化不转为空成功；明确退出/僵尸才排除。观察器 11、ABI/树/缓冲区 23、alias 2、T-091 IPC 19/版本 8、T-078 runtime 11/relay 22 均通过。局部 IO 替身不等于全部原生 T-078 场景重放。 |
| 凭据 | **PASS，限源码与格式扫描。** 生产 `prepare:183` 唯一一次 `read_auth` 在受保护基线之后；显式来源，无枚举/重试/切源。`claudeLoginFiles.py:83–87` 精确读取 `Claude Code-credentials` 和指定 login.keychain-db，stdout 只进内存，复制 OAuth 到私有 0600 文件。R 在 C/F/D 外；security 本身仍有只读、无网络、禁 fork profile。“沙箱外”不能写成 security 完全无沙箱。历史 probe-10 的 `-w` 读取退出 0、两条本地请求 bearer 匹配、扫描 0、隔离根删除；另一次不带 `-w` 的精确存在性查询不读取密码。本轮未重读任何真实凭据。 |
| 已知限制 | **PASS，披露明确。** RESULTS/README 明写 OS 不按主机过滤、正常登录不自动恢复、2.1.302 的完成 onboarding/唯一 cwd 信任内部状态、官方 hello 绕过 BASE_URL、可见预检信号不代表零尝试、400 后 CLI 重试逐条计数。恢复限制的实现不完整另列 P1；本轮未将文案披露当作实现通过。 |

## 主控原件、版本延续和直接 runner

独立脚本 `/private/tmp/t093-r03-uj4pu1e0/audit-originals.py` 实际执行退出 0，保存 `out/original-evidence-audit.json`。读取 146 份 JSON/命令输出；另核对八条事件流，保存 `event-publication-audit.json`。没有采用作者 SUMMARIZE/CHECK 脚本的输出作为答案。

OS 八场全部绑定 57c3bfb63。演练 primary 的主失败是 `rehearsal_primary_probe`；green 与 none 真正通过。chain-11 的五个坏实现分别以 HOME 引用、凭据扫描、漏行对账、首条漏记、空注入集合的指定业务断言失败。每场 cleanup 两类列表为空，fixture 已删除，每条 group/child 退出均确认，U 监听数与关闭数相符。事件流在 cleanup_pending、fixture_removed=false 时已记录主失败，末尾未被清理覆盖。真实 V 的 rehearsal 两场、chain 六场均 PASS；历史 PID 不在本轮重新 signal 查询，避免把 PID 复用后的状态当原时刻证据。

原件中的逻辑转发记录独立重数：正常场次 request 序号 1、2，outcome 为 400、200；独立 U 收据两条，且其接收时已有对应持久记录。drop 的缺记录与预定失败相符。保存的是 JSON 中的逻辑记录，不冒称仍有被删除夹具的 journal 原始字节文件。未读取认证头值或请求正文。

T-096 原始七场逐项核对：

| 场次 | 独立观察 |
| --- | --- |
| tracer | 同原生 session、完整 event/内核 argv、真实 leader/规范路径、原 launch 不变、历史 nonce 可见；显式关闭后归档开窗数 0。 |
| three | 两主控恢复；worker 显示未恢复/只读、无恢复成功事件、receiver 只有最初一份；attempt 不变。 |
| no-argv / version / no-session | 各为原指定拒绝码，无成功事件，界面未恢复且只读；归档仍保留对应打开记录。 |
| isolation | ideation 缺 argv 被拒，executor 完整恢复；worker 与 attempt 不变。 |
| empty-reopen | 第三个真实窗口 panes/keys 为空，saved=true；归档最终打开集也为空；task/attempt 的既有检查均在原收据中通过。 |

七份 run.json 的 revision 都是 57c3bfb63，model_turns=fake_posts=0，cleanup_complete=true，无 cleanup diagnostics/handoff。不是仅查看 status：直接核对外置盘的 before/after、initial/resumed 内核 argv、processInfo、launch_show、恢复事件、实际窗口与 nonce。最终布局只复制停止归档的 state.sqlite3 及存在的 WAL/SHM，到本轮私有目录后 query_only 查询 orchestration_events 中的布局事件；没有打开原 DB 连接、checkpoint 或访问认证表。原件尺寸/mtime 前后相同。

对 (b)：`git diff 57c3bfb63 788d75f4a -- workbench/src workbench/tests workbench/app workbench/hooks workbench/package.json workbench/package-lock.json` 为空。后续差异是证据、README 和 T096 wrapper 的一行输出路径；不会使这些运行结论失效，也不会修复本轮缺字段 P1。

对 (c)：独立比对七份实际 argv、archive replay 和 wrapper 七种模式；panes、fault、check-close、check-empty-reopen、expect、CLI 2.1.302、等待 600 秒全部吻合。wrapper 没有额外业务断言；其 source/HEAD/dirty、外置盘及新输出保护由 runner 自身检查、原 revision/frozen_source 收据和本轮源码差异核对覆盖。直接 runner **没有漏掉业务断言**。修正后的 wrapper 未原生重跑这一限制仍如实保留，不能记成它的七场新运行。

COUNTEREXAMPLE:

一次性副本来自 `git archive`，位于 `/private/tmp/t093-r03-uj4pu1e0/candidate`，没有 worktree。node_modules 只引用已有依赖。三个单处产品变异各先取得相同入口的未改对照；没有用超时、ENOENT 或清理异常充当业务拒绝。

| 单处错误实现 | 未改对照 | 变异结果 |
| --- | --- | --- |
| 正常登录检查移到版本探测之后 | restore-control.json PASS，完整字段正常登录两边界 0 | mutant-late-restore.json，退出 1；`Normal-login restore must stop before version, identity and PTY boundaries`，明确观察到 version 调用。 |
| 预连接主机比较改为 false | host-control.json 五项 PASS | mutant-no-host.json，退出 2；`non_configured_host_must_not_connect`，错误目标开始连接；其他四项仍通过。 |
| 仅非 443 生成结果追加 allow network* | port-control.json 十项 PASS | mutant-test-relax.json，退出 2；18443 和独立 52321 输入均以 `same_generator_must_change_only_the_remote_port` 拒绝；443 正例仍通过。 |

精确命令记录在 `out/local-commands.json`，核心可重放入口如下；每次换全新结果路径：

```sh
node --experimental-vm-modules /private/tmp/t093-r03-uj4pu1e0/candidate/workbench/tests/test_t096_restore.mjs 新结果.json /private/tmp/t093-r03-uj4pu1e0/mutants/panes-late.ts
node --experimental-vm-modules /private/tmp/t093-r03-uj4pu1e0/candidate/workbench/tests/test_t093_forwarder_host.ts 新结果.json /private/tmp/t093-r03-uj4pu1e0/mutants/forwarder-no-host.ts
python3 -B /private/tmp/t093-r03-uj4pu1e0/candidate/workbench/tests/test_t093_forwarder_port_policy.py 新结果.json /private/tmp/t093-r03-uj4pu1e0/mutants/profile-test-relax.py
```

这些变异被拒不代表完成条件已充分：缺认证字段的输入反例仍通过当前产品，正是本轮 NO_GO 的原因。

## 结构、扫描与审查边界

按 design-integrity-review 定位 src 增量的 55 个结构标记后审阅真实 caller/所有权。没有确认额外的吞异常成功、DNS fallback、重试、平行 API 或第二套门禁。转发器将记账/传输错误变成明确失败和 journal_failure；私有 auth/helper 只输出固定错误以免泄露；清理未知状态保留失败而非构造完成。`inet_pton` 的 OSError 分支区分域名和 IPv4，没有改换地址。ClaudeLogin、转发器和 libproc helper 分别拥有生命周期、先记后转和 OS 查询，符合 **Deep modules**；本轮确认的结构缺陷是恢复入口把无法识别的认证记录默认为可普通恢复。

已审 **Tracer bullet** 是现有 controller_start → 私有 HOME/本地转发 → PTY/hook/Stop → 转交/事实/清理；没有实现新切片。**Ubiquitous language** 沿用启动记录、原生会话、attempt 和未恢复，不用进程存在或作者自报代替验收。

`git log --format='commit %H' -p 617863704..788d75f4a75a861a7beb23f3f0ac97a6ecc70938` 在内存扫描 85 个提交，OAuth access/refresh、API key、JWT、长 bearer 五类特征 **0 命中**；仅保存类别/位置/计数于 `history-scan.json`，不输出疑似值。它不证明未知编码/格式或真实 token 原值从未出现。本轮没有读取真实 auth、钥匙串正文或全局配置。

局部验证的初次 archive 请求含不存在文件、系统 Python 3.9 不支持 filter、以及 archive 内 hook 链接预检查，均在提取前失败，诊断单独保留；随后只提取核对过的普通成员。临时测试路径迁移曾破坏 T-091 版本测试的既有根前缀，原 INCOMPLETE 保留；恢复该测试原始字节后以新输出通过 8 项。以上是审查工具问题，不算产品红态。候选生产源码从未更改。

LIMITATIONS:

- 本轮新运行是 L0/L1/真实本地 SQLite 和 SDK 编译；OS 与原生 UI 结论来自主控在相同产品源码上的留存原件。没有重跑供应商 CLI、真实 auth、官方 DNS/TLS 或真实模型，没有以无模型链宣称真实接口已连通。
- `REVIEW-OUTSIDE-04.sh` 提供可选的新 F 编译与生产 443 profile 对活跃非 443 端口的 OS 拒绝补证；只用临时本地 listener，无 auth/CLI/模型，固定当前 SHA。已通过 bash -n 和嵌入 Python AST 检查，**未执行**。既有 r18 原件已支持对应历史结论，无需为确认上述 P1 申请升级或重新跑整套原生场次。
- 所有新产物在本轮 `/private/tmp` 目录；仓库只新增本报告和指定脚本。既有未跟踪原件/脚本保持不动。开始与收尾 project-map 均为 0 problems、0 stale living docs；HEAD 保持完整候选 SHA。没有 submit/acceptance/integration 结论。

RULE:

这延续了第二轮“正常登录从普通恢复路径执行 CLI”的失败类别。应由恢复入口的完成检查在实际 recover 上加入认证字段缺失的正常登录记录，保留其他正常登录标记、合法版本/session 与假 API/legacy 对照，独立记录版本/PTY 调用次数，并要求两者为 0、明确未恢复且历史不变。该可执行检查应随 `test_t096_restore.mjs` 运行；补文字规则不能替代它。修复后须绑定新冻结候选复核，不能沿用本报告的其他 PASS 给新候选整体背书。

T-093 REVIEW NO_GO
