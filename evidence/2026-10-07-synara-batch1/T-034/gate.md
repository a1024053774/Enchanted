REALITY GATE: PASS

目标：T-034 的本地构建、隔离运行、缺盘反例与上游合并演练。非目标：门禁移植、上游核心修改、push、全局 Node 与用户配置。

observed：外置盘是真实且不同设备的挂载点；Bun 1.4.2；全局 Node v26.5.0；fork a2a 基线 f176e8967aa5a4a7faf1dc4bd070360d5fceabec；无正在运行的 Synara。

observed：现有 Cua 身份提供独立 bundle/scheme；SYNARA_HOME 与 Electron userData 分开；源码标记允许 SYNARA_DESKTOP_SMOKE_USER_DATA；Turbo strict 会过滤未列出的缓存变量。

决定：仅新增 a2a/scripts/bun 入口；先检查挂载、设备与路径，再准备 Node、缓存或运行。TURBO_ENV_MODE=loose 传递隔离环境；保留用户 HOME。入口只删除当前隔离子进程的用户 Synara 连接配置。

探针：真实安装与 build、dev HTTP、桌面截图及打开的 profile/SQLite 路径。缺盘及普通内置目录必须在 Bun 启动前退出 2 且无写入；上游临时分支验证。失败输出追加保留，不覆盖。

Tracer bullet：入口 → 上游安装/构建 → 一次隔离界面运行，再完成上游合并演练。Deep modules：沿用上游 runner、desktop identity 和 profile 机制，专属入口只集中管理环境及挂载边界，不复制上游启动实现。Ubiquitous language：沿用 CONTEXT.md 的 worker、主控、交付与验收；Synara home 与 Electron profile 分别记录，不混称为同一数据目录。
