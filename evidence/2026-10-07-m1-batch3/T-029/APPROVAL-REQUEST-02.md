# T-029 Git 暂存权限请求（2026-10-07）

状态：BLOCKED。目录信任已经按主控许可解决，当前是另一项权限对话，不在现有许可内。

原始 UI：`final-runtime-02/w1-p2.txt`；最新 live 核对：`final-runtime-02/handoff-live-scene.json`。请求命令为 `git add -- pager.py`，工作目录为 `/Users/luckye/Documents/Code/a2a/.runtime/final-runtime-01-live_run/state/worktrees/b102c2a0ec3b447f8a022c1c042d2b13`。CLI 理由为：“沙箱禁止写入 Git 的 index.lock。是否允许暂存本任务的 pager.py，以创建你要求的 commit？”当前 UI 提供仅这一次的 Yes、记住该命令前缀、No；worker 没有选择任何选项或发送 Enter。

- 冻结候选：`328922f94cb24ed05a4cb5d448427d87be3fb445`，构建、8/9/18 与 fence 反事实通过。
- 引擎会话：`a2a-t029-ca87eg62`，server PID `62028`，`start_new_session=True`，交接复核仍 running。
- 当前 pane：`w1:p2`，terminal `term_65d38cf3c599c2`。
- task：`automatic-pagination`；attempt：`b102c2a0ec3b447f8a022c1c042d2b13`；session_id：`8eca1e6c59f94b44aca000e5360c5bdd`；fence：`2`；spec_rev：`1`。
- 原 attempt `593b440eec864a42b853a0898c122679` 已通过原 attempt CLI reclaim，旧 worktree、布局和历史保留。
- 当前 task=`claimed`、run outcome=paused；未 commit、submit、verify、integrate 或 reclaim 当前 attempt。worker 的 pager.py 修改保留，git 状态及完整文件在 final-runtime-02 下；模型自测不能替代独立 oracle。
- 此次隔离 CODEX_HOME `/tmp/t029-codex-s21w85ap` 已全部删除，auth 副本未入 evidence/Git，config/hooks/Herdr hook 用户原始字节未变。删除记录为 `isolated-home-cleanup.json`。

请主控明确裁定这个 Git 暂存权限请求。若要在下一次真实 run 中完成整个闭环，还须明确允许的隔离 home Git 写入策略（仅当前已核对夹具的暂存与本地提交）；现有许可只有 auth 副本与项目信任，worker 不自行增加规则、改变沙箱、复制用户 config/rules 或自动批准后续 commit 请求。

原 run 已退出 paused，不能把解除权限对话后的提交算作它自动恢复。恢复步骤需由主控确定；新 run 的验收/集成/清理仍绑定自己的新 attempt，不接管本次 attempt。当前 server 和 blocked pane 均保留，不关用户 Herdr。
