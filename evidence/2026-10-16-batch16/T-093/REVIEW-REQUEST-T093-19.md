# T-093 第三轮独立审查请求

**READY-FOR-REVIEW；整票状态 INCOMPLETE，待第三轮独立审查及唯一门禁验收／集成。** 本请求提交给执行主控安排全新只读 reviewer，不用 worker 的事实复核代替独立审查。task T-093 / attempt a1；worker s16-t093；session 67f986cc-92e4-4089-9c22-802a1143b645、native 01a14ae2-a3df-7731-a7b0-1b679b3bce95、launch-45148b6732394eccab3b21224b238513；执行配置 codex-cli 0.163.0／gpt-6.1-sol／xhigh，不把配置当作供应商实际 tier 证明。

冻结候选为本轮末行 `T-093 READY-FOR-REVIEW <完整 SHA>`。运行证据绑定 57c3bfb634b6908be968fcb88090293ed5d4dd65，本轮 **workbench/src 与 workbench/tests 未变**；T096-REGRESSION-16.sh 仅改一行 output 前缀 T-093→T-096，与主控实际通过的直接命令一致。其余新增均为证据核对／文档。旧 source/worker 候选与旧 FAIL 报告不改、不代替新审查；不 push、不 rebase、不改门禁／地图／验收文件或全局配置。本票不跑真实模型，合入后仍须用户另说开工。

## 必须覆盖的行为

1. **两层网络限制。** 生产 R 入口显式要求上游端口 443，没有端口覆盖 CLI 选项；F 的 OS 规则为 TCP `*:443`，**OS 层不再按主机限制**。F 应用层固定配置 hostname／IPv4，连接前和 lookup 核对、拒绝不符并记账；不跟随 redirect、不接受入站 Host 改目标、无 fallback。CLI C 只允许转发层本地端口，直接访问上游被拒。无模型链用同一个 policies(session) 生成 18443，编译逐字比较仅端口不同；实跑另一个活端口被 OS 拒绝，应用主机反例不联网。不得把测试端口实跑外推成真实上游 443 连通性。
2. **正常登录不恢复。** 按主控 #125，recover 在任何 CLI 命令（含 --version／PTY）前识别 authentication="isolated normal login"，保留为未恢复，错误 normal_login_restore_requires_protected_start，提示从正常登录入口重新启动。即使提供上下文标记也不续接，不读 auth；完整 R/F/D/C 恢复另票。假 API／合法旧记录恢复不退化，worker 不恢复／不改 attempt。
3. **运行时身份。** 版本和 session 核对后、PTY 前由完整 argv[0] 的 realpath 建立 runtimeRecord 的 executable_path；历史 record 不写回，已有规范身份改变即拒绝。不得删合法旧记录正例、截 argv、硬塞 leader、跳过版本或 session。原生七场核对保存的内核 argv、进程／session、任务／角色、原 launch 和历史 nonce；正常登录拒绝另有独立 L0/L1 证据，七场 fake API 不替它背书。
4. **libproc 对所有 pane 的影响。** Panes.processInfo 从 setuid ps 改为 Python libproc helper，不是 T-093 专用路径。审查 helper 的错误传播／树与前台组／唯一规范执行文件，以及所有 14 个直接调用；临时 helper 不可当 leader、未知结果不可放行。不能只看“正常登录链通过”。下表与 T-091／T-078／T-096 回归需一起核对。
5. **证据与收尾。** 请求先逐条持久化后转发，400→200 重试两条都计入；真实 HOME 全目录 OS 禁写、独占不存在文件的拒写与事后不存在、合成 HOME 删规则变异、只读清单按裁定 A 仅报告。凭据／正文不入 Git／日志；R 的原 auth 一次精确读取例外不扩为其他条目。U 零／部分监听也有关闭收据，错误收据／EPERM／活进程不当退出；主失败先落盘、清理错误单列，写入者逐项退出后才删整根。原三个反例、空凭据变体、首条漏记及恒一致计数变异不放宽。

| processInfo 调用点 | 受影响行为 |
| --- | --- |
| panes.ts:302 recover | 恢复后真正找到原 CLI，不能仅有 shell |
| panes.ts:598 sendGateFeedback | worker／主控反馈队列身份 |
| panes.ts:758 releaseByUser | 人工声明空框后的队列放行 |
| panes.ts:781、786 interruptThread | 中断前与写入前两次身份核对 |
| panes.ts:804 release | 初始化放行 |
| panes.ts:846 screenKey | 启动按键的前台／原屏幕绑定 |
| panes.ts:991、996 caller/controller | hook／Stop 的首次与执行前核对 |
| panes.ts:1008 caller/worker | 受管 worker 活动身份 |
| panes.ts:1015 readThread | worker 存活、结束与替换 |
| daemon.ts:38 settleInboxFeedback | 延迟反馈的会话／leader 重查 |
| daemon.ts:161 window assertCurrent | 窗口输入、composition、放行身份 |
| daemon.ts:264 pane_process_info | 对外进程事实命令 |

T-091 IPC 六合同仍为 snapshot、input、composition-start、release-queue、focus-observation、output：单次注册、sender＋pane key 分流、各窗口 sequence／cursor 独立、iframe／跨窗 key／错 task／旧 launch／重复 launch 拒绝，关闭竞态不能影响别窗。T-078 的输入、Esc／晚 Stop、反馈、prompt/native binding 与 once 语义不因换查询方法改变。

## 外部结果与可复数原件

主控 #127 的 OS 运行全部绑定 57c3bfb63、T093_TEST_UPSTREAM_PORT=18443：compile 四项 PASS；primary 为预定 rehearsal_primary_probe，green PASS，真实 V 的两场核对 PASS；chain-11 none PASS，home／scanner／counts／drop／empty 五变异各命中预定业务主失败，真实 V 六场 PASS。每场 cleanup=[]、fixture_removed=true；8 场清单差异都为 0，但不作通过条件。事实摘要及 none 的逻辑原记录／独立 U 收据在 [r18-os-and-chain11-summary-19-02.json](r18-os-and-chain11-summary-19-02.json)；原件为 /private/tmp/t093-r18-*.json、/private/tmp/t093-chain-11-*.json 与同名 events。逻辑记录从原 journal 读入运行 JSON 后留存，不冒称仍有原始字节格式。日志在主控给出的 scratchpad/t093-r18-*.log。

原 T096 wrapper 在首次 tracer 的路径检查前失败，未开进程／窗格；本轮修正并通过七模式实际 Bash argv 红绿，**尚未把修正 wrapper 再跑一次原生七场**。实际七场由主控直接调用原 run_restart.py，output 为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/t093-r18b-<case>-01`，其他 argv、源／版本／新目录检查和逐屏批准相同。七场各 rc 0、PASS、cleanup=true、model_turns=fake_posts=0：

| label 中的 case | 业务结果 |
| --- | --- |
| tracer | ideation 恢复，完整 argv／版本／规范身份／历史 nonce／绑定／原 launch 相符，显式关闭持久化 |
| three | 两主控恢复；worker 未恢复、未重启 receiver／无成功事件，attempt 不变 |
| no-argv | restore_argv_missing，保留未恢复／只读，无成功事件 |
| version | restore_version_mismatch，保留未恢复／只读，无成功事件 |
| no-session | restore_session_missing，保留未恢复／只读，无成功事件 |
| isolation | ideation 缺 argv 拒绝，executor 正常恢复，worker／attempt 不变 |
| empty-reopen | 关闭全部后第三个真实窗口 panes／keys=[]、saved=true，无重新授权／task 变化；归档最终开窗集为空 |

[t096-business-recheck-19-06.json](t096-business-recheck-19-06.json) 独立于 runner 逐字段核对上述 run.json 及保存的 argv、恢复事件、processInfo、视图、task 与最终布局，七场 PASS；七个内存反例均被业务断言拒绝。它是 worker 的事实脚本，不是独立审查 oracle。原 run/archive 共 14 份只读输入在 evidence/T-096/t093-r18b-*，未跟踪也不由本 worker 提交；清单、尺寸／mtime、归档 replay 见 [t096-readonly-inputs-19.json](t096-readonly-inputs-19.json)。外置盘各目录保留原命令输出／真实窗口／退出收据／停止后的 fixture。不能改原件、修改检查使其通过或把读取时的当前 PID 状态混入旧运行。

事实脚本仅复制合成 fixture 的 DB＋WAL 到私有临时目录，副本以 mode=rw 开连接、query_only=ON 做 SELECT；显式关闭后删副本，原件只读、尺寸／mtime 不变。没有连接原 DB 作 checkpoint 或读取 auth 表。SQLite 的 WAL 是数据库持久状态，不能丢掉（[官方文档](https://www.sqlite.org/wal.html#the_wal_file)）。早期取样假设／immutable／ro 打开副本的工具失败均保留，最终只有统一的临时副本读法，不做错误后 fallback／重试，不把这些工具失败归为 T-096 失败。

probe-10 三边界必须保留：两项 2.1.302 内部配置状态升级须重核；官方 hello 候选绕过 BASE_URL，必须避免触发且标出可见迹象，沉默被拒不等于零网络尝试；失败／重试逐条记账。r18 无模型链的真实上游为 0；T-096 原生七场只据其 model_turns=0、fake_posts=0，不额外声称完整网络审计。没有真实模型回合，生产能力不外推为已验证真实接口。

## T-091／T-078 及身份回归

本轮同一产品代码已补 L0/L1：t091-ipc-regression-19（19 项及历史／关闭／空集坏实现）、t091-version-regression-19（8 项及版本删除变异）、t078-runtime-regression-19（11）、t078-relay-regression-19（22）、observer-regression-19（11）、alias-regression-19（2）全 PASS。它们不运行真实 CLI／PTY／内核进程查询；实际 C profile 内的 libproc 来自 r18，原生多窗口／恢复来自 r18b 七场。不能把这些替身扩大成所有 T-078 原生材料已重放。若审查需要额外的 socket/hook/captured-screen 回放，主控按请求 13 的 T-078 材料规则另给全新输出；其中旧 T-096 示例的 T-093 output 已知错误，不再使用。

可在 worker 沙箱重放的只读／给定边界命令（输出必须全新）：

```sh
python3 -B evidence/2026-10-16-batch16/T-093/CHECK-T096-WRAPPER-19.py /private/tmp/新的wrapper结果.json
python3 -B evidence/2026-10-16-batch16/T-093/CHECK-T096-RECEIPTS-19.py --repo . --output /private/tmp/新的T096事实结果.json
python3 -B evidence/2026-10-16-batch16/T-093/SUMMARIZE-R18-19.py --output /private/tmp/新的r18摘要.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /private/tmp/新的T091IPC.json
node --experimental-vm-modules workbench/tests/test_t091_claude_version.mjs /private/tmp/新的T091版本.json
node workbench/tests/test_t078_pane_runtime.ts /private/tmp/新的T078runtime目录
node workbench/tests/test_t078_controller_relay.ts /private/tmp/新的T078relay目录
node workbench/tests/test_t093_process_observer.ts /private/tmp/新的observer.json
node workbench/tests/test_t093_process_alias.ts /private/tmp/新的alias.json
node --experimental-vm-modules workbench/tests/test_t096_restore.mjs /private/tmp/新的恢复合同.json
```

正式 reviewer 必须从用户合同／输入重建预期，不以这些作者检查当独立答案。若需新的 OS 或原生运行，写成脚本交执行主控，不请求升级；使用当前完整冻结 SHA、新 label／输出及已修正 T096 wrapper，仍逐屏批准，真实模型预算 0。没有新问题时不要求把已通过的整套原生运行无意义重复。

## 剩余步骤

执行主控新开第三轮只读审查，核对候选与 57c3bfb63 的运行源码相同、原件出处与上述限制；结论逐字 PASS／INCOMPLETE／NO_GO，不提升旧审查结论。之后仅经唯一门禁完成 submit／验收／集成，不以本请求、Git 冻结或 worker 自报代替收据。当前尚未完成这些步骤。
