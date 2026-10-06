---
id: T-024
title: 一个引擎能否让多个窗口各看不同项目
type: research
status: open
blocked_by: []
claimed_by:
supersedes:
---

## Question

工作台要求每个项目一个窗口。Herdr 服务端在 `src/server/headless/client_views.rs` 中按客户端区分聚焦的标签页，推断多个客户端可以各自聚焦不同的 workspace，但没有核实。

最小验证：用已安装的 Herdr 0.9.3（与引擎同版本）开一个独立命名会话，例如 `herdr --session a2a-focus-probe`；连接两个客户端，各自聚焦不同的 workspace，检查焦点、尺寸和输入是否互不干扰。不得触碰用户正在使用的 server。

## Resolution

未执行。
