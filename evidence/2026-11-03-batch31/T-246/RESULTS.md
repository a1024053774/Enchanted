# T-246 结果（2026-11-03）

结论：**PASS**（复审的阻塞：第 2、3 条已修，第 1 条附证据答复为已知局限；按 T-240 不再开审查轮。Codex 在普通终端里嵌套运行没有端到端跑过）。普通终端的原生会话报告（“复制深度链接”与后台给终端的 `native_session`）改为按报告它的进程分别保存，只用前台进程自己报的。真实 Claude Code 端到端：外层 Claude 用 Bash 工具运行内层 `claude -p`，修前内层运行时链接不可用、`native_session` 变成内层的；修后内层运行时、结束后、后台重启后都是外层的。

用户：“做 T-246”。

## 票面时序能不能到

票面写的是“A 退出后它的钩子才到”。真实钩子助手（`src/terminalCli.ts` 的 `hook`）在钩子运行时沿进程祖先找 CLI 的进程号；A 已退出时钩子进程已被收养，祖先里没有 claude，请求不带 `cli_pid`，后台不会调用 `noteShellHook`。所以这条时序只在助手已算出进程号、请求却晚了几秒才送到时才会出现，没有复现。

同一条不变式（报告只属于报告它的进程）有一条经真实入口就能到的路径：前台 CLI 里再跑一个 CLI。外层 Claude 的 Bash 工具运行 `claude -p`，内层同样经过包装脚本、带 Enchanted 钩子，它的钩子带着内层的进程号与会话号到达，顶替了外层的报告。本票按这条路径复现与验证。

## 改动

- `workbench/src/byProcess.ts`（由 T-242 的 `shellTurns.ts` 改名、泛化为 `ByProcess<T>`）：按进程号保存报告并记下到达时间；前台记为进程号加启动时间，只给出前台进程启动之后到达的、它自己进程号下的那条；已退出进程的那条，以及前台进程号下早于它启动的那条，在下一次记录或前台复查时清掉。回合状态（T-242）与原生会话报告（T-195）共用。（审查后的写法，见末节）
- `workbench/src/panes.ts`：
  - `nativeReports` 取代单槽位的 `nativeReport`；同一进程的报告没变就不再记 `shell_native_session`。
  - 后台重启时按全部 `shell_native_session` 记录重建每个进程最后一条，到达时间取记录的时间（只取最后一条可能是内层的）。
  - 前台读取（`foreground`）多给出前台进程的启动时间（libproc，`processSnapshot.py`；只有读不到前台组的特权行没有它，那种行的 `tpgid` 为 -1，不会被选为前台）。
  - 打开普通终端窗口时，`pane_layout_opened` 只记前台 CLI 自己报的会话，不沿用以前布局里记的（审查非阻塞）。
  - 普通终端的 `pane.native` 改为前台进程自己报的会话：前台复查与 `shellNative` 读到前台时、钩子到达时更新；前台没有报过会话的 CLI（含 CLI 退出后、前台复查第一次看到它之前）为 `null`。以前它一直留着最后到达的会话。普通终端的 `pane.native` 只用于 `pane_status` 与 `pane_layout_opened` 的记录，普通终端不走恢复路径。
  - `status` 的 `hook_turn` 多带报告进程的 `pid`；侧栏只读 `cli` 与 `state`。
- `workbench/README.md`：深度链接一节写明按进程保存、内层 CLI 不顶替。
- `workbench/tests/test_t242_shell_turns.ts` 改名为 `test_by_process.ts`（改用 `ByProcess`）；`test_t242_shell_hook_turn_e2e.py` 的变异体补丁串随之改到 `byProcess.ts`。

## 证据

新测试 `workbench/tests/test_t246_nested_cli_native_e2e.py`：隔离夹具、真实后台与私有 hc core、经包装脚本运行的真实 Claude Code（外层与内层都是 `claude-haiku-5-5`，模型由脚本化 API 应答，内层的模型请求由测试扣住）。外层以 `--permission-mode default --allowedTools Bash` 启动。会话号的预期来自 Claude Code 自己的记录文件（含外层唯一标记的那个会话）。

| 文件 | 结果 |
| --- | --- |
| `nested-red-head.json`、`.log` | 修前（当时的工作区即 `b48248a22`）：失败于“内层运行时链接是外层的”：链接不可用（报告是内层的，进程号与前台不符），`native_session` 是内层的会话 |
| `nested-green.json`、`.log` | 修后 PASS，六项：内层运行时链接与 `native_session` 是外层的；内层结束后仍是；后台重启后链接仍是外层的；外层退出后链接不可用 |
| `nested-mutant-last-report.json`、`.log` | 变异体（取最后到达的报告，不看前台）：失败于“内层运行时”，链接给出内层的会话 |
| `nested-mutant-last-recorded.json`、`.log` | 变异体（重启只按最后一条记录恢复）：前四项通过，失败于“后台重启后”，链接不可用 |
| `search/green.txt` | `test_by_process.ts` 对 `ByProcess` 穷举长度 0～6 的全部 1,111,111 个事件顺序 PASS |
| `search/mutants.txt` | 单槽位、不看前台、不清退出进程三个坏实现分别失败于 I2、I1、I3 |
| `regress-t195_native_link.json`、`.log` | `test_t195_native_link_e2e.py`（深度链接，含终端 Claude 的 /clear 与退出、受管 Claude 与真实 Codex）PASS |
| `regress-t242_shell_hook_turn.json`、`.log` | T-242 回合状态端到端 PASS |
| `regress-t242-mutant-keep-turn.json`、`.log` | T-242 变异体（补丁串改到 `byProcess.ts`）仍失败于“第二个 Claude 第一次提交前”沿用旧状态 |
| `regress-t184_unwired_cli.json`、`regress-t133_t107_terminal_controller.json` 及 `.log` | PASS |

### 测试本身的失败（保留）

| 文件 | 原因 | 处理 |
| --- | --- | --- |
| `nested-harness-auto-mode.*` | Claude Code 已自动更新到 2.1.318，默认权限模式为 auto；外层调 Bash 时 auto 模式的分类器弹出计费说明框，停在 “Enter to continue” | 外层改用 `--permission-mode default --allowedTools Bash` |
| `nested-harness-name-clash.*` | 我新加的私有方法与 Panes 已有的 `shellFront`（T-237）重名，后者覆盖前者，后台在前台复查时报 `unknown_launch` 退出 | 改名为 `noteShellForeground` |
| `nested-harness-restart-operator.*` | 重启时 `daemon_start` 不覆盖已有的 `operator.json` | 照 t124、t137 先改名再重启 |

## 命令

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t246_nested_cli_native_e2e.py --summary <新文件>.json [--revision <版本> | --mutant last-report | --mutant last-recorded]
node workbench/tests/test_by_process.ts [模块路径] [最大长度]
```

## 没有覆盖的

- Codex 在普通终端里嵌套运行没有端到端跑过（同一路径，按进程号保存与 CLI 无关）。
- 票面“退出后晚到”的时序没有复现，理由见上。
- 已退出进程的进程号在前台复查看到别的进程之前就被复用（没有启动时间，分不出来）。

## 审查（`review/REPORT.md`，Codex `gpt-6.1-terra` high，只读）

NO_GO，两条阻塞，都是只读推导：

1. `pane_status.native_session` 用的是缓存的 `pane.native`：A 退出、B 到前台后，下一次前台复查之前读状态仍得 A 的会话；端到端里每次读 `native()` 前先调了会现读前台的 `link()`，掩盖了这一点。**成立，按有界滞后处理，不改设计**：普通终端的 `pane.native` 只在前台读取时更新（输入一行回车后 1.5 秒；CLI 在前台时每 5 秒复查一次），与 T-242 回合状态的滞后同一来源；“复制深度链接”每次自己读前台，不受影响。端到端加一项只读 `pane_status` 的检查：外层 `/exit` 回车后 2.06 秒清掉（`nested-green-2.json` 的 `native_cleared_after_s`；界限按 CLI 自己退出加一次复查，取 10 秒）。
2. 重启重建只按进程号与“现在是否存活”关联，A 的进程号被新的前台 CLI 复用时会沿用 A 的报告。**成立，已修**：见“改动”的启动时间。`test_by_process.ts` 加入进程号复用事件（逻辑时钟，复用只发生在退出之后）。判定按“上次前台读取所指的那个进程”：那个进程已退出或进程号已被复用、而还没有新的前台读取时，允许显示无、它的状态、或之后占用同一进程号的进程的状态（后台此时分不出后者是否已在前台，下一次前台读取纠正），任何时候都不显示别的进程号下的报告。

非阻塞：`rememberOpen` 对普通终端回退到旧布局的会话，已改；重启后没单独核对 `native_session`，已加 `after_restart_native_is_outer`；终端主控身份另经 t133 回归。

| 文件 | 结果 |
| --- | --- |
| `search/round2/green.txt` | 修后穷举（每步 10 个可选事件，长度 0～6，1,111,111 个序列）PASS |
| `search/round2/mutants.txt` | 单槽位、不看前台、不清退出进程、忽略启动时间四个坏实现都失败；忽略启动时间失败于 `exit(101) reuse(101) front(101)`，新进程沿用旧进程的报告 |
| `nested-green-2.json`、`.log` | 修后 PASS，八项（新增重启后 `native_session`、退出后终端状态清掉） |
| `nested-mutant-last-report-2.*`、`nested-mutant-last-recorded-2.*` | 仍分别失败于“内层运行时”“后台重启后” |
| `regress-t242_shell_hook_turn-2.*`、`regress-t242-mutant-keep-turn-2.*` | t242 PASS；变异体（补丁串改到新写法）失败于“第二个 Claude 第一次提交前” |
| `regress-t195_native_link-2.*` | PASS（16 项） |
| `regress-t184_unwired_cli-2.*`、`regress-t133_t107_terminal_controller-2.*` | PASS（t133 为有角色的终端主控） |

第一轮的 `search/green.txt`、`search/mutants.txt`、`nested-green.json` 等是修进程号复用之前的结果，保留作记录。

端到端造不出进程号复用（macOS 顺序分配进程号），这一条只有穷举测试的证据。

## 复审（`review/REREVIEW.md`，最后一轮）

NO_GO，三条阻塞，都是只读推导。第 1、3 条又是“报告只属于报告它的进程”这条不变式的新反例，按 T-240 不再开审查轮。

1. **进程号复用之后旧进程的钩子才到**：助手已取得 A 的进程号、请求还在路上，A 退出，进程号被新的前台 CLI 复用，A 的报告随后到达，按到达时间会算成新进程的。**附证据答复，不改**：要堵住，钩子须在报告时带上 CLI 的启动时间；助手现在读的是 `ps`（没有启动时间），后台用的 `processSnapshot.py` 读整棵进程树，钩子运行时那棵树一直在变，每次钩子多起一次 Python 也加在每个回合上。而这条时序要求进程号在请求路上的毫秒到几秒内被复用：`rereview-answers/pid-allocation.json` 实测本机连续起 200 个进程，进程号严格递增（每次加 1 或 2）；macOS 按顺序分配，用尽到 PID_MAX（99999）才回绕，按这台机器紧凑循环约每秒 750 个算，也要两分钟以上不停地起进程。写作已知局限，没有复现。
2. **前台复查失败后不再安排复查，缓存的会话一直留着**：**成立，已复现并修**。`--front-failure` 在夹具源码里注入：从 `/exit` 起终端自己的前台复查抛错。修前 `front-failure-red.json`：失败于“外层会话从终端状态清掉”，30 秒仍是外层的会话，状态库里只有一条注入的 `cli_wiring_check_failed`（之后没有再复查）。修法：复查失败按“没有观察”处理，清掉前台（和那段原有的“没有观察就不显示警告”一致），会话与回合状态都不再给出，直到之后的读取看到前台。修后 `front-failure-green.json` PASS，失败后 2.07 秒清掉。
3. **同一毫秒内的报告会被当成旧的**：启动时间带小数毫秒，到达时间是整毫秒。**成立（未运行复现：钩子助手是 CLI 起的一个 node 进程，到达不可能落在 CLI 启动的同一毫秒），已修**：前台启动时间向下取整到毫秒。

非阻塞：
- 穷举判定在前台读取过时的窗口里允许同一进程号的后来持有者：是这里的已知局限（后台此时分不出），已在上文写明；它只保证不显示别的进程号下的报告。
- `started` 缺失：只有读不到前台组的特权行没有它，那种行 `tpgid` 为 -1，不会被选为前台；没有另加校验。
- 终端没有 pane（还没恢复）而有旧布局时，`rememberOpen` 仍沿用旧布局的会话：普通终端不走恢复路径，这一条只影响布局记录，不改。
- 重启后的 `native_session` 检查在 `link()` 之后读：直接读时，重启后前台还没被读过，会是 `null`，直到第一次前台读取；这是有意的（没有观察就不给出）。

| 文件 | 结果 |
| --- | --- |
| `front-failure-red.json`、`.log` | 修前（注入前台复查失败）：30 秒内会话没有清掉 |
| `front-failure-green.json`、`.log` | 修后 PASS（八项），失败后 2.07 秒清掉 |
| `front-failure-harness-anchor.log` | 测试本身：注入点在 panes.ts 有两处，补丁要求唯一，未运行；改为定位到 `watchWiring` |
| `rereview-answers/pid-allocation.json` | 进程号分配实测 |
| `nested-green-3.*`、`regress-t242_shell_hook_turn-3.*`、`search/round2/green-after-floor.txt` | 最后两处修改后：不注入的绿态 PASS（八项）、t242 PASS、穷举 PASS |

## 关闭时的清理（2026-11-03）

按只存状态的规则删除 `/private/tmp` 下本票运行留下的 20 个夹具目录（`t246-*`、`t195-*`、`t242-*`、`t184-*`，共约 2.2 GB），删除前核对路径下没有进程；本目录的 JSON 结果、日志与审查报告保留（共约 0.8 MB）。

## 补记（2026-11-04）：Codex 嵌套

`workbench/tests/test_t246_nested_codex_native_e2e.py`：外层是交互式 Codex，它的 shell 工具运行内层 `codex exec`，内层的模型请求由测试扣住。预期来自 Codex rollout 首行 `session_meta`。结果在 `codex-nested/`：修前失败（外层报不来会话，原因与修复见 [T-247](../T-247/RESULTS.md)）；修后 `fixed-6`、`fixed-7` 八项 PASS；变异体 `mutant-last-report` 失败于“内层运行时链接是外层的”这一项，链接给的是内层会话。
