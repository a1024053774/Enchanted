# T-164-3 第二次开跑前额度读数（外层测试员换回 gpt-6.1-sol）

- 读取时间：2026-10-24 约 13:17 UTC（09:17 EDT），外层测试员 b24-t164d（Herdr wG:p2C，launch-fb4f4b23f1024bcc88a6f847a2ebd16c，gpt-6.1-sol high）派任务前，执行主控在其窗格输入 `/status`（本地命令）。
- 5h limit：100% left（resets 14:17 本地时间）；Weekly limit：85% left（resets 04:11 on 31 Oct）；Monthly credit：100% left，1 of 1,250 credits used。
- 实例：`/private/tmp/t164-dogfood-0zw8tib0`（基线 e3b14d27b），Electron PID 23877，daemon PID 23874。
- 停止线：任一窗口已用 ≥ 90%，或应用内 GLM 路线出现额度用尽、限流、鉴权报错（GLM 请求不回报 ChatGPT 额度，见 `quota-start.md`）。
