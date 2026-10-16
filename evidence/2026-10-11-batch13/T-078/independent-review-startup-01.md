# T-078 首启键与 pending inbox 差异：独立审查

STATUS: **NO_GO／需修复完成条件**。本轮独立审查已完成：五种错误实现中四种被对应完成条件拒绝，第五种“首启键收据误算 delivered”在冻结领域测试和真实入口排练中均存活，只被独立时点探针检出。产品一行改动的范围核对与候选已跑行为检查通过，未确认候选产品本身违约；但当前完成条件不够格，不能授予本差异审查 PASS。本报告不判断整票完成，不批准 A-14 续行或新 launch。

TARGET: 候选 `06fc9feca6b91febd9879222d82bcb800e2e18ba`；基线 `d1ca480223dd874721af71c36488af0ed8b96f37`。开始与收尾的 `git rev-parse HEAD` 均为该候选。审查为 fresh-context reviewer；未开子 agent，未读作者会话。角色卡已从主控指定的 `/Users/luckye/Documents/Code/a2a/.project-map/roles/reviewer.md` 读取。

EVIDENCE:

- 目标：只审 unknown 首启有 inbox 队列时，一屏一键仍放行且不投递业务的差异。非目标：实现或修复、整票验收、真实 Claude 新实例、A-14 操作。验收依据是本次派发逐字给出的用户选项 1 与主控 #298/#299 要求；交接说明仅作定位线索。关键检查是完成条件能否拒绝“首启键被误认为 inbox 已投递”；本轮反例已证明它不能。**Tracer bullet** 为 pending→unknown 入队→六键→initial release→同条消息提交→原 I2；**Deep modules** 的边界仍是 screenKey 管单键、drain 管业务写出；**Ubiquitous language** 区分 pending、queued、delivered 与首启控制键。
- `git diff --name-only d1ca48022..06fc9feca -- workbench/src` 只有 `workbench/src/panes.ts`。独立逐字比较确认：仅将基线 assertStartup 行中的 ` && !pane.queue.length` 删除，就得到候选完整 panes.ts；不是近似 diff。其余条件不变，三处调用仍在 `panes.ts:672`、`:674`、`:675`：入队写串前、写串内、异步前台身份核对后。README 仅在 `workbench/README.md:419` 附近说明首启键不放队列。另有两个测试文件及大量过程证据改变，不混算成产品源码改变。工作区已有 RESULTS 与阶段脚本的修改及未跟踪证据均保留；本审查的副本只从冻结提交解出必要路径。

| 核对问题 | 代码与独立证据 | 当前判断 |
| --- | --- | --- |
| 首启键顺带 drain | `panes.ts:640–693` 无 drain、dispatch、release 调用，也不改 pane.state；只写 `keys[key]`。候选领域 15/15、真实入口 14/14 通过；M1 在首键后状态断言失败 | 所列候选检查 PASS |
| release 前写业务 paste / turn_submit | `panes.ts:550` 仍要求 idle，unknown 直接返回；`:561–572` 才执行 paste、CR 与提交记录。首启键不会把状态置 idle；独立读回真实入口 SQLite 时序符合 | 所列候选检查 PASS |
| 用户草稿、写入中、失败、停止等仍按键 | `panes.ts:671` 保留 unknown、无 active、无 failed、未 stopped/archived、未 writing、无 userDraft/pendingInputs；领域测试逐个拒绝，并核对零写入。身份检查中出现草稿也被第三次检查拒绝 | 本地 PASS |
| 身份、快照、信任和键次序 | `panes.ts:642–668` 保留 executor/Claude/controller/隔离假 API、键范围与历史次序；`:675–685` 保留前台、完整字节、信任续帧及安全提示正文核对。候选领域中错误 source、改屏、无前台分别命中预期错误码 | 静态不变；所列三反例本地 PASS，其他旧测试未另跑 |
| delivered 与原 I2 的时点 | `panes.ts:541–547` 只把 turn_submitted 映射为 delivered，排队仍报 queued；`core.ts:2624–2638` 按该收据刷新；`daemon.ts:33–55` 与 `relay.ts:57–65` 只在 delivered 后登记一次原 I2 | 候选代码符合；验收漏检见发现 |
| 后台 drain 绕过 | 其余调用来自 dispatch、用户放行、initial release 和 `daemon.ts:390–402` 的 signal 收尾；都经过同一 drain。pane_screen_key 不在 `daemon.ts:376` 的 settle 列表中。unknown 且无 active 的旧 Stop 不会改成 idle（`panes.ts:748–756`） | 静态未发现新增路径 |
| 吞异常、兜底重试、兼容分支、平行 API、热补丁 | 产品只有一处条件删除。`panes.ts:689–690` 仍记录失败并重抛；`:451–456` 保留失败写串。没有新增重试、入口或 reload。排练原有的 shutdown 兜底未由本差异加入，也不用于判业务成功 | 静态未发现新增结构捷径 |

- 主控交回的 `09b-startup-pending-entry-02/result.json` 是红/绿阶段汇总；本审查另读其原始 red、green result、offline-delivery 及 SQLite。红态在首个 `pane_screen_key` 返回 `screen_requires_startup`；绿态 14 项完成。对保存的 SQLite 使用 `mode=ro&immutable=1` 独立读回，完整性为 `ok`：目标六键 written 事件为 25/29/33/37/41/45，initial_release=48，paste_intent=49，turn_submit_intent=51，turn_submitted=52，原条目 I2 intent=53。业务首次写出在 release 后，六键前后顺序符合要求。此证据的真实边界为 CLI/Unix socket/daemon/SQLite/Stop/relay；PTY 与前台身份是 spy，没有实际供应商进程或模型回合。主控给出的 entry-01 缺 inbox 文件诊断与原始失败保留，没有把模块加载失败当作业务红态。
- 主控 #311 回交了本审查脚本的沙箱外输出 `/private/tmp/t078-startup-review-outside-01.ugXQga`。本 reviewer 读取 controller-run.log、七个 case 的原始测试结果与命令、变异 diff、独立探针 diff/结果，并读回候选和 M5 的 SQLite；没有仅据运行器摘要判断。把每个 snapshot 的 38 个必要文件与冻结提交逐字对比：候选全部一致；基线及五种变异均只改变 panes.ts，两个冻结测试与夹具未改。七个 case 的测试均未超时、stderr 均为空；错误实现的拒绝发生在业务断言，非加载故障。候选真实入口 14/14 PASS、独立探针 PASS；本轮 SQLite 再次读得六键 25/29/33/37/41/45、release 48、唯一原消息提交 52、原 I2 intent 53，完整性 ok。M5 的真实入口同样 14/14 PASS、退出 0，独立探针却退出 1。脚本总退出码 0 只表示预期现象均被正确校验，不代表完成条件或候选取得审查 PASS。
- 只读取仓库内保存的 A-14 readback 与 executor s1 拒绝原件：unknown、有一条队列、零业务写入，首键退出 1 / screen_requires_startup。没有进入 `/private/tmp/t078-2-09b-run-gbxz0tyb`，没有查询其进程、发键、release、Stop、重启或清理；没有执行 `09b-a14-s1-retry-NO-GO.json`。

FINDINGS:

- **[P1，完成条件漏检，需修复]** `workbench/tests/test_t078_startup_pending.ts:58`、`:65` 的正例，以及 `workbench/tests/test_t078_a13_rehearsal.ts:383–392` 的每键检查，只核对 unknown、active、队列、字节和业务事件，没有在首启键之后、release 之前查询 inbox delivery。第 5 个变异令 `readWakeDelivery` 在已有 controller_screen_key_written 时把仍排队的消息报为 delivered；冻结领域测试 15/15 PASS，冻结真实入口排练也 14/14 PASS，测试退出码均为 0。独立探针仅增加一次 `readWakeDelivery(...).state === "queued"` 断言，候选通过，变异精确失败为实际 delivered / 预期 queued、退出 1；同时只有 ArrowUp 字节、unknown 和一条原队列，证明不是由提前业务写入等其他错误遮挡。证据见 [M5 冻结入口结果](/private/tmp/t078-startup-review-outside-01.ugXQga/key_receipt_is_delivery-entry/test/result.json)、[独立探针结果](/private/tmp/t078-startup-review-outside-01.ugXQga/key_receipt_is_delivery-entry/probe/results.json) 与 [仅增加一个时点断言的 diff](/private/tmp/t078-startup-review-outside-01.ugXQga/key_receipt_is_delivery-entry/probe.diff)。最终判定为 **NO_GO／需修复完成条件**。
- 最小修复由验收文件的责任方完成：真实入口排练每键后、release 前，经真实收据刷新路径查询原条目并断言仍 queued、没有 delivered 历史和 I2；保留 M5，证明它在该新增业务断言处失败，且冻结候选正例仍通过。仅在测试里看原本未刷新的 queued 行，不能拒绝这个错误实现。变更完成条件后提交新冻结候选，再按同一边界复验；本 reviewer 不实现、不修复、不预授后续候选 PASS。
- 未确认当前候选产品本身有可达违约；上述是验收证据的缺口，不能把变异行为记成候选缺陷。此项影响本差异审查放行，整票 T-078 的其余未完成项仍按原范围保留。

COUNTEREXAMPLE:

本地一次性副本保留在 `/private/tmp/t078-startup-review-local-01-k3wd7nd9`；第 5 个变异与独立时点探针保留在 `/private/tmp/t078-startup-review-timing-01-1ktwzre1`。每个 case 均有 snapshot、mutation.diff、test-command.json、stdout/stderr、SQLite、results.json 和 review-verdict.json；测试原文不改，独立探针另存文件及 probe.diff。Node 为 v26.5.0。没有复制整个仓库或 auth；必要路径为 workbench/src、package.json、bin/inbox、两个冻结测试和屏幕夹具，依赖仅通过链接读取已有 node_modules。

| 实现 / 变异 | 实跑检查与退出码 | 失败点或存活情况 |
| --- | --- | --- |
| 精确候选 | 冻结领域：0，15/15 PASS；冻结入口：0，14/14 PASS；独立探针：0 | queued 未被首启控制键误报 delivered |
| 历史基线（红态对照，不计入五个变异） | 冻结领域：1；冻结入口：1 | 入口在首个批准键失败，command-5 为 screen_requires_startup；领域两个正例零写入。旧队列条件遮挡了领域改屏/无前台负例，未伪称它们验证成功 |
| M1 startup_drain：首启键后把状态置 idle 并 drain | 冻结领域：1，2 项失败；冻结入口：1 | ArrowUp 后多出业务 paste/CR；入口在 startup remains unknown 0 失败，实际 busy / 预期 unknown |
| M2 early_delivery：入队即报 delivered | 冻结入口：1 | controller_start 只入队步骤，queue admission is not delivered 失败，实际 delivered / 预期 queued |
| M3 no_startup_guard：将 assertStartup 改为空函数 | 两次冻结领域实跑均为 1、11 项失败 | 九种禁止状态全部实际写出 ArrowUp，Missing expected rejection；身份核对中出现草稿也漏放。另一个失败是 release 后负例被历史去重挡住，不将它当成状态守卫证据 |
| M4 duplicate_release：一次 drain 内重复写业务 paste/CR | 冻结领域：1，1 项失败；冻结入口：1 | 入口在 one bracketed paste 失败，实际 2 / 预期 1；领域精确字节断言同样拒绝 |
| M5 key_receipt_is_delivery：首启键收据误算投递收据 | 冻结领域：0，15/15 PASS；冻结入口：0，14/14 PASS；独立探针：1 | **两层完成条件均漏检，NO_GO**；独立探针在首键后精确检出 delivered / queued |

本地可复现命令（每次选一个全新输出根目录；已有目录不覆盖）：

```text
python3 -B /private/tmp/t078-startup-review-local-01-k3wd7nd9/runner.py /Users/luckye/Documents/Code/a2a-wt-t078 <全新输出根目录> candidate domain
python3 -B /private/tmp/t078-startup-review-local-01-k3wd7nd9/runner.py /Users/luckye/Documents/Code/a2a-wt-t078 <全新输出根目录> baseline domain
python3 -B /private/tmp/t078-startup-review-local-01-k3wd7nd9/runner.py /Users/luckye/Documents/Code/a2a-wt-t078 <全新输出根目录> startup_drain domain
python3 -B /private/tmp/t078-startup-review-local-01-k3wd7nd9/runner.py /Users/luckye/Documents/Code/a2a-wt-t078 <全新输出根目录> no_startup_guard domain
python3 -B /private/tmp/t078-startup-review-local-01-k3wd7nd9/runner.py /Users/luckye/Documents/Code/a2a-wt-t078 <全新输出根目录> duplicate_release domain
python3 -B /private/tmp/t078-startup-review-timing-01-1ktwzre1/runner.py /Users/luckye/Documents/Code/a2a-wt-t078 <全新输出根目录> key_receipt_is_delivery domain
```

每份 `test-command.json` 保存实际完整 Node argv、cwd、期限、进程号与退出码；上述是运行器命令，不把运行器验证反例成功的 PASS 当作产品测试通过。

沙箱外完整复现命令为 `bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/REVIEW-STARTUP-OUTSIDE-01.sh`；脚本每次创建全新输出目录。本轮对应 [controller-run.log](/private/tmp/t078-startup-review-outside-01.ugXQga/controller-run.log)。各 case 的精确执行命令分别保存在该目录下 `candidate-entry`、`baseline-entry`、`startup_drain-entry`、`early_delivery-entry`、`no_startup_guard-domain`、`duplicate_release-entry`、`key_receipt_is_delivery-entry` 的 `test-command.json`；M5 的独立探针命令另见 `probe-command.json`。本轮没有重跑、覆盖或清理这些原件。

LIMITATIONS:

- 真实 Unix socket 入口由主控在沙箱外代为执行本 reviewer 准备的脚本，本 reviewer 独立读回原始产物，没有冒称亲自绕过沙箱运行。入口验证仍以 PTY/前台身份 spy 代替供应商进程；M5 独立探针是领域层直接查询 readWakeDelivery，没有冒称已在新入口断言中被拒收。当前冻结完成条件确实让它存活。
- 供应商交互窗口、真实新实例和模型表现均未验证，不外推为整票 T-078 或 09B 通过。A-14 现场与既有 NO_GO 诊断提案均未操作。实际供应商窗口里的业务输入与安全提示显示尚未验证。
- 第一次尝试用本机 Python sqlite3 的 deserialize API 读副本时发现该解释器没有此方法，未产生判定；随后只读 immutable 查询成功并独立检查了事件时序。没有因此改动产品或证据原件。
- session 开始与交付前的 project-map status 均为 Problems 0、Stale living docs 0；地图、ticket、规范与术语表未改。本报告与指定脚本之外没有写仓库文件，没有 commit、checkout、reset、stash、push、submit 或集成。

T-078 STARTUP REVIEW DONE
