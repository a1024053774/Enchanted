STATUS: PASS
TARGET: frozen-candidate-01 — `/Volumes/WD-Elements/dev-cache/a2a/tmp/worker-t025/frozen-candidate-01`

EVIDENCE:
- `build-01` 退出码 0；`Cargo.toml` 与 `Cargo.lock` 锁定 gpui-kit 0.7.1、gpui-pre 0.3.8。
- 两次真实运行均发现原生窗口，窗口查询与 `screencapture` 均成功；截图显示侧栏、输入框、Markdown 中文/代码/emoji 内容。
- `src/tests.rs:6-56` 通过真实 GPUI Render 窗口验证模式、不透明度、多行输入、焦点隔离和 Markdown 区域；使用了 emoji 哨兵输入。
- `green-03` 退出码 0；`mutant-01` 与 `red-03` 均退出码 101。冻结归档与候选目录 `diff -qr` 为空，审查期间候选元数据未变化。
- `MANUAL-CHECK.md:3,45,67-80` 明确保持 IME、跨应用复制和玻璃观感为未知，结论为 INCOMPLETE。

FINDINGS:
- 无达到 P1/P2/P3 的可达违例。

COUNTEREXAMPLE:
- `mutant-01` 将整窗按钮改为保持侧栏模式；在 `src/tests.rs:26` 的状态断言处失败，已拒绝。
- `red-03` 仅渲染空视图；因缺少 `glass-status` 失败，已拒绝。

LIMITATIONS:
- 无真实系统 IME、跨应用剪贴板或外部背景下的玻璃观感证据；这些边界已明确保留为手测未知，不阻止当前 INCOMPLETE 交付。
- 无头测试验证状态标签、输入值和布局，不证明像素级透明度、系统输入法或跨应用复制行为。
