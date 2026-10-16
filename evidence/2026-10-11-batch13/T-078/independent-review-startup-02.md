# T-078 首启键与排队收件箱：第二轮独立审查

STATUS: **PASS，仅限本次冻结的 startup 键与排队 inbox 差异审查**。第一轮 P1 已解决：每键后、release 前通过真实收据刷新路径检查 queued、无 delivered 历史、无 I2；精确 M5 在新增断言处失败，候选正例通过。本轮独立检查的四种错误实现全部被完成条件拒绝，包括第一轮未试过的异步身份核对后状态复查缺失。未确认本范围内的产品缺陷或新增结构捷径。本报告不验收整张 T-078，不批准 A-14 续行。

TARGET: 冻结 HEAD `68d7749c284892a4bd43c9284e949b1ed3ea7e48`，包含产品 `06fc9feca6b91febd9879222d82bcb800e2e18ba`；基线 `d1ca480223dd874721af71c36488af0ed8b96f37`。`git rev-parse` 与两次 `git merge-base --is-ancestor` 已确认上述关系。角色卡先从 `/Users/luckye/Documents/Code/a2a/.project-map/roles/reviewer.md` 只读取得。未读取作者或第一轮审查者会话；仅阅读第一轮报告与指定候选文件、运行证据。未开子 agent。

EVIDENCE:

- 审查目标为 unknown 首启已有 pending inbox 排队时，经批准的一屏一键可写出，业务队列保持，初始 release 后才提交原消息并登记原 I2。依据为本次派发给出的用户选项 1（`answer 20261016T012505Z-ideation-answer-001`）和主控 #298/#299 的要求；未把历史 ticket 或跨会话消息当作新增执行授权。非目标为产品修复、真实供应商启动、模型行为、整票完成和 A-14 操作。本轮外部入口结果已回传并独立读回；真实供应商窗口及模型行为仍在范围外。
- **Tracer bullet**：pending → unknown 入队 → 六个批准键 → initial release → 原消息提交 → 原 I2。**Deep modules**：screenKey 负责首启控制键，drain 负责业务写出；本差异没有新增接口。**Ubiquitous language**：pending、queued、delivered 与控制键 written 是不同事实，不能混算。
- session 开始、收到外部结果后及最终交付前的 `project_map.py status --root .` 均为 Problems 0、Stale living docs 0；已读地图、T-078、CONTEXT、intent 和相关执行规格。地图、ticket、术语表均未改。
- `git diff d1ca48022 HEAD -- workbench/src` 只有 `panes.ts:671` 中删除 `&& !pane.queue.length`。本轮运行器还以完整文件逐字比较证明：对基线 assertStartup 的这一个条件做精确删除后，得到冻结候选整个 panes.ts。README、两个测试与过程证据不计作产品源码。指定测试补强提交没有修改产品源码。

| 核对项 | 代码与观察 | 当前判断 |
| --- | --- | --- |
| 第一轮 P1：是否读真实刷新结果 | 入口测试 `test_t078_a13_rehearsal.ts:386` 每键后运行 `workbench/bin/inbox ... list --role executor`；bin/inbox 转 `gates/cli.ts`，经 daemon 到 `core.ts:2754` 的 inbox_list，`:2771` 调用 refreshInboxDelivery，`:2632` 调用 runtime.readWakeDelivery。断言检查 CLI 返回的原条目、原 message、原 thread 和 queued；随后检查同条目的 delivered 历史为零、I2 为零。不是只读未刷新的 SQLite queued 行 | 本轮领域及真实入口反事实 PASS；P1 已解决 |
| 领域刷新与反事实 | `test_t078_startup_pending.ts:50` 调 inboxDeliveryStatus，`core.ts:2664` 进入同一 refresh；两项正例共七次 release 前刷新。候选 15/15；M5 两项在新增 queued 断言失败，仍 unknown、active=null、一条队列、仅 ArrowUp 字节 | 本轮领域 PASS |
| 每键后与 release 前时点 | 新入口观测及断言在六键循环内，初始 release 在循环后；每键保存 startup-receipt-N.json，再检查 queued、无 delivered 历史、无 I2。领域也逐键检查，release 后另要求 delivered | 本轮六个观测符合；SQLite 证明每个 inbox_list 都在对应键后、下一键或 release 前 |
| 首启键期间 drain / release 前业务写出 | screenKey `panes.ts:640` 到 `:693` 只在串行写入中发送 keys[key]，不改 pane.state、不调用 drain/release/dispatch。drain `:550` 仍要求 idle；业务 paste/CR 与 turn_submitted 在 `:561` 之后。显式 release `:629` 才置 idle 并 drain | 本轮领域及入口候选 PASS；提前 drain 变异在首键后的 queued 断言被拒绝 |
| 草稿、写入中、失败、停止等仍拒键 | assertStartup 保留 unknown、无 active、无 failed、未 stopped/archived、未 writing、无 userDraft/pendingInputs；入串前、串内、异步 processInfo 后三次检查仍在。领域九个禁止状态均拒绝且零写入；身份检查中出现草稿也拒绝 | 本轮领域 PASS；删除守卫和删除异步后复查的变异均被拒绝 |
| 身份、快照、信任、键次序 | operator 权限仍在 daemon.ts:253；screenKey 的 executor/Claude/controller/隔离假 API、前台领导者、完整屏幕字节、单屏去重、主题次序、notice 正文及 trust 续帧全部逐字未变。领域错误 source、改屏、无前台反例通过 | 静态不变及所列领域反例 PASS；未重跑其他旧专项测试 |
| 后台 drain 绕过 | daemon.ts:376 只在 controller_start、pane_release、window_release、signal 后 settle；不含 pane_screen_key。signal 收尾 `:390` 的 drain 仍经过相同 idle 条件。unknown 且无 active 的未匹配 Stop 不会置 idle。其余 drain 调用来自 dispatch 与显式放行 | 未确认新增路径 |
| 吞异常、兜底重试、兼容分支、平行 API、热补丁 | 产品仅删除一个条件；screenKey 写出失败仍记录后重抛；serializeWrite `:451` 不把失败转成功。没有新增恢复、重试、双写、入口或 reload。测试原有 shutdown 兜底和异常保存不由本差异加入，也未把失败项计为 PASS；本次补强只新增观测、断言和六个串行查询所需总期限 | 未确认新增结构捷径 |

主控提供的 `09b-startup-receipt-entry-01` 原件已独立读回，而非只相信其汇总 PASS：candidate/m5 保存的入口测试均与 `68d7749c2` 逐字相同，stderr 均为零字节，SQLite 只读完整性均为 ok。候选入口 14/14；六份 startup-receipt 依次为 queued、历史无 delivered、I2=0、unknown，控制键累计写出数 1～6。SQLite 的六键 seq 为 25/31/37/43/49/55，initial_release=60，原业务 paste_intent=61、turn_submit_intent=63、turn_submitted=64，原 I2 intent=65。后续 ack/反馈有其他业务回合，不混作原消息重复投递。

同批主控 M5 原件在 `startup refreshed delivery 0` 失败，observed=delivered、expected=queued；首键后历史由 queued 追加 delivered，但仍 unknown、一条队列、active=null、只有 ArrowUp、没有 I2。这精确命中新断言，未被身份、夹具或模块加载错误提前遮挡。该批原件只作交接证据；以下是本 reviewer 独立编写脚本后由主控代跑的新结果，不复用旧候选的通过结论。

主控 #314 回传本轮脚本退出 0，输出根为 `/private/tmp/t078-startup-review-outside-02.a7NqbB`。本 reviewer 已逐项读取 controller-run.log、七段 test-command.json、原始 stdout/stderr、测试 result/results.json、逐键观测、mutation.diff，并以只读 immutable SQLite 查询四个入口数据库；没有只依赖运行器 PASS。该目录 runner.py 与交付脚本中的运行器逐字相同。七份副本的 38 个必要文件逐字对照冻结提交：两个候选副本没有差异；基线和四个变异都仅修改 panes.ts，测试、bin/inbox、package.json 与夹具均未改。七项实际测试均未超时、stderr 均为零字节；四个真实 inbox 入口加载预检均到达 inbox_client_arguments，未把模块缺失当成业务红态。

本轮候选真实入口 14/14、领域 15/15，通过且退出码均为 0。六次原生 inbox list 的响应与 startup-receipt-0～5.json 均指向同一原条目 `b8a93a1a-7358-4ebf-9ec7-aa6d2bb679bb`、原 message `3ec2eaf7-862b-4017-8cf7-e81d98dc1af3`，始终 queued、无 delivered 历史、I2=0、unknown、active=null、原队列不变，仅有对应控制键字节。领域另保存七次真实收据刷新观测。SQLite 独立读回完整性为 ok：六键 seq=25/31/37/43/49/55，六个 inbox_list 分别在对应键后、下一键或 release 前；initial_release=60；原消息唯一 paste_intent=61、turn_submit_intent=63、turn_submitted=64；原 I2 intent=65、registered=71。release 前目标窗格无任何业务 paste/提交事件，原 request 对应的 I2 只有一条且确认原 entry delivered，原 stop.created_at 不变。

本轮 M5 入口在 `startup refreshed delivery 0` 精确失败，实际 delivered / 预期 queued；SQLite 只有首键 written=25，无 release、业务 paste/提交或 I2。逐键观测仍 unknown、一条原队列、active=null、仅 ArrowUp，但收据历史错误追加 delivered。提前 drain 入口也在同一 queued 断言被拒绝；其原件证明首键后已 busy、active 非空、队列清空，并在没有 release 时写出业务 paste/CR，SQLite paste_intent=26、turn_submit_intent=28、turn_submitted=29。因此两者都在正确业务失败点被拒绝，M5 的收据错误没有被提前写业务掩盖，提前 drain 的真实错误也没有被环境故障替代。

FINDINGS:

- **P0/P1/P2/P3：本次冻结差异范围内无确认缺陷。** 第一轮完成条件 P1 已解决：真实刷新路径、每键后且 release 前的 queued/历史/I2 断言、M5 新断言处失败及候选正例通过，均有本轮原始证据。产品源码仍只有指定的一处条件删除，未发现新增 drain 放行路径或结构捷径。
- **完成条件够格：PASS。** 四种错误实现均在业务断言失败，包含第一轮未试过的 omit_post_identity_guard。基线真实入口红态也由首键 screen_requires_startup 证明。反例中错误状态不计作候选缺陷；本结论仅覆盖本差异及所列边界，不外推整票、供应商窗口或模型行为。

COUNTEREXAMPLE:

本轮一次性副本在 `/private/tmp/t078-startup-review-local-02-qko02et6`。只从冻结提交解出 workbench/src、package.json、bin/inbox、两个冻结测试和首启屏幕夹具；依赖通过链接只读使用已有 node_modules。没有复制整个仓库或 auth。四个已运行副本的两个测试、bin/inbox、package.json 均再次与冻结提交逐字比较相同；产品变化单独保存在 mutation.diff。每项保存 snapshot-manifest.json、test-command.json、stdout/stderr、完整 results.json、SQLite 与 review-verdict.json。Node 为 v26.5.0。领域测试内临时运行目录由原测试保存数据库后删除，审查副本和测试输出全部保留。

| 实现 / 变异 | 本轮运行结果 | 失败点与含义 |
| --- | --- | --- |
| 精确候选 | 本轮入口退出 0，14/14 PASS；本地及沙箱外领域均退出 0，15/15 PASS | 六键后显式 release 才写业务；六次入口刷新及七次领域刷新均 queued、无 delivered 历史、无 I2；release 后 delivered、原 I2 唯一 |
| M5：首启键收据误算 delivered（第一轮精确变异） | 本地领域退出 1，两项正例失败；本轮入口退出 1 | 领域在 `startup refreshed receipt remains queued: single ArrowUp` / `key 0`，入口在 `startup refreshed delivery 0` 失败，实际 delivered / 预期 queued；仍仅 ArrowUp、unknown、原队列，零业务写出 |
| 删除整个 assertStartup（第一轮有过，本轮重新验证） | 本地及沙箱外领域均退出 1 | 九个 queued_* 禁止状态均 Missing expected rejection 且实际写出 ArrowUp；异步草稿变化也漏放。另有 release 后负例被 screen_key_already_used 遮挡，不用它证明状态守卫 |
| 省略 processInfo 后的 assertStartup（第一轮未试过） | 本地及沙箱外领域均退出 1，仅一项失败 | `state_change_during_identity_check_is_denied` 为 Missing expected rejection，实际写出 ArrowUp；证明仅靠异步前的状态检查不够，新反例被当前完成条件拒绝 |
| 首启键后置 idle 并 drain | 本轮入口退出 1 | `startup refreshed delivery 0` 失败，实际 delivered / 预期 queued；观测及 SQLite 证实没有 release 却已 busy、队列清空并写出额外业务 paste/CR |
| 基线 d1ca48022（红态对照，不计入四种变异） | 本轮入口退出 1 | 首个 pane_screen_key 为 screen_requires_startup，零控制键 written、零业务写出、队列仍 queued；没有 I2 |

已实跑的确切命令为下列命令把 `<case>` 分别替换为 `candidate`、`M5`、`no_startup_guard`、`omit_post_identity_guard`；各测试实际完整 argv、cwd、期限、PID、独立进程组和退出码另见对应 test-command.json。

```text
python3 -B /private/tmp/t078-startup-review-local-02-qko02et6/runner.py /Users/luckye/Documents/Code/a2a-wt-t078 /private/tmp/t078-startup-review-local-02-qko02et6 <case> domain
```

沙箱外脚本为同目录 `REVIEW-STARTUP-OUTSIDE-02.sh`，执行命令：

```text
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/REVIEW-STARTUP-OUTSIDE-02.sh
```

脚本每次创建全新 `/private/tmp/t078-startup-review-outside-02.XXXXXX`，从冻结提交只解出上述必要路径；不借用或修改第一轮运行器。依次跑候选、基线、M5、提前 drain 的真实入口，以及候选和两种守卫变异的领域测试。测试与夹具不变。每段打印段名、新输出目录和退出码，详细原件保存在该目录。运行器 PASS 只表示正反例观察符合预期，不表示错误实现通过产品测试。服务由测试进程托管，运行器以 start_new_session=True 启动，超时只终止自己创建的进程组并保留原件。脚本已通过 bash -n、嵌入 Python 语法及 UTF-8 检查；本轮由主控沙箱外代跑，reviewer 已独立读回原件。

本轮对应 [controller-run.log](/private/tmp/t078-startup-review-outside-02.a7NqbB/controller-run.log)。七段完整 Node argv、cwd、期限、PID、退出码分别保存在该根目录 `candidate-entry`、`baseline-entry`、`M5-entry`、`startup_drain-entry`、`candidate-domain`、`no_startup_guard-domain`、`omit_post_identity_guard-domain` 的 test-command.json；对应变异有 mutation.diff，测试原始结果在各段 test/result.json 或 test/results.json。关键证据为 [候选入口结果](/private/tmp/t078-startup-review-outside-02.a7NqbB/candidate-entry/test/result.json)、[M5 新断言失败](/private/tmp/t078-startup-review-outside-02.a7NqbB/M5-entry/test/result.json)、[M5 首键后观测](/private/tmp/t078-startup-review-outside-02.a7NqbB/M5-entry/test/startup-receipt-0.json)、[提前 drain 观测](/private/tmp/t078-startup-review-outside-02.a7NqbB/startup_drain-entry/test/startup-receipt-0.json)、[新反例结果](/private/tmp/t078-startup-review-outside-02.a7NqbB/omit_post_identity_guard-domain/test/results.json)。没有重跑或覆盖这些外部运行原件。

LIMITATIONS:

- 本差异审查 PASS；四种变异及基线红态均已核实。真实入口证据的边界为 CLI/Unix socket/daemon/SQLite/Stop/relay，PTY 与前台身份使用 spy，未证明真实供应商进程、实际交互窗口或模型表现。沙箱外运行由主控执行本 reviewer 提供的冻结检查脚本，reviewer 独立读取原始证据，没有冒称自行绕过沙箱执行。
- 没有进入或操作 `/private/tmp/t078-2-09b-run-gbxz0tyb`，没有查询、发信号或终止其进程，没有执行 `09b-a14-s1-retry-NO-GO.json`，不批准继续 A-14。只使用仓库已保存的屏幕夹具。
- 建立运行器时，第一次静态逐字比较的锚点过宽，误匹配了文件更早的队列条件，预检 AssertionError；未运行产品测试、未形成反例判定。原初运行器保留在 `/private/tmp/t078-startup-review-local-02-b1z_hnnu`。随后把比较锚点限定到 assertStartup 的 screen_requires_startup 条件，并在全新 qko02et6 目录完成上述检查；没有覆盖失败现场。
- 仓库既有未跟踪 `09b-startup-receipt-entry-01/` 已保留；本轮只新增指定报告和脚本。未改产品、测试、地图或规则，未 git commit/checkout/reset/stash/push/submit/集成，未请求沙箱升级，未调用模型 API、复制 auth 或写全局配置。

T-078 STARTUP REVIEW 02 DONE
