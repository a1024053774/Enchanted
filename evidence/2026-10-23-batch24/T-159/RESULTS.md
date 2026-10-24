# T-159-1 / a1：分屏修复与验证交接

状态：**INCOMPLETE**。真实 Electron 修前红态成立；已实现最小修复，沙箱内三项 T-139 回归通过。真实 Electron 绿态、变异与独立审查待完成，不能用于集成。

## 范围与依据

- worker：`b24-t159`；分支：`exec/t159`；产品起点：`c01742804961214ed025b6c9fb9924a1ea49ee2d`。
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

## 待主控运行

```sh
zsh evidence/2026-10-23-batch24/T-159/RUN-OUTSIDE-02.sh
```

脚本每次创建新 `outside-02-*` 目录，记录候选完整提交号，保留命令输出、摘要和截图；运行真实 Electron 绿态、两个变异及三项 T-139 回归。绿态核对任务菜单事前说明、键盘可达性、IPC 无副作用拒绝、原 worker 与保存布局不变；普通终端从子目录向右/向下分屏时核对数量、类型、几何位置和实际 pwd，并切回任务及单 agent 核对隔离。请返回输出目录。

两个反例：`old-task-split` 在隔离源码副本中恢复修前 main/renderer，必须重现单个普通终端替换 worker；`missing-split-guard` 仅删除创建入口检查，保留菜单说明，必须被 `task_right_ipc_refused_with_explanation` 拒绝。脚本只认这些预期业务失败，启动错误和清理错误不能算杀死变异。

已有相关回归列入脚本：`test_t139_selection.mjs`、`test_t139_layout_store.mjs`、`test_t139_terminal_catalog.mjs`。覆盖三层视图、保存布局与普通终端目录；它们不能替代本票真实 Electron 验收。T-139/T-143 的完整真实 Claude 性能 e2e 未运行，本票不使用真实模型。

## 未完成项

- 真实 Electron 同一测试绿态、两个变异及沙箱外修后回归尚未运行。
- 测试的修前缺陷信号已由真实 Electron 验证；其后半段普通终端分屏场景尚未运行，不能宣称覆盖通过。
- 本次没有宣称行为验收通过，也没有独立审查结论；执行主控应在候选完成后新开只读审查。
- `frontend-less-ai-tone` 的旧独立目录在本机两个指定位置未找到；已按整合技能 `frontend-production` 的 `references/look-and-copy.md` 编写限制说明，其 `SOURCE.md` 明确该规则原样迁入。
- 大夹具不入仓库；后续由执行主控按 T-088 归档，不覆盖或删除本次失败现场。

按派发要求停在 `RUN-OUTSIDE-02` 沙箱外运行交接。
