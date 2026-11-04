# T-247 结果：普通终端里交互式 Codex 的钩子认不出是哪个 CLI

状态：见文末“结论”。

## 起因

2026-11-04 补做 T-246 的 Codex 嵌套端到端（用户：“这条要做”）。外层是交互式 Codex，它的 shell 工具运行内层 `codex exec`。修前结果：外层一次也没报来会话号，链接显示“Codex 还没报来这次会话的会话号”，内层却报上来了（`../T-246/codex-nested/fixed-1.json`）。在信任钩子后重启外层，结果相同（`fixed-2.json`），说明原因不在“当场信任”。

钩子探针（`--probe`，`../T-246/codex-nested/probe-1.json`）显示：

- 外层交互式 Codex 的钩子进程环境里没有 `CODEX_THREAD_ID`。`a2a hook` 按环境变量（`commandCli`）判断 CLI，因此认不出，不带 `cli`、`cli_pid` 上报，后台丢掉了这条会话报告和回合状态。
- 内层能报上来，是因为它继承了外层 shell 工具环境里外层的 `CODEX_THREAD_ID`。

影响：普通终端里交互式 Codex 的深度链接（T-195）和回合状态（T-242）此前从未生效过。此前的端到端只在普通终端里跑过 Claude Code。有角色的终端主控（T-133）不受影响。

## 修改

`workbench/src/terminalCli.ts` 的 `hook` 分支：

- 跳过 shell 中转（`sh`、`bash`、`zsh`、`dash`、`ksh`、`fish`，含登录 shell 的 `-zsh`），取第一个祖先进程作为报告者。
- 这个祖先不是认识的 CLI，就不上报 `cli` 与 `cli_pid`，不再往上找。
- 不看环境变量。

第一版修法是“最近的 CLI 祖先”，被审查阻塞 1、2 推翻（见下），现保留为变异体 `nearest-cli`。`a2a request` 仍用 `commandCli`。`workbench/README.md` 深度链接一节已同步。

## 证据

| 文件 | 内容 |
| --- | --- |
| `../T-246/codex-nested/fixed-1.json`、`fixed-2.json`、`probe-1.json` | 修前（工作区当时未改源码）：失败于 `during_inner_link_is_outer`，外层没报；探针见上 |
| `../T-246/codex-nested/before-fix-HEAD.json` | `--revision HEAD --probe`：同样失败于外层没报 |
| `../T-246/codex-nested/fixed-3.json`～`fixed-5.json` | 第一版修法：八项 PASS（fixed-3 带探针，4、5 不带） |
| `../T-246/codex-nested/mutant-last-report.json` | 变异体“取最后到达的报告”：失败于 `during_inner_link_is_outer`，链接给的是内层会话 |
| `../T-246/codex-nested/fixed-6.*`、`fixed-7.*` | 最终修法：八项 PASS，两次 |
| `runner-fixed.json` | `test_t247_hook_runner.py`，真实 `terminal/bin/a2a hook` 入口加假 CLI 进程树：七种情形 A～G 全部 PASS |
| `runner-red-head.json` | 修前版本：失败于 A、B、C、D、G。C、G 在修前就会报成外层 CLI |
| `runner-mutant-nearest-cli.json` | 第一版修法：恰好失败于 C（不认识的程序跑钩子，报成外层 Codex）、G（运行者路径带空格，报成外层 Claude） |
| `regress-*.json`、`.log` | 最终代码：t246（Claude 嵌套）、t242、t195、t184、t133 Codex 终端主控、t133/t107 全部 PASS |
| `round1/` | 第一版修法时的回归，t133 Codex 那项被中断（改代码前停掉）。它留下的本夹具进程已结束 |

未运行：`test_hook_turn_facts.py`。它测的是 Git 提交尾注钩子，不经 `a2a hook`；回归循环里少传了参数，退出码 2，日志见 `regress-hook_turn_facts.log`。

重跑命令：

```
python3 workbench/tests/test_t247_hook_runner.py --summary <新文件>.json [--revision <版本> | --mutant nearest-cli]
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t246_nested_codex_native_e2e.py --summary <新文件>.json [--revision <版本> | --mutant last-report] [--probe]
```

## 审查

`review/PROMPT.md`、`review/codex.log`：NO_GO，三条阻塞、两条非阻塞。

1. **不认识的程序跑钩子时会报成外层 CLI**：成立。由 `runner-mutant-nearest-cli.json` 的情形 C 复现。已改为不上报。修前版本同样会这样报（`runner-red-head.json` 的 C）。
2. **运行者路径带空格时会被跳过，报成外层**：成立。由情形 G 复现。现在改为不上报。仍是局限：Codex 或 Claude 装在带空格的路径下时，钩子认不出，深度链接与回合状态不可用（`ps` 的整行参数按空白拆分）。
3. **回归证据不完整**：审查时回归还没跑完。现已补齐，见上表。
- 非阻塞 1，探针可能改变被测行为：属实。所以带探针的运行只作诊断，绿态以不带探针的 fixed-4、5、6、7 为准。
- 非阻塞 2，`a2a request` 也依赖 `CODEX_THREAD_ID`：不复现。依据：`fixed-3.json` 的 `hook_probe` 中，内层 `codex exec` 的钩子环境带着外层线程号，说明外层交互式 Codex 的 shell 工具命令环境有这个变量，缺的只是钩子进程。另外 t133 Codex 终端主控回归 PASS，它就是在交互式 Codex 里运行 `a2a request`。

复审：`review/REREVIEW-PROMPT.md`、`review/rereview-codex.log`（结论见下）。

## 已知局限

- `a2a hook` 本身可以被前台 CLI 的 shell 工具手动运行，这时会报成那个 CLI。修前按环境变量判断也一样，不是本次引入。
- 运行者装在带空格的路径下：不上报（见审查第 2 条）。

## 结论

复审（`review/rereview-codex.log`）结论 NO_GO，只有一条阻塞：它在自己的沙箱里重跑 `test_t247_hook_runner.py`，三个版本都在情形 A 收不到上报。**已复现并查明原因，与候选代码无关**（`rereview-answers/`）：

- `in-codex-sandbox.log`、`.json`：`codex sandbox -c sandbox_mode="workspace-write" -- python3 workbench/tests/test_t247_hook_runner.py …` 复现了同一个错误 `('A_codex_direct_no_thread_env', 0, '', [])`。同一命令在沙箱外 PASS（`outside-sandbox.json`）。
- `ps-probe.log`：沙箱里 `/bin/ps` 不能执行（`execvp() of '/bin/ps' failed: Operation not permitted`）。`a2a hook` 读祖先进程用的就是它，抛错后被钩子“不打扰用户回合”的 catch 吞掉，所以什么都没发。
- `socket-probe.log`：沙箱里连 Unix socket 正常，排除了 socket 的原因。

复审的三条非阻塞，与上一轮的非阻塞 1、2 以及审查第 2 条的局限相同，处理见上。按 T-240，复审之后不再开新一轮。

未知（未核对）：用户以 Codex 的 workspace-write 或 read-only 沙箱运行交互式 Codex 时，钩子命令是否也在沙箱里执行。若是，`ps` 不可用，钩子不上报 CLI。修前同样要读祖先进程，所以不是本次引入的。本票的端到端都用 `--sandbox danger-full-access`。

## 结论

**PASS。** 修前红态（真实 Codex 嵌套与假进程树两条入口）、修后绿态（真实 Codex 嵌套最终代码两次，假进程树七种情形）、两个变异体失败于预期处、六项回归 PASS；两轮审查的阻塞意见都已修改或附证据答复。

## 清理

按只存状态的规则，删除 `/private/tmp` 下本票运行留下的夹具目录（`t246c-*`、`t133c-*`、`t246-*`、`t242-*`、`t195-*`、`t184-*` 等）。删除前已核对这些路径下没有进程。本目录与 `../T-246/codex-nested/` 的 JSON 结果、日志和审查报告保留。
