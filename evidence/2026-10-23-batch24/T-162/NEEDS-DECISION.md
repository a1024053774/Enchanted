# T-162 写入边界核对

状态：已解决（主控 #30）。task T-162-1，attempt a1，worker b24-t162，起点 c01742804。

主控 #30 已批准：允许局部修改 `daemon.ts` 的 `role_request_decide` 与 `roleRequests.ts` 的 `decide`，只记录操作员亲自的批准/拒绝并关联角色事件；自动拒绝、过期不算；`gates/core.ts` 移出允许范围。修订来源：main 提交 `1b5d6a8b5` 的任务卡，本分支按文执行，无需合并 main。下文保留初次上报内容。

任务卡允许修改 `workbench/src/gates/core.ts`，限定为“仅角色批准写记录处”。实际代码中，该文件没有角色批准处理：

- `workbench/src/daemon.ts:517` 校验操作员身份，并调用 `roleRequests.decide(...)`。
- `workbench/src/roleRequests.ts:91` 的 `decide` 校验申请状态，99 行追加 `role_request_decided` 事件。
- `workbench/src/roleRequests.ts:122` 还会自动拒绝同角色的其他申请；这不是用户点击的拒绝，不能全部作为用户输入。

建议最小调整：允许修改 `daemon.ts` 的 `role_request_decide` 分支，以及 `roleRequests.ts` 中该分支调用的 `decide`，仅用于把操作员的批准/拒绝与统一用户输入记录关联，并保持事件与记录写入的一致性。继续保留其他产品文件的原边界；不把自动拒绝或过期算作用户输入。

在边界获准前，不修改产品行为。继续准备真实 Electron 红态复现；沙箱外运行由主控执行 RUN-OUTSIDE 脚本。
