# T-259 第一次独立审查

STATUS: FAIL

SUMMARY: 1 项 P1，0 项 pre-existing。审查员为独立、无父会话历史的 gpt-6.1-sol high 会话 `/root/t259_independent_review`，只读固定候选。根据用户本轮隔离修复例外派发，没有走已故障的正式门禁。

TARGET: `fb96f5aee181035a1fc810ead1e952dba10cbef8`；基线 `1013b542377325cc1e37f89bdbf37ceb70b7e0ef`。

EVIDENCE:

- `e2e-candidate.json`：独立运行真实 daemon/socket/PTY 标准回收，9 项通过。
- `unseen-inputs.json` / `unseen_inputs.ts`：未见的 controller_screen_key_intent、terminal_composition_started、hc_send_intent 三种输入，18 项检查通过，均拒绝且保留路径。
- `regression-t253-current.json`：9 项通过；`regression-t170-current.json`：5 项通过。
- 已核对父版和三变异原始结果；冻结验收未改。未修改正式应用或数据库。

FINDINGS:

- [P1] 首候选 `workbench/src/gates/core.ts:4593` 先真实 archiveThread，到 4597–4601 才保存 reclaimed。归档已落盘后异常中断，正常重启时 panes.ts:896 不恢复 archived 窗格；同一 reclaim 在 core.ts:4515 的 readThread 返回 unknown_pane，原 attempt 仍 preparing/runtime_identity=null/reclaimed=false，路径保留却无法继续回收。底层不恢复 archived 的行为已存在，缺口是新 preparing 回收流程没有闭合这个中断窗口。
- 独立命令：`PYTHONPATH=/private/tmp/a2a-t259-repair-20261108/workbench/tests ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 /private/tmp/t259-review-20261108-independent/archive_gap_e2e.py --summary /private/tmp/t259-review-20261108-independent/archive-gap.json`。退出 1、errors=[]；真实 pane_archived 已落盘，再次 reclaim 返回 unknown_pane。复现脚本和 host 原样保存在本目录；从本目录重放时 PYTHONPATH 仍指向候选 workbench/tests，summary 使用新路径。
- 主控在修复前独立复跑同脚本得到同样业务失败：`controller-reproduced.json`，退出 1、errors=[]。没有凭审查建议直接修代码。

COUNTEREXAMPLE: 父版、session/input/提前释放三个变异均判红；首候选未能恢复真实归档后的中断。

LIMITATIONS: L3 本地真实入口，无模型等待程序；不代表模型能力或安装成功。未复跑完整 dispatch→submit→验收→集成。故障由真实归档后抛错再正常停止重启构造，没有 SIGKILL；关键持久化窗口一致。最初 JSON 解析异常来源属于非目标。

RULE: 现有真实 daemon E2E 应覆盖每个持久化副作用后、门禁完成前的中断，至少覆盖 pane_archived→reclaimed；不能只测归档发生前的拒绝。

本文件是独立审查结论的中文归档；主控补充的复现来源已分别标明。独立审查不因后续修复改写成 PASS；后续只允许一次针对性复审。
