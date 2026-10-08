# T-037 主控决定 01：共用文件归属（2026-10-07，Claude Code）

批准 T-037 的建议。本轮（T-037、T-038 并行期间）：

1. `packages/contracts/src/a2aGates.ts` 与 `apps/server/src/a2a/service.ts` 的写入者为 T-037（s2-t037，`~/Documents/Code/synara` 分支 `a2a`）。T-038 不改这两个文件。
2. T-037 对这两个文件只做接入所需的最小改动：run request/result 类型；runtime blocked 与 turn 身份回读；基于可信 dispatchOrigin 的人工介入订阅。主体逻辑放新增的编排文件，状态变更仍只在门禁核心。不删除、不改名 T-036 已有的导出与字段（T-038 正按其读取 status/events）。
3. 人工介入事件的形状（字段名、事件类型）定下后，写进 T-037 证据目录的一个短说明，并告诉主控；主控转给 T-038。
4. T-038 若需要在这两个文件中增加类型或接口：不自己改，停下告诉主控；由主控决定是交给 T-037 代加，还是 T-038 放到它自己的新文件里。T-038 的归属（membership）类型放在它新建的文件中。
5. 其他尚未列出的共用接入文件，仍按任务书规则先问主控。

补充（同日）：T-038 本轮负责 `packages/a2a-gates/package.json`（membership 子路径导出）、contracts 导出入口（新增一行）、`apps/server/src/a2a/httpRoute.ts`（新增 membership 路由）和 web 路由入口，见 `../T-038/controller-decision-01.md`。T-037 不改这些文件；需要时先问主控。
