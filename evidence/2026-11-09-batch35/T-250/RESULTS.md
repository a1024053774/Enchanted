# T-250 结果记录

由 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84` 在本会话里直接实现。用户 2026-11-09 说：

> 不用 codex 了,你自己做完这些部分结束

所以这次没有经门禁派 worker，也没有开 Codex 审查和 Terra 验收。门禁里的 `a2a+T-250-1` 任务认领后，worker 一行代码都没写（它的 worktree 与基线 `4164b43a8` 相同），之后随 T-269 的后台重启结束了。

## 命令

```bash
cd workbench/tests && python3 test_t250_changes_e2e.py --output <新目录> [--mutant groups|counts]
```

运行环境：Node 26.5.0，git 2.52.0。测试用这份源码构建工作台，以独立数据目录启动 Electron，后台用独立 state，hc core 也是私有的。

## 结果

| 运行 | 结果 | 文件 |
|---|---|---|
| 绿态（最终代码） | PASS，23 项 | `green-01/run.json` |
| 变异 groups：已暂存与未暂存互换 | FAIL，在“分组、状态码与 +/- 行数与 git 一致”这一项判红 | `mutant-groups/run.json` |
| 变异 counts：增删行数互换 | FAIL，判红的是同一项 | `mutant-counts/run.json` |

两个变异是在合并格式解析改动之前跑的，被改的那两行这次没有动。

绿态核对的内容：
- 分组、状态码与每个文件的 +/-，跟测试自己解析的 `git status --porcelain=v2`、`diff --numstat`、`diff --cached --numstat`、`diff --no-index` 一致；总计等于各文件之和。
- 图片有前后对比；Markdown 能预览。
- 基线自动识别为 `main`，合并基点与 `git merge-base HEAD main` 相同；文件列表与 `git diff <merge-base> --name-status` 相同；历史只列基线之后的提交。
- 写操作：
  - 暂存用按钮，取消暂存用 `u` 键；
  - 丢弃会先弹确认框：点取消，仓库字节不变；点确认，只恢复了 keep.txt；
  - 提交：有已暂存文件时，Enter 提交的正是这些文件，合并提交有两个父提交；没有已暂存文件时，先暂存全部改动再提交，提交后工作区干净。
  - 每次操作之后，面板都刷新到与 git 相同的状态。
- 审阅备注：在终端里运行 `cat > 文件`，在 diff 里用 CDP 鼠标真实拖选行、写好备注后发送。文件内容逐行等于路径、行号、引用行加备注。
- 门禁 worktree：绕过界面直接请求主进程暂存，被拒绝。
- 用户自己的 hc core 前后快照相同；夹具和构建槽用完已删除。

## 与票面的差异

- **输入记录**：普通终端（shell）的打字按设计不写 `user_inputs`，只有 agent 会话会写。测试改成核对两者记法相同：备注和在同一终端里打字一样，都没有写入（两边计数都是 0）。备注经 `term.paste` 走打字用的那条 `onData` → `window_input` 路径；发到 agent 会话时会照常记录，但这一点没有用真实 agent 会话测过。
- **语法高亮、Markdown**：依赖里没有现成的库，加依赖需要先问用户，所以用了按行的小型分词器和一个小型 Markdown 子集。没有处理跨行注释等情况。
- **未做**：Terra 独立验收（用户这次要求不再用 Codex）；Computer Use 人工点验。界面的截图只在本机看过，没有放进仓库。
