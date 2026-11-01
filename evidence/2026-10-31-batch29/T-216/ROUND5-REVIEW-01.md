# 第五轮首次冻结候选只读审计

STATUS: FAIL
TARGET: `round5-candidate-review1.patch`（审计时名为 round5-candidate.patch；原文件整体移名保留），基线 `9c0e262125edb75ed841609472e32c952adc2bbd`。

EVIDENCE:
- `round5-t133-codex-01.json`：`only_approved_prompts_recorded` 业务断言失败，缺用户选择“先做哪一个？：T-1 先做”。该次真实 Codex 的 `out/user-own-hook.jsonl` 保存完整 `send_user_message_question_reply` 和 call id，模型确实收到答案继续运行。
- Claude 原生记录三个 issue 各 1 次；agy/opencode/Codex 的供应商证据各有 1 条本次原生收件；hc 为 started:true / confirmed。
- states、race、identity、unknown-03 覆盖真实后台/socket/私有 hc；unknown-03 有真实 Electron。T124 固定构件对照 26 PASS；T132、T171、R2 正例通过。

FINDINGS:
- [P1] `daemon.ts:349` / `panes.ts:451`：terminalUserPrompt 精确匹配 attach 文本会挡住 Codex 问题选项生成的包装答复；应保留原有可信问题答复路径，同时继续排除系统投递。

COUNTEREXAMPLE:
- force-blocked-02：startup_auth_no_input 失败，实际输入进入权限框。
- allow-working-02：working_no_input 失败，忙时实际收件。
- resend-unknown-02：unknown_never_resent 失败，实际重复提交。
- R2 duplicate：实际提交计数拒绝。
- allow-blocked-02 PASS：hc 拒绝 blocked、没有输入。

LIMITATIONS:
- 未修改文件、未跑供应商、未再委派，不冒充 agy 审查。
- done 窄竞态按已接受票面处理。
- agy/opencode 复核保留的原生行，未访问用户全局数据库。
- 角色改变、重接已有草稿尚无独立运行证据。

RULE:
- 完成检查点运行真实 `test_t133_codex_terminal_controller_e2e.py`，断言原问题、answer 形态、reply_to，不能只看侧栏恢复运行。
