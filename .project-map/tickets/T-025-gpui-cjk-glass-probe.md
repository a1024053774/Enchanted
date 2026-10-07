---
id: T-025
title: 本机 GPUI 的中文输入、复制与玻璃质感
type: research
status: open
blocked_by: [T-026]
claimed_by: Codex worker wF:pR
supersedes:
---

## Question

在本机（macOS 27.0、Rust 1.96.1、只有 Command Line Tools）上，用锁定的 gpui-kit 0.7.1 做一个最小应用，检查以下三项：

- 系统拼音输入"会话复盘：证据引用"，覆盖连续组词、取消候选、删除、撤销、切换输入框；
- 跨中文、代码、emoji 选中后粘贴到"文本编辑"，与预先写好的期望文本比对；
- 窗口背景设为 Blurred，检查整窗与仅侧栏半透明的观感，透明度可调。

丢字、候选窗错位、选区乱序都算失败。保存屏幕录制、操作步骤，以及期望与实际文本。构建按 T-026 放在外置盘。

## Resolution

**INCOMPLETE（2026-10-06）**。自动探针已交付，真人手测尚未进行，保持 `status: open`。

- 独立包位于 [`probes/t025-gpui/`](../../probes/t025-gpui/)，锁定 gpui-kit 0.7.1 / gpui-pre 0.3.8，提交 Cargo.lock；构建均经 `MUSTER_BUILD_SLOT=worker-t025 ./scripts/build`。
- 已自动核实：真实窗口版本编译成功，两个原生窗口模式分别出现并经 screencapture 截图；GPUI 无头检查通过真实 Render 操作模式、不透明度、多行换行和焦点隔离。空视图合同红态与忽略整窗切换的坏实现均被拒绝，恢复正确源码后的最终检查通过。
- 已记录：首轮依赖编译 403.37 秒（最后因接线错误失败），窗口版本构建 243.13 秒，最终 target 1,897,528 KiB，二进制 28,941,552 字节；Rust 编译修错 3 轮。完整失败、原始输出、精确命令与适用边界见 [RESULTS.md](../../evidence/2026-10-06-m1-batch2/T-025/RESULTS.md)。完整代码版本以包含本 Resolution 的本地提交及终端交接 SHA 为准。
- 待真人核实：系统拼音组词、候选窗位置、取消/删除/撤销与输入框切换；跨中文、代码和 emoji 的选区及文本编辑粘贴结果；受控背景下的玻璃质感和不同不透明度观感。预写期望与实际结果位置在 [MANUAL-CHECK.md](../../probes/t025-gpui/MANUAL-CHECK.md)。本 worker 不宣称 IME、跨应用复制或观感通过。
- 本版本多行组件为 Textarea / TextareaState，单行框为 Input / InputState；Root 默认背景必须清除，才能让 Blurred 窗口透过面板显示。依赖来源与类型核对在证据目录的 API-NOTES.md。
- [独立只读审查](../../evidence/2026-10-06-m1-batch2/T-025/acceptance-review.md) 认可本次自动证据及 INCOMPLETE 交付；审查 PASS 不等于本 ticket 通过，真人边界仍未知。

后续由主控协调用户手测并据实际文本、录屏和观感结论决定是否关闭；旧自动通过不能代替真人验收。
