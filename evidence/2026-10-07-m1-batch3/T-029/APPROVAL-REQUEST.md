# T-029 目录信任请求（2026-10-07）

状态：BLOCKED。主控为 Claude Code（Herdr pane `wF:pM`）。

真实 `run` 在目录信任对话前暂停，未投递任务，未 submit、verify、integrate 或回收。没有自动回答任何选项，正常 `~/.codex` 的 config、hooks 和 Herdr hook 原始字节未变。

- 冻结候选：`0bea0e6728548fd894addbcb54ccccbfff6ff2a2`。
- Muster 二进制：`/Volumes/WD-Elements/dev-cache/a2a/target/worker-t029/debug/muster`。
- 隔离原生引擎会话：`a2a-t029-2uoclfw5`，server PID `54150`。
- 主调用 pane：`w1:p1`；Codex worker pane：`w1:p2`，terminal `term_65d38969efec12`。
- task：`automatic-pagination`；attempt：`593b440eec864a42b853a0898c122679`；session_id：`1729eadd3c2c4b0782fac2c37e7bf4f3`；fence：`1`；spec_rev：`1`。
- 权限请求的仓库根目录：`/private/tmp/t029-2uoclfw5/fixture`。原始 UI（暂停时，非当前 live）见 `final-runtime-01/w1-p2.txt`。
- 夹具只跟踪 `pager.py`、`CONTRACT.md`，与 supplied fixture 原始字节一致，工作区干净，无项目 `.codex`。检查见 `approval-fixture-inspection.json`。

请主控核对并明确批准或拒绝这一个夹具根目录的目录信任；此请求不包含 hook trust、sandbox/权限改变或其他目录的信任。如果批准，由主控处理这次 trust UI（或明确交给 worker）；不以任何旧许可代替。

暂停的原 `run` 已返回 paused，不能把解开 trust 后的 idle 当作任务已投递。批准后先核对 server 退出原因与持久会话。未核对之前不要重启、重派或清理。只有重建/恢复隔离引擎并获得权威 pane 清单、核对身份后，才能经 `coop.py reclaim --attempt 593b440eec864a42b853a0898c122679` 核对并撤销、回收原 pane；保留旧 attempt、状态、worktree 与证据。下一次真实 `run` 使用已核对的同一 fixture repo、新输出目录与新 attempt，显式设置 submit 等待期限。不要重新对原 attempt 投递，也不要把新 attempt 的验收/清理交给旧 run。

控制命令必须使用 context.json 中的隔离 XDG 目录和 `--session a2a-t029-2uoclfw5`，不能操作默认 Muster 或用户 Herdr server。暂停时未发送 stop，原 server/pane 曾保留。但交接前只读复核返回 server_not_running，server PID 已不存在；当前只能保留运行记录、会话目录与归档，不能把原 pane 当作 live handle。见 handoff-live-scene.json、handoff-server-exit.json。
