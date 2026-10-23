# 任务卡 T-155-1（像真实用户一样使用 Enchanted；Codex Computer Use 实测）

先读 `.project-map/tickets/T-155-real-user-dogfood.md`、`.project-map/inbox/20261023T190226Z-ideation-assign-001.md`、`workbench/README.md`（使用部分）、`findings/README.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-155-1 |
| 来源 | T-155 ready_rev 1（ready_by ideation；用户原话与授权见 ticket） |
| 目标 | 以不知道内部实现的用户身份，完整用一轮 Enchanted 的多 agent 流程，按 Herdr 体验对照找出不合理处，写成中文发现报告。只报告，不修。 |
| 非目标 | 改产品代码；把模型自报当验收；用用户的真实项目与数据；修发现的问题。 |
| 修改边界 | 允许：`findings/2026-10-23-real-user-dogfood.md`（新报告）、`findings/README.md`（只加一行索引）、`evidence/2026-10-23-batch24/T-155/**`（脚本、文本证据、小截图；大文件按 T-088 归档外置盘留 `*.archive.json`）。禁止：`workbench/src/**`、`workbench/app/**`、其他测试、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`。 |
| 任务类型 | 调研 |
| 复杂度 | L |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t155`，worktree `/Users/luckye/Documents/Code/a2a-wt-t155`，分支 `exec/t155` |

## 隔离（硬性）

- 被测应用是你自己启动的隔离实例：独立的 daemon state 目录、Electron user-data 目录、socket，全部放在内置盘新建的临时目录（例如 `/private/tmp/t155-dogfood-XXXX/`）。绝不连接或读写用户正在用的编排后台 `~/Library/Application Support/a2a-orchestrator`，也不碰用户的 Herdr。参考现有界面测试的 `--state`、`--user-data` 用法（`workbench/tests/electron_client.py`、`electron_driver.mjs`）。
- 被测的 Git 项目是新建的一次性小仓库（同一临时目录下），不是用户的项目。
- 启动、关闭、重开应用：写成 `START-APP.sh`、`STOP-APP.sh`（后台脱离进程组，打印 PID、state、user-data、socket 路径），交我在沙箱外运行。需要重开时停下说 `REOPEN`，我来跑。

## 怎么测

- **只用 Computer Use 操作界面**（鼠标、键盘、截图），像真实用户一样看屏幕决定下一步；不要用 CDP、DOM 注入、门禁命令行或直接读数据库来**驱动**流程。事后可以只读查看日志/数据库来解释现象，但要在报告里标明那是事后核对。
- Computer Use 只操作你自己启动的隔离 Electron 窗口。遇到系统设置、隐私授权（屏幕录制、辅助功能）、登录与密码、付款、发消息或发布内容、操作用户自己的应用或数据、删除文件——停下报我，不要自己处理。
- 场景按 ticket 第 1 条全部走到：打开项目 → 在项目终端里自己输入命令启动 CLI（主控用 `claude --model claude-haiku-5-5`）→ 申请执行主控 → 在界面批准 → 对主控说一件需要拆成 2～3 个任务的事 → 主控派出多个 worker（含并行）→ 看流程页、侧栏、终端 → 回答 worker 的上报 → 审查 → 集成 → 看记录页、Reflect、指标。再加“难”的情形：两个任务同时在跑、一个 worker 被打回、你中途在 worker 窗格里打字、切换窗格与滚动、关掉再重开应用（REOPEN）。
- 预算与并发：Codex 会话全局同时最多 3 个（含你自己）；应用里同时最多 2 个 Codex 会话，其余用 Claude Code `claude-haiku-5-5`。应用里的真实模型回合合计不超过 60 个，逐场记录。被测任务要小（几分钟能做完的改动）。

## 产出

1. `findings/2026-10-23-real-user-dogfood.md`：每条发现写现象、复现步骤、截图（路径）、为什么不合理、严重程度（阻断/严重/一般/轻微）、建议；标注类别：GPT/Claude 模型行为、分工协调、工程与证据处理、界面与交互。最后写“Herdr 对照”小结：开 agent、看到谁在干什么、切换、盯进度、回复，每一项“已达到 / 未达到 / 部分”，并写检查了什么。没有发现问题的环节也要写检查了什么，不空泛。
2. 至少挑一条发现，在全新的隔离实例上（同一 main 版本）按复现步骤再现一次，记录结果（ticket 的“红态意义”）。
3. `RESULTS.md`：版本、启动命令、每一步的截图索引、真实回合统计、代批记录引用、未完成的步骤及原因。
4. `findings/README.md` 加一行索引。

`git add --sparse` 提交，完成说 `DELIVERED <提交号>`。语义拿不准、需要用户判断的，停下报我。
