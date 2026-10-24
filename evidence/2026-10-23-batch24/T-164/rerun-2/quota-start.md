# T-164-2 开跑前额度读数

- 读取时间：2026-10-24 08:14 UTC 前后，外层测试员 b24-t164b（Herdr wG:p27，launch-ba370acf37754311a1d5ffd6a2c2c696）派任务前，由执行主控在其窗格里输入 `/status`（本地命令，不发模型请求）。
- Codex v0.163.0，账号类型 Business（用户 2026-10-24 切换的新号；账号地址不入证据）。
- 5h limit：100% left（resets 09:10 本地时间）
- Weekly limit：100% left（resets 04:10 on 31 Oct）
- Monthly credit limit：100% left，1 of 1,250 credits used（resets 20:00 on 31 Oct）
- 停止线：任一窗口已用 ≥ 90% 即停（任务卡 card-2.md）。
- 已知风险：外层测试员由 `scripts/launch-worker` 启动，启动参数没有 T-167 的 `notice.hide_rate_limit_model_nudge=true`（那是工作台受管会话的参数）；执行主控派发时注意其状态栏模型是否保持 GPT-6.1-Sol high。
