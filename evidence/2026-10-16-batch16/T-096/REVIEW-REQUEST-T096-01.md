# T-096-01 独立审查请求

状态：**候选冻结，审查待派发**。实跑七场 PASS；门禁交付／验收／集成未完成。本文件不是独立审查结论。

由执行主控经现有门禁另开干净、只读 reviewer 会话，使用 gpt-6.1-sol／xhigh；不得复用实现会话，不 claim、submit、集成或改文件。仓库为 `/Users/luckye/Documents/Code/a2a-wt-t096`，task T-096、attempt a1、writer s16-t096。按收到的 `T-096 FROZEN <完整 SHA>` 锁定唯一候选；本请求随该冻结提交保存。可用下列只读命令解析本请求首次交付的版本，并与主控传入 SHA 核对：

```sh
git log -1 --format=%H -- evidence/2026-10-16-batch16/T-096/REVIEW-REQUEST-T096-01.md
```

比较起点为 `3c9016d02`，最近实现／runner 修复版本为 `752dc62a179cb0fca8a18670a24b507d1bff471b`，冻结提交在此基础上只增加最终证据、文档和本请求。审查期间候选若变化，返回 INCOMPLETE，由主控重新冻结。

合同以用户任务卡 T-096-1、main `8cf91b26e` 的 T-096“裁定”节和主控 #89／#107 为准：恢复主控窗格，并按原启动记录完整参数续接原生会话；worker 保留“未恢复”，不启动 CLI、不重绑定、不改 attempt，按现有中断语义另行 reclaim。主控不是受管 worker，没有固定旧 PID 绑定。不得改 gates、Herdr、用户全局配置，不用裸 resume 或默认参数补位，不产生恢复模型回合。

请按 behavioral-acceptance-review 审查独立行为证据，并覆盖设计审查关注的异常边界；不要把新增测试的绿色当作唯一依据。独立检查以下方面：

1. `store.ts`、`panes.ts`、`daemon.ts` 与 app main／preload／renderer：创建／显式关闭即时保存窗格集、位置和原生会话；仅退出应用保留打开集；同库现有事件与 launch 记录是否足够，有无平行状态、旧队列重放或隐式新会话。
2. `paneRecovery.ts` 与恢复调用链：只替换会话选择器，其他 argv 全字段保留，版本／session／缺 argv 均拒绝并保留失败窗格；一个失败不污染其他窗格；启动记录不可变，worker 无恢复副作用。
3. `transport.ts` 的死端点处理：核对 PID、端点和异步期间的身份变化，不删除活动／未知端点；门禁源码与语义无修改。
4. 独立 oracle：核对外置盘实际 argv、native history nonce、Electron 原始读回、门禁前后完整 task／attempt、fake API 请求与关闭集，而非只读摘要中的 PASS。红态是 main 真实死端点阻断第二轮启动，未声称观察到了第二轮空窗口。历史对是明确标注的合成夹具；它证明 CLI 按原 session 显示所给历史，不是供应商模型生成的记录。
5. 反事实：旧版本／定向变异是否被相同业务断言拒绝；已有 T-091 IPC、Electron driver 与测试调整是否削弱原检查。重点看“nonce 恒真”“私密文件混入归档”“PID 身份变化仍发信号”等反例。
6. runner 收尾：只作用于隔离夹具，未知退出不升级为成功；预期红态与未知启动失败分开；正常退出请求已接受后的等待仍要求 Popen 退出和 PID 消失。version-b-02 没有重现旧瞬态错误，不能据此补称已证明 version-b-01 的准确竞态路径；该分支有替代 AppKit／ps 的反事实证明，旧原始缺口保留在 RESULTS。

证据索引如下，原始资料根目录为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/`，仓库只保留文本摘要和清单，不把原始 fixtures／sqlite／日志复制进 Git。

| 范围 | 仓库入口 | 外置盘核对重点 |
| --- | --- | --- |
| main 红态 | red-b-05.run.json／archive.json | command 响应、死亡端点、ownership、预期行为 NO_GO |
| 单格 Tracer bullet | tracer-b-05.run.json／archive.json | ideation.before、resumed-argv、resumed-view、synthetic-history、window-2 |
| 两主控＋worker | three-b-01.run.json／archive.json | 两份实际 argv／历史、gate-before／after、worker 未恢复和 receiver 未重启 |
| 缺 argv | no-argv-b-02.run.json／archive.json | 真实拒绝、只读未恢复、无成功事件 |
| 版本不符 | version-b-02.run.json／archive.json | 9 项检查、quit 回执、完整收尾 |
| 缺 session | no-session-b-01.run.json／archive.json | session 原件保留、不新建会话、真实拒绝 |
| 失败隔离 | isolation-b-01.run.json／archive.json | 另一主控实际历史、完整 gate task／attempt 相等 |
| 真实进程树 | process-tree-red-02／green-01.run.json | Z 状态、自然退出无信号、存活 exec 替代仍拒绝、两层收尾 |
| 固定残留清理 | cleanup-version-b-01.run.json、version-b-01-cleanup-version-b-01.archive.json | 只停止固定 daemon 79664 一次，原件和私密排除范围 |
| 局部合同与失败诊断 | decision-b-contract-02、layout-ipc-contract-02、daemon-restart-contract-b-02、version-cleanup-contract-03、RESULTS.md | 明确替代边界；不要把它们当真实 CLI／AppKit 证明 |

no-argv-b-01、version-b-01 及更早失败保留原状态；清理成功不改变其失败摘要。初始化全部由执行主控逐屏批准：每个主控六键＋一次空队列就绪放行，raw screen／批准回执位于各 run 的 startup-screens，所有最终场景 fake POST／模型回合均为 0。未真实登录。配置绕过 hasCompletedOnboarding／隔离目录信任状态的问题由构思主控另行处理，本票不实现。

审查可以做只读代码与现有证据核对、沙箱内静态／纯合同检查。不要自行启动 Electron、daemon、PTY、供应商 CLI，或在沙箱外执行 ps／截图；如证据不足，请列出精确缺口和待主控运行的命令，不申请升级，不改候选。

请返回 PASS／FAIL／INCOMPLETE，绑定冻结 SHA，列出可复现的发现、文件行号、反例与限制；没有独立证据时不得因摘要绿色而宣称通过。发现由主控协调修复，不由 reviewer 修改或接管本 attempt。
