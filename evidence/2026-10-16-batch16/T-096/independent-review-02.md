STATUS: PASS
TARGET: 17a8ec8f20b97b732ad561c4fa02213a4f0e23f7

结论：**PASS（T-096 用户裁定 B 的独立行为审查）**。第一轮“关闭最后一格后又加入当前 worker”的缺陷已修好，合同反事实和新产品版本上的真实 Electron 重开原件均支持这一结论。未确认阻断性的行为或结构缺陷；下列 P3 文档矛盾交执行主控在集成前处理。本结论不是 submit、门禁验收、集成或工作台日常切换的批准。

2026-10-18，执行主控 #114 派发。审查对象为 T-096／attempt a1／writer s16-t096 的上述冻结提交，比较起点 `3c9016d02`。先读取共享仓库 reviewer 角色卡，再用 `git -C /Users/luckye/Documents/Code/a2a show main:.project-map/tickets/T-096-restore-panes-and-sessions-after-restart.md` 读取最新版 ticket；main 为 `8e5a976a6844abfa905de311db993473a21348c8`。按当前派发与用户裁定 B 重建答案：两个主控使用记录的完整 argv 续接原 session；worker 显示“未恢复”，不启动、不重绑定、不改 attempt；不改门禁。RESULTS、worker 脚本及新增测试只作证据定位和受审对象。

使用 project-map、evidence-first-testing、behavioral-acceptance-review、design-integrity-review、document-writing。没有作者会话历史、子 agent、模型调用、真实应用启动或沙箱升级。候选未改；仅写本报告、`REVIEW-OUTSIDE-02.sh` 和自己新建的 /tmp 目录。没有 commit、checkout、reset、stash、push、submit 或集成，第一轮报告与脚本原样保留。

EVIDENCE:

- **版本归属：PASS。** 初始工作区干净，HEAD 为指定完整 SHA。审查请求 02 的首次提交也是该 SHA。`git diff d61876fe2 17a8ec8f2 -- workbench` 无差异，故新实跑的产品与冻结候选相同。旧实跑的 `f2b96001daea2653b01fdbbb0aba4d43387b3b7c`、`752dc62a179cb0fca8a18670a24b507d1bff471b` 到第一轮冻结 `11b32303b` 的 src/app 无差异。红态所用 main `fbba0002481941ea566d395bc9caa01d790b6689` 与起点的 src/app 无差异。
- **原件核对：PASS，限下表所列事实。** 直接读取 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/` 下的真实原件；SQLite 连同存在的 WAL／SHM 先复制到新 /tmp 目录，再查询副本，没有打开原件的可写连接。独立核对结果为 `/tmp/t096-review-02-h45m4dsf/raw-audit-02.json`，就绪批准另见同目录 `ready-audit.json`。

| 原件 | 独立核对结果 |
| --- | --- |
| red-b-05 | command-47.json／stdout 的真实 daemon_start 退出 1，报 `daemon_call_failed` 与 `socket exists; query its owner, do not replace it`；没有 epoch 2 收据，按键 0。这是死端点阻断重启的真实红态，未观察到第二轮空窗口，不把未发生的窗口读回当成证据。 |
| tracer-b-05 | 初次实际 argv 等于记录；续接实际 argv 只将 `--session-id` 改为 `--resume`，其余字段逐项相等。launch／task／role／session 一致，shell 身份改变；合成历史的随机 nonce 出现在恢复后真实终端，重启前没有该 nonce。 |
| three-b-01 | 两个主控分别满足上述 argv／session／nonce 条件；worker 真实窗格显示“未恢复”、只读，没有 pane_restored，receiver 仅首次启动一份。gate-before／gate-after 的完整 task 及最终 SQLite task 相等，包括 attempt 与原 runtime_identity。 |
| no-argv-b-02 | 真实事件拒绝 `restore_argv_missing`；窗格显示“未恢复”、只读，没有该 launch 的 pane_restored。 |
| version-b-02 | 拒绝 `restore_version_mismatch`；保留只读“未恢复”，无成功事件。原始正常退出记录保留；不把此场扩大成重现了 version-b-01 的特定瞬态竞态。 |
| no-session-b-01 | 拒绝 `restore_session_missing`；保留只读“未恢复”，无成功事件，没有新 session 补位。不声称这一场实际执行过“已有文件改名”操作。 |
| isolation-b-01 | 构思主控缺 argv，明确失败且无成功事件；执行主控继续按原 argv 恢复并显示自己的历史 nonce；worker 未恢复，receiver 一份，完整 task／attempt 前后及最终 SQLite 读回相等。部分首轮顶层身份字段缺失时使用该条原始 snapshot.launch 核对，没有补造字段。 |
| empty-reopen-b-01 | 产品为 d61876fe2；两主控实际初始／续接 argv、原 session／历史 nonce 均核对通过；worker 只读未恢复、receiver 一份、完整 task 及最终 SQLite task 不变。三个显式 close 都有持久事件。关闭全部后的前后布局读回均 saved=true、panes=[]；第三个真实窗口的 panes／pane_keys 均空，bridge 正常，DOM 显示“当前任务没有打开的窗格。”。最终 close 后没有新增 pane_layout_opened、window_opened 或 pane_restored；window-2／3 都有正常 quit／exit_code=0。 |

- **逐屏批准：PASS（记录一致性）。** 八场合计十个实际初始化的主控 profile、60 次成功写键；其中新实跑为两个 profile、12 键。逐个比对 startup-keys、SQLite intent／written、批准文件、key-receipt 与原始屏幕字节：launch、session、directory、screen_id、key、purpose、selected_label、authorization_ref 一致，intent 先于 written，批准者为 executor。每个 profile 都是主题 ArrowUp／ArrowDown／Enter、须知 Enter、信任 ArrowDown／Enter；原始屏内容符合用途。十份独立 startup-ready 批准均与原 launch／session／目录、空 active／queue／writing／draft 回执相符，对应 initial_release 事件晚于信任确认，reason 等于批准引用加本屏 basis。
- **批准记录瑕疵如实保留。** 多场 approval_ref 文本沿用了 `tracer-b-05`／主控 #15 标签，包括新场；它与实际写键 intent 的引用相同。新场每屏 basis 明确写本次 `empty-reopen-b-01`／主控 #19，且 launch／session／screen／path 均为本次唯一身份，未复用旧场屏幕批准。它是引用标签不清晰，不是观察到未获逐屏批准。three-b-01 中未完成的 `startup-screens/ideation/o1.approval.json` 仍为不完整 JSON；成功写键有各自完整批准和回执，该文件没有被计为成功批准。建议主控追加澄清引用，不改原始批准文件。本审查不能独立认证“executor”字符串背后的人身身份。
- **模型回合与边界：PASS，限隔离假 API。** 八场原始 fake-api-requests 均无 POST。恢复没有提交提示词或放行旧队列。历史 user／assistant 是停机后写入、明确标注的合成夹具；nonce 证明原生 CLI 载入指定历史，不证明真实模型能力。源码及原记录的 HOME／CLAUDE_CONFIG_DIR／CODEX_HOME 使用隔离夹具，恢复沿用原环境；未发现新增写用户 ~/.claude 或 ~/.codex 的路径，审查也未写它们。没有全局写入监视器，不能据此声称追踪了 CLI 的全部文件系统副作用。
- **失败原件保留：PASS。** red-b-01／tracer-b-01 的 NoneType 异常、no-argv-b-01 的初始化不完整、version-b-01 的收尾不完整摘要仍为 INCOMPLETE，对应外置目录仍存在。未把旧探索失败改成业务红态或 PASS。新归档独立重数为 1,237 文件、568,773,593 字节，与清单相符；没有重算校验值，也没有重做已不存在的源目录与归档之间的复制比较。

**第二轮四个产品文件对旧七场的影响：PASS（下述可复用范围）。** `git diff 11b32303b 17a8ec8f2 -- workbench/src workbench/app` 只修改四个文件：

| 文件与位置 | 独立判断 |
| --- | --- |
| store.ts:58 | hasPaneLayout 只查询该 task 是否曾有打开／关闭事件，不写表或启动记录。openPanes 的投影没有改。对任一非空保存集，必然已有 pane_layout_opened，因此新 saved=true 与旧“长度大于零”相同；只在已明确清空时改变旧版的错误分类。合同另证实原生元数据、别的 task 不会冒充本 task 的保存事实。 |
| daemon.ts:113 | 只给 pane_layout 响应增加上述 saved；panes／recovering、恢复调度及其他命令不变。失败事件并不删除 pane_layout_opened，故某个恢复失败也不会改变这一非空集等价关系。 |
| main.ts:167、170 | 对旧七场的非空保存集，新旧 saved 都为 true，仍用同一 requireSavedPane、原位置与固定 launch，不重新开窗格或发凭据。显式 launch 的分支未改。空集才走新分支，并由真实第三窗口及拒绝旧版本的合同重新证明；首次未保存仍选当前窗格，显式空 launch 列表仍拒绝，显式指定 launch 可重新打开。 |
| preload.ts:6 | 只去掉“空数组非法”的条件；对此前所有非空 key 数组，校验和 IPC 方法相同。零 key 的新边界在真实 preload／renderer 上已重新证明。 |

panes.ts、paneRecovery.ts、transport.ts、claudeLaunch.ts、renderer 和 gates 在这两版间均未改。旧七场没有失效，但各自实际运行版本仍是旧版：red 继续是历史已知坏反例；tracer 的单格实跑没有在新版本重复，不能单独证明空集；旧 three 的共享三格布局读入与两主控／worker 绑定已由新场重跑。三个故障及“一个主控失败、另一个成功”没有在 d61876fe2 重新注入，不能称为新候选实跑；它们的恢复／拒绝实现、非空布局选择和非空 preload 行为没有变化。本轮又在新候选运行了三个拒绝共存的合同及失败 sibling 的 main/preload 检查，结合新真实共享路径，足以支持这些未改行为；未发现需要补跑真实故障才能消除的改动耦合。此判断来自调用链和分支条件，不是直接采信 RESULTS 的适用性表。

**结构与回归：**

- **结构 PASS。** paneRecovery.ts:11 复制记录 argv，只换原 session 选择器；缺 argv／错误选择器明确拒绝。panes.ts:208 先拒绝 managed attempt，再核对主控类型、旧进程、argv 完整性、task/spec、实际 CLI 版本、原生 session 文件及 trace；版本探针与 PTY 都使用记录可执行文件和环境。没有裸 resume、默认配置补位或失败后新 session。恢复的逐窗格 catch 在本层记录 pane_restore_failed 并继续 siblings；终止不明时另存 cleanup 原因与 restore_cleanup_unconfirmed，没有吞掉错误并报告成功。成功事件在前台 executable leader 确认后写入。
- **状态归属 PASS。** 打开与显式关闭经 operator 请求即时追加到同一事件流；应用退出只关视图凭据。saved 是事件流已有事实的查询，不是另一份可写布局或 profile。resume_argv 用于完整性对照，配置来源仍是 launch argv。worker 在任何 spawn 之前被拒，完整 task 只读。起点到冻结候选没有 gates 或 Herdr 改动。**Deep modules**：参数与 session 文件核对有明确边界，未发现为第二种实现增加浅包装或平行 API；**Ubiquitous language** 沿用主控、worker、attempt、launch、窗格、未恢复。单格 **Tracer bullet** 的原件与新三格路径分别核对，没有拿模型自报替代业务状态。
- **端点保护 PASS（所覆盖分支）。** 只在 PID 明确不存在、端点为 socket 且拒绝连接时移除死端点，异步探测后再核对 PID 文件。活进程、未知 owner、活 socket、非 socket 和 owner 改变都拒绝，不静默接管；这些合同在本轮通过。没有声称穷尽全部并发／操作系统竞态。

以下检查在 git archive 的一次性副本执行；没有建 worktree，没有真实 Electron、daemon、PTY、供应商 CLI 或模型：

| 检查 | 结果与边界 |
| --- | --- |
| test_t096_restore.mjs | PASS；真实 SQLite／session 文件，替代进程与 PTY。两主控、三个拒绝、worker 无 PTY、完整 task 不变、实际 spawn 的全部参数、零提示写入、空集跨数据库重开／task 隔离。 |
| test_t091_pane_ipc.mjs | PASS；真实 main/preload、替代 Electron／transport。原 key／sender／iframe／序号／输出／旧 attempt／关闭竞争检查通过，原两个坏版本仍被拒；关闭最后一格后连续重开为空，同一业务断言拒绝 11b32303b。 |
| test_t096_daemon_restart.mjs | PASS；替代 IO／进程边界，死端点正例和五类拒绝；起点坏实现被业务断言拒绝。 |
| test_t091_claude_version.mjs、test_t091_driver_selection.mjs、test_t091_start.mjs | PASS；版本拒绝及变异、明确窗格选择／全文输出、三份 launch 转发。 |
| test_t078_controller_window.ts、test_t078_screen_key.ts | PASS；nullable 主控、旧 worker／撤销／spec 拒绝，主题／信任逐屏限制。 |
| test_t096_restart_cleanup.py、test_t096_red_startup.py、test_t096_runner_materials.py | PASS；新第三窗口退出不明时不重复退出、不停后台、不归档，严格历史 oracle、逐屏批准／空队列放行，argv 缓冲解析。均为替代边界，不是另一场真实收尾。 |
| project_map.py status | 会话开始退出 0，0 problems／0 stale living docs；完成前再次运行并保存结果。 |

Node 合同与变异结果：`/tmp/t096-review-02-cxec1he6/results.json`，各条完整命令、源码、stdout、stderr、退出码均保留。三个 Python 合同的精确命令／环境／结果在同目录 `python-contracts.json`；它们读取候选归档中的 runner/helper，GIT_DIR 仅指向原仓库以只读取得已知坏版本，没有 Git 写操作。

FINDINGS:

- 没有确认阻断裁定 B 的行为或结构缺陷；第一轮空集缺陷关闭。
- **[P3，文档跟进] workbench/README.md:503、515。** 新增首段已说明主控会重建 PTY、经核对的死端点可重启，但后段仍无角色限定地写“原窗格只作历史查询，不重建 PTY”及“崩溃残留的 socket/PID 文件阻止启动”。它们与本次实际实现及原件冲突，容易误导使用者。最小修正是按裁定 B 限定主控／worker，并区分可证明的死端点与活／未知端点。责任交执行主控，建议在集成前统一这些现行说明；复核条件为文字与上述冻结行为一致、status 无 stale。此项不改变已验证的运行行为，未据此要求重跑 CLI。本审查没有修改 README 或地图，也没有通过另一个写入通路登记事项。

COUNTEREXAMPLE:

先确认冻结候选的八组合同及更换外部 sentinel 后的独立基线通过，再在 /tmp 副本分别做以下三个单处错误实现。独立调度去掉原测试内部的变异循环，使用新随机 model sentinel 和 medium effort；业务答案仍来自裁定 B，不从生产 helper 生成。三份错误源码与各次完整失败保留。

| 变异 | 业务断言及实测结果 |
| --- | --- |
| M1：恢复交给 PTY 的命令丢掉原启动参数，只剩 executable／--resume／session；成功事件仍记完整 argv | 退出 1，命中 `Actual PTY command must carry every independently supplied argv field`。本轮新增的实际 spawn 断言已经填上第一轮指出的“只检查事件 argv”缺口；随机输入也正常通过候选。 |
| M2：把恢复失败事件写成 pane_restored | 退出 1，命中 `A failed pane must not have a success receipt`。不是依赖、解析或初始化错误。 |
| M3：recover 开头将 task.current_attempt.state 改成 ready | 退出 1，命中 `Worker attempt must remain byte-for-byte unchanged`；拒绝了恢复过程篡改 attempt。 |

精确复现主合同／回归与三种变异：

```sh
sh evidence/2026-10-16-batch16/T-096/REVIEW-OUTSIDE-02.sh
```

此脚本固定完整候选 SHA，每次创建新 git archive 副本；已有 node_modules 只作依赖来源，不安装、不清理、不改全局配置。必须同时看到 results.json 中候选基线 PASS、三个 business_rejection=true，才是合同回放 PASS；单独退出 1 不算变异证据。脚本已实际运行，退出 0。没有必须交主控在沙箱外执行的新增验证步骤，也没有待逐屏批准的应用启动；原生实跑由本报告的只读核对承担。

LIMITATIONS:

- 本轮新执行的是合同级检查；八场原生 Electron／daemon／Claude 是主控实跑原件。没有重新登录、真实模型回合、全局写入监视或完整全仓回归，不把所列 T-078／T-091 相关检查扩大为这些 ticket 的全部场景复验。
- 旧故障真实运行没有冒称是在新版本发生；新共享布局／空集边界有真实新版本证据，未改故障路径的复用依据已逐项列出。version-b-01 的特定瞬态仍未重现，不上调旧未知结论。
- 审查工具失败保留：首版脚本将恢复和初始 worker 启动共有的文本标记误当成唯一标记，在变异前停止；该次已通过基线及日志留在 `/tmp/t096-review-02-h45m4dsf/`。修正为只变异第一个恢复调用后，另建 cxec1he6 副本得到上述结果。首版 raw-audit.json 对空 current_attempt、异步恢复事件早于 daemon_started、未完成批准文件的读取假设不成立；修正读取方式后另存 raw-audit-02.json，没有覆盖旧失败，也没有将其当作产品失败。
- 对原生能力的证明限于本票隔离假 API、Claude 2.1.302、受控 worker receiver 和合成历史。worker 自动续接／重新认领／门禁重绑定不在裁定 B 的本票范围。

RULE:

- 第一轮已知坏空集实现现在被 test_t091_pane_ipc.mjs 的“最后一格关闭→连续重开为空”业务断言拒绝；真实 empty-reopen-b-01 另外证明了实际 UI／后台边界。无需以新文字规则替代该机械检查。
- 完整 argv 的实际 PTY 输入现有断言已能拒绝 M1，避免“日志正确、实际参数丢失”；本轮没有遗留需新增的验收 oracle 缺口。

T-096 REVIEW PASS
