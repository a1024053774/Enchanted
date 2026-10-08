# T-037 主控决定 03：observer 失败修复与 httpRoute.ts 分段归属（2026-10-08，Claude Code）

同意判定为本 ticket 缺陷及修复方向（核心持有可查询的 observer 失败状态，不加重试，修存储后重启回放）。

1. `apps/server/src/a2a/httpRoute.ts` 按段分写：T-037 只改既有门禁 GET 处理（`/api/a2a?thread=...` 的返回）那几行；T-038 只新增 membership 路由与 OPTIONS 预检。双方都不改对方的段，不重排文件。两个分支的合并冲突由主控处理。
2. 失败后的拒绝范围：只读请求（status、events 及 GET 查询）必须继续可用并显示 `human_input_observer=failed`、源事件与原因，否则失败不可见；改变状态的请求明确拒绝并给出专用错误码。在 RESULTS 中列出每个命令属于哪一类及理由；回收（reclaim）是否放行要单独说明。
3. 先取真实 engine + 隔离 SQLite 写锁的红态，再实现、转绿、重新冻结。a493421 上已开始的全仓测试结果照常保留，标明被新候选取代，不替新候选背书。
