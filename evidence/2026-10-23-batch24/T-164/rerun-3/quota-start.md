# T-164-3 开跑前用量读数

- 读取时间：2026-10-24 约 10:10 UTC，外层测试员 b24-t164c（Herdr wG:p2B，launch-bb855e58621245358a3db23a073ac3ef，`zcode/GLM-5.3-Flash` max）派任务前，执行主控在其窗格输入 `/status`（本地命令）。
- `/status` 显示：Model GLM-5.3-Flash · ZCode（reasoning max），Model provider openai；账号 Business；5h limit 3% left（resets 09:11 本地时间）；Weekly limit 85% left（resets 04:11 on 31 Oct）；Monthly credit 100% left，1 of 1,250 credits used。
- 这些窗口是 ChatGPT 账号的额度。执行主控随后用隔离 CODEX_HOME（只复制 auth.json 与用户配置里的 `openai_base_url` 一行，用后整个删除）发一次最小的 GLM 请求：会话记录里模型为 `zcode/GLM-5.3-Flash`，`rate_limits` 的 primary/secondary 均为空。即 GLM 请求不回报 ChatGPT 账号额度，`/status` 读不到 GLM 自己的用量。
- 停止线：GLM 路线出现额度用尽、限流或鉴权报错即停；ChatGPT 账号窗口只在有请求实际回报 rate_limits 时才作数（本轮应用内与外层都只用 GLM，不用 gpt-6.1-sol）。
