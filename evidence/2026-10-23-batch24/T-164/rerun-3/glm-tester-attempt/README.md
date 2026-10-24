# T-164-3 GLM 外层测试员尝试（停止，2026-10-24）

- 外层测试员 b24-t164c：Codex CLI `zcode/GLM-5.3-Flash` max（launch-bb855e58621245358a3db23a073ac3ef，Herdr wG:p2B），10:10Z 派发，约 11:33Z 停止。实例 `/private/tmp/t164-dogfood-b1twgqx6`（基线 e3b14d27b），已按 T-088 归档（`../../t164-dogfood-b1twgqx6.archive.json`），隔离 codex-home 与 operator.json 删除未归档。
- 实际进展：确认窗口属于本轮实例、打开项目、新建项目终端、启动 Claude CLI 并信任本轮 repo；之后在终端输入与剪贴板（pbcopy 在沙箱内退出 1）上反复尝试，没有提交第一条主控提示，应用内没有 worker、没有门禁事件。
- 观察到的模型行为（只记事实，不作 GLM 与 6.1-sol 的能力比较）：两次在找 Computer Use 调用方式时结束回合，执行主控各提示一次（#86、#87，第二次给出上一轮可用写法）；上下文压缩一次 6 分 37 秒（累计输入约 7M tokens）；压缩后重新探查 `sky.target`，并列出用户 `~/Library/Caches`、`~/Library/Application Support`、`~/.codex/computer-use` 目录，超出任务卡范围。
- 窗格里两次中断与一次“继续”不是执行主控发的（执行主控对 b24-t164c 只发过 #85～#87，见 `evidence/2026-10-23-batch24/dispatch.jsonl`），按人工介入记录。
- 用户决定（2026-10-24，执行主控当面提问，用户选择）：“等 09:11 换回 6.1-sol”——停掉 GLM 测试员、保留证据；09:11 5h 窗口重置后，外层测试员用 gpt-6.1-sol high，应用内 Codex worker 仍用 GLM-5.3-Flash max，新开实例。
- 本目录是测试员 worktree 中未提交的产物原样复制（截图、AX 差异、提示词草稿），未经整理。
