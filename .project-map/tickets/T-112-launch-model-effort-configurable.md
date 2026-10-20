---
id: T-112
title: 受管会话的模型与思考强度不再写死：设置里可改，主控派发时可指定，门禁只记录不按固定值拒绝
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：执行主控缺陷上报 `worker:s18-t108-issue-001`（`workbench/src/panes.ts:500` 的 `worker_executor_mismatch` 要求 `effort === "xhigh"`，README:465 同写），与用户 2026-10-19 定的 high 冲突。

用户逐字（2026-10-20，会话"a2a-构思主控"）："worker_executor_mismatch 还要求 effort 必须是 xhigh,这个不要写死,用户可以自行修改,也可以在和主控聊天时,主控来选择,而不是写死 effort"

本票**取代**执行主控原计划的"把 xhigh 改成 high"的缺陷票：不是换一个写死的值，而是去掉写死。

1. **去掉写死**：门禁与 `panes.ts` 不再按固定 effort 拒绝启动；`worker_executor_mismatch` 不再检查 effort 取值（身份、版本、路径等其余检查不变）。
2. **默认值可改**：工作台设置里按角色（worker、reviewer、monitor，以及各主控）配置模型与思考强度，用户随时可改，存进 a2a 自己的库；出厂默认按 AGENTS.md 当前规定（Codex 的 `gpt-6.1-sol` high，不传 Fast）。取值范围取各 CLI 当前文档化的选项（读已装版本的帮助核对，不凭记忆写死枚举）。
3. **主控可指定**：主控派发时可以带模型与强度参数覆盖默认（用户在和主控聊天里说"这个用 xhigh"，主控照做），没带就用设置里的默认。
4. **只记录、不判断**：完整启动 argv（含模型与强度）照旧写进启动记录；不把请求配置当作供应商实际 tier 的证明（AGENTS 已有此规则）。是否合理由用户和主控判断，不做策略引擎。
5. **同一原则的适用范围**：用户纠正的是"写死 effort"，同类的"写死模型"一并处理（模型同样走设置默认加主控覆盖）；Fast 的开关同理，出厂默认不传 Fast。若发现某处写死会使安全边界失效（如 reviewer 必须只读沙箱），那是权限不是强度，保持不变。
6. README 与角色卡里写死 xhigh 的说法一并改成"默认见设置，可改"。

## Acceptance

- [ ] 红态：当前 `effort: high` 的受管 worker 派发被 `worker_executor_mismatch` 拒绝（真实入口复现）。绿态：high、xhigh、其他文档化取值都能启动，启动记录里的 argv 与所选一致。
- [ ] 设置：界面里改 worker 的强度后，下一次派发使用新值；主控派发带覆盖参数时优先于设置；都没有时用出厂默认。
- [ ] 反例：覆盖参数取了该 CLI 不支持的取值时，a2a 不改值、不替 CLI 做取值判断，原值原样进入完整启动 argv 与启动记录，并原样传给 CLI；reviewer 的只读权限不受强度设置影响。（2026-10-20 用户裁定修改，原文为“由 CLI 自己的错误暴露并被记录为启动失败”；实测 Codex 0.162.1 不在启动时拒绝，而是把该值原样放进首轮请求，真实供应商的响应没有实测。用户在执行主控会话中选择：“改验收，原样传递即可 (Recommended)”。）
- [ ] 全仓检索确认没有其他写死 effort/model 的拒绝逻辑（列出命令与结果）；`project_map.py status` 0 问题。

## 不做

不做按成本或额度自动选强度；不做强度策略引擎；不改身份、版本、路径边界等其他门禁检查。
