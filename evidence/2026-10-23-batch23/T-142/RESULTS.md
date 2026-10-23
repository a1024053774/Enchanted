# T-142-1 / a1：INCOMPLETE

实现已完成；后台契约 PASS。执行主控已运行 RUN-OUTSIDE-01：T-124、T-139/T-143 通过，T-091 与起点一致；完整链路的 green/red/mutant 均被 Claude auto mode 计费说明对话框挡住而超时。测试夹具已固定 default 权限模式，并补上 Claude 2.1.309 的 hasSeenAutoDefaultNudge 标志，待 RUN-OUTSIDE-03 复验；整体仍为 INCOMPLETE。T-121 由执行主控本轮裁定交 T-147，不计入 T-142。

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
zsh evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-03.sh
```

每次创建新的 outside-03-* 目录，保存完整命令、退出码和 JSON，不覆盖旧证据。新脚本只重跑 green/red/mutant；产品代码未改，已通过的回归不重复跑。默认新 e2e 使用 claude-haiku-5-5 的真实交互 CLI，经真实 a2a request、界面批准、调用 terminal_open；点入项目层普通终端，核对 launch.id 并经界面输入 pwd。

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
- 静态检查：`zsh -n evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-03.sh`、`PYTHONPYCACHEPREFIX=/private/tmp/t142-pycache python3 -m py_compile workbench/tests/test_t142_terminal_open_e2e.py`、`git diff --check` 通过。RUN-OUTSIDE-03 尚未执行，完整 UI 绿态、起点红态、变异与独立验收仍为 INCOMPLETE，交执行主控继续确认。

所有新探针的原始现场保留在 summary.fixture 指向的 /private/tmp/t142-*；包括 run、sqlite、PTY 与未来截图。按派发要求截图不提交，原始现场由执行主控按 T-088 归档；本提交只包含小文本摘要和重放脚本。初始已有的 card.md 派发修订保留原样，未由 worker 修改或纳入 worker 提交。收件箱上报条目由 scripts/inbox 生成，留在 worktree 供主控读取，不纳入本 ticket 代码提交。
