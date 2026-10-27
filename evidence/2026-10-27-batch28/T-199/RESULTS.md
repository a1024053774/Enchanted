# T-199 结果：后台重启后，已消失的 worker 窗格报 “This API only accepts integers”

用户 2026-10-27：“修复新发现的问题”。发现经过：T-192 装进 /Applications 后，a1024053774.github.io 的 T-1 的 agy worker 窗格显示该报错，内容为空（`../T-192/ui/16-installed-github-io-T-1-pane-error.jpg`）。

## 根因

后台重启时，上一个后台留下的 worker/reviewer 窗格如果进程已确认消失，`registerGone`（`workbench/src/panes.ts`）把它登记成一个只有 shell pid 的替身（`pty: { pid }`），没有终端。`status()` 仍按 `{ cols: pane.pty.cols, rows: pane.pty.rows }` 返回尺寸，序列化成 `size: {}`。界面（`app/renderer.tsx`）把它当作 PTY 尺寸，只读窗格按此调用 xterm 的 `term.resize(undefined, undefined)`，xterm 抛出 “This API only accepts integers”，窗格停在报错。

用户真实后台只读核对：该 agy 窗格 `pane_status` 为 `lifecycle: interrupted`、`stopped: true`、`size: {}`，与上述一致。

## 改动

- `registerGone` 的替身显式标记 `gone: true`（与事件 `pane_gone_confirmed` 同名）；`status()` 对它返回 `size: null`，其他窗格照旧返回终端尺寸。
- 界面快照类型声明 `size` 可为 `null`。
- `tests/test_t124_controller_e2e.py` 的 `restart-working` 场景加两项检查：重启前活 worker 的尺寸是整数；重启后同一 worker 已消失，尺寸为 `null`。加已知坏实现 `gone-size-empty`。

## 证据

真实入口端到端（真实后台、socket、node-pty 里的真实 Claude Code，模型换成本地脚本化接口），命令：

```
cd workbench && python3 tests/test_t124_controller_e2e.py --end restart-working --summary <新路径> [--revision 606a5e193 | --mutant gone-size-empty]
```

| 运行 | 代码 | 结果 |
| --- | --- | --- |
| `e2e/green.json` | 工作树：`e2e/green-base-revision.txt`（606a5e193）加 `e2e/green-working-tree.diff` | PASS；重启前 160×45，重启后 `size: null`；T-124 原有检查全部通过 |
| `e2e/red-606a5e193.json` | 修前版本 606a5e193（测试按 `--revision` 从 git 取源码） | 退出 1，`gone_worker_has_no_size: size {}` |
| `e2e/mutant.json` | 变异 `gone-size-empty` | 退出 1，同一检查 |

界面（隔离状态库 `/private/tmp/t190/state`，打包的 Enchanted Test）：

- 修前：`ui/01-red-integer-error.jpg` 出现同样报错，`red-pane-status.json` 为 `size: {}`。
- 中间候选（`isSafeInteger` 写法）：`green-pane-status-gone.json` 为 `null`，`green-pane-status-live-shell.json` 是活终端 160×45，`ui/02`。
- 最终代码：构建记录见 `ui-final-build.txt`（基准版本、工作树 diff、包内 `panes.ts` 对应行）。`final-pane-status-gone-4.json` 为 `size: null`、`lifecycle: interrupted`，`ui/03-green-final-build.jpg` 无报错，窗格只读显示原输出。

`ui/01`、`ui/02` 那两次打包，日志没有记源码版本。打 `ui/01` 时工作树里 workbench 没有改动（打包前 `git status` 无输出，只有对话记录可查），所以这两张图只作现象记录；版本可核对的反事实以端到端三行为准。

收尾：两次测试 attempt 都经门禁撤销并回收（`cleanup-*.json`、`final-cleanup-*.json`），测试应用和构建目录已删除。

## 审查

- 第 1 轮（`review-01/REPORT.md`）结论“需修复”：
  - 证据没有绑定代码版本（P2），已补端到端三行和最终构建记录。
  - 界面类型没有声明 `null`（P3），已改。
  - 建议在替身上显式标记，不靠 `isSafeInteger` 推断，已改为 `gone`。

- 第 2 轮（`review-02/REPORT.md`）结论“可合并”：
  - 三点都已处理。`gone` 标记只出现在替身上，回收、归档、signal、写入、resize 在替身上都没有新问题。
  - 审查员自己重跑端到端，被它的沙箱拦住（`sandbox-exec: Operation not permitted`），在前置检查就失败了，没有跑到重启那一步，因此没有据此给出绿态结论。

## 顺带观察（未处理）

- 最终复验时，被测 Claude Code worker（haiku）在后台 SIGTERM 退出后仍在运行，SIGTERM 也没能结束它。因此每次重启都记为 `pane_gone_unconfirmed`；我用 SIGKILL 结束这个测试进程后，才得到 `pane_gone_confirmed`。第一次红态复现时同一流程下 worker 正常退出了。原因没有查。
- `pane_gone_unconfirmed` 的窗格走历史分支，本来就没有 size，不受本缺陷影响。
