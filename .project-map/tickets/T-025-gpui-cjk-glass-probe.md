---
id: T-025
title: 本机 GPUI 的中文输入、复制与玻璃质感
type: research
status: open
blocked_by: [T-026]
claimed_by:
supersedes:
---

## Question

在本机（macOS 27.0、Rust 1.96.1、只有 Command Line Tools）上，用锁定的 gpui-kit 0.7.1 做一个最小应用，检查以下三项：

- 系统拼音输入"会话复盘：证据引用"，覆盖连续组词、取消候选、删除、撤销、切换输入框；
- 跨中文、代码、emoji 选中后粘贴到"文本编辑"，与预先写好的期望文本比对；
- 窗口背景设为 Blurred，检查整窗与仅侧栏半透明的观感，透明度可调。

丢字、候选窗错位、选区乱序都算失败。保存屏幕录制、操作步骤，以及期望与实际文本。构建按 T-026 放在外置盘。

## Resolution

未执行。
