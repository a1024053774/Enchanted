STATUS: PASS  
TARGET: Synara `a2a` 冻结候选 `fa3fc3352805d00e41c454fa6f810807528de3a9`，基线 `a9cc30c395af9ffd51476a1841d80bca66568993`

EVIDENCE:
- `git rev-parse HEAD` 与候选一致，目标源码工作树无差异；冻结绑定的 27 个 source/snapshot 均 `cmp` 通过。
- 原测试与 `test_run_native_e2e.py` 均保留 18 项；`final-run-03` 记录 18/18、failures=0、errors=0。原 2 秒 deadline 与 3 秒 `run_busy` 断言未放宽；仅第 8/10 项改为获准的 30/60 秒窗口。
- `final-delivery-recovery-03` 经 T-036 同一入口运行 17 项，全部通过。
- done-without-submit mutant 的业务结果实际变为 accepted、Git ref 移动并执行 oracle；expected-attempt mutant 实际绕过 stale guard 并改变状态/ref，均被业务断言拒绝。
- 原生 engine 证据记录了真实 user 消息的 task/attempt/thread 绑定，并排除了 agent、automation、assistant、非受管 thread；真实 SQLite 写锁后 status/events/GET 显示 failed 与源事件原因，9 类变更命令含 reclaim 均返回专用错误，重启回放遗漏消息各一次。
- 异步 oracle 记录失败返回结构化 `human_input_observer_failed`，保持 verifying 状态与 Git ref 不变。

FINDINGS:
- 无。在限定 T-037 范围内未复现可达违反。

COUNTEREXAMPLE:
- `mutant-done-final-03`：拒绝“done+commit 即 submit”，业务断言观察到错误 accepted/ref/oracle 变化。
- `mutant-attempt-final-03`：拒绝忽略 expected attempt，业务断言观察到 stale verify/integrate 被执行。

LIMITATIONS:
- 18 项使用隔离 native thread-service 替身；不证明真实 provider、模型、service tier 或生产可靠性。
- 本结论不覆盖 UI、M1 切换、发布或全仓检查。
