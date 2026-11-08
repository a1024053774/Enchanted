---
id: T-254
title: 后台停止时等原生会话绑定收尾没有上限
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来由：T-253 的修复（`b01096b84`）让后台停止时先等还在进行的原生会话绑定收尾，再关门禁库和编排库，但这一步没有时间上限；T-253 的 Resolution 把它列为没覆盖的项。2026-11-08 用户看到这一条后要求：“这个应该设置一个合理的上限”（父会话“Worker 回收与派发问题” `local_e9998522-d926-46a1-aac9-eda70d24d2b9`）。

现状（读 `workbench/src/daemon.ts` 与 `workbench/src/gates/core.ts` 核对）：

- 停止流程在 `panes.shutdown()`、关监听之后 `await Promise.all([...bindings])`，没有期限。
- 门禁的 `nativeSessionLearned` 每轮先读窗格（`readThread`），读完查一次后台是否在停，在停就拒 `daemon_stopping`。所以停止开始后，一次绑定在下一次窗格读取之后就结束：正在读的就是手上这一次；正在等锁的，还要再睡 100ms、读一次（审查 01 指出，原写“只等手上这一次读取”不准确）。真实读取里的进程查询有 5 秒的 exec 超时，正常情况下几秒内就会收尾。
- 读取比这慢或不返回时，停止流程就一直等，库不关、`daemon.pid` 与套接字不删。

要做：

- 停止时等绑定最多 10 秒（一次窗格读取的进程查询上限 5 秒的两倍）。到期仍没收尾的绑定，在关库前逐个记 `native_session_bind_abandoned`（launch、会话号、等了多久），然后照常关库、删 pid 与套接字。
- 被放弃的绑定之后再收尾时什么都不写：库已经关了，它的结果已由 `native_session_bind_abandoned` 记下。attempt 保持未绑定，回收照旧拒绝（与 T-253 没覆盖的“重启后恢复的窗格”同样处理）。
- 绑定按时收尾时，计时器要清掉，不能让后台在停完之后再多挂 10 秒。

不做：

- 停止流程里其他没有期限的等待（请求排空、恢复、`resumedRunsSettled`、窗格终止）不在本票改。
- 不改绑定本身的锁与重试规则，不补重启后的绑定。

## Acceptance

- [ ] 修前红态：后台层测试新场景 `binding_outlives_stop`（窗格读取在停止开始后 30 秒才返回）在 `1bb19fa21` 上，停止后要等读取返回、约 30 秒才关库，没有放弃记录。（原写“20 秒内库没关、`daemon.pid` 还在”；测试量的是关库时刻，没有在第 20 秒采样 pid，按实际量到的改写。）
- [ ] 修后：同一场景在约 10 秒时关库、删 pid，记一条 `native_session_bind_abandoned`；读取返回后不再写任何记录，stderr 没有 `event_write_failed`，后台以 0 退出；门禁没有 `runtime_bound`。
- [ ] 原有的 `stop_while_binding`、`record_write_fails` 仍通过；`stop_while_binding` 关库后很快退出（计时器已清）。
- [ ] 变异：去掉期限、不标放弃、不清计时器，各自被至少一个检查判红。
- [ ] 回归：T-253 的单元测试 `t253_native_bind.ts` 通过。
