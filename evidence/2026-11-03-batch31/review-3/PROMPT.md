你是只读审查员。不改任何文件，不运行会启动后台、Electron 或 CLI 的测试；只读代码、证据，可以运行只读命令（git diff、grep、cat、python3 -m py_compile）。

仓库：/Users/luckye/Documents/Code/a2a。工作区改动相对 HEAD 20f1d8581，用 `git -C /Users/luckye/Documents/Code/a2a diff` 与 `git status --short` 查看（新文件未跟踪）。本轮范围与证据（各有 RESULTS.md）：

- T-245（evidence/2026-11-03-batch31/T-245）：夹具 `.claude.json` 写入 `MARKETPLACE_SKIPPED`（workbench/tests/scripted_claude.py 与约 29 个测试/探针），`stop_fixture_core` 收尾检查 `.claude/plugins/marketplaces`。
- T-244（T-244）：workbench/src/hcDistribution.mjs 第二版——每个固定值装进 `state/hc/herdr-core-<版本>-<sha8>/`，临时目录解包后一次 rename；新测试 workbench/tests/test_t244_pin_change_e2e.py；README 第 7 行；t212、t228、t230 改用 `hc_binary`/`hc_installs`。
- T-243（T-243）：workbench/tests/electron_client.py 的 `capture_and_stop`（用户已同意：Electron 退出未确认时先记现场再结束，取代 T-091 的“从不自动结束”）；test_electron_e2e.py、test_t078_input_entry.py 的未确认路径；26 个批次脚本的分类表。
- T-242（T-242）：用户已同意改设计——没有角色的普通终端里 Claude Code/Codex 的回合状态取自钩子、只在内存里、不记录。workbench/src/daemon.ts（`hookTurnState`、`terminal_hook`）、workbench/src/panes.ts（`hookTurn`、`noteShellTurn`、`watchWiring` 清除、`status` 的 `hook_turn`）、workbench/src/sidebar.ts、workbench/app/renderer.tsx 标签；新测试 workbench/tests/test_t242_shell_hook_turn_e2e.py。

按各票 Acceptance 与 RESULTS 审查：
1. 根因是否找对，修复是否在根因层；有没有新的失败方式（例如：T-244 并发首次安装、rename 失败的其他错误码、旧 `hc/bin` 的 core；T-242 状态沿用到别的进程、有角色时的路径是否被改变、提示词或回合是否会进记录；T-243 `capture_and_stop` 会不会结束不是测试启动的进程）。
2. 新测试是否能在已知坏的实现上失败（红态、变异体证据是否真的打到声称的失败方式），期望是否来自需求而不是被测代码的输出。
3. 证据里的数字和结论是否来自证据文件本身，有没有向上取整；分类表与证据是否一致。
4. 是否引入了吞异常、fallback、兼容分支或平行 API。

每条意见写成缺陷声明：位置（文件:行）、具体失败场景、依据。区分 阻塞 / 非阻塞。最后给总结论 PASS 或 NO_GO。用中文写，输出到标准输出。
