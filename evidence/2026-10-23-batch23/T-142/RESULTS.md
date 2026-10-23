# T-142-1 / a1：INCOMPLETE

实现已完成；后台契约 PASS。真实 Electron + 真实 Claude 的完整链路、T-124 与 T-139/T-143 回归待执行主控在沙箱外运行。T-121 的必跑回归在起点也失败，不能报告整体 PASS。

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
zsh evidence/2026-10-23-batch23/T-142/RUN-OUTSIDE-01.sh
```

每次创建新的 outside-* 目录，保存完整命令、退出码和 JSON，不覆盖旧证据。默认新 e2e 使用 claude-haiku-5-5 的真实交互 CLI，经真实 a2a request、界面批准、调用 terminal_open；点入界面项目层的普通终端，核对 launch.id 并经界面输入 pwd。脚本还运行完整起点红态、cwd-unchecked 变异、T-121、T-124（--gui）、T-139/T-143 和 T-091。RESULT.json 只有全部必需结果满足条件才会标 PASS。

真实 UI 链路尚未在本 session 跑过，不能把后台绿态当成 UI 通过。T-121 当前预计仍会因起点问题使总结果为 INCOMPLETE；由主控结合 T-146-4 裁定。T-133 已知失败不计入本候选。

所有新探针的原始现场保留在 summary.fixture 指向的 /private/tmp/t142-*；包括 run、sqlite、PTY 与未来截图。按派发要求截图不提交，原始现场由执行主控按 T-088 归档；本提交只包含小文本摘要和重放脚本。初始已有的 card.md 派发修订保留原样，未由 worker 修改或纳入 worker 提交。收件箱上报条目由 scripts/inbox 生成，留在 worktree 供主控读取，不纳入本 ticket 代码提交。
