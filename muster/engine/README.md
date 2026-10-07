# Muster 引擎

这是 Muster 工作台的终端引擎，代码来源、固定提交和许可见 [NOTICE](NOTICE) 与 [LICENSE](LICENSE)。

从 a2a 根目录执行 `MUSTER_BUILD_SLOT=worker-t027 ./scripts/build build --locked --manifest-path muster/Cargo.toml`。构建入口要求外置盘；不直接调用 Cargo 或 Zig。

可执行文件为 `muster`，配置目录为 `~/.config/muster`；环境变量以 `MUSTER_` 开头。用 `muster --session NAME server` 启动独立后台会话，控制命令见 `muster --help`。本切片保留 CLI 的 workspace/tab 字段，分别对应项目/任务。

在线自更新、预览通道、公告和检测清单下载已禁用；检测清单来自本地源码。集成安装会写目标 agent 配置；本地验收通过独立 `CODEX_HOME` 安装，不修改用户已有 hook。
