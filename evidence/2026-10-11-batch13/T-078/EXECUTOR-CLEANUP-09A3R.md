# 主控执行请求：停止本轮沙箱受限的回归后台

2026-10-14，T-078 09A-3 变基后复验。状态 **INCOMPLETE：环境权限错误，清理待主控执行**。

worker 误将旧 coop 受控回归在沙箱内运行。八个测试均在 `/bin/ps` 身份核对处被沙箱拒绝，清理也在同一处失败，留下本轮隔离 fixture 的八个后台；不是产品红态，不回写失败为通过。原件见 `rebased-coop-local-09a3/`。

请先在沙箱外执行已经准备的阶段脚本 cleanup 模式：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/rebased-stage-09a3.py --mode cleanup
```

固定夹具根 `/private/tmp/s3f-92fdj4n_`。脚本逐个核对八个固定 PID、原 host ready manifest、命令行、state 路径、当前后台返回身份，再用本 fixture 的 private operator credential 调生产 daemon_stop。确认 PID、socket、pidfile 退出后记结果。只处理这些隔离后台，不发强制信号，不删除根、凭据或证据；身份未知则停止，不自动重试。

本轮未启动真实 Codex／Claude／API／模型，问题仅来自隔离 Node 测试后台。后续其余沙箱外回归会放在同一个脚本的 regression 模式，冻结候选后再交主控，不通过提问工具发出请求。
