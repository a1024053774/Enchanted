你是只读审查员。不改任何文件，不运行会启动后台、Electron 或 CLI 的测试；只读代码、证据，可以运行只读命令（git diff、grep、cat、python3 -m py_compile）。

仓库：/Users/luckye/Documents/Code/a2a。工作区改动（相对 HEAD 827b6c9fc，用 `git -C /Users/luckye/Documents/Code/a2a diff` 查看）：
- workbench/src/hcDistribution.mjs（T-244）
- workbench/tests/scripted_claude.py 与十几个 workbench/tests/test_*.py（T-243）
- 票：.project-map/tickets/T-242、T-243、T-244、T-245
- 证据：evidence/2026-11-03-batch31/T-242、T-243、T-244（各有 RESULTS.md）

按票面 Acceptance 逐项审查：
1. T-243：每个改过的测试是否无论通过还是失败都会停私有 core 并核对残留；有没有调用点用错参数（state 目录 vs 夹具目录）；残留检查会不会误伤非夹具进程；分类表与证据是否一致；“未运行、未判定”是否如实。
2. T-244：修复是否找对根因；固定值改变时是否会重装；打包路径（app/package.mjs）是否不受影响；有没有新的失败方式（如 release.json 存在但二进制损坏、并发启动）。
3. T-242：原因分析是否有代码依据；结论 INCOMPLETE、待用户决定是否恰当。
4. 证据里的数字和结论是否来自证据文件本身，有没有向上取整。

每条意见写成缺陷声明：位置、具体失败场景、依据。区分 阻塞 / 非阻塞。最后给总结论 PASS 或 NO_GO。用中文写，输出到标准输出。
