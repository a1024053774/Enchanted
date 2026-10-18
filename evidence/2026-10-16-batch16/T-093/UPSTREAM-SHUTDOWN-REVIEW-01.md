STATUS: FAIL
TARGET: 74b7db2bd200ec7e206831facff565baee6ce7cd
EVIDENCE:
- 审查开始、结束 HEAD 均为冻结候选；`git diff --exit-code 74b7db2bd200ec7e206831facff565baee6ce7cd --` 返回 0，原有未跟踪文件保留。
- upstream shutdown 7 项、counts selection 10 项、publication 5 项、cleanup oracle 12 项均通过。命令、退出码见 `/private/tmp/t093-r14-review-2vd0XE/commands.json`。
- 独立新时序执行真实 D 与最终 writer 回调：7 项中 5 项通过、2 项命中业务失败；原件 `/private/tmp/t093-r14-review-2vd0XE/independent-shutdown.json`。
- 可复现脚本：`node /private/tmp/t093-r14-review-2vd0XE/independent-shutdown.mjs /private/tmp/t093-r14-review-2vd0XE/independent-shutdown-replay-NEW.json`，输出须不存在。
- `--counts-only` 仅改变显式选择集合，复用原每场断言；默认六场要求、候选绑定及单场范围说明保留。project-map status 为 0 problems、0 stale。
FINDINGS:
- [P1] `workbench/tests/test_t093_login_chain.ts:198` — `all_exited` 在逐项最终查询前由 `quiet()` 计算；随后 group 或 child 查询返回 EPERM 时，明细成为 `exited:false`，汇总仍为 `all_exited:true`，`finishChain` 因而删除夹具。独立反例已复现。最小修正：最终 `all_exited` 同时约束已采集的全部 `groups/children.exited`；任一未确认行必须阻止删除，保留原等待期限及失败记录。
COUNTEREXAMPLE:
- 对 U 组或登记 child 提供 `ESRCH → ESRCH → EPERM`：最终明细未确认，候选仍执行删除；两例均未被现有测试覆盖，被独立检查拒绝。
- EPERM-as-exited、永不确认退出、基线回调均被测试的业务断言拒绝，rc 2。持续存活、持续 EPERM、缺关闭收据、主失败丢失、错候选及默认六场不足也被对应检查拒绝。
- D 的新时序 `EPERM → alive → EPERM → ESRCH` 通过；持续拒绝时禁止删除。
LIMITATIONS:
- 全部运行属于 L1，PID 查询与收据均为合成输入；未执行实际 OS 查询、sandbox-exec、CLI、daemon、网络、认证或模型。
- 当前候选的实际 counts 同 profile 复验与 V 真实核对未运行，仍为 INCOMPLETE；既有六场证据仅绑定基线。
- T-096 跨票恢复检查仍未解决。
RULE:
- 在最终 writer 回调合成检查中加入上述组与 child 反例，断言 `all_exited:true` 必须对应每项 `exited:true`，且任一最终 EPERM 禁止删除。该条件可机械验证，无需新增文字规则。
