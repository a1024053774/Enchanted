---
id: T-091
title: 工作台单窗口同任务多窗格：两个主控窗格加一个 worker 窗格同屏
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

[spec](../specs/native-cli-orchestration-2026-10-10.md) 写的是"界面按项目 → 任务 → 会话展开，一个任务里有多个会话窗格"。现状（执行主控 2026-10-16 只读核对，`workbench/app/renderer.tsx:54`、`:161` 只建一个 Terminal，`workbench/app/main.ts:29` 每次只开一个 BrowserWindow）是一个窗口一个终端窗格，产品里没有同窗口多窗格。

本票做同一个 Electron 窗口里、同一任务下的多个会话窗格，至少能同时显示两个主控窗格和一个受管 worker 窗格。每个窗格独立的窗口身份、输入序号和输出流，复用现有输出与输入通路和唯一门禁，不另造业务接口；全局 IPC handler 随之调整。

## 来源与取舍

T-078 原验收有一条"Electron 截图或录屏：两个主控窗格、一个 worker 窗格同时在一个任务下"。用户 2026-10-16（逐字，会话"a2a-构思主控"，AskUserQuestion）选"拆出去：T-078 其余先收，截图项另开 UI 票 (Recommended)"，选项原文："承认单窗多窗格是产品工作，另开一张 UI 票做（spec 里本来就写“一个任务里有多个会话窗格”）。T-078 把这一项从验收里移出并在 Resolution 写明，其余项独立审查通过就可以关。这是你对验收条件的修订，要你本人确认。"

## Acceptance

- [x] 红态：当前 `main` 上同一任务不能在一个窗口里同时显示三个窗格（读回现状）。
- [x] 绿态：一个窗口里同一任务的两个主控窗格加一个 worker 窗格同时可辨，各自绑定正确的 task、角色与 launch；三份真实 `workbench_snapshot` 与进程身份核对，不靠标题。
- [x] 反例：给第三个窗格绑错 task 或旧 launch，检查拒绝；不得用三张图拼接或顺次切换冒称同时显示。
- [x] 截图或录屏用原始单帧（可附不剪辑的短视频），范围只含这个隔离窗口；Computer Use 仅限 worker 自己启动的隔离 Electron，缺屏幕录制或辅助功能权限由用户在系统设置里给。
- [x] T-074/T-075 的正反例不退化；T-078 已有的主控窗格与输入行为不退化。
- [x] 独立审查通过；`project_map.py status` 0 problems。

## 说明

- 构思主控建票，未标 ready；开工前先过一遍界面方向（可用 `frontend-production` 与 `same-visual-family` 两个 skill 的约束）。与 T-078 不再互相等待。
- 不改门禁、不改紧急停止或收件箱语义。

## 就绪

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："那现在都idle了，让他继续啊，漏掉的也开工"，构思主控据此标就绪（`ready_rev: 1`）。

## Resolution

**INCOMPLETE，验收未完成，ticket 仍 open。** 2026-10-17 用户裁定 A（收件箱 `20261017T133907Z-ideation-answer-001`，执行主控 #18 逐字转达）：主控 CLI 的路径与预期版本从配置读取，启动时实际执行一次 --version 核对；不符报错，不改用户全局设置，不关闭自动更新，不自动改用其他版本。

T-078 已有证据及 T-091 的 red-02 使用 Claude Code **2.1.296**，仅对各自冻结版本成立。T-091 新绿态夹具配置为 **2.1.302**；green-01 因 2.1.296 路径已不存在而在建窗前 INCOMPLETE，原件保留。green-02 的三格同屏、版本／错误绑定反例及四类 GUI 回归 -02 已在 f20a74ada 取得真实 PASS；core -03 的四组原套件与 fence 反例通过，CAS 变异触发业务断言但分类器漏判，lock 未执行。分类器修正后待 core -04，最终独立审查仍未完成。整票不能上调 PASS，验收框仍由主控在完成检查后处理。执行材料及具体结果见 [RESULTS](../../evidence/2026-10-16-batch16/T-091/RESULTS.md) 与 [实跑清单](../../evidence/2026-10-16-batch16/T-091/THREE-PANES-RUN.md)。

重复的 CAS 分类器漏判已接入机械前置检查：[test_t091_business_mutant.py](../../workbench/tests/test_t091_business_mutant.py) 由 core 回归入口自动执行，要求完整三项违反并拒绝不完整／无关失败；主控无需再记住另做人工补判。起点 main 的相同方法计时未取得，不把候选上超时归因于 T-091。

## Resolution

2026-10-17，执行主控按门禁验收 **PASS**，合入 main（不 push）。冻结候选 `e4dcb2739af449396a3c6982e9826326d64a4369`（exec/t091），起点 main `44bbb7828`；之后的 `247942bdc` 只补审查报告与计时证据。

- **产品**：同一 BrowserWindow 内按 sender 与 pane key 路由六条 IPC（每进程注册一次）；每格独立的 window_id、sequence、放行声明与输出游标；上方两个主控、下方全宽 worker，窗宽 <1000px 改为三行；每格显示 role+preset、task、launch，worker 还显示 attempt；"正在输入"只跟随实际键盘焦点。daemon 只在 `workbench_snapshot` 中补出已有的 preset。门禁、紧急停止、收件箱语义均未改。
- **主控 CLI 版本**（用户 2026-10-17 裁定 A，收件箱 `20261017T133907Z-ideation-answer-001`）：不再写死 2.1.296 的路径，改为从启动配置读取，启动时实际执行 `--version` 核对，不符即报错；配置值为 2.1.302。不写用户全局设置，也不关自动更新。起因：重启后 Claude Code 自动更新删掉了 2.1.296，main 上的主控窗格在本机无法启动。**T-078 的 09B/09C 证据绑定 2.1.296，没有在新版本上重跑。**
- **证据**（原件在外置盘 `a2a-evidence/2026-10-16-batch16/T-091/`）：
  - 红态 red-02：后台 3 个会话，窗口只显示 1 格。
  - 单格 tracer-01 PASS。
  - 三格绿态 green-02 PASS：两个主控 CLI 2.1.302，模型回合 0、假 POST 0；1 个 Electron，3 个受控 receiver 串行；三份 snapshot 与进程身份核对；1440×900、1200×800、900×650 三张原始单帧只截隔离窗口；错 task 与旧 attempt 两个反例在建窗、发凭据之前即被拒绝。
  - 回归：core-04（coop 8、recovery 9、run 18、CAS 1，fence/CAS/lock 三个业务反例）PASS；window、runtime、input-failures、worker-inbox 四个 -02 PASS。
- **测试调整（主控裁定，有起点证据）**：
  - `test_electron_e2e.py:170` 的旧断言自 T-078 起已过时，改为逐项列出实际 bridge 方法。
  - 三个完整质量流程正例的适配器预算由 8 秒改为 30 秒。quality-timing-01 显示：同为 8 秒时，起点与候选各 9/9 次都触发了 deadline，所以这是既有问题，不是本票造成的退化。负例预算与原断言不变。
- **独立审查**：reviewer s16-t091-rev（launch-e1cd719b7b644f5e9b617716d1faf133）`independent-review-01.md` **PASS**；M2/M3 两个真实入口变异命中预定业务断言，M1 更早被身份绑定检出（mutation-verdict=false，保留）。
- **过程**：2026-10-17 08:51 机器内存耗尽后死机重启。Herdr 以不带参数的 `codex resume` 恢复了 worker，没有启动记录，已关闭；之后用 launch-worker resume 接回，又被"conversation is open in another app"锁住，于是新开会话 launch-71afbd1600cb451a9d9354aa7768e72b 接手。red-01 留下的 Electron 卡在 ready 之前，正常退出被拒，由主控核对身份后发了一次 SIGTERM。
- 打分 `score-c9e338907bdc48308ebde063b321ab21`（边界 3、工程 2）。
- **未覆盖**：系统输入法不在本票范围；没有做真实模型回合；真登录见 T-093。
