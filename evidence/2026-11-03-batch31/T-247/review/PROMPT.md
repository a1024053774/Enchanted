你是只读审查员。不改任何文件，不运行会启动后台、Electron 或 CLI 的测试；可以读代码与证据，运行只读命令（git diff、grep、cat、ps）。

仓库 /Users/luckye/Documents/Code/a2a，审查对象是工作区相对 HEAD 的改动，范围限 T-247：
- 票：.project-map/tickets/T-247-terminal-codex-hook-cli-unrecognized.md
- 代码：workbench/src/terminalCli.ts 的 `hook` 分支（报告者改为最近的 CLI 祖先进程，不再按环境变量 commandCli）；对照 workbench/src/terminalClis.ts（cliProgram、commandCli、inCommand）、workbench/src/daemon.ts 的 terminal_hook、workbench/terminal/bin/codex 与 Claude 插件的钩子定义
- 测试：workbench/tests/test_t246_nested_codex_native_e2e.py（新）
- 证据：evidence/2026-11-03-batch31/T-246/codex-nested/（fixed-1、fixed-2、probe-1 为修前；fixed-3～5 修后；mutant-last-report；before-fix-HEAD）与 evidence/2026-11-03-batch31/T-247/regress-*

要核对的不变式：普通终端里，钩子上报的 cli 与 cli_pid 是运行这个钩子的那个 CLI 进程（Claude Code 或 Codex），与是否嵌套、环境变量是否继承无关；不是 Claude Code、Codex 跑的钩子不得被记成它们的。另核对：
- 最近的 CLI 祖先会不会不是钩子的运行者（如 CLI 经包装脚本、node/bun 运行、`sh -c` 中转，或 agy/opencode 里再跑 Claude/Codex，或 Claude 与 Codex 互相嵌套）；
- `a2a request`、`a2a mcp` 等仍用 commandCli 的路径是否受影响，或同样有交互式 Codex 不设 CODEX_THREAD_ID 的问题（只读推导要写明）；
- 有角色的终端（T-133）钩子路径是否受影响；
- 测试的预期是否独立于实现（来自 Codex 自己的 rollout），红态、绿态、变异体是否真的打到所声称的检查；探针补丁是否只作诊断、不改变被测行为。

每条写成缺陷声明：文件:行、具体失败场景（输入或进程树）、依据；能用实际运行的反例证明的附命令与结果，只读推导的写明“未运行复现”。分 阻塞 / 非阻塞。最后给总结论 PASS 或 NO_GO。中文，输出到标准输出。
