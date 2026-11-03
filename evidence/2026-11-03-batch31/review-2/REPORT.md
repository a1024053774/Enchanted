**总评：NO_GO。** T-243 的失败清理路径和 T-244 的安装完整性仍有阻塞问题；两张票的验收结论也高于现有证据。以下是只读审查中的缺陷声明，未运行会启动后台、Electron 或 CLI 的测试。

**阻塞**

1. **T-243：后台停止失败时，部分测试会跳过 core 清理和残留核对。**  
   位置：[test_electron_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_electron_e2e.py:225)、[test_t078_inbox_entry.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t078_inbox_entry.py:130)、[test_daemon_gates_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_daemon_gates_e2e.py:62)。  
   例如 Electron 窗口退出未确认、`daemon_stop` 失败或等待超时，异常会跳到外层处理，后面的 `stop_fixture_core` 不执行；`DaemonCards` 还在等待 host 之前清空 `_daemon_state`，此后失败也不会执行 core 清理。测试会报 INCOMPLETE，但不能满足票面“通过或失败都停 core 并核对残留”。现有故意失败证据只覆盖了 t193 在后台启动后抛错的路径。

2. **T-243：改过的 t104、t212 仍不能保证失败时清理及核对残留。**  
   位置：[test_t104_shell_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t104_shell_e2e.py:309)、[test_t212_hc_boundaries_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t212_hc_boundaries_e2e.py:145)。  
   t104 的 `stop()` 抛错时不会调用 `stop_private_core`；t212 仅在 `running` 为真且后台停止、等待均成功后停 core。两者调用的是 `stop_private_core`，没有夹具进程残留检查。state 参数本身已改正确，但不能据此认定失败清理完整；这两项也明确未运行。

3. **T-243：分类和总体 PASS 超出了验收证据。**  
   位置：[T-243 RESULTS.md](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-243/RESULTS.md:3)。  
   票面要求逐项判定能否运行，并对仍能运行的测试取得修后证据；报告明确列出一批“未运行、未判定”，t104、t212、t216 也未运行。因此限定为“hc core 残留”的 **PASS** 仍不足以代表整票通过。报告说 14 个会起 core 的测试修后不再留 core，但其中 t078 被分类为已失效；应把统计口径和未判定项分开，整票维持 INCOMPLETE。t124 的 git 残留及其两次失败已如实记录，不能算作该测试完整清理通过。

4. **T-244：release 标记不能证明当前二进制完整，失败或并发安装可把坏文件当成有效安装。**  
   位置：[hcDistribution.mjs](/Users/luckye/Documents/Code/a2a/workbench/src/hcDistribution.mjs:27)。  
   命中缓存仅检查二进制存在及 `release.json` 文字相等，不验证二进制内容。若二进制被截断或替换，下一次启动仍直接使用。更具体地，旧标记仍在时重新解包若中途失败或进程中断，旧标记可能继续与固定值相符，而目标文件已被部分覆盖；后续启动就会跳过重新安装。并发首次启动也可同时通过检查并向同一目录解包，导致 inode 再次改变。`hcBinary` 在后台端点和 pid 排他建立之前调用，不能从当前代码认定后台启动锁已排除这一竞争。上述是代码路径推导，现有证据没有验证这些场景。

5. **T-244：缺少票面要求的修后反事实，PASS 过早。**  
   位置：[T-244 RESULTS.md](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-244/RESULTS.md:13)。  
   有修前失败、修后 t123 PASS 和修改标记后的重装探针；但票面要求“修复撤回时又失败”，报告引用的两次失败都标为修前，不能替代修后撤回验证。`pin-probe.json` 改的是标记文件，证明不匹配时会重装；它不是实际改变固定值后运行的端到端证据。当前应为 INCOMPLETE，独立审查也尚有阻塞意见。

**非阻塞**

1. **T-243：残留检查可能误报非夹具进程。**  
   位置：[scripted_claude.py](/Users/luckye/Documents/Code/a2a/workbench/tests/scripted_claude.py:56)。  
   `fixture_processes` 对完整 `ps -E` 行做夹具路径子串匹配；其他进程若仅在参数或环境中引用该路径，也会被报告为残留。该函数本身只报告，不会杀掉匹配进程；报告中分诊脚本曾误杀用户 SSH 代理进程的事故属于另一条路径，已在证据中披露。

2. **T-243：清理失败后 t118 仍删除夹具，可能丢失现场。**  
   位置：[test_t118_shell_env_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t118_shell_env_e2e.py:135)。  
   即使残留检查抛出 `AssertionError` 并将状态改为 INCOMPLETE，代码仍无条件删除夹具目录；这可能使仍存活进程的诊断现场不完整。

3. **T-242：复现证据缺少票面指定的一部分后台观察。**  
   位置：[probe_shell_claude_state.py](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-242/probe_shell_claude_state.py:73)。  
   探针记录 UI、`sidebar_snapshot` 和相对提交时间，但没有采集票面要求的 `pane_status`，也没有记录每次采样的绝对时间。不能称复现验收逐项完成。报告保持 **INCOMPLETE** 是恰当的。

其余核对结果：T-242 的原因分析有代码依据：普通终端 Claude/Codex 的状态分支返回 unknown，未获批角色的 hook 回合事件不保留，“正在输入”来自输入焦点标签；是否改变显示或状态边界交用户决定是恰当的。T-244 的 inode 根因与现有探针相符，固定值不匹配会走重装分支；打包脚本直接调用未改动的 `installHc`，代码审查未见打包路径变化，但未做构建验证。

项目状态命令还报告 [workbench/README.md](/Users/luckye/Documents/Code/a2a/workbench/README.md) 因 `hcDistribution.mjs` 未提交改动而被标为 stale；本次没有修改文件。
hook: Stop
hook: Stop
hook: Stop Completed
hook: Stop Completed
tokens used
92,689
**总评：NO_GO。** T-243 的失败清理路径和 T-244 的安装完整性仍有阻塞问题；两张票的验收结论也高于现有证据。以下是只读审查中的缺陷声明，未运行会启动后台、Electron 或 CLI 的测试。

**阻塞**

1. **T-243：后台停止失败时，部分测试会跳过 core 清理和残留核对。**  
   位置：[test_electron_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_electron_e2e.py:225)、[test_t078_inbox_entry.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t078_inbox_entry.py:130)、[test_daemon_gates_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_daemon_gates_e2e.py:62)。  
   例如 Electron 窗口退出未确认、`daemon_stop` 失败或等待超时，异常会跳到外层处理，后面的 `stop_fixture_core` 不执行；`DaemonCards` 还在等待 host 之前清空 `_daemon_state`，此后失败也不会执行 core 清理。测试会报 INCOMPLETE，但不能满足票面“通过或失败都停 core 并核对残留”。现有故意失败证据只覆盖了 t193 在后台启动后抛错的路径。

2. **T-243：改过的 t104、t212 仍不能保证失败时清理及核对残留。**  
   位置：[test_t104_shell_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t104_shell_e2e.py:309)、[test_t212_hc_boundaries_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t212_hc_boundaries_e2e.py:145)。  
   t104 的 `stop()` 抛错时不会调用 `stop_private_core`；t212 仅在 `running` 为真且后台停止、等待均成功后停 core。两者调用的是 `stop_private_core`，没有夹具进程残留检查。state 参数本身已改正确，但不能据此认定失败清理完整；这两项也明确未运行。

3. **T-243：分类和总体 PASS 超出了验收证据。**  
   位置：[T-243 RESULTS.md](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-243/RESULTS.md:3)。  
   票面要求逐项判定能否运行，并对仍能运行的测试取得修后证据；报告明确列出一批“未运行、未判定”，t104、t212、t216 也未运行。因此限定为“hc core 残留”的 **PASS** 仍不足以代表整票通过。报告说 14 个会起 core 的测试修后不再留 core，但其中 t078 被分类为已失效；应把统计口径和未判定项分开，整票维持 INCOMPLETE。t124 的 git 残留及其两次失败已如实记录，不能算作该测试完整清理通过。

4. **T-244：release 标记不能证明当前二进制完整，失败或并发安装可把坏文件当成有效安装。**  
   位置：[hcDistribution.mjs](/Users/luckye/Documents/Code/a2a/workbench/src/hcDistribution.mjs:27)。  
   命中缓存仅检查二进制存在及 `release.json` 文字相等，不验证二进制内容。若二进制被截断或替换，下一次启动仍直接使用。更具体地，旧标记仍在时重新解包若中途失败或进程中断，旧标记可能继续与固定值相符，而目标文件已被部分覆盖；后续启动就会跳过重新安装。并发首次启动也可同时通过检查并向同一目录解包，导致 inode 再次改变。`hcBinary` 在后台端点和 pid 排他建立之前调用，不能从当前代码认定后台启动锁已排除这一竞争。上述是代码路径推导，现有证据没有验证这些场景。

5. **T-244：缺少票面要求的修后反事实，PASS 过早。**  
   位置：[T-244 RESULTS.md](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-244/RESULTS.md:13)。  
   有修前失败、修后 t123 PASS 和修改标记后的重装探针；但票面要求“修复撤回时又失败”，报告引用的两次失败都标为修前，不能替代修后撤回验证。`pin-probe.json` 改的是标记文件，证明不匹配时会重装；它不是实际改变固定值后运行的端到端证据。当前应为 INCOMPLETE，独立审查也尚有阻塞意见。

**非阻塞**

1. **T-243：残留检查可能误报非夹具进程。**  
   位置：[scripted_claude.py](/Users/luckye/Documents/Code/a2a/workbench/tests/scripted_claude.py:56)。  
   `fixture_processes` 对完整 `ps -E` 行做夹具路径子串匹配；其他进程若仅在参数或环境中引用该路径，也会被报告为残留。该函数本身只报告，不会杀掉匹配进程；报告中分诊脚本曾误杀用户 SSH 代理进程的事故属于另一条路径，已在证据中披露。

2. **T-243：清理失败后 t118 仍删除夹具，可能丢失现场。**  
   位置：[test_t118_shell_env_e2e.py](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t118_shell_env_e2e.py:135)。  
   即使残留检查抛出 `AssertionError` 并将状态改为 INCOMPLETE，代码仍无条件删除夹具目录；这可能使仍存活进程的诊断现场不完整。

3. **T-242：复现证据缺少票面指定的一部分后台观察。**  
   位置：[probe_shell_claude_state.py](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-242/probe_shell_claude_state.py:73)。  
   探针记录 UI、`sidebar_snapshot` 和相对提交时间，但没有采集票面要求的 `pane_status`，也没有记录每次采样的绝对时间。不能称复现验收逐项完成。报告保持 **INCOMPLETE** 是恰当的。

其余核对结果：T-242 的原因分析有代码依据：普通终端 Claude/Codex 的状态分支返回 unknown，未获批角色的 hook 回合事件不保留，“正在输入”来自输入焦点标签；是否改变显示或状态边界交用户决定是恰当的。T-244 的 inode 根因与现有探针相符，固定值不匹配会走重装分支；打包脚本直接调用未改动的 `installHc`，代码审查未见打包路径变化，但未做构建验证。

项目状态命令还报告 [workbench/README.md](/Users/luckye/Documents/Code/a2a/workbench/README.md) 因 `hcDistribution.mjs` 未提交改动而被标为 stale；本次没有修改文件。
