# T-063 重放命令

所有命令都在 a2a 仓库运行，标签必须全新；证据不会覆盖。正式工作台与正式数据目录不用参与。Bun 与 Node 始终经过 fork 的 `a2a/scripts/bun`。

```sh
python3 evidence/2026-10-09-batch11/T-063/start-isolated.py replay01
python3 evidence/2026-10-09-batch11/T-063/run-command.py replay01-ui /Users/luckye/Documents/Code/synara/a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-063/ui-probe.mjs /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-063 /Volumes/WD-Elements/dev-cache/synara/instances/t063-replay01 replay01-ui normal
python3 evidence/2026-10-09-batch11/T-063/stop-isolated.py replay01
```

先确认 8077/8078 没有被占用。`start-isolated.py` 使用新的 root、空认证目录、禁用 provider 的真实服务端及 Vite；没有模型调用。启动须检查保留的 dry-run 输出。若端口已被本次 probe01 占用，先按 `current-launch.json` 的身份记录停止本轮实例；不要停止其他实例。

验收期望由 ticket 给出：主界面出现并完成任务数据读取；横幅、logo、标题、输入区互不重叠；两种尺寸和启动后的 resize 都须观察。`ui-probe.mjs` 在 dev 页通过 CDP 禁用 HTTP 缓存，保留 profile 与产品 localStorage；加长中文文案是 DOM 布局压力输入，产品没有语言切换功能。

历史实际命令及退出码分别见 `counterfactual-red01-command.json`、`green07-resume-command.json`、`green05-command.json` 和 `delayed01-launch.json`。后两个分别包含损坏已看标记、延迟本轮服务端就绪的输入。反事实运行的旧源码与候选源码分别保存为 `baseline-ChatView.tsx`、`candidate-ChatView.tsx`；`counterfactual.py` 保存、临时换回旧源码、在 finally 恢复候选。审查者只读它，不在共享 checkout 运行源码切换。

相关浏览器测试的实际命令见 `browser-tests04-pinned-command.json`。`browser-pinned.config.mts` 沿用原仓库配置，仅选择项目固定 Playwright 对应的 Chromium Headless Shell；安装命令见 `playwright-install01-command.json`，下载路径在外置盘。

正常缓存的固定浏览器复验：见 `green11-pinned-resume-command.json`；该轮 `T063_BROWSER_BINARY` 在 UI JSON 中记录为外置盘固定 Headless Shell，`httpCacheDisabled=false`。重开保留筛选状态；通过指定的三条 seed 输入核对数据，不限制是否同时显示另两条输入。
