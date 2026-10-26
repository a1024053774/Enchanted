# T-187 结果：增加 agy 与 opencode 的支持并实测

## 状态：PASS（四条验收都有真实入口证据；第五轮独立审查 `T-187 REVIEW PASS`）

## 依据

ticket T-187（ready_rev 1；2026-10-25 起 ready_rev 2）。用户 2026-10-25 原话：“增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”。实测事实见 `facts.md`。worker 权限的决定请求见 inbox `20261025T150744Z-executor-needs-decision-001`。

## 做了什么（终端侧：作主控与普通终端）

- `src/terminalClis.ts` 是唯一的 CLI 登记处。每个 CLI 登记三件事：怎样判断它经过了包装脚本、回合状态从哪里来（钩子还是 OSC 7501）、怎样从命令的环境认出它。新增 agy、opencode。这里还有 OSC 7501 的解析，一条报告被拆在两段输出里也能读出。
- 包装脚本 `terminal/bin/agy`：设 `A2A_SHIM=agy` 和 `AGY_CLI_OSC7501=on`（用户自己设了就用用户的）。agy 没有按会话的指令参数；第五轮起交互启动时加 `--add-dir <开局说明目录>`，agy 读其中的 AGENTS.md（见下“真实运行”）。
- 包装脚本 `terminal/bin/opencode`：设 `A2A_SHIM=opencode`，用 `OPENCODE_CONFIG_CONTENT` 把开局说明作为 instructions 传入，并加 `--standalone`。有子命令、用户自己传了 `--server`/`--standalone`、或用户自己设了 `OPENCODE_CONFIG_CONTENT` 时原样转发。
- 开局说明挪到 `terminal/orientation/AGENTS.md`（第五轮从 `terminal/orientation.md` 再挪一次，好让 agy 按目录读入），只此一份：Claude、Codex 通过 `a2a session-context` 读它，opencode 作为 instructions 读它，agy 作为工作区目录的 AGENTS.md 读它。
- `processArgs.py` 增加读取启动环境里的 `A2A_SHIM`，只读这一个变量。绕过包装脚本启动的 agy、opencode 也会得到 T-184 的“没接入”提示。
- 后台读出项目终端里最后一条 OSC 7501 报告，前台程序退出后清掉。agy、opencode 主控的侧栏与窗格头状态按报告取：working → 运行中；idle、done、clear → 空闲；提问 → 等待用户回答；权限确认、登录、还没有报告 → 未知。
- `a2a request` 改为按 `terminalClis.ts` 认出 CLI：`CLAUDECODE`、`CODEX_THREAD_ID`、`OPENCODE_SESSION_ID`、`A2A_SHIM=agy`，CLI 自己设的变量优先于包装脚本的。角色申请接受登记过的全部 CLI。
- 侧栏“已知缺口”、设置页说明、`workbench/README.md` 同步更新。

## 验证

| 运行 | 结果 | 说明 |
| --- | --- | --- |
| `green-02`（`test_t187_osc_cli_e2e.py`，审查前） | PASS 19/19 | 真实后台、项目终端、Electron。agy、opencode 用原生替身 `t187_fake_cli.c`，按 facts.md 里真实 CLI 的报告格式输出 |
| `red-main-01`（`--revision main`） | 16 项失败 | 角色记成未知 CLI，状态一直未知，绕过包装脚本时不提示，opencode 没有 `--standalone` 也没有开局说明 |
| `mutant-no-carry-01` | 被拒（`opencode_split_report_running`） | 只在单段输出里找报告 |
| `mutant-blocked-is-waiting-01` | 被拒（`agy_permission_unknown`） | 把权限确认也当成等待回答 |
| `mutant-kept-after-exit-01` | 被拒（`opencode_exit_unknown`） | CLI 退出后沿用最后一条报告 |
| `regression-t184-01`、`regression-t185-01` | PASS | 接入判断改用登记表，开局说明改从文件读取，两项回归都通过 |
| `real-opencode-03`（`test_t187_real_opencode_controller_e2e.py`） | PASS | 真实 opencode v2.1.4（默认免费模型 Big Pickle），2 条真实提示。按开局说明运行 `a2a help`、`a2a whoami`、`a2a request executor`，没有在文件系统里找 a2a；申请记成 opencode；侧栏条目的 `data-agent-state` 依次显示空闲 → 等待用户回答 → 空闲，后台状态流为运行中 → 空闲 → 运行中 → 等待用户回答 → 运行中 → 空闲。截图在外置盘 |
| `real-opencode-02` | PASS（后台状态） | 当时还没有核对侧栏 DOM：截图拍在界面刷新前，条目还在转圈。加上 DOM 核对后重跑为 03 |
| `setup-error-01` | 测试自身的错误 | 01：选择器写错（`data-terminal-launch`）。green-01：替身写死申请 executor，第二个终端的申请被拒 |

## 还没做

- 无。

## 已知限制

- agy、opencode 主控：用户对它们说的话和对提问的答复不记入用户输入（这两个 CLI 没有按会话的钩子）。
- agy 作主控须以 `agy --dangerously-skip-permissions` 启动（用户 2026-10-25 选定）；`--mode auto` 下每条命令都要用户在终端确认。
- agy 受管 worker、审查员不经包装脚本，没有开局说明；角色卡照常是首条提示的开头。
- 权限确认、登录时状态显示未知。
- 一个终端里先后运行两个 CLI 且中间没在 shell 提示符下提交过一行时，后一个 CLI 发出第一条报告之前，会短暂沿用前一个 CLI 的最后一条报告。

## 事故

probe-01 把一个临时夹具目录写进了用户 agy 配置的 `trustedWorkspaces`，详见 facts.md。已报告构思主控，没有回退。

## 独立审查第一轮（`review-agy-01.md`，候选 ff3caefbd）：`T-187 REVIEW INCOMPLETE`

- F1（P1，成立）：facts.md 写的是“沿父进程链找”，代码却只按环境变量的登记顺序判断。在 Claude 会话里启动的 opencode 继承了 `CLAUDECODE`，会被认成 claude。修法：只有一个 CLI 的变量匹配时直接用它；有两个以上匹配时，`a2a request` 沿父进程链往上找，取最近的那个（`terminalClis.ts` 的 `commandCli`、`terminalCli.ts` 的 `ancestors`）。测试：终端 C 先 `export CLAUDECODE=1` 再启动 opencode；变异 `env-order`（按登记顺序取第一个）被拒。
- F2（P1，成立）：前台只在用户提交一行后才复查一次。CLI 自己退出、用户没在 shell 里敲回车时，最后一条报告会一直留着。修法：只要还有报告就每 5 秒复查前台。原测试用 `exit` 加回车退出，回车本身就触发了复查，掩盖了这个问题；改为替身 3 秒后自己退出（`leave`）。变异 `enter-only`（只在回车后复查）：01 用旧测试没抓到，归入 setup-error-01；02 用新测试被拒。
- F3（P2）：审查说明里我把 ticket 文件名写错了，实际是 `T-187-antigravity-opencode-cli.md`。
- F4（P2，成立）：报告恰好在开头的 `ESC ] 7501 ;` 中间被拆开时会丢失。修法：输出末尾停在开头标记中间时也保留到下一段；本地按每一个拆分位置都验证过。替身新增 `prefix` 步骤；变异 no-carry-02 在 split 和 prefix 两项上都被拒。
- F5（P2，成立）：没有 `=` 的字段会被切错。改为只解析含 `=` 的字段。
- F6（P3，成立）：替身 opencode 启动时补发探测信号 `?`（oc-01 实测有这一条）。

修后：green-04 PASS 21/21；red-main-02 失败 18 项；变异 no-carry-02、blocked-is-waiting-02、kept-after-exit-03、enter-only-02、env-order-01 都被拒。red-main-02、blocked-is-waiting-02、env-order-01 是在改退出步骤之前跑的，与现行测试只差退出那一步。

## 独立审查第二轮（`review-agy-02.md`，候选 680d59a10）：`T-187 REVIEW INCOMPLETE`

- F1（P2，成立）：`a2a request` 沿父进程链找 CLI 时只看 `argv[0]` 的文件名。npm 安装的 CLI 在进程表里是 `node <路径>/<cli>`，认不出。T-184 的接入判断有同一个问题。修法：`terminalClis.ts` 新增 `cliProgram`，`argv[0]` 是 node、bun 或 deno 时看 `argv[1]`，两处都用它。单独检查 `check_cli_program.ts`：候选 6/6（`check-cli-program-green-01.txt`）；修前的 680d59a10 没有这个函数，直接报错（`check-cli-program-red-680d59a10.txt`）。本机四个 CLI 都是原生二进制，真实运行不受影响。
- F2（P3，成立）：CLI 退出时如果另一个程序立刻占了前台（`opencode; sleep 60`），最后一条报告会一直留到那个程序结束。修法：前台程序不是会自报状态的 CLI 时清掉报告。测试：终端 C 再以 `opencode; sleep 30` 启动；变异 `other-in-front`（去掉这一行）被拒。
- F3（P3，不成立）：`opencode --help` 写明唯一的位置参数是目录（`opencode <subcommand> [flags] [<directory>]`），非目录的首参数在 opencode 自己的语法里就是子命令，包装脚本原样转发是对的。核对时发现一个相关的真缺口：交互子命令 `mini` 经包装脚本原样转发，拿不到开局说明。它是否接受 `--standalone` 没有实测，记入已知限制。

修后：green-05 PASS 23/23；变异 other-in-front-01、env-order-02（补丁随新代码更新）被拒；T-184 回归 regression-t184-02 PASS 8/8。

## Git 元数据守护（ready_rev 2，验收第 1 条）

用户 2026-10-25 选“C 两者都作 worker”，选项原文：“agy 用 --dangerously-skip-permissions 全放开，只靠门禁事后检查；Git 元数据可能被改，每次派发写一次 ~/.gemini”。

- 门禁在认领建好 worktree 后读一次 Git 元数据（`core.ts` 的 `gitMetadata`），记在 attempt 上：worktree 的 HEAD、仓库 config、worktree config、hooks 目录里每个文件（权限位加内容的 sha256，代替把文件本身存进 attempt）。
- verify 时在路径边界检查之前比对（`checkGitMetadata`）。有改动就以 `git_metadata_changed` 拒绝交付，点名改了什么，记为一次“路径边界”打回并回写 worker；不跑完成条件，不审查，不集成。
- refs 的判定：用户在同一仓库里照常提交、建分支、切换，所以不能拿 refs 前后对比。规则是含有 worker 提交（`base..候选`）的 ref 算 worker 的改动；attempt 自己的分支和门禁的 `refs/a2a/` 本来就含，不算。
- 所有 worker 都走这一检查，不按 CLI 区分。Codex、Claude worker 有操作系统沙箱，正常不会触发。

| 运行（`test_t187_git_metadata_guard_e2e.py`） | 结果 | 说明 |
| --- | --- | --- |
| `guard-green-05`（第三轮修后） | PASS | 同下，加 merged 案例：worker 提交后、交付前，用户在 main 上提交并被合进 worker 分支，照常通过 |
| `guard-green-02` | PASS | 真实后台、门禁、终端主控、Claude Code worker 与审查员（脚本化模型）。交付后、验收前由测试从外面改动：放 hooks/post-merge、设 core.fsmonitor、分离 worktree HEAD、把候选挂到新分支并移动已有标签，四个都被拒并点名；正例中用户同时在主 checkout 建分支、提交、切换，照常通过审查并集成 |
| `guard-red-main-01`（`--revision main`） | 16 项失败 | 修前四个反例都被验收 |
| `guard-mutant-refs-ignored-01`、`-config-ignored-01`、`-head-ignored-01` | 各在自己的案例上被拒 | 只看一部分元数据 |
| `guard-mutant-own-branch-counted-01` | 正例被拒 | 把 attempt 自己的分支也当成泄漏 |
| `setup-error-01/guard-green-01-head-made-a-ref` | 测试自身的错误 | head 案例的篡改步骤顺手建了一个指向候选的分支，门禁把它也点了名（判断正确），期望写漏；改为只分离 HEAD |

已知限制：worker 把别的 ref 删掉、回退，或挂到不在候选历史里的提交上，这一规则认不出（无法和用户自己的操作区分）。集成分支被动过时，集成本身的 CAS 会拒绝。

## 独立审查第三轮（`review-agy-03.md`，候选 105cbaa7c）：`T-187 REVIEW INCOMPLETE`

- F1（P1，成立）：守护用认领时的 base 算 worker 提交。集成分支在认领后前进、又被合进候选（冲突返工或 worker 自己合并）时，集成分支本身被当成泄漏 ref，交付必被误拒。修法：worker 提交改为 `rev-list 候选 ^base ^集成分支头`。测试：新增 merged 案例；修前的 main 上 `guard-red-main-merged-03` 失败（main 没有守护），变异 `base-only`（回到只排除 base）`guard-mutant-base-only-03` 被拒。
- F2（P2，不成立）：审查认为 `for-each-ref` 的多个 `--contains` 是“与”。实测是“或”：只含 W1 的 `leak` 也被列出（`check_for_each_ref_contains.sh`、`check-for-each-ref-contains-01.txt`，git 2.52.0）。
- F3（P2，成立）：候选里的 ticket 还是 ready_rev 1。rev 2 在 main 上，已把 main 合进 exec/t187。
- F4（P3，成立）：补上变异 `hooks-ignored`，`guard-mutant-hooks-ignored-03` 在 hooks 案例上被拒。

## agy、opencode 作 worker 与审查员（ready_rev 2）

设计见 `worker-design.md`，README 有对应一节。要点：
- 任务卡 `executor.cli` 接受 `agy`、`opencode`。启动参数：agy `--dangerously-skip-permissions --model --effort`、`AGY_CLI_OSC7501=on`；opencode `--standalone --auto <worktree>`、模型经 `OPENCODE_CONFIG_CONTENT`。在用户自己的 HOME 运行，不复制凭据。
- 回合取自 OSC 7501（`panes.ts` 的 `reportedTurns`、`reportedStop`，后台 `daemon.ts` 的 `reportedTurnEnd`）：回合结束时 worker 的交付请求经与 Stop 钩子相同的转交路径进门禁；审查员把结论写进 `review-result.json`。
- 交付事实：这两个 CLI 报不出本回合的模型与强度，门禁对它们接受 `unknown`，交付与尾注都记 `unknown`（`core.ts` 的 `delivery_facts_unknown` 检查）。
- agy 信任：核对画面（目录、选中项）后才按回车，再核对 settings.json 只有 `trustedWorkspaces` 多了这一个目录；条数记在 `agy_trust_written`。
- 审查员：审查 checkout chmod 只读，门禁的审查启动检查核对不可写。

| 运行（`test_t187_managed_worker_e2e.py`） | 结果 | 说明 |
| --- | --- | --- |
| `worker-green-agy-02` | PASS | 真实后台、门禁、终端主控；agy 替身作 worker 与审查员。启动参数与环境、侧栏运行中 → 空闲、交付、审查通过、集成、尾注 unknown；信任写入 2 条（worker、审查员各一），其他键不变 |
| `worker-green-opencode-02` | PASS | 同上，opencode 替身 |
| `worker-green-agy-trust-no-02` | PASS | 信任框选中的是 “No, exit”：不按键，记 `agy_trust_failed`，settings 不变，没有交付，侧栏未知 |
| `worker-red-main-02`（`--revision main`） | 被拒 | 修前任务卡不接受 agy（`invalid_task_card`） |
| `worker-mutant-reviewer-writable-02` | 被拒 | 审查 checkout 不 chmod：门禁 `review_launch_boundary` |
| `worker-mutant-trust-unchecked-02` | 被拒 | 不看画面就按回车：trust-no 案例失败 |
| `worker-mutant-facts-required-01` | 被拒 | 要求观察到模型与强度：交付 `delivery_facts_unknown`，任务停在未交付 |

回归（同一份最终源码）：`green-07`（终端侧）PASS，`regression-t184-04` PASS，`regression-t180-02` PASS，`guard-green-05` PASS。

开发中暴露并修掉的问题（现场在 `setup-error-01/`）：
- `worker-dev-01-fake-no-version`：替身不认 `--version`，后台取版本时卡住（测试自身）。
- `worker-dev-02-trust-idle-race`：agy 在信任写入核对完成之前就报了 idle，会话一直没被当成已启动。修法：核对完成时若已报过 idle 就启动（`reportedStart`）。
- `worker-dev-03-delivery-facts`：门禁要求观察到模型与强度，交付被拒；见上“交付事实”。
- `guard-green-03-…`、`guard-mutant-base-only-01-…`：源码在运行中被我改动，作废。`guard-mutant-hooks-ignored-01-…`：变异补丁删掉整行后语法错误，改为把条件换成 false。`guard-red-main-merged-01-…`：测试的 else 分支让 merged 案例也执行了 clean 的步骤。
- `worker-dev-04-…`：测试在审查会话回收前就集成（`operation_busy`），改为等 `review_reclaimed`。
- 另有一次回归：`panes.ts` 里新加的局部变量 `cli` 遮住了模块级的 gate CLI 路径，Claude worker 的钩子命令变成 `node 'Claude Code' …`，会话开始钩子报 `MODULE_NOT_FOUND`。修前的 main 上同一案例通过，改名后通过。`superseded/` 是修这些之前的一批运行。

已知限制：后台重启后不恢复 agy、opencode 的受管窗格；回合内工具调用不逐条记录；agy worker 没有开局说明；opencode 没有按会话的思考强度参数。

## 独立审查第四轮（`review-agy-04.md`，候选 0a56efa44）：`T-187 REVIEW INCOMPLETE`

INCOMPLETE 的理由只是真实 worker 运行还没做；没有 P0–P2。两条 P3 记为限制，不改：
- F1：`agyTrust` 要求 `~/.gemini/antigravity-cli/settings.json` 已存在。没登录过 agy 的 HOME 没有这个文件，也跑不了无人值守的 agy；这时记 `agy_trust_failed`、不按键。
- F2：opencode 受管启动不传额外目录。opencode 没有对应的放行参数，`--auto` 下也没有 OS 沙箱；建窗格与门禁复核用同一个构造，两边一致。

## 真实运行（验收第 2 条）

`test_t187_real_worker_e2e.py`：隔离后台与 Electron，CLI 用用户本机安装与真实 HOME（用户 2026-10-25：“用我电脑原生的就行,隔离 HOME 可能不太行”），不登录、不复制凭据。项目终端里启动一种 CLI → 让它申请执行主控 → 测试代用户在界面批准 → 主控运行测试写好的 dispatch.sh、verify.sh、integrate.sh（命令仍以主控自己的终端身份执行，脚本只免去模型手抄 JSON）→ 另一种 CLI 的 worker 交付 → 同 CLI 的审查员只读审查 → 门禁集成。每次 4 条真实提示。截图与屏幕文本含 agy 账号邮箱，只在外置盘（各目录 `fixture.archive.json`）。

| 运行 | 结果 | 说明 |
| --- | --- | --- |
| `real-worker-opencode-agy-03` | PASS 8/8 | opencode 主控（申请记 opencode）→ agy worker（`gemini-3.8-flash-high`、high）。侧栏 worker 未知 → 运行中 → 空闲；审查员 agy 只读审查“可合并”（4 个变异全被完成条件拒绝）；集成后 main 有 done.txt；尾注 `A2A-Tool: 1.4.7`、`A2A-Model: unknown`、`A2A-Effort: unknown`。**agy 信任写入用户 `~/.gemini/antigravity-cli/settings.json` 共 2 条**：worker worktree 与审查 checkout 各一条（都在已删除的 /private/tmp 夹具下），其他键不变 |
| `real-worker-agy-opencode-05` | PASS 8/8 | agy 主控（`agy --dangerously-skip-permissions`，项目目录在已信任的 `/private/tmp/t187-probe/repo`）自己读开局说明、运行 `a2a request executor`，申请记 agy → opencode worker（`opencode/big-pickle`）→ opencode 审查员“通过” → 集成；尾注 `A2A-Tool: opencode v2.1.4`、模型强度 unknown。信任写入 0 条 |

本组开发中的失败（现场保留）：
- `setup-error-01/real-worker-opencode-agy-01-idle-wait-mark`、`-02-pane-not-yet`、`-03-done-not-end`（agy 那条在 `setup-error-01/real-worker-agy-opencode-03-done-not-end`）：测试自身问题（等回合结束的起点、窗格尚未建好就查、agy 以 done 结束未再报 idle）。
- `real-worker-agy-opencode-01`：**产品缺口**。agy 主控没有开局说明，不知道 `a2a request`，只回复“已就绪”，角色申请超时。修法：包装脚本交互启动时 `--add-dir terminal/orientation`，开局说明改名为该目录下的 AGENTS.md。实测：`agy --print` 加 `--add-dir <只含 AGENTS.md 的目录>` 能按其中的指令作答，信任列表条数不变。替身测试 `green-08` PASS（新检查 `agy_orientation_same`）；`red-head-orientation-01`（`--revision HEAD`，修前）只有 `agy_orientation_same` 失败。
- `real-worker-agy-opencode-02`：开局说明生效（agy 自己运行了 `a2a help`），但 `--mode auto` 下 agy 对每条 shell 命令弹权限框，测试不代批，申请超时。agy 没有按会话的命令白名单；用户选“主控也用全放开”，README 写明。
- `real-worker-agy-opencode-04`：**产品缺陷**。真实 opencode worker 的首个任务丢了（`turn_start_missing`，停在 claimed）：后台在 opencode 第一次报 idle 时就粘贴，opencode 那时还不收输入。探针 `opencode_paste_probe.py`（`opencode-paste-probe-01.txt`）：idle 时粘贴 3/3 丢失；idle 后第一次显示光标（ESC[?25h，约 0.36 s 后）时粘贴 3/3 进入回合。修法：`terminalClis.ts` 给 opencode 登记 `inputAfterCursor`，`panes.ts` 的 `reportedTurns` 对它在首次 idle 之后看到光标显示才算会话已启动、才派发。替身按真实行为改为 idle 后 1 秒、显示光标前丢弃输入：`worker-green-opencode-03` PASS，`worker-red-head-cursor-01`（`--revision HEAD`，修前）失败于 `submitted`，`worker-green-agy-03` PASS（agy 不受影响）。

清理：每次运行的夹具与 `/private/tmp/t187-probe/repo` 归档外置盘后删除；一次运行残留的测试后台进程已结束。

## 独立审查第五轮（`review-agy-05.md`，候选 cee251cda）：`T-187 REVIEW PASS`

没有 P0–P2。一条 P3 记为限制：包装脚本只在没有参数或第一个参数以 `-` 开头时加开局说明目录；以后 agy 若支持把路径作为第一个参数启动，这种启动拿不到开局说明。当前 agy 1.4.7 没有这种用法。

回归（本轮最终源码）：`regression-t184-05` PASS、`regression-t185-02` PASS（开局说明改路径后 Claude、Codex 照常读到）。

## 验收对照

| 验收 | 结论 | 证据 |
| --- | --- | --- |
| Git 元数据守护 | PASS | `guard-green-05`；反例 `guard-red-main-merged-03` 与变异 base-only、hooks-ignored 等被拒（见“Git 元数据守护”一节） |
| 真实 agy、opencode 各走一遍 | PASS | `real-worker-opencode-agy-03`、`real-worker-agy-opencode-05`；截图在外置盘 |
| worker 状态在侧栏正确，做不到的显示未知 | PASS | 真实运行侧栏 worker 未知 → 运行中 → 空闲；替身 `worker-green-*`、`green-08` 覆盖等待回答（主控）、权限与登录显示未知。按 T-124 裁定 1a，worker 的提问记录不显示为等待 |
| AGENTS.md 与 README 同步 | PASS | AGENTS.md 第 23、33 行；README agy/opencode 各节 |

agy 信任写入用户 `~/.gemini/antigravity-cli/settings.json` 的条数：本 ticket 的真实运行共写入 2 条（`real-worker-opencode-agy-03` 的 worker worktree 与审查 checkout），只动 `trustedWorkspaces`；此外是 facts.md 记录的探针误写 1 条（用户选择保留）。替身测试都用夹具 HOME，不写用户配置。
