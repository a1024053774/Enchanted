# 第五轮最终变异靶点核对

STATUS: PASS
TARGET: 最终 `round5-candidate.patch`；范围仅为 T133 变异靶点 P2 修复。

EVIDENCE:
- 冻结补丁对应当前 23 个受控文件与 4 个新增文件。相对 review3 快照唯一差异为 T133 第 92 行的变异匹配文本；生产 daemon、普通/结构化回复路径及正例断言均未改变。
- 旧靶点匹配 0 次，新靶点 1 次；夹具要求唯一匹配后才注入。
- 正例 verified-t133-codex 16 PASS，实际数据库有 answer、原问题/选项及非空 reply_to。
- 两份矩阵剔除 ENOSPC 的原 T124、加入另名 T124-02 后共 27 项，退出码均符合预期；其中 4 项故意预期退出 1。

FINDINGS:
- 无新增发现；限定的 P2 已关闭。

COUNTEREXAMPLE:
- reply-as-message 强制置空结构化回复解析。定位修正后，真实 Codex/hc 交互先通过 12 项，再在 only_approved_prompts_recorded 业务断言失败，数据库缺用户答复。
- mutant-business 日志/JSON/.hc.json 一致：退出 1、api_error=null、独立私有 core；不是定位、依赖或启动错误。
- 旧 mutant-target-red 只是夹具定位错误，没有计为业务反例。

LIMITATIONS:
- 独立只读核对，未重跑；正例运行早于这一行靶点修正，该行仅在指定 --mutant 时生效。
- 不扩展为全仓重新验收，不替代 agy 审查。Codex 用真实 CLI 与本地脚本化响应。

RULE:
- N/A，无新增或重复发现。
