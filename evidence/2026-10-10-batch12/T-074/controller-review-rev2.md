# T-074 rev 2 交付：执行主控核对（2026-10-11）

worker 交付：`T-074 DONE BLOCKED 2fcd1d0`。我的结论：**BLOCKED 成立**，不关闭 ticket；阻断点属于设计层，交构思主控。

## 我复跑的
- `python3 -B evidence/2026-10-10-batch12/T-074/analyze-rev2.py`：退出 0。
- 注入统计（RESULTS 中的命令）：Codex never M3 idle ok 3、never_after_denial ok 3、on-request idle ok 1；Claude dontAsk M3 idle ok 3、never_after_denial ok 3、manual idle ok 1。旧轮次的行原样保留，其中包括 `codex rev1 M3 awaiting_approval taken_as_approval 1`。
- Codex hook 原始 stdin（`rev2-codex-hook/hook-lifecycle.jsonl`）：只有 PermissionRequest 开始事件，字段为 session_id 和 turn_id，没有请求标识；model 为 gpt-6.1-sol。
- `project_map.py status`：0 stale。
- 探针源码里涉及 `~/.claude` 的只有一处：读取本次会话的 transcript 路径（`probe-rev2.py:56`）。没有发现写设置或读凭据的代码。

## 我补记、报告里漏掉的一项
worker 窗格 wF:p22 的现场（`herdr pane read`）显示以下经过：
1. 跑 analyze-rev2 首次断言失败后，会话被中断，界面显示 "Conversation interrupted"。
2. 随后界面显示 "Model changed to gpt-6-astra xhigh"。
3. 之后有人输入了一条没有 ⟦主控⟧ 标记的“继续”。

按共同规则，这条“继续”算用户的人工介入。worker 的收尾（修正分析脚本、写 RESULTS、提交）是在 gpt-6-astra 下完成的。按 RESULTS 的记载，所有模型探针在 01:03:19Z 之前已停止，是在 gpt-6.1-sol 下测的；所以换模型只影响收尾和整理证据，不影响测出来的终端事实。RESULTS 没有记下这次中断、换模型和人工介入，这里补记。

## 交构思主控决定
见 `needs-decision-03.md` 和 blocking issue `20261011T011326Z-worker:s12-t074-issue-001`：
- worker 不问模式：已有两家各 3 次的样本证据，可以按 spec 第 6 节用。
- 主控“等批准时暂停”：PermissionRequest hook 只有开始事件，没有结束事件，也没有请求标识。需要在两条路里选一条：
  - 暂缓主控窗格的自动注入；
  - 授权核实另一条结构化接口，例如 Codex 内部日志里带 request_id 的 serverRequest/resolved。这超出了 rev 2 已授权的 hook 范围。
- 还没测：分段注入的竞态；Claude R7 只有 7 次，不到 10 次，且没有 running 状态。
- 已用额度：Codex 23/30，Claude 11/15。
