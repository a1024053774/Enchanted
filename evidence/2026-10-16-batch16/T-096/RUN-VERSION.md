# T-096：version-b-01 收尾与 version-b-02

状态 **INCOMPLETE**。先完成固定夹具收尾；确认摘要 PASS／cleanup true 后，再启动 version-b-02。两个命令均由执行主控在沙箱外运行，本 worker 不申请升级。

version-b-01 的八项业务检查全部 PASS，包括 `restore_version_mismatch`、真实 Electron 中只读“未恢复”、没有 `pane_restored`、fake POST 0。第二个窗口 79678 在 12:06:59 UTC 完成 ready／读回，12:07:01.860 UTC 记录 will_quit／quit，exit_code 0；无 fatal 或崩溃退出。journal 中的启动时间和最后两次已保存 ps 一致。现有证据支持正常退出阶段的身份核对竞态，没有证据表明版本反例触发提前退出或 PID 被复用。旧 helper 没保存触发拒绝那次 ps，也没把正常退出回执传到最终摘要，不能把推断写成已证实排除 PID 复用。

当前修复只处理已有正常退出请求已接受之后的该错误：等待并回收本 runner 的 Popen 子进程，最多 3 秒，随后独立核对 PID 不存在；不再发退出请求。请求前身份不符、请求未接受、持续存活、PID 被复用、超时或其他错误仍拒绝并交回。非零退出仍记诊断。`electron_quit_events` 现在在 helper 报错时也会留在摘要，供重跑判定阶段；本修复未更改 T-091 的历史脚本或产品逻辑。

固定收尾预算与操作清单在 `cleanup_version_01.py` 开头。它只接受 `/private/tmp/t078-2-t096-lqlqpvha` 的原 epoch 2、daemon 79664 和原 ownership journal；Electron 79678 及其余登记 PID 必须已退出。核对完整启动时间／command、内核 argv、原 daemon_started 事件与私有 operator-2 socket，核对无 daemon 子进程或其他夹具写入者。两次完整核对后至多发送一次 daemon_stop；任何不符都不继续，不强杀、不新建 epoch、不重试停止请求。

```sh
python3 evidence/2026-10-16-batch16/T-096/cleanup_version_01.py --label cleanup-version-b-01 --approval-ref '执行主控 T-096 #14：核对固定身份后停止 version-b-01 并归档'
```

退出后确认全部登记 PID 和端点均不存在，复制到 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/version-b-01/fixture` 并比较数量／字节／路径。全部原件保留，operator-1／2 私密文件只从副本排除。仓库产物为 `cleanup-version-b-01.run.json`、`version-b-01-cleanup-version-b-01.archive.json`；旧 version-b-01.run.json 不变。停止回执丢失时不重试，独立核对退出与归档，摘要仍记 INCOMPLETE 并保留 stop_error。

version-b-02 只换标签与路径，沿用主控逐屏批准的 6 键与一次空队列就绪放行；完整预算见 `run_restart.py` 开头。Claude 路径沿用本轮实际核对过的 2.1.302 文件，runner 仍执行版本检查。最多一个 Electron，模型预算 0。

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/version-b-02 --label version-b-02 --approval-ref '执行主控 T-096 #14：版本反例重跑' --claude /Users/luckye/.local/share/claude/versions/2.1.302 --claude-version 2.1.302 --panes 1 --expect restore --startup-wait-seconds 600 --fault version-mismatch
```

启动批准 context 为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/version-b-02/ideation.startup.json`；capture／每键审批／就绪放行仍按 [RUN-RESTART.md](RUN-RESTART.md)。重跑须同时满足原来的版本反例与只读窗格断言、0 POST 和可核对的正常收尾，不因这次八项业务检查已通过而略过。
