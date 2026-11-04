你是只读复审员。不改仓库里的任何文件。可以运行只读命令，也可以运行 `python3 workbench/tests/test_t247_hook_runner.py --summary /private/tmp/<新文件>.json [--revision HEAD | --mutant <名字>]`。你自己的 Codex 沙箱里 `/bin/ps` 不能执行，网络关闭时 Unix socket 也连不上；遇到这种情况，以保存的结果为准，并写明没能重跑。

仓库 /Users/luckye/Documents/Code/a2a。上一轮审查见 evidence/2026-11-03-batch31/T-247/limits/review/codex.log 末尾：NO_GO，一条阻塞（“CLI 的直接子进程”这一放宽没有核对子进程的身份，任何被 CLI 直接启动的程序都能冒认外层），两条非阻塞（G 情形只走了不读进程表的那一步；RESULTS 是第一版的结论）。

本轮只核对这些意见的处理，以及修改本身有没有引入新问题：
- workbench/src/terminalCli.ts 的 hookRunner：直接子进程必须与声明的 CLI 同名（comm 的 basename）。
- workbench/tests/test_t247_hook_runner.py：npm 原生二进制改为以 codex 命名的可执行文件（Node 的符号链接，ps 按这个路径命名它）。新增 H3（带空格路径下的 npm、经 sh，要读进程表里带空格的名字）、J 与 J2（Codex 直接启动的其他程序运行钩子），以及变异体 any-direct-child。结果在 evidence/2026-11-03-batch31/T-247/limits/runner-*.json，上一版测试的运行在 limits/round1/。
- evidence/2026-11-03-batch31/T-247/RESULTS.md：第一版各段已标注版本；第二版一节由实现者在回归结束后补写。如果你读到时还没有，就写明没有。

每条写成缺陷声明：文件:行、具体失败场景、依据。能运行复现的附命令与结果，只读推导写明“未运行复现”。分阻塞、非阻塞两类，最后给总结论 PASS 或 NO_GO。用中文，输出到标准输出。
