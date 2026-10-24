# T-159-1 / a1：分屏修复与验证交接

状态：**INCOMPLETE（新增绿态待运行；P1 待决定）**。此前真实 Electron 红态、绿态、两个变异及 T-139 三项回归证据保留。主控消息 #37 确认 P3 前提与实测不符，撤回修改产品判据及新增按 role 判断变异的要求，仅补已批准项目主控终端分屏的真实 Electron 绿态场景。P1 验收语义仍交构思主控决定，此前通过结论不用于上调本次审查状态。

## 范围与依据

- worker：`b24-t159`；分支：`exec/t159`；产品起点：`c01742804961214ed025b6c9fb9924a1ea49ee2d`。
- 修复提交：`9a4cc2dd68610ab143517bb9b90688f84c9d6d2c`；已完成的真实 Electron 绿态候选：`977bd408de4dd53ba4c3b320e52da372b64ee64b`（含 README 同步）。消息 #37 的补充仅改本票测试、运行脚本和报告，不改该候选的产品代码。
- 目标：修复任务 worker 分屏后被项目普通终端替换的问题。非目标：改变 T-139 的三层视图、门禁或任务归属。
- Ubiquitous language：使用 `CONTEXT.md` 的项目、任务、Agent 会话、普通终端术语。
- 根因：`workbench/app/main.ts` 的 `a2a:pane-action` → `createTerminal` 未区分任务会话与普通终端。任务中分屏先调用 `shell_start`，再 `changeView` 到项目层，清掉相对窗格。`renderer.tsx` 的分屏回调只更新窗格和布局，没有同步任务标题，因此还显示旧任务上下文。真实 Electron 红态与该路径一致。
- T-139 明确普通终端只在项目层；T-159 允许不能混屏时在操作前说明。现按该已授权分支处理：任务会话菜单禁用右/下分屏，事先说明“任务视图只展示 Agent 会话。请在普通终端中分屏。”；键盘导航跳过禁用项。创建入口在 `shell_start` 前拒绝任务会话的分屏请求，防止直接 IPC 绕过菜单。保留普通终端分屏。产品修改仅涉及 `workbench/app/main.ts` 与 `workbench/app/renderer.tsx`。不新增平行视图或兼容路径；沿用现有布局接口，遵守 Deep modules 原则。
- 本次不跨存储、门禁和 API 实现新能力，无需新增 Tracer bullet；测试通过现有真实后台、门禁、PTY、Electron 完整入口观察。

## 已有证据

1. session 启动的 `project_map.py status --root .`：Problems 0、Stale living docs 0。
2. Python 初次语法检查被默认缓存目录的写入限制阻断；改用 `PYTHONPYCACHEPREFIX=/private/tmp/t159-pycache` 后通过。未申请提权。
3. 沙箱运行命令：

   ```sh
   python3 workbench/tests/test_t159_split_e2e.py --summary evidence/2026-10-23-batch24/T-159/sandbox-red-01.json --revision c01742804961214ed025b6c9fb9924a1ea49ee2d
   ```

   结果：**INCOMPLETE**。真实后台与受控原生 worker 已启动；Electron CDP `127.0.0.1:65525` 连接被拒绝，等待项目出现超时。没有执行到分屏操作，不是缺陷红态。摘要见 `sandbox-red-01.json`；夹具保留在 `/private/tmp/t159-cc0_42f1`，停止流程未报告 cleanup_errors。没有真实 CLI 模型调用。
4. `zsh -n evidence/2026-10-23-batch24/T-159/RUN-OUTSIDE-01.sh` 与 `git diff --check`：通过。
5. 执行主控消息 #31 返回 `RUN-OUTSIDE-01` 的 rc=0；已读取 `outside-01-dJtqcETt/red.json`、`exits.txt` 和回归摘要核对。真实 Electron 修前红态：worker `ddd67143-d12e-423a-bcab-4c326f1b5d28` 被一个普通终端替换，新窗格在项目根目录，菜单未事先说明。预期业务断言 `task_right_explains_before_action` 失败；没有 cleanup_errors。截图、摘要与小日志随本票提交；原始夹具 `/private/tmp/t159-qxrk1prm` 保留，待主控归档。T-139 selection、layout-store、terminal-catalog 的修前回归均通过。
6. 修复后在沙箱内运行三项已有回归，均通过：

   ```sh
   node --experimental-vm-modules workbench/tests/test_t139_selection.mjs evidence/2026-10-23-batch24/T-159/local-selection-02.json
   node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs evidence/2026-10-23-batch24/T-159/local-layout-store-02.json
   node workbench/tests/test_t139_terminal_catalog.mjs evidence/2026-10-23-batch24/T-159/local-terminal-catalog-02.json
   ```

   这三项只证明相关逻辑与存储边界，不替代 Electron 绿态。
7. 更新后的 Python 测试语法检查、`zsh -n RUN-OUTSIDE-02.sh`、`git diff --check`：通过。
8. 产品提交后 `project_map.py status` 检出 `workbench/README.md` 过期。卡中允许修改必要 README 行，已同步普通终端章节的分屏限制，并纠正同一段仍称普通终端混入任务视图的旧说明；未修改地图。

## 沙箱外验证结果

执行主控消息 #33 返回 `RUN-OUTSIDE-02` 的 rc=0。已读取 `outside-02-TzKrStnh/` 的候选号、六份测试摘要与退出码，并查看菜单和普通终端分屏截图；所有运行均无 cleanup_errors。真实后台、门禁、受控原生 PTY 与真实 Electron 经 CDP 运行；零模型调用。

| 场景 | 结果与证据 |
| --- | --- |
| 修后真实 Electron | `green.json`：PASS，25 项检查通过，exit 0。任务右/下分屏事先说明、保持原 worker、拒绝直接 IPC 且布局和启动记录不变；普通终端从子目录右/下分屏的数量、类型、几何位置与实际 pwd 正确；切回任务与单 agent 后仍隔离。 |
| 恢复修前实现 | `mutant-old.json`：exit 1，`task_right_explains_before_action` 失败，并再次只剩一个普通终端、原 worker 不在画面。 |
| 仅删除创建入口检查 | `mutant-guard.json`：exit 1，菜单说明仍通过，`task_right_ipc_refused_with_explanation` 失败。证明仅禁用菜单不能通过本票验收。 |
| T-139 selection | `selection.json`：PASS，25 项，exit 0。 |
| T-139 layout-store | `layout-store.json`：PASS，10 项，exit 0。 |
| T-139 terminal-catalog | `terminal-catalog.json`：PASS，2 项，exit 0。 |
| 运行脚本 oracle | `exits.txt`：`green=0 old_mutant=1 guard_mutant=1 selection=0 layout=0 catalog=0`，`oracle=0`。两个变异摘要的原始状态均为 INCOMPLETE；脚本核对它们是上述预期业务断言失败，而非启动或清理失败，才判定变异被拒。 |

截图：[任务菜单的事前说明](outside-02-TzKrStnh/green-02-menu-right.png)、[普通终端向右分屏](outside-02-TzKrStnh/green-04-shell-right.png)、[继续向下分屏](outside-02-TzKrStnh/green-04-shell-down.png)。

重放命令（每次生成新目录，保留原证据）：

```sh
zsh evidence/2026-10-23-batch24/T-159/RUN-OUTSIDE-02.sh
```

脚本每次创建新 `outside-02-*` 目录，记录候选完整提交号，保留命令输出、摘要和截图；运行真实 Electron 绿态、两个变异及三项 T-139 回归。绿态还核对键盘导航跳过禁用项及说明文字在当前窗口内完整可见。

两个反例：`old-task-split` 在隔离源码副本中恢复修前 main/renderer，必须重现单个普通终端替换 worker；`missing-split-guard` 仅删除创建入口检查，保留菜单说明，必须被 `task_right_ipc_refused_with_explanation` 拒绝。脚本只认这些预期业务失败，启动错误和清理错误不能算杀死变异。

已有相关回归列入脚本：`test_t139_selection.mjs`、`test_t139_layout_store.mjs`、`test_t139_terminal_catalog.mjs`。覆盖三层视图、保存布局与普通终端目录；它们不能替代本票真实 Electron 验收。T-139/T-143 的完整真实 Claude 性能 e2e 未运行，本票不使用真实模型。

## 边界与交接

- 本票采用 T-159 明确允许的“不能混屏时事前说明”分支，没有让任务 worker 与项目普通终端混屏；普通终端分屏仍保留原窗格。此边界与 T-139 一致。
- 独立审查与最终门禁验收不属于本 worker 的通过声明；执行主控按既定流程新开只读审查。
- `frontend-less-ai-tone` 的旧独立目录在本机两个指定位置未找到；已按整合技能 `frontend-production` 的 `references/look-and-copy.md` 编写限制说明，其 `SOURCE.md` 明确该规则原样迁入。
- 结果目录约 1.1 MiB，仅含小文本和截图，已逐文件核对无超过 5 MiB 的文件。大夹具不入仓库；`/private/tmp/t159-u40ztvev`（绿态）、`/private/tmp/t159-5113q34s`（旧实现变异）、`/private/tmp/t159-xfpaa_9q`（缺入口检查变异）保留，后续由执行主控按 T-088 归档，不覆盖或删除失败现场。

## 独立审查后：项目主控分屏前提核对

消息 #34 要求项目层已批准主控可以分屏，并用按 role 判断的变异证明。事实探针发现：同一个已批准项目终端的侧栏角色为 controller，但真实 `workbench_snapshot.launch.role` 仍为 shell，因此当前菜单仍允许分屏；消息中“快照 role 变为 controller，所以被禁用”的前提尚未复现。仅把菜单改回按 role 判断的变异也不会被该真实场景拒绝。

见 [原问题上报](ISSUE-CONTROLLER-SCOPE-01.md)、[实测摘要](controller-scope-probe-01.json) 和 [重放探针](PROBE-CONTROLLER-SCOPE-01.py)。执行主控消息 #37 明确：“你的探针是对的，我上一条（#34）把它定成‘回归’是错的”，并撤回产品判据修改和按 role 判断变异的要求。原上报与探针保留，不改写成已复现的产品缺陷。

按消息 #37，仅在 `test_t159_split_e2e.py` 末尾增加真实场景：使用夹具已完成角色申请、批准和确认的项目执行主控终端；核对真实角色与侧栏归属，在项目视图从菜单向右分屏，原 launch 和 pane key 保留，新窗格在右侧、两者目录仍为项目目录，主控批准身份不变。保留真实 `launch.role: shell`，不替换快照。新增菜单与分屏截图供复核。

交主控运行：

```sh
zsh evidence/2026-10-23-batch24/T-159/RUN-OUTSIDE-03.sh
```

脚本只跑更新后的完整真实 Electron 绿态和原两个变异 `old-task-split`、`missing-split-guard`，每次保留新 `outside-03-*` 目录；要求新增主控场景通过，并核对原两个变异仍在预期业务断言失败。原 T-139 三项回归已在未变的产品代码上通过，本次不重复运行。

本地检查：Python 测试及脚本内 oracle 的语法、`zsh -n RUN-OUTSIDE-03.sh`、UTF-8 回读和 `git diff --check` 均通过；产品源码与已验证候选无差异，项目地图无问题或过期文档。当前仅完成测试与脚本准备，新增场景未运行，不能称其已通过。P1 未决不在本 worker 范围内处置。
