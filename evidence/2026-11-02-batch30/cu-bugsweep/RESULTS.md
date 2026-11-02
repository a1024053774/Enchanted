# Computer Use 实测排查结果（2026-11-02）

结论：**INCOMPLETE**。用户原话：“让 codex 用 6.1 terra的 computer use 再测试软件找找 bug. 对我我所设想的那些功能. 他要是让授权,你帮我点同意就行.”

- 测试员：侧边终端里的 Codex `gpt-6.1-terra` high，Full Access，用 Computer Use 操作隔离的 Enchanted（HEAD `2b3b12dac` 打包，`/private/tmp/a2a-build-cu-test-20261102/Enchanted.app`，数据目录 `/private/tmp/a2a-cu/`）。任务书 `BRIEF.md`，报告 `BUGS.md`（第一轮）、`BUGS-r2.md`（第二轮）。
- 第一轮按任务书在 Codex 钩子信任框处停下；第二轮按用户授权选了同意（目录信任 3 次、Codex 钩子信任 1 次，均限 `/private/tmp/a2a-cu/project`）。

## 登记的 ticket

- T-236（缺陷，主控已复现根因方向）：项目终端里 Claude Code 首次启动没有任何输出（3 次）。主控在普通终端用同一插件启动时，Claude 提示上次 fullscreen renderer 没能启动完成、改用 classic renderer，说明全屏渲染器在 Enchanted 终端里卡住。
- T-237（缺陷）：复盘 CLI 退出、后台重启后，复盘列表仍显示“进行中”。
- T-238（疑问）：项目终端里 Codex 第一句话一直排队、agy 一直运行不回复；后台没收到这些终端的任何钩子或申请。它挡住了取得主控身份，所以任务卡到集成的闭环、问题面板、人工介入记录都没测到。

## 测试事故

第一轮测试员在关掉隔离窗口后，用不带参数的 `open` 误打开了用户真实数据目录 `~/Library/Application Support/a2a-orchestrator`，约 10 秒后停掉。主控只读核对用户的 `state.sqlite3`：新增 1 条 `daemon_started`、3 条 `pane_gone_confirmed`（a2a-lcu-demo T-1、T-2，a1024053774.github.io T-1，这三个窗格的进程早已不在）和几条只读请求；留下过期的 `daemon.pid`、`control.sock`。用户的 Herdr server 与 core（2846、76491、87407）都在。第二轮任务书加了“每次启动后核对后台 state 路径”的要求，第二轮两次启动都核对过。

## 没测到的

功能 1、3～6、8、10 未测或未测完整；见 `BUGS-r2.md` 最后一节。截图在本目录 `shots/`，按只存状态的规定不进版本控制。
