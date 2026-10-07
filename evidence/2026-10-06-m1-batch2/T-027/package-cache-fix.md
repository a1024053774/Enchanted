# Zig 0.16 包目录：真实构建补核

**首个源码提交 1a64cdb 为拒绝候选。** 它错误包含构建期间生成的 `vendor/libghostty-vt/zig-pkg`，共 31 MiB。这也反证了仅检查 Cargo/Zig cache 环境变量不足以证明所有缓存都在外置盘。

Zig 0.16 在项目旁提取包目录，区别于受 `ZIG_GLOBAL_CACHE_DIR` 控制的全局缓存。核对来源为已安装的 compiler/build_runner.zig、运行时生成的目录和 [Zig 官方 2026 devlog](https://ziglang.org/devlog/2026/)。`--system` 会关闭 package fetching 并改变 system-package mode，不把它用作本任务的缓存重定位接口。

修正位于 `muster/engine/crates/ghostty-vt/build.rs`：从已有受管 `ZIG_GLOBAL_CACHE_DIR` 派生包目录，创建源码中的 ignored symlink 后执行正常 Zig build。已有实际目录、不匹配的 symlink 或包目录逃出受管缓存都会报错；没有内置盘 fallback，没有自动吞掉异常或搬迁未知内容。

只把本 worker 生成的目录移到外置盘；没有删除原数据。移除的是 Git index 中错误添加的缓存，原始错误提交和完整缓存仍保留。命令、文件数及物理位置见 `cache-contamination.json`、`package-cache-layout.json`。后续 `git add` 尊重原有 ignore，不再 force-add 生成目录。
