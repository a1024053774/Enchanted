# A-07 I1 ideation 回合待批材料

绑定来源是 A-07 `readiness.json`、B1 P1 的真实 `input.json`/process manifest，以及 ideation API 的 `api-ready.json`。预先批准的正文见 `i1-prompt.txt`。driver 先经产品 `pane_dispatch` 登记正文，由真实返回提供 dispatch id 与全局 seq；API 请求到达后记录实际 request_id，真实 Stop hook 到达后记录实际 stop_id，再补齐 `protocol-registry.json` 登记。随后只调用一次 `pane_release`。

预期预算为 1 root / 1 Messages（ideation 上限 4 roots / 6 Messages）。协议正文、seq、attempt/session/fence、role、request_id、stop_id 或预算不符均 409，driver 停止且不重送。停止条件：一个 SSE 响应、一个 Stop/idle、无 I2 或 executor 动作。

材料为 `NO_GO`；本轮只写材料和提交脚本，不发送任何请求。
