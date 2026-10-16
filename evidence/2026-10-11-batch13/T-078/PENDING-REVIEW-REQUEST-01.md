# T-078 pending 投递候选：独立审查交接

状态：本地实现与局部回归 **PASS**；主控 #300 沙箱外真实 worker/Electron 回归 14 项 **PASS**（`09b-pending-runtime-01`）；新独立审查 **INCOMPLETE**，A-14 **NO_GO**。本记录不是独立审查结论。

主控 #299 批准实现。用户原答复的字节副本为 `20261016T012505Z-ideation-answer-001.md`。该答复要求 pending 可见、pending 时不回灌、上线再投递、protocol 与预算不变；#299 进一步明确原有 I2 只在 delivered 后登记，与原 request_id/entry_id 关联，不重做 send。

候选由 `commit-pending-delivery.sh` 冻结；提交后 `pending-source-freeze-01.json` 的 revision 为产品/测试源码提交，后续仅证据提交。审查应在主控新开的只读上下文中按该冻结版本开展，不复用旧审查或实现会话的自述。

范围：core.ts 仅收件箱投递/恢复/结果判定；daemon.ts 的 controller_start 接线、Stop 反馈筛选与 delivered 后反馈登记；relay.ts 的待反馈查询/意图去重。reviewer 启动和 T-082 区域无改动。README 同步当前状态说明。P1/I1 生成器、路径恢复、签字和 A-13 运行原件是此前尚未提交的交接材料，同批保留，但不替 pending 新实现背书。

验收应从用户决定重建，并用真实入口独立核对：

- 无 executor 会话时真实 send/Stop 生成原条目和可按发送方 request_id 查询的 pending 回执；无 gate feedback。
- 真实 controller_start 上线只入队；首启 unknown 时零业务 PTY 字节；初始 release 后存在真实 turn_submitted 才追加 delivered。
- 原 request/entry 只对应一条 I2，先有目标写出收据，再有反馈意图与派发；原 relay_results 不覆盖。反馈意图结果不明时不重送。
- 原条目 created_at 不变；executor 用真实请求文件/Stop ack，重复 ack 不新增 ack/wake；ideation 越权 ack 仍拒绝。
- 有会话仍直接 delivered，歧义仍错误；bare pending/unknown 历史不能因角色上线自动重送；旧 Stop/错 launch/preset/身份仍受原校验。
- 不借 operator 发 send/stop/ack、不添加新业务入口、不增加 protocol roots/Messages。

已知坏行为证据：`09b-pending-live-red-01` 为 A-13 实际事件 116/117，`09b-pending-chain-red-01`～`-03` 为修复前真实 daemon/inbox/Stop/relay 的新契约红态。`09b-pending-local-03` 是当前源码的 11 组检查；native process/PTY 仅是外部边界 spy，pending/relay/gates/startController 均为生产调用。它不证明真实双 Claude 完整 09B 通过。

保留的中间失败：`09b-pending-green-01` 是夹具未等回执写出就开始下个 ack，随后改为等待真实提交收据；`09b-pending-local-02` 是扩展串行入口总期限耗尽，后续保留单命令 5 秒期限、总期限按最多 17 次调用改为 90 秒，并保存耗时。不能把这些结果改为 PASS。

需主控执行的完整命令见 `09B-PENDING-OUTSIDE-COMMANDS.txt`。A-13 脱敏归档已只读完成（13 requests/2 responses），owner-bound 回收仅备好脚本。A-14 的阶段驱动须在新审查通过后，把 I1 的 pending 停点与后续 executor B1/I2 关联；本候选未生成或运行 A-14，不更改冻结 protocol 和预算。
