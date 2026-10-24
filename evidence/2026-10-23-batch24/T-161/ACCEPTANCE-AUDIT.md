STATUS: PASS
TARGET: frozen candidate `9f7deae97425c1602af10f434ea41c690c637010`

EVIDENCE:
- Ticket 明确要求只读 reviewer/历史 worker 无输入错误和焦点，主控窗格保留“普通终端 + 执行主控”；见 `.project-map/tickets/T-161-readonly-view-and-role-label.md:18`、`:25`、`:26`。
- 真实 Electron/后台/PTY 绿态：`OUTSIDE-06/green.json` 为 `PASS`，17 项全通过；截图确认 reviewer、history 无横幅/焦点，隐藏侧栏仍显示角色，真实 IPC 输入失败仍显示错误。
- 修前 red04 在真实 Electron 中复现 reviewer/history 输入错误与焦点抢占，且主控缺角色标签。
- 四个变异均被拒绝：观察焦点、抢只读焦点、缺角色标签、吞输入错误；均 exit 1 且对应断言失败。
- T-157 recover/expired 与 T-159 split 均通过。候选 `18ba7ced315d334511084c4e4804d6752c27e1df` 到冻结候选仅新增证据文件，产品代码和本票测试无差异。

FINDINGS:
- 无。

COUNTEREXAMPLE:
- 已知坏实现均被拒绝：`mutant-observation`、`mutant-focus`、`mutant-role`、`mutant-input-error`。

LIMITATIONS:
- `OUTSIDE-06/RESULT.json` 整体仍为 `INCOMPLETE`，原因是范围外已知 T-165 的 `t157-stop-input` 失败；未将全套结果上调为 PASS。
- 本票按任务卡使用受控 PTY，不主张真实供应商模型行为；Electron/UI 边界已实际覆盖。
