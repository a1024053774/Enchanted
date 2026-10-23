STATUS: INCOMPLETE
TARGET: 65d56a39238ed1d23c4c2ea28e20cc4df56a34cc
EVIDENCE:
- 独立合同：card.md 完成条件及 inbox 20261023T125315Z-ideation-answer-001.md 问题 3。三处必须保留结束会话并标“已结束”；关闭主控须保留角色和项目层身份，不能重复成普通终端。
- 静态路径符合目标方向：sidebar.ts:173–188 保留最近确认角色；flow.ts:38–46 保留 ended；renderer.tsx:696 显示结束标签；Reflect 与流程继续消费侧栏状态。
- 已存隔离证据：projection-green-01.json、两个 *-02.json 变异、T-111 新旧合同互拒。预期值直接写明身份、状态和归属，没有从生产常量计算答案。
- build-final.json 记录构建退出 0；T-091 起点与候选同样失败，仅支持“不更差”。
- 首尾 HEAD 均为目标提交，工作树干净；project-map status 两次均无问题、无 stale。
FINDINGS:
- [P2] RUN-OUTSIDE-01.sh:30 — 所有红态共用宽泛判据，flow_running 加任意“natural_cli_exit”或“侧栏轮询已刷新”错误即可宣称已知坏行为被拒绝。尤其 controller 变异可能在关闭主控前因无关侧栏同步超时被计作有效反例。应按用例核对目标阶段及保存的实际违约字段；同步超时保留为 INCOMPLETE。
COUNTEREXAMPLE:
- 已存控制器回退普通终端变异在业务断言 Closed confirmed controller must remain an agent 失败；流程隐藏 ended 变异在预期 ended 的断言失败。有效，但只覆盖隔离投影。
- 独立检查 run_red 判据：一个只有初始运行检查、侧栏轮询超时、没有关闭主控观察的 sentinel 报告仍被接受。该判据不能证明 controller 变异确实被目标合同检出。
LIMITATIONS:
- 未运行真实服务、Electron、CLI 或沙箱外脚本；没有候选真实截图、CLI 自然退出、主控关闭后 UI/后台同步证据。不能据隔离绿态宣布整体 PASS。
- 本次相关能力轴为编排状态、异步轮询、身份范围、桌面交互；其他能力轴对本变更 N/A。上述真实边界均仍 INCOMPLETE。
- 指定五项 e2e 回归未运行；T-139 项目终端不进入任务视图尚无候选真实入口复验。
- 未静态确认新的产品行为违约；P2 是验收判据缺陷。构建成功不能补足运行证据。
RULE:
- 在沙箱外反例判定中，按 baseline／flow／controller 分别要求对应阶段、目标对象和业务字段违约；启动或同步失败不得计作已知坏实现检出。
