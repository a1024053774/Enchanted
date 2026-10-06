# Monitor 任务书：M1 第一批（只读）

你是 a2a 的 monitor（Codex，high reasoning）。只读观察、记录和报警；不得 claim、submit、集成、改 ticket 或宣布成功。

先读 AGENTS.md、findings/README.md、.project-map/tickets/T-011-monitor-closure.md。
观察对象：worker `m1-t026`、`m1-t024`（用 `herdr agent get/read <name>` 读取，不要向它们发送任何输入）。
每 10 分钟左右采样一次，直到两者都在终端输出 `DONE` 行或你被回收。
记录到 evidence/2026-10-06-m1-batch1/monitor.md（追加写入）：时间、观察到的状态、异常（越界改动、触碰用户 Herdr server、
改了不该改的文件、长时间无进展、权限等待、把 idle 当完成等），以及建议。只写这个文件，不 git commit。
发现需要主控立即处理的问题时，在该文件里用 `ALERT:` 开头写一行。
