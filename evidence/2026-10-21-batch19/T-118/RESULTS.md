# T-118 结果

状态：PASS（第 6 轮独立只读审查 PASS），附下列未覆盖边界。

## 复现命令

- 终端环境：`python3 workbench/tests/test_t118_shell_env_e2e.py --summary <新路径> [--revision 3070bbe1a… | --mutant prefix-filter]`
- 版本：`node --experimental-vm-modules workbench/tests/test_t091_claude_version.mjs <新路径>`；`node --experimental-vm-modules workbench/tests/test_t096_restore.mjs <新路径> [panes.ts 候选]`；`node workbench/tests/test_t112_execution.mjs <新路径>`
- 界面：`cd workbench && node app/package.mjs --slot ui-test-12 --variant test`，再 `t118run.sh "<Enchanted Test.app>" <端口> <输出目录>`（同目录 t118drive.mjs、frames.py、register.mts）。构建身份见 ui-build-identity.json。

## 结果文件

| 内容 | 绿 | 红／变异 |
| --- | --- | --- |
| 终端环境 | shell-env-green-04.json | shell-env-red-3070bbe1a.json、shell-env-red-HEAD.json、shell-env-red-mutant-prefix-filter.json |
| Claude 主控版本 | claude-version-03.json | 同文件 known_bad、mutant 字段 |
| Codex worker 版本 | codex-version-green-03.json | codex-version-red-HEAD.json |
| 恢复 | restore-green-04.json | restore-red-HEAD.json、restore-red-runtime-version-mutant.json |
| 界面 | ui-12-zoomclose-{1,2,3}.json、ui-dark-after-recovery.png | ui-restore-red-ui-test-05.json、ui-resync-red-ui-test-09.json、ui-11-zoomclose-c.json |
| 审查 | review-06.md（PASS） | review-01～05.md（NO_GO）；完整 Codex 日志归档在外置盘，见 review-0N.log.archive.json |

过程记录：ui-green-11-run1-driver-stopped-early.json 是驱动在两帧等待期间提前停止采样，已改驱动停止条件；ui-restore-green(-07/-08/-09/-10).json 为中间候选。

## 未覆盖

小积压重连、无 launch 后绑定、空输出／读取错误、导航／新建／关闭超过 10 秒期间崩溃、连续崩溃、外部 SIGTERM、恢复版本的界面展示、正常登录最终审计（run_t108_real.py 需真实登录）。界面采样约 20ms 一次，不是逐帧证明。
