# T-142-1 / a1：INCOMPLETE

实现已完成；后台契约 PASS。真实 Claude Code 2.1.309 的成对探针已证实：相同隔离 home/settings 下，裸 a2a call 成功；增加输出重定向后出现结构化权限拒绝，即使 out/ 已在 additionalDirectories 内。完整测试现改为让 Claude 执行裸命令，读取绑定 tool_use_id 的原始工具回执并与后台 launch 交叉核对。RUN-OUTSIDE-05 的完整 UI 绿态、起点红态、变异仍待主控沙箱外确认，整体 INCOMPLETE。已通过的 T-124、T-139/T-143 与 T-091 不更差结论保留，T-121 按主控裁定交 T-147，不计入 T-142。

## 改动

- `daemon.ts`：角色申请已批准的终端主控可调用 `terminal_open`；项目从角色绑定读取，显式指定其他项目被拒。cwd 必须为存在的绝对目录，经 realpath 后位于项目主目录或额外目录内。
- 复用 `panes.startShell`：新终端为项目普通 zsh，task、attempt、session、fence 都为空，回执的 `launch.id` 为终端标识。已有侧栏轮询会展示它，用户点入；没有新增通知协议或自动切换焦点。
- `terminalCli.ts` 支持 `a2a call terminal_open --cwd '<绝对目录>'`，JSON 形式也可用。更新 help、插件 SKILL.md 与 README。
- 未改 panes.ts、sidebar.ts、Electron main/renderer、受管 CLI 参数、门禁和 oracle_paths。

## 已运行的证据

同一真实后台、socket、PTY、zsh、a2a CLI 契约探针：

```sh
python3 workbench/tests/test_t142_terminal_open_e2e.py --backend-only --summary evidence/2026-10-23-batch23/T-142/green-backend-02.json
python3 workbench/tests/test_t142_terminal_open_e2e.py --backend-only --revision c113e71203bd37e151241b6ce44bd4bf773e356f --summary evidence/2026-10-23-batch23/T-142/red-revision-backend-01.json
python3 workbench/tests/test_t142_terminal_open_e2e.py --backend-only --mutant cwd-unchecked --summary evidence/2026-10-23-batch23/T-142/mutant-backend-02.json
```

| 检查 | 结论与证据 |
| --- | --- |
| 实现前红态 | `red-02.json`：退出 1，main_opened 收到 role_command_not_scoped。 |
| 显式起点红态 | `red-revision-backend-01.json`：同样退出 1、role_command_not_scoped。 |
| 候选绿态 | `green-backend-02.json`：退出 0、20 项 PASS；主目录、子目录与额外目录的真实 pwd 正确，返回标识在项目普通终端目录中，不在任务布局中。 |
| 边界反例 | 同一绿态：同前缀兄弟目录、符号链接逃逸、未批准会话、本项目主控指定其他项目、其他项目已批准主控指定本项目均被拒。 |
| 变异 | `mutant-backend-02.json`：删除 cwd 范围检查后退出 1；兄弟目录被错误打开，sibling_refused 捕获。 |
| T-121 | `regression-t121-01.json` 与 `baseline-t121-01.json` 均退出 1，前 43 项通过后在 sidebar_drops_closed_controller 失败。已上报 `20261023T151510Z-worker:b23-t142-issue-001`，正文见 issue-t121.md；不修改 sidebar.ts。 |
| T-091 | 加 `--experimental-vm-modules` 的 `regression-t091-02.json` 与 `baseline-t091-01.json` 均退出 1，IPC handler 名单断言失败；status、checks、error 和三项已知坏实现结果完全一致，无更差。 |
| 静态检查 | `git diff --check`、`zsh -n RUN-OUTSIDE-01.sh`、`PYTHONPYCACHEPREFIX=/private/tmp/t142-pycache python3 -m py_compile workbench/tests/test_t142_terminal_open_e2e.py`、`node workbench/src/terminalCli.ts help` 通过。 |

T-091 命令：`node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs <新summary路径>`；基线另带 `--source /private/tmp/t142-ipc-base-tbbxm2u7/source`（该隔离源由共享夹具的 source_tree 按起点 revision 导出）。T-121 命令见各 summary.argv。

首轮 `red-01.json` 因起点不识别命名形式，stdout 为空而超时；它不作为 role_command_not_scoped 红态。`regression-t091-01.json` 未加 VM 开关，是运行参数错误；不作为产品回归。首次 py_compile 受系统 PYTHONPYCACHEPREFIX 指向用户缓存影响报权限错误，改用 /private/tmp 后通过。失败记录均保留。

## 待沙箱外运行

```sh
zsh evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-05.sh
```

每次创建新的 outside-05-* 目录，保存完整命令、退出码和 JSON，不覆盖旧证据。新脚本只重跑 green/red/mutant；产品代码未改，已通过的回归不重复跑。默认新 e2e 使用 claude-haiku-5-5 的真实交互 CLI，经真实 a2a request、界面批准、调用 terminal_open；点入项目层普通终端，核对 launch.id 并经界面输入 pwd。

## RUN-OUTSIDE-01 回传与夹具修正（2026-10-23）

- 执行主控回传目录：`outside-20261023T153047Z-v7ZOxk`。T-124、T-139/T-143 为 PASS；T-091 与起点一致。T-121 仍在 sidebar_drops_closed_controller 失败；主控明确裁定：“t121 失败是已知的裁定 B 冲突，由 T-147 修改 T-121 断言处理，不算你的。”未修改 T-121。
- 三个完整链路均为“main 开终端回执”超时，不能作为红态或变异证明。夹具 `/private/tmp/t142-ww34jo3s` 的主控 PTY（launch `3aaa45ad-a15d-491f-862b-1e07a0c3e071`）可见 auto mode 计费说明。已核对 Bash 调用被该说明挡住；没有发送 Enter/Esc 关闭它。
- 仅在新测试夹具的隔离 home 写 `permissions.defaultMode="default"`，保留 `Bash(a2a request:*)`、`Bash(a2a call:*)` 两条 allow。summary.observed.fixture_permissions 记录实际写入配置。未改产品代码、全局配置、Claude 版本或模型。
- RUN-OUTSIDE-02 的 red 必须退出 1、完成真实角色申请和界面批准、在 main_opened 收到 role_command_not_scoped；mutant 必须退出 1、完成三个目录的界面 pwd 核对，再于 sibling_refused 捕获错误放行。另核对夹具配置与清理错误；相同超时不能使 RESULT.json 通过。
- 本轮静态检查：`zsh -n evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-02.sh`、`PYTHONPYCACHEPREFIX=/private/tmp/t142-pycache python3 -m py_compile workbench/tests/test_t142_terminal_open_e2e.py`、`git diff --check` 通过。`run02-checker-negative.json` 记录新汇总器对上一轮三个超时 summary 的实际拒绝：退出 1，red_expected_refusal 与 mutant_caught 均为 false。该检查不代表修正后的 UI 链路通过。
- RUN-OUTSIDE-02 已执行，回传及后续修正见下节；RUN-OUTSIDE-01、旧 summary 和原始现场均保留。

## RUN-OUTSIDE-02 回传与夹具修正（2026-10-23）

- 证据目录：`outside-02-20261023T154933Z-uhlQPc`。green/red/mutant 均在“执行主控申请”超时，未形成产品红态或变异证明。green 夹具 `/private/tmp/t142-1mg9k2cq` 的主控 PTY（launch `e465a31e-4bfd-408c-b83b-80f99ab9df2f`）可见“Make auto mode your default permission mode?”。
- 执行主控已核对 Claude Code 2.1.309 安装包的 mJr 条件：hasCompletedOnboarding 为真、缺少 hasSeenAutoDefaultNudge，且 userSettings 配了非 auto defaultMode 时出现此提示。本轮按指令在隔离 home 的 `.claude.json` 中与 hasCompletedOnboarding 并列写 `hasSeenAutoDefaultNudge: true`；保留 `permissions.defaultMode="default"` 与原 allow 规则。测试失败方式第 7 条记录了版本、两个提示及处理条件。未新增发送 Enter/Esc 关闭提示的代码，未改产品代码或用户全局配置。
- 新的 RUN-OUTSIDE-03 只重跑 green/red/mutant，创建独立 outside-03-* 目录；沿用具体业务断言、退出码、界面 pwd 与清理检查，不接受同一个超时。`run03-checker-negative.json` 记录新脚本对 RUN-OUTSIDE-02 三个“执行主控申请”超时的拒绝，red_expected_refusal、mutant_caught 均为 false。
- 静态检查：`zsh -n evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-03.sh`、`PYTHONPYCACHEPREFIX=/private/tmp/t142-pycache python3 -m py_compile workbench/tests/test_t142_terminal_open_e2e.py`、`git diff --check` 通过。RUN-OUTSIDE-03 已执行，回传及后续修正见下节。

## RUN-OUTSIDE-03 回传与夹具修正（2026-10-23）

- 证据目录：`outside-03-20261023T162737Z-KqE4Kr`。green/red/mutant 仍在“main 开终端回执”超时，未形成产品红态或变异证明。执行主控核对 green 夹具 `/private/tmp/t142-1cme1k11` 的 PTY 后回传：Claude 已发出真实 Bash(a2a call ... > out/main.json)，但弹出项目目录外写入的确认；原 Bash allow 规则仅放行命令，没有放行 out/ 的写入。
- 本轮仅在隔离 settings.json 的 permissions 中加入 `additionalDirectories: [str(fixture.out.resolve())]`，数组只含该夹具专用 out/ 的真实路径；defaultMode、两条 allow、hasSeenAutoDefaultNudge 及交互逻辑保留。注释第 7 条补充了此失败方式。未发送确认按键，未修改产品或全局配置。
- RUN-OUTSIDE-04 创建新的 outside-04-* 目录，仅重跑 green/red/mutant。汇总器按每个独立 fixture 的 out/ 路径核对完整 permissions，拒绝缺少该目录或扩展到其他目录的配置；原有具体红态、变异、退出码与界面 pwd 检查保留。
- 本轮 `zsh -n evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-04.sh`、`PYTHONPYCACHEPREFIX=/private/tmp/t142-pycache python3 -m py_compile workbench/tests/test_t142_terminal_open_e2e.py`、`git diff --check` 通过。`run04-checker-negative.json` 记录新汇总器对 RUN-OUTSIDE-03 缺少 additionalDirectories 且超时的三个旧结果均拒绝；这不是新 UI 链路的通过证据。
- RUN-OUTSIDE-04 已执行，结果未通过；实测归因和后续改动见下节，既有证据均保留。

## RUN-OUTSIDE-04 回传、最小探针与事实门禁（2026-10-23）

REALITY GATE: PASS（仅指选择“模型不重定向、测试读取原始回执”的方向；完整 UI 验收 INCOMPLETE）

- GOAL / NON-GOALS：区分相同 a2a call 加输出重定向是否改变 Claude 权限判定；不继续放宽权限，不发按键关确认框，不改产品实现。
- OBSERVED：`outside-04-20261023T163652Z-Yzeocp` 三项仍在 main 开终端回执超时。主控核对 `/private/tmp/t142-cc9t4odw` 的设置已含 out/，但重定向命令仍弹确认。此前“加 additionalDirectories 就能解决”未经实测支持，RUN-OUTSIDE-04 已否定其有效性。
- PROBE：`workbench/tests/probe_t142_bash_redirect.py`，复用真实后台、项目终端、已批准角色和同一隔离 home/settings，真实 Claude `-p --model claude-haiku-5-5 --output-format json` 配本地脚本化接口。两次模型 Bash 命令完全相同，B 仅增加 `> '<fixture.out>/main.json'`。外层 zsh 捕获 CLI 报告，不属于被测模型工具命令。`PROBE-01.sh` 可在新目录复放。
- MEASURED：`probe-local-02.json`（CLI 2.1.309；fixture `/private/tmp/t142-probe-ttsfzrga`）。A：permission_denials=[]，后台新终端 1 个，工具返回 ok=true 与 launch；B：permission_denials 明确指向带重定向的 Bash，后台新终端 0 个，目标文件不存在。两次 CLI 退出均为 0，因此退出码不能代替权限证据。
- 根因证据：B 的真实 tool_result 写明 `Output redirection ... needs approval`，并明确该路径已在 session working directories 中。这证实本场景是 Bash 输出重定向的写入审批，不是 a2a 返回被门禁拒绝，也不是 additionalDirectories 未加载。print 模式记录的是结构化拒绝；交互确认框由主控前一轮 PTY 提供独立佐证。不推断所有版本或其他重定向形式的规则。
- UNKNOWN / STOP：原始交互 UI 尚未验证新收集路径，交 RUN-OUTSIDE-05；如不是预期业务断言失败，保留现场，不改权限碰运气。
- 首轮探针 `probe-local-01.json` 因 Claude 在用户 prompt 前附 system-reminder，脚本化计划的标签定位失败；修正为只匹配 prompt 末尾的探针标签后取得第二轮结果。首轮不是权限证据，保留原始失败。

## 依据探针的最小修正与 RUN-OUTSIDE-05

- 模型的三个 terminal_open 命令均移除重定向。测试从真实 CLI 发往脚本化接口的 tool_result 中，按 tool_use_id 和完整命令绑定原始回执；summary.observed.tool_returns 保留命令、原文与 is_error。JSON 前可能有 Bash 的非零退出码提示，只解码其中原始 JSON，不让模型转述结果。
- 回执仍须 ok=true、项目/cwd/普通终端身份正确；新增完整 launch 与后台 workbench_snapshot.launch 一致的断言。保留实际 zsh pwd、界面 launch.id 与 pwd、项目普通终端目录、任务隔离和全部拒绝反例。backend-only 由测试自己的 zsh 捕获 stdout，不让 Claude 写回执文件。
- 权限和启动配置保持 RUN-OUTSIDE-04 的同一套，不新增批准规则。主目录 JSON 形式、额外目录与子目录的命名参数形式仍通过真实 CLI。
- `green-backend-05.json` PASS（23 项，含三个回执与后台一致检查）；`red-revision-backend-05.json` 退出 1、main_opened 收到 role_command_not_scoped；`mutant-backend-05.json` 退出 1、sibling_refused 捕获放行。这些是后台证据，不代表交互 UI 通过。
- `RUN-OUTSIDE-05.sh` 仅重跑完整 green/red/mutant，另核对绑定命令的原始工具回执、命令不带重定向、回执与后台一致。原有角色申请/界面批准、具体红态、变异、界面 pwd 和退出码检查保留。`run05-checker-negative.json` 证明新汇总拒绝 RUN-OUTSIDE-04 的超时及缺失回执，避免把环境失败当业务反例。
- 静态检查：新 Python 探针和 e2e 的 py_compile、PROBE-01.sh 与 RUN-OUTSIDE-05.sh 的 zsh -n、git diff --check 通过。复放探针：`zsh evidence/2026-10-23-batch23/T-142/PROBE-01.sh`；本地实测命令见 probe-local-02.json.argv。完整 UI、红态、变异及独立验收仍交主控，INCOMPLETE。

所有新探针的原始现场保留在 summary.fixture 指向的 /private/tmp/t142-*；包括 run、sqlite、PTY 与未来截图。按派发要求截图不提交，原始现场由执行主控按 T-088 归档；本提交只包含小文本摘要和重放脚本。初始已有的 card.md 派发修订保留原样，未由 worker 修改或纳入 worker 提交。收件箱上报条目由 scripts/inbox 生成，留在 worktree 供主控读取，不纳入本 ticket 代码提交。
