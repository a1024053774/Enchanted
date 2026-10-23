# T-152 第 2 轮：编辑前旧入口清单

状态：INCOMPLETE。主控 #6 授权依据 01 的真实失败修正局部夹具，保留共享基类及全部业务断言，改后交付 RUN-OUTSIDE-02。

失败证据：`outside-01-cudCk6ZY/SUMMARY.json` 绑定 `c4197a89b`；T-141 reviewer 契约 PASS，另 10 项 INCOMPLETE、零业务断言。绿态现场 `/private/tmp/t152-m9rps0h_/run/tracer_review_copy/command-0011.stderr.bin` 是 pane_release 的 CLI usage error。该失败不是业务红态。

逐层核对 T-082/T-090 实际调用链（不是扫描所有继承类的未调用案例）：

| 入口 | 命令 | 现行处理 |
| --- | --- | --- |
| 本地 start_host / close_fixture | daemon_status、daemon_stop | 仍登记，保留 PID 与进程组核对。 |
| inherited registered / save_card | card_save、create | 仍登记，完整任务身份已迁移，保留。 |
| inherited start_worker → release_worker | dispatch、pane_status、**pane_release** | 仅 pane_release 已删除；本地覆盖 release_worker，绑定 launch/native 后等待自动 busy/turn 与 codex_startup_ready 事件。 |
| 本地 start_review | verify、pane_status、**pane_release** | 同上，删除显式放行调用，等待自动 busy/turn 与本次 launch 的 ready 事件。 |
| inherited worker_submit / stop_turn / relay_result | submit、signal、pane_status；SQLite 只读 | 均仍有效，保留 Stop、唯一 ACK 结束事件及 durable relay 回执检查。 |
| inherited send_review / wait_review_reclaimed / events / orchestration | signal、status、events、orchestration_events | 仍登记，保留。 |
| 本地集成窗口 | integrate、status | 仍登记，保留 held socket 与结束前拒收断言。 |

现行放行依据：T-127 移除 pane_release（`282906b9e`）；T-141 与 `test_t141_startup_signal.mjs` 区分 Open restricted 屏幕选择和 native ready。当前 `panes.ts:929–942` 在收到 OSC ready 且前台身份成立后自行 drain；`createReview:648–661` 创建并排队审查提示。本测试只等待对应 launch 的事实，不直接调用 drain、不造事件。

另有已发生的证据采集错误：01 绿态 `cleanup_failures[0]` 为 Unexpected non-regular request evidence。只读 launch 记录显示 worker TMPDIR 为 `/private/tmp/a2a-requests-z7svLA/.a2a-tmp/`，其中 `.a2a-tmp` 是普通目录。当前 `panes.ts:755–759` 创建该独立临时目录；旧 close_fixture 将所有目录均当异常。局部覆盖 close_fixture 的证据采集，递归保留请求文件和目录（含空目录），继续拒绝符号链接、特殊文件、错误根路径，并保留原来的数据库/Git 快照、PID 核对、stop、失败记录及凭据清理。共享文件不改，01 不覆盖。
