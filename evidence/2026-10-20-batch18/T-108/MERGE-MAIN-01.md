# T-108 先合入 main（2026-10-20，主控 #26）

**INCOMPLETE：脚本已准备，实际 merge 与合并提交待主控沙箱外执行。** 当前 `exec/t108` 为 `93fe03dcd54535bc3b48d58e30a6244bf697fca1`；本次 main 为 `12190c32f2cee01dcef3654b2e90860887eabee6`，包含 T-111 的 `e00f4d6de`，以及 T-109 的层级功能。共同起点为 `6411bdff8482ba47da207efa6a295a12666222aa`。

本次只准备合并，不提前在未合入 main 的产品代码上做第三轮状态修复。Git 元数据在 worker 沙箱内只读，按派发约定交主控执行：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-MERGE-MAIN-01.sh
```

脚本执行真正的 `git merge --no-commit main`，仅用本次命令的 `-c merge.conflictStyle=merge` 固定可审查的冲突格式；不是 rebase，不写 Git 配置。HEAD/main 改变、索引或受控文件已有修改、存在未完成 merge、冲突集合或内容不符时停下并保留现场，不 reset、abort 或丢弃未跟踪的审查文件。

只读三方预览发现两个冲突文件：

- panes.ts：保留 main 的 AsyncLocalStorage 与 T-108 的提问模块 import；其他两边改动由 Git 合并。
- test_t091_pane_ipc.mjs：默认采用显式 `questions-flow` 合同，同时核对 answer、flow、层级返回值和原有拒绝项。保留原历史合同选项，不删任何业务拒绝或错误实现检查。其他 main/preload/renderer、父 launch、流程页及 README 变动由 Git 正常合并。

固定版本的冲突块处理见 `resolve_main_merge_01.py`，两文件全部校验完成后才写入。只读预览的 main/preload 与合并后的 IPC 合同已在 /tmp 运行，结果 PASS，见 [merge-main-01.ipc-preview.summary.json](merge-main-01.ipc-preview.summary.json)：22 个 handler、23 个 bridge 名称，answer 与 flow 都覆盖；旧拒绝与变异检查保留。这个预览不是实际分支合并，也不是完整产品验收。

实际 merge 脚本在提交前运行 T-108 原合同、组合 IPC、T-107 侧栏、T-109 层级与 T-111 流程合同。摘要写入新建的 `/private/tmp/t108-main-merge-01-*`，打印准确路径；失败则保留 merge 状态和摘要，停止提交。通过后以 `git add --sparse` 暂存冲突处理和本次脚本资料，生成两个 parent 的合并提交，既有 hook 自动加尾注。不 submit、不 push，不调用模型或读取登录凭据。

收到合并结果后，再在合并后的真实分支实现统一的当前回合可信度，并把公共字段缺失和权限等待矩阵纳入 test_t108_questions.mjs 默认入口；届时另交修复提交脚本。第三轮 NO_GO 尚未修复，不把合并预览 PASS 上调为本票通过。

结束的 project_map status 为 rc=1、8 个既有稀疏检出缺失链接、0 stale；原文保存为 project-map-merge-prep-01.txt。脚本 zsh 语法、resolver Python 3.9 AST、UTF-8 与 git diff --check 均通过。
