# T-164-2 执行主控对测试员提问的答复

2026-10-24 约 08:37Z，b24-t164b 一次排了三个问题，执行主控逐条在其窗格作答（逐字见 Herdr wG:p27 与 Codex 会话记录）。

1. 额度读数：测试员会话无 `/status` 入口。答以会话日志 `rate_limits`（08:35:58Z）：5h 窗口已用 39%，周窗口已用 6%；开跑前 `/status` 两窗口 100% left。提醒 5h 窗口约 25 分钟用掉 39%，到 90% 即停。
2. “恰好 1 个 Codex worker”的口径：B 独审打回且需改卡，测试员问能否回收 B 旧会话后为同票重派新 attempt。执行主控选“允许同票回收后重派，任何时刻只 1 个活跃 Codex worker”。依据：用户原话“应用内只用 1 个 Codex worker”（answer 20261024T061431Z-001）限制的是并行 Codex 用量；revise→reclaim→重派是任务卡要求的正常门禁流程。此为执行主控的解释，已在给用户的回复中说明。
3. REOPEN：执行主控只重开隔离 Electron（`STOP-APP.sh` 不带 `--all`，再 `START-APP.sh`），daemon 60015 保留；新 Electron PID 77811。A 的 reclaim 报 `worker_working` 按实情记录，不强制回收。
