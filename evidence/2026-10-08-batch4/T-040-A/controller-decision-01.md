# T-040 A 主控决定 01：先定位恢复首轮 2 秒超时的边界（2026-10-08，Claude Code）

INCOMPLETE 交付与独立审查 FAIL 原样保留。主控查看 `after-recovery/process-load.txt`：失败时有一个 `next-build` 占 107% CPU（并非本 ticket 进程），另有 photolibraryd、cloudphotod 等。T-036 的 fence mutant 轮也出现过一次 busy 时限失败。合理假设是：busy 判定本身很快，但原生门禁 CLI（Python 转接 → bun → TypeScript）冷启动在负载下接近或超过 2 秒；旧 `coop.py` 冷启动只有几十毫秒。这是假设，需证据。

授权 A 部分 worker 做一轮有界定位，不改 fork、不放宽断言：
1. 对忙状态下的 verify/integrate 拒绝路径分段计时：Python 转接启动、exec 到 bun、bun 加载 TS 并解析参数、打开 state/取锁判定、输出并退出。用外部单调时钟与进程内时间戳（如可行，只用环境变量开启、不改产品行为的方式；若必须改 fork 代码才能取时间戳，先停下问主控）。
2. 两种条件各至少 20 次：系统空闲；人为施加可控 CPU 负载（例如 N 个 `yes > /dev/null` 进程，只停你启动的）。报告每段的中位数与最大值，以及超过 2 秒的次数和发生在哪一段。
3. 结论写进证据，给出最小修正选项（例如缩短 CLI 冷启动的方式及其代价），交主控决定。若数据显示是锁判定本身慢或等待了锁，那是门禁缺陷，同样报告。
