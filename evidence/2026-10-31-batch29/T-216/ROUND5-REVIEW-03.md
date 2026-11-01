# 第五轮恢复修正后的只读审计

STATUS: PASS
TARGET: `round5-candidate-review3.patch`（审计时为 round5-candidate.patch；移名保留），基线 9c0e262125edb75ed841609472e32c952adc2bbd。

EVIDENCE:
- 完整候选与冻结文件一致；当前 verified 矩阵覆盖全部场景。Claude 三条问题、agy/opencode/Codex vendor/local 原生记录实际各一次。
- 恢复红态为队列丢失及未知提示缺失；绿态恢复两条消息顺序，未闭合 intent 持久记 unknown、实际仍仅收一次。
- idle if:idle、done 无条件且无 force；HC 身份/caller/wait 与关联结果一致。草稿、角色切换、前台 CLI、更换项目路由及答后关闭符合要求。
- T133 当前 16 项通过，DB 读回普通提示、带 reply_to 的问题答复、release 提示；T124 ENOSPC 保留为失败，另名复跑通过。

FINDINGS:
- [P2] T133 reply-as-message 旧变异靶点失效，在夹具定位处中止。更新靶点并确认业务断言失败；本轮真红绿与当前 T133 正例独立成立，不阻断上述结论。

COUNTEREXAMPLE:
- force、放行 working、未知重发被实际输入断言拒绝；仅放行 blocked 仍由 hc 拦住；重复 Claude 原生记录确为 2 次。

LIMITATIONS:
- 只读核对源码/SQLite/原生记录/Electron，没有启动测试或供应商。
- 不替代 agy 独立审查或发布批准；供应商探针不证明模型能判断全部问题类别。

RULE:
- 变异必须核对业务失败位置，夹具定位失败不算捕获成功。
