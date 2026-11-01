# 第二轮定向只读行为验收复审

状态：PASS，仅限主控本轮授权的跨项目路由、先答后关显示与实际 CLI 提交次数断言，不代表整个 T-216 已通过。

候选：7 个第二轮文件与 [round2-candidate.patch](round2-candidate.patch) 逐字一致。复审是按 `behavioral-acceptance-review` 技能进行的定向只读复审，不是 agy 审查。审查未修改文件或外部状态。

## 证据

- `controller_launch` 来自后台 `sessionFacts(caller.thread).launch.parent_launch`，上报参数不能指定；读取前后均复核调用者身份。
- `inboxTargets` 按该 launch 精确筛选执行主控，首次投递与排队恢复共用筛选，不借用任务项目的另一位执行主控。
- 路由红态分别证明旧候选误投 B、错误排队；对应绿态中 A 实际提交一次、B 零次、收据为 delivered，问题的 `controller_launch` 等于 A。
- processor 红态在关闭后仍标“主控已答”；绿态通过真实 Electron 显示“主控已关（executor）”，历史答复仍可见。
- 第二轮 T-124、T-132、T-171、T-216 回归分别通过 26、6、11、15 项。
- `daemon.ts` 与第一轮逐字相同；`panes.ts` 仅修改目标筛选，没有修改队列、drain、钩子绑定或 transcript 匹配。

## 发现

本轮授权子范围未发现新的可达缺陷。第一轮发现 2、3 已有相应真实入口红态、绿态。

## 反例

[round2-duplicate-counterexample-01.json](round2-duplicate-counterexample-01.json) 中，真实 CLI 收到同一正文两次，transcript 保存两个不同 uuid/prompt_id，`dispatch_queued_count` 仍为 1，`cli_actual_submission_count_is_one` 明确失败。

计数逐条读取 CLI 自己的 root user transcript 行，不去重，不使用重复携带历史的 API 请求数量。随机 nonce 核对问题原文随输入变化。三个修前反例均在业务断言失败，不是缺依赖或启动崩溃。

## 限制

- agy/opencode 投递按本轮指令延期，等待 T-212 后统一 hc 方案确认，本轮没有修复。
- 新增真实 CLI 场景使用 Claude，没有扩展其他 CLI 实测。
- 未覆盖跨项目 reviewer/monitor 上报及角色撤销、重新上线竞争；源码共用路由不等于这些入口已经实测。
- 本地脚本化接口只证明机械行为，不证明模型自主判断。
- 本复审不能替代任务书要求的 agy 独立只读审查。
