# T-057 问题上报面板完整化

状态：**BLOCKED，待主控决定；未实现、未验收，ticket 保持 open。**

依据：主控 #6 任务书、主控 #7 worker 角色卡、T-057 `ready_rev: 2`、`controller-split-user-input-2026-10-09.md` 第 4 节。共同规则中残留的 `ready_rev: 1` 按任务书首段与当前 ticket 的明确版本 2 执行。fork 基线为 `2330534b2cf906b9d8f0a0b643adb370683d7fe0`；没有 fork 候选提交。

## 范围与决定

目标是补齐处置、视图、本机草稿、按会话打包/逐个发送、一次性关闭告知、计数徽标、静音系统通知以及完整可点击的回复按钮。非目标是改门禁业务状态、角色权限方向、生产部署、重启正式工作台或 Herdr、修改别的任务或构建输出。

验收条件是 ticket 的全部勾选项，预期取自 spec，先在父修订保留合同红态，再取得同一入口绿态与反例。Tracer bullet 先贯通一项处置到真实面板，再扩展其他动作；Deep modules 保持核心拥有记录与派生状态；Ubiquitous language 使用现有问题、答复、处置、task/attempt/thread。

**REALITY GATE: BLOCKED。** observed：四处必需的现有接入在任务书指定目录之外；已有桌面通知桥和设置开关可复用。unknown：主控是否允许改这四个上游文件、隔离系统通知验证是否需要 macOS 权限。只读探针已经定位具体接入，未启动隔离服务。决定及下一行动归主控，见 [needs-decision.md](needs-decision.md)。没有使用 fallback 或替代入口绕开限制。

T-055 最终独立审查 PASS 与当前 fork 基线一致；其报告里的历史 INCOMPLETE 保留。core 与 inbox 的 `forward` 超时派生不一致，属于本票要求补齐的状态，后续以 spec/inbox 为准；当前仅记录，未修复。

## 证据与未运行项

- [scope-probe.json](scope-probe.json)：只读源码位置、完整版本、argv、cwd、退出码和输出；[scope-probe.py](scope-probe.py) 可重放。它不证明产品行为。
- 已按 worker 角色卡追加 blocking issue：[20261009T132451Z-worker:s11-t057-issue-001](../../../.project-map/inbox/20261009T132451Z-worker:s11-t057-issue-001.md)。命令为 `scripts/inbox send --from worker:s11-t057 --to triage --kind issue --title 'T-057 需要批准四处上游接入' --body-file evidence/2026-10-09-batch11/T-057/needs-decision.md --blocking --ref ticket:T-057 --ref file:evidence/2026-10-09-batch11/T-057/needs-decision.md`，退出码 0。
- 项目地图开工检查：Problems 0，Stale living docs 0；结束检查保存为 `map-status-final.log`。
- 没有产品代码改动，因此未运行合同红绿、真实 HTTP/MCP/CLI 行为、截图、真实模型、typecheck、lint、fmt 或既有套件；未执行 fresh-context 独立审查，尚无冻结实现候选。这些均不写为通过。
- ticket 指定的六种失败方式（并发答复、活跃 turn、送达前结束、关闭与答复交叠、时钟回拨、分隔文字原样保存）尚未实现或验证，后续必须逐项保留实际处理与证据。
- 仅创建本票证据与更新本票 Resolution；保留 T-061 暂存文件、controller 日志和 fork 未跟踪的 `.grok/`。不碰正式数据目录、用户配置、dist、依赖、T-061 checkout；未 push。

本次交接为阻塞报告，不是已完成候选的 submit，不宣称门禁验收/集成或 ticket 关闭。
