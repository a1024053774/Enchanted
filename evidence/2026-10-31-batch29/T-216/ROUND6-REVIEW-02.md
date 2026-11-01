STATUS: FAIL
TARGET: round6-candidate-review2.patch（审查时名为 round6-candidate.patch；之后只新增迟到钩子的失败测试，产品代码未变）
EVIDENCE:
- round6-red-unsent-01 在 unsent_body_is_user 失败，round6-green-unsent-01 全通过，纯意图吞用户已修。
- provenance 两家真实 CLI、本地接口的排队无关用户、系统正文排除一次、第二次同正文记录已通过；未知恢复与重启恢复通过。
- round6-verified-restart-unknown 实际收到一条系统提交，只有 intent 与恢复 unknown，没有 hc_send_result。
FINDINGS:
- [P1] workbench/src/panes.ts:505 — 实际已送但返回未落库即退出，恢复后迟到 UPS 会误记用户。需能核对实际发送关联，并同时守住未发意图不吞用户。
COUNTEREXAMPLE:
- 独立只读审查从冻结方法原体，用 Node SQLite :memory: 输入上述持久状态：claimedAsSystem=false，wouldAppendUserInput=true，claimEvents=0。
- restart-unknown 替身不发 UPS，原有 system_not_user_input 没覆盖该误分类。
LIMITATIONS:
- 审查时最终矩阵未完成；当时尚未另跑真实 CLI 迟到钩子。本文件对应审查原结论，随后实现者新增真实入口 round6-red-late-hook-01 验证。
- 本次只读审查未连接 hc、调用供应商、修改或委派，不替代 agy 审查。
RULE:
- 保留两个真实崩溃窗口：RPC 未发时同正文记用户；RPC 已送但结果未落库时迟到 UPS 应排除一次。核对原生钩子和最终用户记录。
