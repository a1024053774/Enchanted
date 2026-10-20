# T-110 退出态清理修复

INCOMPLETE。本轮起点 `92bc8820800bf7990cacfb3bcb4cddcfe4b48217`。父版作答对照已经 PASS，第七轮四个业务红态均成立、green PASS；disabled 的 11 项业务检查已过，唯一失败是清理时把同一 CLI 的 `?E` 退出状态误判为身份变化。现已修正清理辅助函数，本地退出态合同已通过，完整真实入口仍待主控重跑。原始第七轮保持 INCOMPLETE，不事后改写结果。

## 原件与判断

`/private/tmp/t110-receipt-compare-01.json` 绑定 92bc88208：e1c7b5c27 在同场景作答回执超时且有 invalid_window_sequence，当前候选完成原答复合同及原 PTY 后续输入。`/private/tmp/t110-outside-07.json` 绑定同一提交：隐藏通知、断连角标、恢复视图、修前作答四个红态符合预期，正常闭环 16 项检查通过；禁用通知的 11 项检查全部通过，但 PID 63428 清理失败。两份原件的精简文本在 `outside-07-summary.json`。

主控 #47 已确认：PID 63428 后来自行退出。失败时 pid、pgid 和启动时间仍相同，ppid 已变成 1，stat 为 `?E`，command 为 `(2.1.304)`。这是 macOS 的退出标记导致 command 文字变化，不是新进程。原清理函数先比完整 command，所以报 identity changed；原函数另有 Z 状态提前返回的分支，未先核对核心身份，本轮一并按用户要求收紧。

## 修复边界

`workbench/tests/t108_cleanup.py` 的 stop_owned 先核对 pid、pgid、启动时间。三者相同且 stat 含 E 或 Z 时，只等待，不发 SIGTERM／SIGKILL；只有观察到 PID 消失才返回 `status: exited`，并记录等待期间的 `exit_states`。沿用原有两段各三秒的上限，仍可见就报失败。状态检查每次都重新核对核心身份，等待中换 PID／pgid／启动时间也拒绝；退出态不使后续运行中进程的 command 检查失效。

其他运行中进程仍需完整 command 匹配才允许向已核对 PID 发信号；原来的 TERM、等待、KILL、等待顺序保持。检查失败照常抛错，未吞异常、未过滤 process_cleanup_errors，也未把未知或僵尸仍可见的状态伪造为完成。只有测试清理模块、其合同、外跑入口和 README 改动；本轮 main、transport、renderer、sidebar、设置页、panes.ts 和原作答回执 helper 均未改。

## 证据与复发检查

先新增 `test_t110_cleanup.py`，再跑修前实现：`cleanup-contract-red-01.json` 在同一身份、command 已缩短的 `?E` 案例失败，原错误正是 `Process identity changed`。修后同一合同 `cleanup-contract-green-01.json` PASS，共 19 项，使用实际 stop_owned，只提供 ps 观察、时钟和发信号边界；测试不会操作真实 PID。

覆盖 E／Z 等待到消失、TERM 后进入 E／Z 不再升级信号、核心身份变化的 E／Z 反例、运行中 command 变化、等待中 PID 身份更换、退出态转回其他运行中命令、持续 E／Z 超时且不发信号、普通存活进程仍终止／升级、观察失败传出。期望来自主控 #47 与原有清理安全约定，未从辅助函数输出复制答案。

`RUN-OUTSIDE-NO-MODEL` 的 Python 入口现在在复制依赖、启动真实进程前自动运行上述合同，旧实现必须在缺陷断言失败。这样同一类 E 状态清理误拒不会再依靠真实 CLI 恰好停留在 E 状态才暴露。后面的四个真实业务红态、green、disabled 以及所有清理成功断言均保留。

本地检查和原 T-091／T-108 回归结果另保存在 `cleanup-regressions-01.json`、`cleanup-local-checks.json`。它们不能代替当前候选的新真实清理结果或独立复审。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t110
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT-06.sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t110-outside-08.json
```

本轮未改变应用与作答逻辑，已通过的父版对照不必重复。第八轮须仍取得四个红态、green 和 disabled 均通过，且无 process_cleanup_errors；若再次出现 E／Z，清理回执可读到 exit_states，若没有出现，该边界由自动执行的确定性合同覆盖。只用本地假 API、真实 CLI 和 Electron，不调用模型，不操作旧 PID 63428，不保存截图，不申请沙箱升级。
