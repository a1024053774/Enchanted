---
id: T-062
title: 修复任务窗口里残留的浮层，它盖住问题上报面板的标题
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 2
---

## What to build

T-055 的面板截图（`evidence/2026-10-09-batch8/T-055/round4/panel-final-*.png`）左上有一个浮层，像新手导览的残留，盖住了"问题上报"标题的一部分。查明它是产品缺陷还是隔离 dev 环境才有的导览，是产品缺陷就修；是环境问题则说明依据并让验收截图不再带它。用户要求修复："浮层这个要修复"。

## Acceptance

- [x] 复现并查明来源（产品还是 dev 环境），保存证据与重放命令。
- [x] 修复后任务窗口里该浮层不再遮挡面板标题；真实 dev UI 截图（含有问题上报时）作证，外观由用户判断。
- [x] 若是产品缺陷：先红后绿的界面用例；既有套件、typecheck、lint 通过，上游文件改动列清单。
- [x] 产品修复（用户 2026-10-09 选 B，逐字："062选B"）：已查明浮层是 Synara 首次使用 Activity 提示（`apps/web/src/components/Sidebar.tsx:1157`），正式工作台全新 profile 也会出现。改到它不再压住任务窗口（改位置，或任务窗口打开时不弹，取最小改动并在 RESULTS 说明理由）；提示框文字看不清（白底浅色字）一并修到可读。全新 profile、提示出现期间的真实 dev UI 截图作证（1600×1050 与 1280×900），外观由用户判断。允许改的上游文件仅限 `Sidebar.tsx` 及其直接样式，列入上游文件改动清单；不改导览其他步骤。

## 说明

- 授权来源：用户 2026-10-09 说"浮层这个要修复"；`ready_rev` 2 增加产品修复一项，依据用户选 B（逐字："062选B"），见 inbox 里的 revise 条目；与 T-057 同改任务窗口时，同一文件同一时间只能有一个写入者，由执行主控安排。

## Resolution

2026-10-09，worker `s11-t062`：INCOMPLETE（聚焦红/绿通过，唯一一次独立审查无效），保持 open，待主控关闭。

来源是 Sidebar 首次使用 Activity 提示：全新隔离 profile 在 Skip tour 后显示，约 8 秒自然关闭；它并非 dev 专属。本次旧截图拍在启动提示期间，按 brief 环境分支，仅修正 T-062 截图夹具等待，不改产品。`red03` 因提示覆盖标题而预期失败；`green03` 在真实 dev UI 的 1600×1050 与 1280×900 下标题无遮挡。外观由用户判断。fork 无提交、无上游文件改动，基线保留 `d9fc40a5f8b14d22ec7568c7ccef542572e79102`。

证据、重放命令、原样失败与隔离收尾见 [RESULTS](../../evidence/2026-10-09-batch11/T-062/RESULTS.md)。重开持久 profile 停在启动画面、窄窗口会话空态重叠已分别非阻塞上报，均未扩大修复范围；不声称重开通过。正式实例未访问，真实模型调用 0 次。

冻结候选 `45893b7c70b30b2659337875b043795127819686`。审查返回 INCOMPLETE，并自报读入禁止的实现说明导致独立结论无效；另把候选外持续更新的主控日志视为冻结失效。原文已保留并上报，未改他人的日志，遵守 brief 不自行追审。缺少有效独立审查结论，交执行主控处理。

2026-10-09，worker `s11-t062-rev2`，依据 ready_rev 2：INCOMPLETE（产品修复、红绿和检查已完成，一次独立审查待执行）。保持 open，待主控关闭。

父修订 `d9fc40a5f8b14d22ec7568c7ccef542572e79102` 的全新 profile 在提示出现期间复现标题遮挡；fork 候选 `4ac5ba00e7125279b08c241037d1404450455ff6` 仅修改 `Sidebar.tsx` 四行，使首次提示向下展开并右对齐铃铛，文字沿用现有 popup 主题色。亮暗主题、1600×1050 与 1280×900 的提交后真实 dev UI 四组截图均显示提示可见且任务窗口/问题上报标题无交叠。相关 Vitest 188/188，最终完整 browser tests 14/14，全 workspace typecheck、lint（0 errors）、fmt:check 通过；首次完整浏览器套件断联的失败保留，原因未定且已非阻塞上报。证据、重放、上游清单与局限见 [RESULTS-02](../../evidence/2026-10-09-batch11/T-062/RESULTS-02.md)。本轮旧证据未改，未访问正式实例，工作台内真实模型调用 0 次。

2026-10-09，rev2 最终交付：PASS，保持 open，待主控关闭。一次有效 fresh-context 独立审查针对 a2a 冻结提交 `d5d0af3704c3ede71df6b84e539c7b030395ccd9` 与上述 fork 提交返回 PASS、无 findings，明确未读 RESULTS、Resolution、inbox 正文或旧审查；原文见 [rev2-acceptance-review-raw](../../evidence/2026-10-09-batch11/T-062/rev2-acceptance-review-raw.txt)。没有追审，审查后仅追加结论与收尾记录。外观由用户判断；本轮非阻塞 issue `20261010T025815Z-worker:s11-t062-rev2-issue-001` 未自行关闭。

**执行主控关闭（2026-10-09）：PASS。** 依据 ready_rev 2（用户原话"062选B"）。worker `s11-t062b` 交付 fork `4ac5ba00e`（只改 `apps/web/src/components/Sidebar.tsx`，4 行：首次 Activity 提示改为从铃铛下方展开、右对齐，去掉白字与 accent 背景，改用 popover 主题前景色），a2a 证据 `d5d0af3`（冻结）/`795b49f`（追加审查结论）。父修订红态：标题交叠 351 px²、亮色文字对比度约 1.03；候选绿态：标题与任务窗口交叠 0、对比度亮 19.27/暗 17.47，四组截图（亮/暗 × 1600×1050/1280×900）均在提示可见期间拍摄。相关 Vitest 188/188、Activity/导览 browser 14/14、全 workspace typecheck、lint（0 errors）、fmt:check 通过。fresh-context 独立审查一次，PASS，无 findings，确认未读禁止材料（`rev2-acceptance-review-raw.txt`）。主控审阅了 diff 与 `rev2-green02-light-1280x900.png`：提示现在落在侧栏内、压住侧栏上方几行导航约 8 秒，不再碰任务窗口。外观由用户判断。局限：browser 套件第 4 轮 WebSocket 提前断开、原因未定，已上报 `20261010T025815Z-worker:s11-t062-rev2-issue-001`（非 blocking，留给用户）；截图里会话空态文字与输入区重叠由 T-063 处理。
