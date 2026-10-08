# T-038 主控决定 04：界面验证改用 Playwright（2026-10-08，Claude Code）

用户于 2026-10-08 在对话中明确批准（原话："可以"，答复主控关于 T-038 改用 Playwright 的提问）。范围与条件：

1. 只用 fork 现有的 Playwright 依赖（`apps/web` 的 playwright 与 Electron e2e 配置），不新增依赖。
2. 只操作本 ticket 启动的隔离 dev 或 Electron 实例；不用用户浏览器 profile，不读写用户的 Synara 数据、浏览器数据或 Herdr。
3. 需要下载浏览器二进制（`playwright install` 等）时先停下问主控；获准后下载到外置盘（例如设置 PLAYWRIGHT_BROWSERS_PATH 到 /Volumes/WD-Elements 下），未挂载即报错，不回退。
4. 操作脚本、确切命令、截图或录屏都存入 T-038 证据目录，可复现；外观仍由用户判断。
5. 只用于本 ticket 的界面验证，不扩大到其他 ticket。
