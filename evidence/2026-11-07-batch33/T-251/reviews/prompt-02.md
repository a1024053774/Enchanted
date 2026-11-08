你是 a2a（Enchanted）仓库的独立审查员，只读：不改任何文件、不提交、不运行会写仓库的命令。工作目录是一个 git worktree，分支 `fix/t251-untrusted-turn`。用中文写结论。

这是复审，只审上一轮（审查 01，结论原文 `evidence/2026-11-07-batch33/T-251/reviews/review-01.md`）之后的修复范围：`git diff ab912013b HEAD -- workbench .project-map evidence/2026-11-07-batch33/T-251`。需求见 `.project-map/tickets/T-251-claude-worker-cwd-untrusts-turn.md`；项目规则见 `AGENTS.md`、`REVIEW.md`。实现者对审查 01 每一条的处理与依据写在 `evidence/2026-11-07-batch33/T-251/RESULTS.md` 的“审查 01 与处理”一节。

请逐条核对：
1. 第 1 条（符号链接）实现者没有改代码，依据是真实 Claude Code 2.1.319 探针（`review-probes/symlink-cd.json`、`review-probes/probe_symlink.py`）：cd 进向外的链接后 Claude Code 自己把 shell 目录重置回工作区，钩子从不报链接路径；并认为钩子里的 cwd 是会话自报字段，按真实路径解析不增加身份保证。这个依据是否成立？有没有真实入口能让 Claude Code 报出指向工作区外的链接路径（例如链接指向 extra_directories、或 Codex 的情形）？拿不准写“未证实”。
2. 第 2 条：`workbench/src/gates/core.ts` 的 `turnRefused` 文案是否已不再断言窗格空闲；README 同处是否一致。
3. 第 3 条：`workbench/README.md` 补的 T-251 例外是否与代码一致（只对 Claude worker；Codex、agy、opencode 不变）。
4. 新修：`workbench/src/panes.ts` 的排队绑定改用 `insideLaunchDirectories`。核对：前缀相同的兄弟目录、工作区外、别的会话仍不绑定；与 T-157、T-165、T-166 的排队语义是否冲突；测试 `workbench/tests/test_t251_queued_subdir.ts` 的期望是否来自需求，红态（`red/queued_subdir.json`）是否在修前源码上取得。
5. 新检查：端到端测试的 `issue_sent_through_inbox`（先写成 `issue_delivered_to_executor`，期望写错后改）与变异 `no-delivery` 是否真能区分“送达”与“只记录不送达”；看 `green/e2e-cd-r3.json`、`green/e2e-compact-r3.json`、`green/e2e-untrusted-r4.json`、`mutants/e2e-no-delivery-r2.json`（`green/e2e-untrusted-r3.json` 与 `mutants/e2e-no-delivery.json` 是改检查前的运行，原因见 RESULTS.md）。

只报这个范围内的问题；上一轮已经确认没问题的部分不要重审。每条给文件:行号、输入或时序、会出什么错。结尾给结论：可合并 / 需修复（列出必须修的）/ 无法判断（缺什么）。
