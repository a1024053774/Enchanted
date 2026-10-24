# T-159-1 / a1：任务内分屏讨论终端

状态：**INCOMPLETE**。`RUN-OUTSIDE-04` 的两个变异均在预期业务断言被拒，T-139/T-143 回归通过；真实 Electron green 在正向对照处因测试基线变量被覆盖而中断。已按执行主控 #60 只修该基线，待 `RUN-OUTSIDE-05` 单独补跑 green。旧禁用方案的通过结论不替新实现背书。

## 当前授权与边界

- worker：`b24-t159`，task `T-159-1`，attempt `a1`，分支 `exec/t159`。
- 原始产品起点：`c01742804961214ed025b6c9fb9924a1ea49ee2d`；本轮开始于 `17796b166`（旧独立审查记录，已被用户方向裁定取代）。
- 来源：执行主控消息 #54，转述构思主控 answer `20261024T024128Z-001` 中用户 2026-10-24 原话：“任务视图里也可以分屏吧,比如说我想对这个任务有疑问,想开一个分屏侧边聊天来讨论这个任务”。同条派发明确撤回禁用分支，允许修改与旧规则相关的 `test_t139_*`，并允许复用 `outside-01` 红态。
- 目标：任务内向右/向下分屏保留原 worker，新增标明“普通终端”的 zsh，目录为任务仓库根。终端只有视图布局关联，不成为任务 agent、不认领任务路径、不记为 worker 的人工介入。
- 非目标：修改门禁、PTY 生命周期、角色投影、侧栏分类、主控权限或其他票。未修改 `panes.ts`、`gates/**`、`sidebar.ts`、`preload.ts`、地图、术语表或 ticket。当前 worktree 内 ticket 仍是旧文字，以消息 #54 的明确裁定执行并在本报告记录；不自行改写治理文件。
- 已读 main 的 T-159 新验收；main 的 T-139 ticket 仍有“只在自己视图出现”的旧目标，已非阻塞上报 `ISSUE-T139-DOC-SYNC-01.md`，请主控同步治理说明。worker 的 README 与对应测试已同步。

## 实现

1. `workbench/app/main.ts`：删除任务分屏的拒绝与切到项目视图的路径；沿用现有 `shell_start`，保留原窗格与任务上下文，按菜单方向插入新叶子。从任务 agent 分屏时使用 `task.repo`，从普通终端分屏时仍沿用其启动目录。
2. 新终端绑定 `project`，不绑定 gate `task/attempt/session/fence`。快照、输入、关闭仍走普通终端通道，原 worker 凭据不重建、不改投递目标。后台现有布局校验已经允许任务布局引用同项目 shell，无需新增后台入口。
3. 任务布局恢复只补回保存树中明确引用、仍在同项目打开集中的普通终端；不自动加入其他项目终端。任务打开集仍只登记 agent。布局读取由 `taskPaneLayout` 同时服务任务恢复和单 agent 视图的布局保存；这是两个真实调用点，沿用现有 SQLite 布局事实，符合 Deep modules 原则。
4. 单 agent 视图分屏保存时把当前子树放回原叶子，保留隐藏兄弟窗格、讨论终端及名称；恢复右/下嵌套结构。关闭讨论终端只关闭该 shell 并移除布局叶子。
5. `renderer.tsx`：恢复任务窗格向右/向下分屏按钮，删除禁用说明；终端头仍按真实 shell 快照显示“普通终端”。README 同步任务布局说明。
6. Ubiquitous language：普通终端与 Agent 会话保持区别。Tracer bullet 使用真实 shell → 应用窗格绑定 → 已有布局保存/恢复 → 普通终端输入这一条生产路径；没有新增存储或平行 API。

## 红态与已运行检查

- **真实 Electron 红态复用（仅证明替换现象）**：`outside-01-dJtqcETt/red.json`，产品版本 `c01742804961214ed025b6c9fb9924a1ea49ee2d`，原 worker `ddd67143-d12e-423a-bcab-4c326f1b5d28` 在分屏后消失，画面只剩一个项目根目录普通终端，任务选择被切走；截图 `red-03-after-right.png`。原运行断言名属于已撤回的禁用方案，本轮不复用该断言的语义，也不复用旧通过结论。`RUN-OUTSIDE-04` 会核对记录中的实际窗格与版本。
- **布局恢复反事实**：新增 T-139 SQLite 场景在 `17796b166` 的真实 main.ts 上退出 1，业务断言 `task_restores_only_explicit_project_shell` 失败；见 `local-layout-store-parent-red-04.json`。已有声明的普通终端未被恢复，不是环境失败。
- **布局恢复绿态**：最终 main.ts 运行同一测试退出 0，14 项通过，见 `local-layout-store-final-04.json`；覆盖只恢复明确加入的终端、单 agent 改名保留讨论布局、关闭讨论终端保留 agent、讨论终端不进入任务打开集。前一检查点的 `local-layout-store-04.json` 同样保留。
- `test_t139_selection.mjs`：最终代码 25 项通过，见 `local-selection-final-04.json`；前一检查点的 `local-selection-04.json` 保留。
- `test_t139_terminal_catalog.mjs`：2 项通过，见 `local-terminal-catalog-04.json`。
- 前一交付的 Python 测试、脚本内两个 oracle 的语法、`zsh -n RUN-OUTSIDE-04.sh`、UTF-8 回读和差异空白检查通过；本次真实运行结果见下节。
- 沙箱内 Electron CDP 不可达的原始失败 `sandbox-red-01.json` 保留为 INCOMPLETE，不当成产品红态；本轮不重复这一环境失败，不发起沙箱外运行提权请求。

## 本轮测试变更与理由

- `test_t159_split_e2e.py`：将旧“任务分屏被拒绝”断言改为当前真实用户行为。受控原生 PTY、真实后台/门禁、真实 Electron，不调用供应商模型。分别从 worker 向右、向下分屏；核对数量、类型、几何位置、任务仓库根实际 pwd、侧栏仍是普通终端、worker 数量不增加、task/attempt/workspace/路径边界和 worker 状态不变。切换后恢复明确加入的终端与嵌套方向；关闭讨论终端保留 worker；单个 worker 视图仍只显示自己；保留项目主控分屏场景。
- 观察独立读取 SQLite `user_inputs` 与门禁 `human_intervention` 事件。讨论终端输入不得增加二者；最后向 worker 直接输入必须增加二者，作为观察器正例，避免只比较空列表。这个正例是夹具中的人工介入，不用于声称讨论终端产生了介入。
- `test_t139_layout_store.mjs`：增加新裁定允许的明确终端布局关联与关闭/恢复场景，使用实际 SQLite 与后台原有布局校验。
- `test_t139_selection.mjs` 和 `test_t139_t143_views_perf_e2e.py`：只将旧“任务只有 agent”措辞改为“排除未选择的项目终端”。原场景未做任务内分屏，所以原排除条件继续有效，不放宽隔离断言、不改性能测量或输入权限条件。
- 旧两个变异对应旧方向，本轮改为两种当前已知坏实现：`replace-worker` 恢复创建 shell 后切走任务的错误；`shell-input-to-worker` 在隔离 main.ts 副本中把讨论终端的输入误发给同屏 worker，必须产生并被 `task_right_no_intervention` 拒绝。后者不修改后台或测试 oracle，检查真实输入记录与事件。

## RUN-OUTSIDE-04 结果与正向对照修复

- 执行主控 #60 返回 `outside-04-Agwb7jjs/`，候选 `5d6eb3bbb74197b274e1ed79082d8367e5cbc0b6`。原目录的小文本与截图原样提交，未覆盖失败证据。退出码为 `red=0 green=1 replace=1 intervention=1 selection=0 layout=0 catalog=0 t139_t143=0 oracle=1`。
- green 摘要已记录的 44 项检查全部通过，包括任务右/下分屏保留 worker、普通终端类型/目录/输入隔离、布局恢复及项目主控分屏。随后在 `intervention_observer_positive_control` 求值时抛出 `KeyError: 'inputs'`，该项与最后的零模型请求断言未完成，整体为 **INCOMPLETE**，不是完整绿态。原因是同一函数中的 `before` 已被项目主控场景改为 Electron selection 结构。
- 仅在正向对照输入前增加 `control_before = task_facts()`，比较输入与人工介入计数时使用此基线。两项各增加 1 的期望不变，其他断言及产品代码均未改动。
- 本次静态检查通过：Python 与 05 内嵌 oracle 的语法、`zsh -n`、UTF-8 回读、证据文件边界及 `git diff --check`；产品目录差异为空。项目地图 status 为 0 Problems / 0 Stale docs，见 `project-map-status-08.txt`。这些检查不替代待运行的 green。
- `replace-worker` 在 `task_right_keeps_worker` 被拒；`shell-input-to-worker` 在 `task_right_no_intervention` 被拒，均为预期业务失败。selection 25 项、layout-store 14 项、terminal-catalog 2 项及真实 T-139/T-143 23 项回归通过，摘要均无清理错误。本次不重跑这些已完成场景。
- 夹具保留：green `/private/tmp/t159-qho8_pob`，替换变异 `/private/tmp/t159-sxu8ba07`，介入变异 `/private/tmp/t159-se3dptop`，T-139/T-143 `/private/tmp/t139-ub3lm9_h`；完整位置以各摘要为准。

## 待执行主控运行（仅 green）

```sh
zsh evidence/2026-10-23-batch24/T-159/RUN-OUTSIDE-05.sh
```

每次生成新 `outside-05-*` 目录，保留完整候选号、摘要、退出码和截图；只运行 T-159 真实 Electron green，不覆盖 04，也不重跑红态、变异或回归。脚本核对全部检查通过，包含实际 worker 输入的正向对照及零模型请求检查。

05 只有 green 退出 0、摘要为 PASS、关键断言齐全、版本匹配且无清理错误才返回 PASS。目前 05 尚未运行；独立审查与最终门禁验收由执行主控安排。

## 历史处置与证据保留

- `outside-02-TzKrStnh/` 与 `outside-03-WDUFSMFa/` 的通过结果均属于已撤回的禁用方案，保留为历史记录，不能用于当前方案验收；历史提交不改写。
- 旧审查 P3 把侧栏 controller 投影误当成窗格快照角色。真实探针 `controller-scope-probe-01.json` 证明已批准主控的窗格角色仍为 shell；执行主控 #37 已撤回该问题，不新增不会失败的按 role 变异。
- 原 P1 的方向疑问已由消息 #54 的用户裁定解决：允许任务内分屏讨论终端，撤回“禁用并说明”。不再以旧“普通终端只在项目层”规则拒绝本次实现。
- 报告、小摘要和截图入仓库；整个原始夹具留在摘要列出的 `/private/tmp/t159-*` 路径，由执行主控按 T-088 归档。未删除、覆盖旧失败证据，未更改用户全局配置。
