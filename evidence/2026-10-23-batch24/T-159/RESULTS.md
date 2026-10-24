# T-159-1 / a1：红态验证准备

状态：**INCOMPLETE**。当前提交只交付测试与沙箱外运行脚本；产品修复尚未开始，不能用于验收或集成。

## 范围与依据

- worker：`b24-t159`；分支：`exec/t159`；产品起点：`c01742804961214ed025b6c9fb9924a1ea49ee2d`。
- 目标：修复任务 worker 分屏后被项目普通终端替换的问题。非目标：改变 T-139 的三层视图、门禁或任务归属。
- Ubiquitous language：使用 `CONTEXT.md` 的项目、任务、Agent 会话、普通终端术语。
- 代码定位：`workbench/app/main.ts` 的 `a2a:pane-action` → `createTerminal`。任务中分屏先调用 `shell_start`，再 `changeView` 到项目层，清掉相对窗格。`renderer.tsx` 的分屏回调只更新窗格和布局，没有同步任务标题，因此还显示旧任务上下文。这是源码诊断，尚未取得真实 Electron 缺陷红态。
- T-139 明确普通终端只在项目层；T-159 允许不能混屏时在操作前说明。后续拟按该已授权分支处理：任务会话菜单在操作前说明限制，拒绝会切走原 worker 的分屏；保留普通终端分屏。预计产品修改只涉及 `workbench/app/main.ts` 与 `workbench/app/renderer.tsx`。不新增平行视图或兼容路径；沿用现有布局接口，遵守 Deep modules 原则。
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

## 待主控运行

```sh
zsh evidence/2026-10-23-batch24/T-159/RUN-OUTSIDE-01.sh
```

脚本每次创建新 `outside-01-*` 目录，保留命令输出、摘要和截图。红态 oracle 必须同时看到预期断言失败、只剩一个普通终端、原 worker 不在画面中、清理没有报错；启动失败不能通过 oracle。请返回输出目录。

已有相关回归列入脚本：`test_t139_selection.mjs`、`test_t139_layout_store.mjs`、`test_t139_terminal_catalog.mjs`。覆盖三层视图、保存布局与普通终端目录；它们不能替代本票真实 Electron 验收。T-139/T-143 的完整真实 Claude 性能 e2e 未运行，本票不使用真实模型。

## 未完成项

- 真实 Electron 修前红态、修复、同一测试绿态、`--mutant old-task-split` 反例及修后回归均未完成。
- 测试已提供 `--summary`、`--revision`、`--mutant`；除沙箱受阻运行外，测试场景尚未验证。后续绿态还应核对任务菜单事前说明、IPC 无副作用拒绝、普通终端右/下分屏的几何位置与实际 pwd、返回任务及单 agent 的隔离。
- 本次没有宣称行为验收通过，也没有独立审查结论；执行主控应在候选完成后新开只读审查。
- `frontend-less-ai-tone` 的旧独立目录在本机两个指定位置未找到；已读整合技能 `frontend-production` 的 `references/look-and-copy.md`，其 `SOURCE.md` 明确该规则原样迁入。当前未改界面文案。
- 大夹具不入仓库；后续由执行主控按 T-088 归档，不覆盖或删除本次失败现场。

按派发要求停在沙箱外运行交接，收到有效红态后再修产品。
