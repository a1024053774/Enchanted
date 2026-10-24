# T-171 修订后旧 attempt 的问题提示“可能已随修订失效”：结果

- 写入者：执行主控（Claude Code）。来源 T-164 第四轮 N07；用户选“建票:标“已随修订失效”，由我一键确认关闭”；例外语义按构思主控 answer 选 A（用户确认时看原文判断，门禁不分类）。
- 基线 main 15a444674。真实后台、门禁、终端主控、真实 Claude Code worker（本地脚本化 Messages 接口，0 个厂商模型回合）、真实 Electron（DevTools 协议）。
- 运行：`python3 -B workbench/tests/test_t171_superseded_issue_e2e.py [--revision 15a444674 | --mutant auto-close|any-attempt] --summary <new>`；汇总 `CHECKS.json`，运行目录按 T-088 归档（`runs.archive.json`）。

| 项 | 结果 |
| --- | --- |
| 红态 red-2（修前 15a444674） | 两条 blocking 都是“等你决定”，项目行与页签角标 2；无确认按钮（`red-2-01.png`、`red-2-failure.png`） |
| 绿态 green-2、green-3 | PASS：a1 的问题“可能已随修订失效”并带 attempt；a2 的问题“等你决定”；角标 1；主控 `disposition close` 被拒 `blocking_requires_user`；卡片含原文与确认按钮；点击后门禁“已关闭”、处置来自 user、原因“已随修订失效”、记 1 条 `action`/`issue-panel` 用户输入（`green-2-01.png`、`green-2-02.png`） |
| 变异 auto-close（失效即关闭） | 被拒：old_issue_marked_superseded、confirm_shows_full_issue 失败 |
| 变异 any-attempt（不看 attempt） | 被拒：new_issue_still_waiting 失败，角标为 0 等待超时 |
| 回归 T-132 问题面板 | PASS |
| 早期运行 green-1、red-1 | 测试未等 a1 回合结束就 reclaim，被 `worker_working` 拒，属测试错误；改为按 T-158 的静止判据等待后重跑。保留不删 |

未覆盖：门禁生成的问题（`from: system`）与普通 `revoke` 的不提示路径没有在端到端里构造。
