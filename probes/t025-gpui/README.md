# T-025 GPUI 本机探针

独立 Cargo 包，不加入 Muster workspace。锁定 gpui-kit `=0.7.1`（gpui-pre `=0.3.8`）；运行依赖与无头测试依赖均通过同一 facade，完整版本见 Cargo.lock。仅用于 T-025 研究。

从仓库根目录构建、测试、启动：

```sh
MUSTER_BUILD_SLOT=worker-t025 ./scripts/build build --locked --manifest-path probes/t025-gpui/Cargo.toml
MUSTER_BUILD_SLOT=worker-t025 ./scripts/build test --locked --manifest-path probes/t025-gpui/Cargo.toml -- --nocapture
MUSTER_BUILD_SLOT=worker-t025 ./scripts/build run --locked --manifest-path probes/t025-gpui/Cargo.toml -- --glass sidebar --opacity 0.75
```

`--glass window` 为整窗半透明，`sidebar` 为仅侧栏半透明；`--opacity` 是面板不透明度，范围 0.10～0.95，默认 0.75。左栏也可切换模式和三个不透明度档位。外置盘未挂载时入口拒绝构建，不回退。关闭最后一个探针窗口后退出探针进程。

多行输入使用此版本公开的 `Textarea`，第二个单行框使用 `Input`。Markdown `TextView` 支持拖选并以纯文本复制。WindowOptions 使用 Blurred，应用清除组件 Root 的默认不透明背景；仅侧栏模式由右侧面板以 alpha 1 绘制。

无头测试通过真实窗口与 Render 路径操作模式、不透明度、多行输入与焦点，读取组件的原生无障碍值及布局。它不证明真实系统 IME、macOS 跨应用剪贴板或玻璃视觉效果。真人操作按 [MANUAL-CHECK.md](MANUAL-CHECK.md)；手测前结果为 **INCOMPLETE**。

自动记录命令可使用以下形式，证据目录必须是新的目录：

```sh
MUSTER_BUILD_SLOT=worker-t025 python3 probes/t025-gpui/run-command.py evidence/2026-10-06-m1-batch2/T-025/<新的运行目录> ./scripts/build test --locked --manifest-path probes/t025-gpui/Cargo.toml -- --nocapture
```

runner 保存精确 argv、cwd、耗时、退出码及完整 stdout/stderr。窗口截图辅助 `observe-window.py PID` 只读取指定探针进程的屏幕窗口元数据，不操作其他窗口；随后以返回的窗口编号调用 `screencapture -x -l<编号> <新的图片路径>`。

结果、截图、编译失败与源码快照见 [T-025 证据](../../evidence/2026-10-06-m1-batch2/T-025/)。自动通过与真人待测分别记录，ticket 由主控在手测后决定是否关闭。
