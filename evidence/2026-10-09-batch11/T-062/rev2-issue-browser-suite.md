# T-062 相关既有浏览器套件首次完整运行出现断联

`rev2-browser-tests04.log:21` 记录：运行 `SidebarActivityBellButton.browser.tsx` 时，Vitest 的 Browser WebSocket 提前关闭；整轮退出 1，统计为 13 项通过、14 项已发现、1 个未处理错误。这不是断言已通过，原始日志与命令回执均保留。

此前三个启动失败也保留：默认 Playwright 浏览器未安装；使用已有 Chrome 时误把第二个 `--config` 传给含固定 config 的 package script；外置 `.ts` 配置被当成 CommonJS。取证配置现在为 `.mts`，合并原有 browser config，仅指定已有 Chrome 的 executablePath，未改产品、既有测试或上游配置。

断联原因尚未确认，同命令的后续完整复跑正在执行（`rev2-browser-tests05`）。建议执行主控将首次断联作为既有测试/环境异常跟踪，不用本次 UI 修复声称解决了它；本轮不修改这些测试。T-062 的真实 dev UI 四组截图已通过，继续完成本 ticket，最终报告会明确该套件实际结果。
