# T-257 派发记录（2026-11-08）

状态：INCOMPLETE。仅完成身份、任务卡和派发；修复与验收尚未完成。

- 执行主控终端：`55d61e9f-3657-41c2-9827-8cfd5c04cb9b`。
- 角色申请：`94be9df4-1496-4c90-8a11-f3218398fa32`，界面批准时间 `2026-11-08T10:41:50.097Z`。
- 本轮授权：用户要求“先修 T-257，走门禁派发并盯到结果，再继续 T-249/T-250；别启动 Claude，别跳过敏感变更集成前的用户证据批准。”完整交接见 `evidence/2026-11-08-controller-switch/executor-handoff.md`。
- 初始源码：`489da2212e56e709950c5da38263c4ff2b2976b0`；授权记录提交：`5c7df3a93019cea1a690194773d967bebb69a4ef`，也是 attempt 基线。
- task：`a2a+T-257-1`，spec_rev/card_version/ready_rev 均为 1。
- attempt：`42b3cd31-9194-45ba-85ea-4744b051cfe5`；session：`8563938f-d5bf-4ab7-b1ce-157ee39503ab`；fence：1。
- launch：`6b6a329a-5072-416c-a00f-af1b62183969`；thread：`3d277255-4396-40d2-8277-c3c939307849`。
- worktree：`/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-257-1-a1`。
- 启动参数实际记录：`worker-launch-checked.json`。Codex CLI `0.167.0`；模型请求 `gpt-6-astra`，强度 `xhigh`，`service_tier="default"`。这些是启动配置证据，不证明供应商实际服务层级。
- reviewer 设置只读核对：事件 137637 为 `gpt-6-astra`、`xhigh`、`fast=false`；真正审查启动后仍需核对 argv。

首次卡保存被拒，原因是 `task_type` 未使用允许的枚举。`task-card-v1.json` 保留这次输入；改为模板的“后端逻辑”后，`task-card-v1-valid.json` 保存为门禁 v1。其后 create 成功。

首次 dispatch 报 `path_overlap`，只列出 T-257 两个新测试与旧 T-249 卡的 `workbench/tests/` 重叠。已独立读取旧候选 `dc5158883..0c3da7ade` 的文件清单：只含三份 `test_t249_*` 测试，与 T-257 的文件无交集。按本轮授权记录 overlap_reason 后 dispatch 成功。没有回收或重派旧 T-249，也没有修改门禁数据库。

实现者负责 worker 子目录；执行主控负责本目录与票。保留原工作区历史脏改和旧失败现场。下一门槛是修前真实入口红态；随后同入口绿态、工作中拒绝回收的反例、门禁机械检查和独立审查。仅限触及 REVIEW.md 敏感路径时，集成还需用户读证据批准。T-249/T-250 的 terra Computer Use 验收安排不变。
