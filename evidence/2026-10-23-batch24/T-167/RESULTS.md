# T-167 Codex worker 的门禁回执粘贴后提交未生效：结果

- 写入者：执行主控（Claude Code），按构思主控 answer 20261024T070244Z-ideation-answer-001 转述的用户决定：“让执行主控修,然后做完每个票让 agy 审查”。
- 基线：main `a808c1137`。真实 Codex CLI `codex-cli 0.163.0`；模型端为本地脚本化 Responses（响应头 `x-codex-primary-used-percent: 94`），厂商模型回合 0；夹具 CODEX_HOME 在夹具目录内，不含 auth.json，不读写用户 `~/.codex`。
- 逐项结果见 `CHECKS.json`；运行目录已按 T-088 归档，清单见 `*.archive.json`。

## 根因（先由归档事件定位，再用真实 CLI 复现）

T-164 实例 B（launch `5314796c…`）的原生记录：回执 #3 在 06:26:08.528 粘贴、06:26:08.829 按回车后，Codex 没有写 `task_started`，而是连写三条 `thread_settings_applied`：模型 `gpt-6.1-sol` high → `gpt-6-luna` medium → high → medium；06:29:23 人工回车后的回合带 `<model_switch>`。同一回合的 token_count 报告周额度已用 94%。

Codex 0.163.0 的二进制里有 `rate-limit-switch-prompt`：“Approaching rate limits / Switch to … for lower credit usage? / Keep current model …”，随后是 “Select Reasoning Level for …”；配置项 `notice.hide_rate_limit_model_nudge`。额度接近上限时，Codex 在回合结束后弹出这个提示；a2a 随后写入的回执粘贴与回车答掉了提示（默认项为换模型），回合没有开始，后台却记 `turn_submitted`。这不是时序竞态：探针里回执晚 30 秒写入，提示仍在等回答。

附带影响：T-164 中 worker B 自 06:26:08 起实际运行在 `gpt-6-luna`，不是启动参数里的 `gpt-6.1-sol` high。

## 修改

- `workbench/src/panes.ts`
  - 受管 Codex 会话启动参数加 `-c notice.hide_rate_limit_model_nudge=true`，与已有的 `check_for_update_on_startup=false` 同类：不让 CLI 的提示被任务输入答掉。只经启动参数，不写 home。
  - 写入提交键后 20 秒内没有原生开始信号（`turn_start_signal`），记 `turn_start_missing`；状态带 `start_missing`。不重发、不补按键。
- `workbench/src/sidebar.ts`、`workbench/app/renderer.tsx`：侧栏与窗格头显示“回合未开始”，窗格内说明“消息已写入终端并按了提交键，但 CLI 没有开始新回合……后台不会重发，也不会替你按键”。
- `workbench/README.md` 两条说明。

## 证据

| 项 | 命令 | 结果 |
| --- | --- | --- |
| 事实探针 | `probe_codex_nudge.py`（真实 Codex CLI 在 PTY 中，无 a2a） | 不隐藏：提示出现，回执回车后无第二个模型请求，模型换成 luna（medium/high/medium，与 T-164 相同）；`--hide-nudge`：无提示，回执开始回合，模型保持 sol high。探针的 `tui_ready`/`first_turn_answered` 判定因转义序列拆字没有命中，为探针自身判定问题，结论以请求数与 rollout 为准 |
| 红态（端到端） | `test_t167_codex_start_e2e.py --revision a808c1137` | red-1、red-base：`red_reproduced=true`，回执未开始回合、模型被换、窗格忙、侧栏未知，与 T-164 一致 |
| 绿态 | 同上，修后，`--scenario receipt` | receipt-1/2 PASS：回执开始回合，模型与强度不变，只写入一次，无“回合未开始” |
| 如实显示 | `--scenario dialog-open`（去掉隐藏参数，让提示真实出现） | dialog-open-1/2 PASS：回合未开始，记一次 `turn_start_missing`，状态、侧栏、窗格头都显示“回合未开始”，只写入一次、不重发 |
| 已知坏实现 | `--scenario dialog-open --mutant no-start-check` | 只在四项“如实显示”检查上失败 |
| 回归 | `RUN-01.sh` | build、Claude worker 粘贴提交（T-157 stop-input、T-165 ordered）、T-127 Codex home 全部 PASS |

## 未覆盖

- 未用真实 Codex 复验（真实账号与厂商模型）。按构思主控 answer 20261024T072734Z-ideation-answer-001，T-167 的真实 Codex 复验与 T-164 重跑集中成一次连续运行。
- 隐藏的是 Codex 的换模型提示；额度提示仍以 Codex 自己的“Heads up … weekly limit”文字出现在终端里（见 dialog-open 截图），不影响输入。别的 CLI 提示若吃掉回车，现由“回合未开始”如实显示，未逐一枚举。
- `readWakeDelivery` 仍以 `turn_submitted` 报 delivered（收件箱唤醒的投递状态），未改；本票的显示以原生开始信号为准。

状态：agy 独立审查 PASS（`review-agy-01.md`，三条 P3 观察，无需改动）。未用真实 Codex 复验。
