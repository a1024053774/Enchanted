# T-152 第 3 轮：提交后 PTY 输出

状态：INCOMPLETE；主控 #9 授权核对 02 现场后，只改专用 host 并交付 RUN-OUTSIDE-03。

02 摘要：`outside-02-JpvDMYo4/SUMMARY.json`，版本 `02fe808bdc0994d47b540ff6bcc047a3eb1a073a`；T-141 reviewer PASS，另 10 项在 release_worker 等待 fixture-turn-1 时 harness_error，零业务断言，清理失败为 0。01 的 pane_release 与请求目录采集问题已不再阻断。

真实入口失败信号：`/private/tmp/t152-zpk5zopx/run/run.json` 与 `/private/tmp/q76-yznvjz9f/c-iwwa_6nt`。control/writes.jsonl 依次记录开目录 Enter、任务 bracketed paste、任务 Enter；rollout 已有 session_meta、task_started(fixture-turn-1)、turn_context。持久事件里，19:28:26.922 读取 session_meta，19:28:27.752 记录 codex_startup_ready，19:28:28.053 记录 turn_submitted；等待失败时仍为 busy、active.nativeTurn=null、turn=null。两条 turn native_record 到 19:28:32.279 清理阶段才出现，不把清理后的数据库状态当作等待期间已扫描。

根因：共享 PTY 的 write 在第二个及后续 Enter 同步追加 rollout，但没有输出；专用 host 之前只在第一个 Enter 后发 native ready。产品 onData 会 scan（panes.ts:797–801），pane_status 不 scan（1366）；首次原生会话已经建立，因此提交后的无 native 定时分支（1249）也不触发。不是门禁业务失败。

修正：仅在 `t152_review_host.ts` 的非首个 Enter 分支，先让共享 write 追加 rollout，再异步 callback 一段普通文本。这样真实 onData 自行读取并绑定本回合，不直接调用 scan，不改状态/数据库，不生成 idle/Stop 或门禁回执。worker、ACK 和 reviewer 回合使用同一输出规则。产品与共享 PTY 不改，已有 wait_pane 条件与全部业务断言不改。

新入口：`zsh evidence/2026-10-23-batch23/T-152/RUN-OUTSIDE-03.sh`，保留相同绿态、8 个变异、T-090 和 T-141 回归，写新 `outside-03-XXXXXXXX/`。02 全部小摘要入仓库，原始现场不改。当前仅语法/差异检查，不宣称已有有效业务红绿态。
