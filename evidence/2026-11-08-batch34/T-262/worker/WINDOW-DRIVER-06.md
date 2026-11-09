# T-262 真实窗口尺寸驱动修正

INCOMPLETE：已修测试启动器，待主控运行新的完整候选。已有有效父版红态和候选前 21 项通过证据保留；本轮不重跑父版或启动应用。

**Works**：`red-outside-05.json` 在排序和双区任务筛选两项业务断言失败，真实 select 的 input/change 已生效。`green-outside-02.json` 通过前 21 项业务检查，`failed=[]`，随后因页面 CDP 端点没有 `Browser.getWindowForTarget`（-32601）中断。两次清理均成功；原始摘要副本为 `controller-red-outside-05.json`、`controller-green-outside-02.json`。
**No regression**：本轮只改测试与本目录证据。`static-window-06.json` 证明原窄窗断言、其余全部业务期望和后续流程、四个变异、select/Enter 驱动与清理方法不变；自有启动器通过语法检查。未运行真实窗口或完整回归，不能据此称整轮 PASS。
**Risk / undo**：原生窗口尺寸设置尚待外部实跑。若窗口没有达到 900×700 或进程身份不符，测试报告 INCOMPLETE，不将夹具问题计作业务失败。修正前脚本保留在 `test-before-window-06.py`，用于复核本轮精确差异；旧失败证据不覆盖。

## 根因、来源与修正

先核对本机现有 Electron 43.4.1 的 `electron.d.ts`：BrowserWindow 提供 `setBounds(bounds, animate?)`、`getBounds()` 和 `getContentSize()`。同仓 `cdp_launch.cjs` 通过 CommonJS 入口设置调试端口后调用产品 `run()`；`t103_picker_driver.mjs` 和 `electron_driver.mjs` 也读取真实 BrowserWindow。产品 `main.ts:817` 的 `run()` 在加载页面后返回该窗口，最小宽度为 900。

本票测试现在在其专有临时目录生成 `t262-launch.cjs`，保留现有启动方式、独立状态库和 userData。产品 `run()` 返回后，启动器直接调用 `window.setBounds({ width: 900, height: 700 }, false)`，将 `getBounds()`、`getContentSize()`、window id 和 pid 写入本夹具的 `window-bounds.jsonl`，随后记录原生 resize 事件。窗口尺寸记录就绪并核对通过后，才开始场景操作。因此整套场景都在窄窗口运行。

原来的两条 Browser CDP 调用已删除，没有兼容回退。在原窄窗检查位置读取最近的原生尺寸记录并核对 900×700 与 Electron pid，然后执行原来的页面 clientWidth/scrollWidth 不溢出断言；没有给 DOM 宽度赋值、模拟设备宽度、修改产品返回值或碰共享启动器。尺寸记录进入 `native_window` 报告和清理前 diagnostics，删除夹具后仍可追溯。

## 本次检查与下一步

静态命令为 `python3 evidence/2026-11-08-batch34/T-262/worker/check-window-06.py`，结果已保存。该检查对照本轮修正前脚本做 AST 核对，再以 `node --check` 检查 CJS/ESM 和 Python `--help` 核对参数入口，不启动应用、后台、模型、ps 或构建。

准确外部命令在 `controller-runs-06.command`：先候选完整运行到原窄窗、异步、错误和空态检查，再跑四个既有变异。父版已取得有效红态，无须重复。每次保留摘要与 diagnostics、退出码和清理状态；候选需 PASS，变异需业务 FAIL，驱动 INCOMPLETE 不算检出。

原生 select 的键盘 Computer Use 与独立审查仍待主控完成。README 候选说明由主控同步，旧 base 的 stale 不扩大 worker 权限；本轮没有修改 README、地图、共享 `cdp_launch.cjs` 或产品文件。当前身份仍为 attempt `64d48cf7-0cfc-4078-8a13-6f0067297990` / fence 2 / spec_rev 2。未 Git 提交、未 submit，额外可写目录 []，无额外目录改动。不存在等待重启事项。

本次集中 issue 请求 `2cbf02f0-7a16-4463-bc6c-22e838151395` 返回 `queued=true, delivered=false`，仅表示已排队，受理状态尚未确认。回显见 `issue-queued-06.txt`；请求文件留在本 attempt 请求目录，不进 Git。
