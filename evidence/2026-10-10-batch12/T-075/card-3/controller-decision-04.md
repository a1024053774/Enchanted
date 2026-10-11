# T-075-3 执行主控决定 04：按 T-075 rev 4 执行（2026-10-11）

用户的决定已由构思主控以 revise `20261011T043706Z-ideation-revise-001` 转来，ticket T-075 也补了“修订 rev 4”一节。

## 1. 先用 1 个回合验证 A2
- 被测 Codex 用每会话启动参数打开托管网络代理（`features.network_proxy=true`），域名名单留空，并设 `network.allow_unix_sockets=[<后台 socket>]`。其余参数照旧，仍是 `-a never` 加 workspace-write。
- 同一个回合里要全部验证：
  - 后台 socket 能连上，challenge 能被回送并写入库；
  - 另一个夹具 socket 被拒；
  - 127.0.0.1 上的 TCP 被拒；
  - 任意外部域名被拒，例如 `curl https://example.com`，只发请求、不下载任何东西；
  - git 钩子在沙箱里能连上后台；
  - 整个回合没有弹出批准。
- 另外把代理进程的身份记下来（pid、argv），并说明它的生命周期。
- 真实回合累计上限仍是 10（已用 2）。

## 2. A2 只要有一项没过，直接改走 B，不再回来问
- B 的做法：worker 在自己的 worktree 里，按约定写一个交付请求文件（显式 submit，带 task、attempt、session、fence、spec_rev 和完整提交号）。回合结束的 Stop hook 不受沙箱限制，由它读取这个文件，经后台 CLI 转交。查状态和上报问题也走同一条路。
- 转交的结果要用 `⟦门禁 #序号⟧` 的格式写回 worker 窗格，写之前先登记，并且只在窗格空闲时写。
- 交付必须由 worker 自己发起。“回合结束”本身不算交付；worktree 里没有请求文件，就什么都不转交。
- 请求文件不能进入候选提交：放在 git 忽略的位置，或者 worktree 之外、但沙箱可写的目录（例如本 attempt 专用的 /tmp 目录）。具体选哪种，在 RESULTS 里说明理由。
- 反例至少包括以下三项，每项都要在后台留下事件：
  - 请求文件身份不符；
  - 请求文件不完整；
  - 同一请求被重复转交，且后台不重复处理。
- 走 B 时同样只发 1 个真实回合，用来完成那一次真实交付。
- RESULTS 里写明最后走的是 A2 还是 B，以及原因。

## 3. 模型
本会话中途不换模型。T-075-4 起，新启动的 Codex 会话默认用 `gpt-6.1-sol`；遇到复杂任务改用 `gpt-6-astra`，并在任务卡里写明理由。被测 Codex 的模型以 RESULTS 里记录的实际参数为准；如果本卡还要新开被测会话，用 `gpt-6.1-sol` xhigh Fast。

## 4. 其余照旧
决定 01～03 中与本决定不冲突的条款继续有效。完成后照旧回复 `T-075 OUTSIDE-SANDBOX READY`。
