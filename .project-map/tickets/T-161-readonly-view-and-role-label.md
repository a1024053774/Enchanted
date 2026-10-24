---
id: T-161
title: F02+F07：只读查看报输入错误横幅；窗格头不显示主控角色
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

报告 F02（一般）：点只读审查员/历史 worker 即出现 `a2a:focus-observation: Window is not available for input` 横幅，未输入任何字符。F07（轻微）：窗格头仍写普通终端，角色只在侧栏。
目标：只读窗格不申请可写输入焦点，真正输入失败才报错；窗格头同时显示载体与已确认角色。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [x] 真实 Electron：点审查员与历史 worker 无错误横幅；真实输入失败仍提示。
- [x] 批准后的主控窗格头显示角色，收起侧栏仍可辨认。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。`renderer.tsx` 收紧可写焦点与焦点观察条件：审查员会话、失效 attempt 的历史 worker 等只读查看不再请求输入焦点、不出现输入错误横幅；真实可写会话的输入失败仍然提示。窗格头在“普通终端”标签后显示已确认的主控角色，来源是已确认的角色事实而不是窗格名，侧栏收起或窗格改名后仍可辨认；README 同步。
沙箱外真实 Electron（0 个真实模型回合）：red04 在修前版本只在 6 条缺陷断言失败；outside-06 green 17 项 PASS，4 个坏实现（只读也观察输入错误、只读也请求焦点、不传递角色、吞掉真实输入失败）都只在预期断言被拒；T-157 recover/expired、T-159 split 回归 PASS。同场的 `test_t157_stop_input_e2e.py` 失败是合并前 main 已有的时序缺陷，执行主控另开 T-165 跟进，不计入本票。独立审查 agy PASS，无发现。合并 ab8cb0fa4；合并后检查见 `evidence/2026-10-23-batch24/merge-checks/ab8cb0fa4/README.md`。证据 `evidence/2026-10-23-batch24/T-161/RESULTS.md`。
