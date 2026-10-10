# T-074 执行主控决定 01：Codex 探针继续（2026-10-10）

回应 `needs-decision-01.md` 与收件箱 `20261010T195439Z-worker:s12-t074-issue-001`。R6、R7 按 spec 第 13 节由执行主控负责，实验协议由我定。

## 1. R7 发送协议：三种方法分开登记
你停下是对的。1 次未送达是一个事实，不是结论：任务卡要的是“原始次数和失败的样子”，门槛由构思主控和用户定。改用别的写法是新实验，不算重投；每种方法单独计数，本轮那 1 次计入方法 M1。
- **M1**：文字加 `\r`，一次 `pty.write`（已有 1 次）。
- **M2**：先写文字，间隔 300 ms 后单独写 `\r`。
- **M3**：用 bracketed paste 包裹文字（`ESC[200~ … ESC[201~`），间隔 300 ms 后单独写 `\r`。
参考事实：本项目日常用 `herdr agent prompt` 往 Codex pane 派发文字，一直能送达（见各批 `dispatch.jsonl` 和 worker 的回复）。可以读 herdr 的文档或 `--help` 了解它的写法，作为 inferred 记下，不读 herdr 源码以外的用户数据。
- 先在 idle 状态对 M1、M2、M3 各做 2 次。之后选送达的方法（可多于一种），在 idle、running、awaiting_approval 三种状态下合计至少 10 次。没送达的方法只报 pilot 的次数。
- 送达的观察窗口：60 秒，以原生 rollout 里出现对应的 `user.text` 为准。
- `r7-injections.jsonl` 增加 `method` 字段；旧那一行补 `method: M1`。完成条件 1 的统计按 (cli, method, state, outcome) 报。

## 2. R6：在夹具里真实触发一次批准请求
启动参数用需要批准的模式（例如 `-a on-request`），让模型在夹具里做一件 allow 规则之外、只影响夹具的事（例如写一个文件），触发命令或补丁批准。记录 notify、OSC 9、rollout、终端控制序列各自收到了什么、什么时刻收到。在等批准的状态下注入一条文字，单独记下它是否被当成了批准的回答。副作用只限夹具；不要用 Enter 去默认批准。

## 3. 额度
本卡 Codex 主 turn 上限 **30 个**（含已用的）。超出就停下报告，不自动增加。

## 4. findings 索引
允许你在 `findings/README.md` 加一行，指向新报告，让 `project_map.py status` 回到 0 stale。

## 5. Claude
Claude 的认证仍等用户决定，构思主控在问。Claude 部分继续保持不启动。Codex 部分做完后交付：Claude 还缺就交 BLOCKED，写明只差 Claude。
