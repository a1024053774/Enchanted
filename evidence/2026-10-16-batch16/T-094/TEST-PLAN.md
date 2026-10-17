# T-094-1 验证边界（2026-10-17）

状态：INCOMPLETE。主控 #63 已否决写 shell 回执，裁定使用 1500 毫秒稳定窗口、100 毫秒目标采样间隔和 30 秒总期限；子进程出现就重计窗口。两个受控场景已在同一修正夹具上取得旧红新绿，新候选 9 项边界测试通过；真实 busy-02 和独立审查待主控进行，两个受保护旧验收断言冲突另见 RESULTS.md。稳定窗口可能在初始化空闲超过窗口时误判，此局限已写入 README。

主控 #60 的新增合同：收到 busy 后第一次 process-info 的前台进程组与 argv 直接出现在错误身份及报错摘要，不新增等待或重试。先在旧候选上取得合同红态，再验证新候选；默认 8 次真实复现由主控运行 `outside-busy.sh`，不把夹具中的 git status 当作真实根因证据。

独立预期来自任务卡与 ticket Acceptance。边界夹具不证明真实 Herdr 的时序根因，仅隔离以下可观察缺陷：

- Herdr 启动失败时，stdout、stderr、错误码丢失，只留下退出码。
- Codex 前台进程已起但未注册名称，被混记为普通失败。
- 名称已注册但被首屏审批阻断，被误报为成功或未注册。
- 失败后未记录 pane，主控无法处置；或入口擅自关闭 pane。
- 查询注册状态失败，被错误解释为名称未注册。
- 修复关闭了成功 pane，或在失败后再次调用 agent start。

夹具通过真实 `scripts/launch-worker` 命令入口调用，只替换 PATH 内显式 Herdr/Codex 边界，不启动服务、不发提示。每种场景固定一次 start；状态由夹具独立输入决定。预期的独立结果分类为 `outcome=not_started`、`started_unregistered`、`started_not_ready`。保持现有记录 phase 的拒收语义，半成功的 phase 仍为 failed，同时必须带明确 outcome；不修改范围外的记录校验器。

主控 #57 已修订处置方式：入口保留失败 pane、写清身份和结果，是否关闭由主控决定。因此保留 `acceptance/test_launcher_shell_ready_e2e.py` 的既有断言并运行原测试。此前按初始任务卡实现自动关闭的 contract-red-01/02、contract-green-01、diagnostic-red-01 保留为历史证据，不作为最终候选通过结论。最终证据使用 contract-final-*。

Tracer bullet：先通过命令入口取得诊断红态，再修启动入口的诊断与分类，最后由主控在同一稀疏 worktree 复跑。Deep modules：沿用唯一启动入口，不加重试入口或通用编排层。Ubiquitous language：沿用启动记录、pane、agent 会话与原生会话。
