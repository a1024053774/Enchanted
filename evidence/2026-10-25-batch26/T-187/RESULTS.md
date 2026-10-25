# T-187 结果：增加 agy 与 opencode 的支持并实测

## 状态：INCOMPLETE（终端侧已实现并通过替身测试和真实 opencode 运行；worker 权限待用户决定，真实 agy 运行要用户点一次信任，验收第 1 条的完整流程还没走）

## 依据

ticket T-187（ready_rev 1）。用户 2026-10-25 原话：“增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”。实测事实见 `facts.md`。worker 权限的决定请求见 inbox `20261025T150744Z-executor-needs-decision-001`。

## 做了什么（终端侧：作主控与普通终端）

- `src/terminalClis.ts` 是唯一的 CLI 登记处。每个 CLI 登记三件事：怎样判断它经过了包装脚本、回合状态从哪里来（钩子还是 OSC 7501）、怎样从命令的环境认出它。新增 agy、opencode。这里还有 OSC 7501 的解析，一条报告被拆在两段输出里也能读出。
- 包装脚本 `terminal/bin/agy`：设 `A2A_SHIM=agy` 和 `AGY_CLI_OSC7501=on`（用户自己设了就用用户的）。agy 没有按会话的指令参数，所以拿不到开局说明。
- 包装脚本 `terminal/bin/opencode`：设 `A2A_SHIM=opencode`，用 `OPENCODE_CONFIG_CONTENT` 把开局说明作为 instructions 传入，并加 `--standalone`。有子命令、用户自己传了 `--server`/`--standalone`、或用户自己设了 `OPENCODE_CONFIG_CONTENT` 时原样转发。
- 开局说明挪到 `terminal/orientation.md`，只此一份：Claude、Codex 通过 `a2a session-context` 读它，opencode 作为 instructions 读它。
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

- 验收第 1 条的完整流程（申请主控 → 派卡给另一种 CLI 的 worker → 独立审查 → 门禁集成）：worker 用哪种 CLI、权限怎么定，等用户决定。
- 真实 agy 运行：agy 在隔离 HOME 下没有登录；在用户自己的 `~/.gemini` 下，每个新夹具目录都要用户本人点一次信任。
- AGENTS.md 的支持范围：等 worker 的决定定下后一起改。

## 已知限制

- agy、opencode 主控：用户对它们说的话和对提问的答复不记入用户输入（这两个 CLI 没有按会话的钩子）。
- agy 没有开局说明。
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
