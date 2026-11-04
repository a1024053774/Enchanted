你是只读复审员。不改任何文件，不启动后台、Electron 或真实 CLI；可以运行只读命令，以及 `python3 workbench/tests/test_t247_hook_runner.py --summary /private/tmp/<新文件>.json [--revision HEAD | --mutant nearest-cli]`（只起假 CLI 与一个本地 socket，结果写到 /private/tmp）。

仓库 /Users/luckye/Documents/Code/a2a。上一轮审查：evidence/2026-11-03-batch31/T-247/review/codex.log 末尾的结论（NO_GO，三条阻塞、两条非阻塞）。复审范围只限这些意见是否已处理，以及修改本身有没有引入新问题：

- 代码：workbench/src/terminalCli.ts 的 hook 分支，现在跳过 shell（sh、bash、zsh、dash、ksh、fish，含登录 shell 的 `-zsh`）后取第一个祖先；它不是认识的 CLI 就不上报 cli 与 cli_pid。
- 新测试：workbench/tests/test_t247_hook_runner.py（真实 `terminal/bin/a2a hook` 入口，假 CLI 进程树，预期来自假 CLI 自己写出的进程号）；结果 evidence/2026-11-03-batch31/T-247/runner-fixed.json、runner-red-head.json、runner-mutant-nearest-cli.json。
- 回归：evidence/2026-11-03-batch31/T-247/regress-*.json（最终代码），round1/ 是第一版修法时被中断的一轮；Codex 嵌套 evidence/2026-11-03-batch31/T-246/codex-nested/fixed-6、fixed-7（最终代码）。
- 对非阻塞 2 的答复依据：codex-nested/fixed-3.json 的 hook_probe 中，内层 `codex exec` 的钩子环境带着外层线程号，说明外层交互式 Codex 的 shell 工具命令环境有 CODEX_THREAD_ID；只是钩子进程没有。
- README：workbench/README.md 深度链接一节。

每条写成缺陷声明：文件:行、具体失败场景、依据；能运行复现的附命令与结果，只读推导写明“未运行复现”。分 阻塞 / 非阻塞，最后给总结论 PASS 或 NO_GO。中文，输出到标准输出。
