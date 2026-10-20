# T-108 独立审查 F1 修复（2026-10-20）

**本地回归 PASS；交付 INCOMPLETE，待主控执行提交脚本及独立复审。** 起点为 `afcc78b0d856680491f0e99410b7ff9acec54dab`。本次模型调用、供应商调用均为 0；未重跑真实回合。原真实入口的原件仍由独立审查报告说明，本报告不将其冒充为修订后的新运行。

目标是修复缺少 `tool_name` 的工具 hook 被静默丢弃、侧栏仍显示“运行中”的 F1。只改工具 hook 的入口校验和正式合同；不改门禁、屏幕识别、版本入口或界面。沿用 `native_question_unverified` 追加事实。

`questionFromHook` 现在先核对原有根来源、当前回合以及工具事件公共字段，再判断是否为提问工具。完整且无关的合法工具返回 null，入口照旧忽略；字段不全则由现有 catch 记录未知事实并抛出拒绝。原 session、子 agent、prompt/turn、cwd、transcript 与运行身份检查保留。`Panes.signal` 的工具分类提前返回已删除，正常问题、确认与取消路径未另造实现。

正式测试新增三种工具事件缺 `tool_name`、空值/非法类型、缺工具 ID、缺工具输入的反例，以及合法无关工具仍忽略的正例；经实际 `Panes.signal → SQLite → agentState` 观察未知状态和追加事实。另覆盖 Codex 缺工具名，保留过期/异会话拒绝、重复作答和输入变化拒绝。PTY 与运行身份仍由夹具提供，不据此声称新增了活 CLI 或 OS 边界证明。

修前先只改正式测试，产品源码仍为原候选。命令退出 1，`/private/tmp/t108-f1-red-01.json` 的业务断言为 `running != unknown`，不是依赖或夹具失败。修后同一测试退出 0；最终摘要 `/private/tmp/t108-f1-green-02.json`，15 项 PASS。二者及相关检查摘要保存在 [f1-local.summary.json](f1-local.summary.json)。

精确命令如下；再次执行需换一个不存在的摘要文件名，测试会拒绝覆盖旧证据。

```sh
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t108_questions.mjs /private/tmp/t108-f1-red-01.json
# 产品修复后，同一正式测试：
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t108_questions.mjs /private/tmp/t108-f1-green-02.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t108_hook_replay.mjs --samples evidence/2026-10-20-batch18/T-108/native-hook-samples.json --summary /private/tmp/t108-f1-codex-01.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /private/tmp/t108-f1-ipc-01.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t107_sidebar.mjs /private/tmp/t108-f1-sidebar-01.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES=/Users/luckye/Documents/Code/a2a-wt-t108/workbench/node_modules node --experimental-vm-modules /private/tmp/t108-review-01-ja7ea3bs/candidate/workbench/tests/review_t107_daemon_readonly.mjs /private/tmp/t108-f1-readonly-01.json /Users/luckye/Documents/Code/a2a-wt-t108 readonly
```

上述回放、IPC、侧栏和实际 daemon 只读检查均 PASS。最后一项使用 reviewer 已保留的 harness，只将依赖链接改为普通复制，产品源码取本 worktree 当前版本；依赖取本 worktree，自始至终不链接主仓库依赖。它核对 SQLite 表和 trace 零写入，`cleanup_complete=true`。未更改 T-107 测试文件或放宽断言。

提交由主控执行 `zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-03.sh`。脚本要求 HEAD 仍为上述原候选、索引无已有暂存内容，逐项 `git add --sparse`，由既有 hook 加尾注；不包含 reviewer 的两个未跟踪文件，不 submit、不 push。本轮未改 `sidebar.ts`、`renderer.tsx`，T-109 冲突清单仍见 [CONFLICT-LINES.md](CONFLICT-LINES.md)。

主控提交后至少重跑正式缺字段合同（新摘要例如 `/private/tmp/t108-f1-recheck-01.json`），并按上表重核相关合同；独立复审由主控安排。无需再跑真实模型回合。项目地图检查仍为稀疏检出已有的 8 个缺失链接、0 stale，不将其记为 0 问题。
