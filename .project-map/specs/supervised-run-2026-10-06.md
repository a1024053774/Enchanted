# T-008：受管自动运行（2026-10-06）

在既有受管入口上自动编排正常任务，目标是减少主控记忆流程，不增加自主授权范围。
承接 T-006 与 T-007；继续使用既有 task/attempt、oracle、操作锁和 Git 集成门禁。
本切片不实现守护服务、邮箱、租约、自动模型重试或自动权限审批。

## CLI 与结果

新增 `python3 coop.py --state ABS run --task ID --parent-pane LIVE --name NAME --wait-seconds N`。
N 必须为正整数。这个时限约束成功投递后等待显式 submit 的阶段，不承诺完整运行的硬实时总时限。
现有子进程自身的启动、验收和取消时限仍适用；采用单调时钟计量等待。
主控调用 run 前已通过 create 注册任务和独立 oracle；run 不替模型编造 commit。

成功：exit 0，ok=true，task.state=accepted，run 含非空 run_id、attempt_id 和 outcome=completed，
且自己的 pane 已核对回收。失败：exit 1，ok=false，error 指明原因；已创建 run 时仍返回其记录。
等待结束仍无提交：error=run_deadline；当前 attempt 被替换：error=run_superseded。
相同 task 同时只能有一个活跃 run，第二个立即 error=run_busy；不能多次 prompt。
先校验输入再做有副作用操作，不能用非法 wait 参数启动 worker。
run 记录存同一 state 下并关联既有 task/attempt；它是协调执行记录，不是第二套任务成功状态。

## 自动步骤与作用域

1. 原子确定 run 执行者并记录 run_id；调用既有 dispatch，保存它实际创建的 attempt/session/fence/spec。
2. 有界观察当前 task 和已绑定 pane，事件只按阶段或必要状态变化追加，不保存无变化的巨量轮询副本。
   idle/done、自然语言完成、消息已投递均不能推进；只有当前 attempt 的 submitted 才可继续。
3. 使用原有受锁的 verify / integrate 入口，强制绑定此次 run 的 attempt，再以独立 oracle/真实 Git 结果判断。
4. 正常完成，或者可核对的超时/验收拒绝，回收此次 run 创建的 pane，保留所有 worktree、候选和历史。
   启动权限等待、身份冲突、未知副作用必须暂停并保留现场，不自动答复、不盲重试/关闭。
5. 若替换为别的 attempt，旧 run 必须停止推进。只可核对清理自己的历史 attempt，
   不能验收/集成新的 attempt，也不能因错误查询关闭新 worker。
6. run 在自身进程中断后不自动重新投递；既有状态/证据保留，由已有核对入口恢复。
   本轮不声称完整 run 进程自动恢复。

为步骤 3/4 扩展原命令：verify / integrate / reclaim 接受可选 `--attempt ID`。
- verify/integrate 在其事务和操作锁边界核对当前 attempt；不匹配则 stale_attempt，
  包括 accepted 幂等返回之前也要核对。无该参数时仍是 controller 明确针对当前任务的原操作。
- reclaim 带参数时只处理该 task 下该历史 attempt 的绑定，不能选择另一个当前绑定。
  已回收的同一历史 attempt 可无副作用重放；改变业务 task 只允许 current_attempt 仍等于该 attempt。
  任意身份不确定就拒绝。未知/其他 task 的 attempt 不允许跨任务关闭。
以上是同一入口的额外 ownership 条件，不建第二套 API。

## 验收

新 acceptance/test_run_e2e.py 验证 CLI 入口、真实 Git/SQLite 与控制行为，不 import 产品实现。
若用可控 Herdr 边界替身制造 no-submit、replacement、blocked 场景，必须明确标为隔离编排证据；
它不能证明 Herdr/模型边界。至少一次真实 Herdr/Codex run 必须另外通过完整入口。
新代码前先获得缺失 run 或 guard 的契约红态。已有门禁与恢复套件必须保持通过。

必须证实：自动正常交付实际推进 Git；无 submit 即使 done 也超时而不接受；
同时 run 只有一个投递；期限/参数非法不会创建工作；替换身份和外来 attempt 不被旧 run 处理；
oracle 失败或未知/blocked 不会变成成功；正常回收只影响自己。
既有 guard 新参数应以真实 CLI 与状态/引用不变证明，不能只检查错误字符串。
反事实优先选择“接受 done 而无需 submit”或“忽略 expected attempt”，必须在业务断言上失败。

真实运行保存精确 argv、版本、任务/attempt、原始外部结果、权威 Git 引用读回和 pane 清单。
避免多次重复模型实验；复用已经检查并可信的隔离 fixture 或显式完成新的夹具信任准备。
用户其他项目、主控 pane 和 Herdr server 不变。失败材料不覆盖。
