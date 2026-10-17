# 09B 材料审阅：独立目录与回合预算前置

主控 #185 要求先交计划性材料，不启动。单角色真实转交已 PASS，但当前 `claudeLaunch.ts` 第 21／31／40～46 行仍是 P1：state/repo 必须属于同 root，两个 preset 共享 root/home、claude、requests、hooks、tmp、shell；turn_limit 只收1/2。`panes.ts` Claude signal 第 721 行同样只承认1/2。

静态构造探针已实际证明共享六个路径及第三根被拒，证据在 `09b-profile-preconditions/results.json`；这是已知新行为尚未接通，不把当前 P1 约束叫做产品缺陷。09B 完整因果链至少需要 ideation3根、executor3根；为同场实际重复 ack 反例，材料提议 executor4根。拟预算 I=3/4、E=4/7（根/主Messages），合计11，低于 #163 批准的每角色6/12、合计24。

建议材料审阅后统一启动 profile：按 preset 推导各自 HOME/config/tmp/shell/requests/hooks/debug/user-data，保留同 broker/state/repo；按批准 manifest 支持所需3/4根，并同步 P1 生成器和两个现有限制，不保留共享目录 fallback。09B 假 API／阶段驱动应以实际登记文本与实际 stop/request ID 绑定，不能沿用单角色写死的 #1/#2；共库 dispatch.seq 是全局号，目标派发也占号。

本轮不改产品、不构建双角色可执行入口；冻结包明确为 plan-review，launch NO_GO，批准字段空。此 issue 非 blocking 材料准备；后续实现与真实入口红绿／权限反例由主控审阅后安排。未新增或修改 ticket，不自行关闭本问题。
