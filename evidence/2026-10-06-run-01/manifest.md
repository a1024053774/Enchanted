# T-008 受管自动运行（2026-10-06）

状态：PASS，限 T-008。完整结论、实际失败与分层证据见 [RESULTS.md](RESULTS.md)。

- 父版本 571b45a；只扩展正常编排与 expected-attempt 条件，沿用 task/attempt 和恢复门禁。
- run-check 独占验收；run-build 独占 coop.py / README；主控管理真实运行、反事实、规范与复核。
- 两 worker 请求 gpt-6.1-sol xhigh Fast，启动与实际 UI 记录在 commands.jsonl；不证明供应商实际 tier。
- 父版新 run/guard 不存在，是 expected-red 新契约缺失，未冒充旧缺陷。
- 隔离矩阵使用显式 Herdr/Codex 替身与真实 Git/SQLite；它不能证明实际 Herdr/模型可用。
- 最终隔离矩阵18/18，原门禁8/8与恢复9/9通过；真实自动run及独立审查通过。
- 一次夹具错误为 post-prompt 观察屏障错误地同时阻塞 controller reclaim；改为一次性屏障后，
  替换竞态仍在：旧观察悬挂直到新 attempt 已提交，断言没有放宽。原错误保存在 build/check 文件。
- 真实夹具 .runtime/run-live-fixture 是本轮创建的独立 Git repo（仅 starter与contract）；
  主控核对后依据本项目授权完成目录信任准备，未给准备进程模型任务，随后关闭。
- 真实验收脚本 acceptance/live_run.py 只调用一次 run 推进流程，之后只做独立状态、Git、oracle和pane读回。
