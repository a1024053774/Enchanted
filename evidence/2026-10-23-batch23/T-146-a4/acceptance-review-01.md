STATUS: INCOMPLETE
TARGET: a2ec0db9d7f0025c414cc4988e411c1b41c98ddf
EVIDENCE:
- 依据任务卡 T-146-4、T-133/T-107 既有合同及用户裁定 B 重建期望；受保护验收文件未被候选修改。
- 独立复跑 released_projection、ended_projection 均 PASS；新报告位于 `/private/tmp/t146-a4-review-release-20261023T1620.json`、`/private/tmp/t146-a4-review-ended-20261023T1620.json`。这仅证明 L1 投影逻辑。
- 新投影测试的期望使用合同规定的角色、生命周期和状态，没有从生产输出生成答案；额外覆盖 unknown、新角色替换、历史角色、权限不恢复和只读性。
- RUN-OUTSIDE-01.sh:34–54 要求起点版本、目标超时、前置业务检查及成功 released 回执；不接受任意启动失败作为红态。关闭主控反例经既有 red_verdict.py 核对关闭成功、Reflect ended、同一 launch 被降为 shell，判据能定位业务违约。
- RESULTS.md 明确标为 INCOMPLETE，没有把投影 PASS 冒称真实入口通过。
- 本次适用状态编排、异步更新、角色撤销和桌面交互；检索、媒体、外部业务写入及部署为 N/A，本候选未涉及这些合同。

FINDINGS:
- [P2] evidence/2026-10-23-batch23/T-146-a4/RUN-OUTSIDE-01.sh:55 — T-133/T-107 绿态在交回角色后核对 sidebar_snapshot 移除主控及后续 CLI 输入，但未核对该阶段侧栏普通终端的 DOM 状态和流程 DOM 移除。即使此脚本将来全绿，交回后的完整可见行为仍缺直接证据。补充独立 Electron 驱动或人工记录，在同一次交回后核对 API、侧栏、流程和 Reflect；无需修改受保护验收文件。

COUNTEREXAMPLE:
- 起点仍保留运行中终端的主控条目：baseline-counterfactual-01.json 在“Released live terminal must not remain a controller”业务断言失败。
- 已结束主控降为普通终端：closed-controller-mutant-01.json 被既有 ended_projection 的“Closed confirmed controller must remain an agent”断言拒绝。
- API 正确而交回后 UI 残留主控的反例：未执行；上述现有真实入口检查尚不能排除。

LIMITATIONS:
- 当前候选的真实 Electron／CLI 绿态和 RUN-OUTSIDE 回归未运行，L3 边界为 NOT_RUN；不能宣布整体验收通过。
- 已有真实入口红态在本候选中仅保存摘录；本次未复跑原始现场。
- 新增 final-checks-01.json 不属于冻结提交，未用于验收结论。未修改源码、测试、Git 或启动 Electron。

RULE:
- API 状态通过不能替代 UI 行为证据；交回角色的 L3 验证应在独立 Electron 驱动中同时保存并断言可见状态与后台状态。
