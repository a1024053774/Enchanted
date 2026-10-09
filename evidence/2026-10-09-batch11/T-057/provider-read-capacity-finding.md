# 范围外：上游 provider 查询反复触发昂贵读取容量拒绝

非阻塞上报，T-057 的其他验证继续。当前隔离服务 `/health` 为 startupReady=true、projection healthy；在真实 dev UI 的新浏览器上下文中，面板已显示，但 WebSocket 多次返回 `RPC_EXPENSIVE_READ_CAPACITY_EXCEEDED`，主要涉及 `provider.listPlugins`，还有 provider models/usage 查询。`ui-probe-fresh-01.json` 保留请求/退出标签、错误代码与截图，不保存 token。

位置：Synara `apps/server/src/wsRequestAdmission.ts:127`，证据在 `evidence/2026-10-09-batch11/T-057/ui-probe-fresh-01.json`。T-057 的问题读取走 HTTP，不占这个 WebSocket 昂贵读取入口。尚未比较父修订，不能宣称是上游既有缺陷，也不能认定它是持久 profile 启动停滞的原因；持久 profile 的独立探针仅见 Vite WebSocket，尚未建立应用 WebSocket。

建议执行主控另分配范围内缺陷 ticket，核对冷启动的 provider 查询与读取预算，不由本 worker 扩大接入范围或加 retry/fallback。本票保留失败与 profile 现场，用新隔离 profile 验证自身的功能；若仍无法完成实际刷新/重启，会按 INCOMPLETE 报告，不以模拟 storageState 替代重启。
