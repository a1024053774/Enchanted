# A-09 queued dispatch recovery

只读代码核对：`workbench/src/gates/cli.ts` 暴露 `pane_dispatch`、`pane_release`、`pane_status`、`orchestration_events`，没有 queued dispatch cancel/remove 命令；`Panes.drain` 只在 idle 时消费 queue，`release` 只处理 initial unknown 状态。当前 A-09 active 是 `null`、queue 有一条真实 dispatch，因此没有合法撤回 API。

安全恢复路径是 driver 的 `--resume-queued`：先通过只读 `pane_status` 取唯一 queued id，再通过只读 `orchestration_events` 取同 id 的真实 `dispatch_queued` 原文和 seq；核对原文等于批准提示的末尾 CR/LF 规范形式后，写 protocol registry 并调用一次 `pane_release`。它不调用 `pane_dispatch`、不伪造 id/seq/正文，也不重送。当前只生成此路径，等待主控裁定和批准，不执行。
