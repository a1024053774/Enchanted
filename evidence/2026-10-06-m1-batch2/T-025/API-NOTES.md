# 锁定版本与 API 核对（2026-10-06）

依据公开版本源码和类型定义编写，不把最新分支当作锁定版本。下载源码仅作参考，放在外置盘 `tmp/worker-t025/source-reference/`；构建的 Cargo registry 同样位于外置盘。

| 事项 | 核对结果 | 来源 |
| --- | --- | --- |
| 外层依赖 | gpui-kit **=0.7.1** | [crates.io](https://crates.io/crates/gpui-kit/0.7.1)、[发布 Cargo.toml](https://docs.rs/crate/gpui-kit/0.7.1/source/Cargo.toml) |
| GPUI 家族 | gpui-pre / gpui-pre-platform **=0.3.8**；组件和 base 解出 0.7.1，完整传递版本在 Cargo.lock | [该版本 Cargo.toml](https://github.com/longbridge/gpui-kit/blob/v0.7.1/Cargo.toml) |
| 初始化与窗口 | application → init → open_window；open_window 自动包一层 Base Root，调用者返回内容即可 | [0.7.1 文档](https://docs.rs/gpui-kit/0.7.1/gpui_kit/)、发布源码 `src/lib.rs` |
| 窗口模糊 | WindowOptions.window_background = WindowBackgroundAppearance::Blurred | gpui-pre 0.3.8 发布源码 `src/platform.rs` |
| 多行输入 | 0.7.1 的公开组件为 Textarea / TextareaState，Input / InputState 用于单行；使用前者承接任务书“多行 Input”的测试意图，不添加旧 API 兼容层 | gpui-component 0.7.1 `src/input/mod.rs`、`src/input/textarea.rs`；gpui-base 0.7.1 `src/input/base/state.rs` |
| 正文 | TextView::markdown，selectable(true)，selection_format(Plain) | gpui-component 0.7.1 `src/text/compat.rs` |
| 无头检查 | test-support 提供真实视图快照、click/input/press；测试通过生产窗口入口 | gpui-kit 0.7.1 `tests/ui.rs`、`tests/input/textarea.rs`、[测试指南](https://docs.rs/crate/gpui-kit/0.7.1/source/TESTING.md) |

编译修错轮数与具体问题在 RESULTS.md 中按实际运行填写。源码抽取辅助脚本的 Python 版本问题单独记在 setup-anomalies.txt，不混计为 Rust API 编译问题。
