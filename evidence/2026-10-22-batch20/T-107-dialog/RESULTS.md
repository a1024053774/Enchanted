# T-107 “打开项目目录”系统对话框验证

- **来源**：
  - T-107 验收第 4 条后半句“新增项目目录与 T-106 的注册结果一致”。自 `3070bbe1a` 起，新增项目改为在侧栏“打开项目目录”。
  - 用户 2026-10-23 逐字：“验证一下“打开目录”系统对话框,如果没有要修复”；操作方式选“让 Codex worker 用 Computer Use”。
- **结论**：**PASS**。产品没有问题，不需要修复。
- **测试**：`workbench/tests/test_t107_open_directory_dialog.py`。真实后台，从源码构建的真实 Electron 窗口，真实 macOS 打开面板。命令见 `commands.sh`。

## 怎么做的

- **对话框由谁操作**：Codex（`codex-cli 0.163.0`，`codex exec -m gpt-6.1-sol -c model_reasoning_effort="high" --sandbox workspace-write`，完整 argv 在各次摘要的 `codex_argv`）。它经 Computer Use 只操作这个测试窗口和它弹出的对话框。
- **为什么在用户的 `~/.codex` 下运行**：Computer Use 的插件与授权装在那里。没有写用户配置；Codex 只是操作者，不是被测对象。
- **步骤**：
  1. 点“+”，在对话框里点“取消”；
  2. 再点“+”，用 Command+Shift+G 跳到夹具目录 `pick-me`，点“打开”。
- **判定不依赖 Codex 的自述**：
  - 每一步之后，脚本自己读后台的 `sidebar_snapshot` 和窗口的 DOM。
  - 期望来自 ticket 与 git：`pick-me` 比上游领先 1 个提交，按 `git rev-list --left-right --count HEAD...@{u}` 计算。

## 结果

| 运行 | 结果 | 说明 |
| --- | --- | --- |
| green-01 | PASS，6 项 | 测试的早期版本，还没有 `codex_finished_the_steps` |
| mutant-pick-ignored-01 | 失败 | 变异：主进程登记对话框的默认目录，不用用户选中的目录。Codex 看到工作台显示 `home` 和“不是 Git 仓库”后自己停下，没写 `opened`，测试因此中止。这次失败靠的是 Codex 的判断，不算脚本的反例证据；之后改成 Codex 停下时照样核对登记 |
| mutant-pick-ignored-02 | 失败 | 脚本自己失败在 `registers_the_picked_directory`：后台登记的是 `…/home` |
| green-02 | PASS，7 项 | 最终版本 |

green-02 核对了：
- 开始时没有项目；
- 取消后不登记任何项目，界面没有报错；
- 打开后，后台登记的正是 `pick-me` 的 realpath（项目 id 现场是 `pick-me`，测试不断言 id，只断言登记的目录）；
- 侧栏这一行被选中，提示里有完整路径；
- 第二行是 `main · ↑1 ↓0`，与 git 一致；
- Codex 走完了全部步骤，没有遇到权限请求。

截图（`01-before.png`、`02-after-cancel.png`、`03-opened.png`）、Codex 的事件流 `codex.jsonl` 和最后回复都在各夹具的 `out/` 里。夹具已归档，见 `fixtures.archive.json`。夹具里测试后台的操作凭据 `operator.json` 已由测试在结束时删除。

## 没覆盖

- 只验证了“取消”和“选一个 git 目录打开”。选非 git 目录、选已登记目录（后台返回 `created: false`）、在对话框里新建文件夹，都没有走真实对话框。
- 每次运行都会在用户的 `~/.codex/sessions` 里留下一次 Codex 会话记录，这是 Codex 的正常行为。

## 审查 01 的处理与复跑

独立审查 `review-01.md`（agy gemini-3.8-flash-high，只读）：PASS，有一条 P1、四条 P2、两条 P3。

| 发现 | 处理 |
| --- | --- |
| P1：取消一步可能空过：对话框没弹出、Codex 也照样写了 `cancelled`，检查仍会通过 | 已改。对话框打开期间“+”按钮是禁用的；脚本在等待时看到它变成禁用，才算对话框弹出过（`dialog_opened_before_cancel`） |
| P2：没有核对主区域切到这个项目 | 已改：页头的项目名与目录（`main_area_shows_the_project`） |
| P2：取消分支没有变异 | 已加 `cancel-registers-default`：取消时登记对话框的默认目录 |
| P2：Codex 早退后仍白等 20 秒，真实原因被超时掩盖 | 已改：Codex 停下后直接读登记现状；两个阶段都不因 Codex 停下而中止，都由脚本的检查判定 |
| P2：取消后固定等 2 秒 | 已改：等“+”恢复可用 |
| P3：RESULTS 写了“项目 id 是 `pick-me`”，测试没断言 | 已改措辞，见上 |
| P3：清理时只结束了 Codex 本身，没结束它的进程组 | 已改：用 `os.killpg` |

复跑用最终版本，一次跑一个（共用一块屏幕）：

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green-03 | PASS，9 项 | — |
| mutant-pick-ignored-03 | 失败 | `registers_the_picked_directory`：登记的是 `…/home` |
| mutant-cancel-registers-default-01 | 失败 | `cancel_registers_nothing`：取消后登记了 `…/home` |

两个变异里 Codex 都看到界面异常、自己停下了；判定来自脚本的检查，不来自 Codex。夹具见 `fixtures-02.archive.json`。

结论维持 **PASS**：界面经系统对话框新增的项目与后台登记一致，取消不登记、不报错。
